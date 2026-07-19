from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.commerce.models import Order, Payment, Product, Subscription, UserAccess
from apps.commerce.providers.registry import get_payment_provider
from apps.commerce.selectors import get_order_for_user, get_tariff_rank, get_user_subscription, subscription_can_renew
from apps.commerce.utils import activity_duration
from apps.partner.engine import BonusEngine
from apps.partner.services import PartnerActivationService
from apps.users.models import Notification, User


class OrderValidationError(ValueError):
    pass


class OrderService:
    WALLET_PRODUCT_TYPES = {
        Product.TYPE_TOKENS,
        Product.TYPE_TARIFF,
        Product.TYPE_SUBSCRIPTION,
    }

    @staticmethod
    @transaction.atomic
    def create_order(user: User, product_slug: str, order_type: str) -> Order:
        product = Product.objects.select_related("tariff_plan").get(
            slug=product_slug,
            is_active=True,
        )
        subscription = get_user_subscription(user.id)
        OrderService._validate(user, product, order_type, subscription)

        Order.objects.filter(
            user=user,
            product=product,
            status=Order.STATUS_PENDING,
        ).update(status=Order.STATUS_EXPIRED)

        previous_tariff_id = None
        if order_type == Order.TYPE_UPGRADE and subscription:
            previous_tariff_id = subscription.tariff_id

        wallet_only = getattr(settings, "STORE_WALLET_ONLY", True)
        if product.type in OrderService.WALLET_PRODUCT_TYPES:
            if OrderService._wallet_can_cover(user, product.price_usd):
                order = Order.objects.create(
                    user=user,
                    product=product,
                    amount_usd=product.price_usd,
                    status=Order.STATUS_PENDING,
                    order_type=order_type,
                    previous_tariff_id=previous_tariff_id,
                )
                return OrderService._pay_with_wallet(user, order)
            if wallet_only:
                from apps.wallet.services import WalletUpdater

                available = WalletUpdater.refresh(user).available_usd
                raise OrderValidationError(
                    f"Недостаточно средств на балансе: нужно ${product.price_usd}, "
                    f"доступно ${available}"
                )

        order = Order.objects.create(
            user=user,
            product=product,
            amount_usd=product.price_usd,
            status=Order.STATUS_PENDING,
            order_type=order_type,
            previous_tariff_id=previous_tariff_id,
        )

        provider = get_payment_provider()
        intent = provider.create_invoice(
            order=order,
            amount_usd=order.amount_usd,
            description=f"ReRise — {product.name}",
        )

        Payment.objects.create(
            order=order,
            provider=provider.provider_name,
            external_id=intent.external_id,
            amount_usd=intent.amount_usd,
            currency_crypto=intent.asset,
            status=Payment.STATUS_PENDING,
            payment_url=intent.payment_url,
            instructions=intent.instructions,
            expires_at=intent.expires_at,
        )
        return get_order_for_user(order.id, user.id)

    @staticmethod
    def _wallet_can_cover(user: User, amount) -> bool:
        from apps.wallet.services import WalletUpdater

        balance = WalletUpdater.refresh(user)
        return balance.available_usd >= amount

    @staticmethod
    def _pay_with_wallet(user: User, order: Order) -> Order:
        from decimal import Decimal

        from apps.ledger.services import LedgerError
        from apps.wallet.services import WalletUpdater

        balance = WalletUpdater.refresh(user)
        amount = Decimal(str(order.amount_usd))
        if balance.available_usd < amount:
            raise OrderValidationError(
                f"Недостаточно средств на балансе: нужно ${amount}, доступно ${balance.available_usd}"
            )

        payment = Payment.objects.create(
            order=order,
            provider="wallet",
            external_id=f"wallet-{order.pk}",
            amount_usd=amount,
            status=Payment.STATUS_PAID,
            payment_url=None,
            instructions="Оплачено с баланса кошелька",
            paid_at=timezone.now(),
        )

        try:
            OrderService._debit_store_purchase(user, order, payment_id=payment.pk)
        except LedgerError as exc:
            raise OrderValidationError(str(exc)) from exc

        OrderFulfillmentService.fulfill(order)
        return get_order_for_user(order.id, user.id)

    @staticmethod
    def _debit_store_purchase(user: User, order: Order, *, payment_id: int | None = None) -> None:
        """Идемпотентное списание стоимости заказа с кошелька (с блокировкой баланса)."""
        from decimal import Decimal

        from apps.ledger.constants import ENTRY_TYPE_STORE_PURCHASE
        from apps.ledger.models import Entry
        from apps.ledger.services import LedgerError, LedgerWriter
        from apps.wallet.models import Balance
        from apps.wallet.services import WalletUpdater

        key = f"store-purchase:{order.pk}"
        if Entry.objects.filter(idempotency_key=key).exists():
            WalletUpdater.refresh(user)
            return

        balance, _ = Balance.objects.select_for_update().get_or_create(user=user)
        WalletUpdater.refresh(user, locked_balance=balance)
        amount = Decimal(str(order.amount_usd))
        if balance.available_usd < amount:
            raise LedgerError(
                f"Недостаточно средств на балансе: нужно ${amount}, доступно ${balance.available_usd}"
            )

        LedgerWriter.debit(
            user,
            ENTRY_TYPE_STORE_PURCHASE,
            amount,
            source=order,
            metadata={
                "product_slug": order.product.slug,
                "product_name": order.product.name,
                "payment_id": payment_id,
            },
            idempotency_key=key,
            description=f"Покупка: {order.product.name}",
        )
        WalletUpdater.refresh(user, locked_balance=balance)

    @staticmethod
    def _validate(
        user: User,
        product: Product,
        order_type: str,
        subscription: Subscription | None,
    ) -> None:
        has_active_subscription = bool(subscription and subscription.is_active)

        if order_type == Order.TYPE_PURCHASE:
            if product.type == Product.TYPE_TARIFF and has_active_subscription:
                raise OrderValidationError(
                    "У вас уже есть активный тариф. Используйте upgrade или renewal."
                )
            return

        if order_type == Order.TYPE_UPGRADE:
            if product.type != Product.TYPE_TARIFF:
                raise OrderValidationError("Upgrade доступен только для тарифов")
            if not subscription:
                raise OrderValidationError("Нет активного тарифа для апгрейда")
            current_rank = get_tariff_rank(subscription.tariff_id)
            target_rank = get_tariff_rank(product.slug)
            if target_rank <= current_rank:
                raise OrderValidationError("Нельзя апгрейдиться на этот тариф")
            return

        if order_type == Order.TYPE_RENEWAL:
            if product.type != Product.TYPE_SUBSCRIPTION:
                raise OrderValidationError("Продление доступно только для подписки")
            if not subscription:
                raise OrderValidationError("Нет тарифа для продления")
            if not subscription_can_renew(subscription):
                raise OrderValidationError(
                    "Продление пока недоступно. Окно открывается ближе к окончанию активности."
                )
            return

        raise OrderValidationError(f"Неизвестный тип заказа: {order_type}")


class AccessService:
    @staticmethod
    def _create_tariff_access(user: User, product: Product, order: Order) -> UserAccess:
        return UserAccess.objects.create(
            user=user,
            product=product,
            granted_at=timezone.now(),
            expires_at=None,
            is_active=True,
            source_order=order,
        )

    @staticmethod
    @transaction.atomic
    def grant_tariff(user: User, product: Product, order: Order) -> UserAccess:
        access = AccessService._create_tariff_access(user, product, order)
        months = product.tariff_plan.included_months

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                "tariff_id": product.slug,
                "active_until": timezone.now() + activity_duration(months),
                "last_renewal_at": None,
            },
        )
        return access

    @staticmethod
    @transaction.atomic
    def upgrade_tariff(user: User, product: Product, order: Order) -> UserAccess:
        UserAccess.objects.filter(
            user=user,
            product__type=Product.TYPE_TARIFF,
            is_active=True,
        ).update(is_active=False)

        access = AccessService._create_tariff_access(user, product, order)

        subscription = Subscription.objects.select_for_update().get(user=user)
        subscription.tariff_id = product.slug
        subscription.save(update_fields=["tariff_id", "updated_at"])
        return access

    @staticmethod
    @transaction.atomic
    def extend_subscription(user: User, months: int = 1) -> Subscription:
        subscription = Subscription.objects.select_for_update().get(user=user)
        base = max(subscription.active_until, timezone.now())
        subscription.active_until = base + activity_duration(months)
        subscription.last_renewal_at = timezone.now()
        subscription.save(update_fields=["active_until", "last_renewal_at", "updated_at"])
        return subscription


class OrderFulfillmentService:
    @staticmethod
    @transaction.atomic
    def fulfill(order: Order) -> Order:
        order = (
            Order.objects.select_for_update()
            .select_related("product", "user")
            .get(pk=order.pk)
        )

        if order.status == Order.STATUS_PAID:
            return order

        order.status = Order.STATUS_PAID
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "paid_at", "updated_at"])

        handlers = {
            Order.TYPE_PURCHASE: OrderFulfillmentService._fulfill_purchase,
            Order.TYPE_UPGRADE: OrderFulfillmentService._fulfill_upgrade,
            Order.TYPE_RENEWAL: OrderFulfillmentService._fulfill_renewal,
        }
        handler = handlers.get(order.order_type)
        if handler:
            handler(order)

        return order

    @staticmethod
    def _fulfill_purchase(order: Order) -> None:
        product = order.product
        user = order.user

        if product.type == Product.TYPE_TARIFF:
            AccessService.grant_tariff(user, product, order)
            OrderFulfillmentService._credit_tariff_tokens(user, product, order)
            PartnerActivationService.on_tariff_purchase(user, product, order)
            BonusEngine.process_purchase(order)
            OrderFulfillmentService._notify(
                user,
                title="Тариф активирован",
                body=f"Доступ к тарифу {product.name} успешно выдан.",
                metadata={"order_id": order.id, "product_slug": product.slug},
            )
        elif product.type == Product.TYPE_TOKENS:
            OrderFulfillmentService._credit_token_pack(user, product, order)
            OrderFulfillmentService._notify(
                user,
                title="Покупка токенов",
                body=f"Начислено токенов по заказу {product.name}.",
                metadata={"order_id": order.id, "product_slug": product.slug},
            )

    @staticmethod
    def _fulfill_upgrade(order: Order) -> None:
        AccessService.upgrade_tariff(order.user, order.product, order)
        PartnerActivationService.on_tariff_upgrade(order.user, order.product, order)
        BonusEngine.process_upgrade(order)
        OrderFulfillmentService._notify(
            order.user,
            title="Тариф обновлён",
            body=f"Ваш тариф обновлён до {order.product.name}.",
            metadata={
                "order_id": order.id,
                "product_slug": order.product.slug,
                "previous_tariff_id": order.previous_tariff_id,
            },
        )

    @staticmethod
    def _fulfill_renewal(order: Order) -> None:
        months = order.product.metadata.get("months", 1)
        AccessService.extend_subscription(order.user, months=months)
        PartnerActivationService.on_renewal(order.user, order)
        BonusEngine.process_renewal(order)
        OrderFulfillmentService._notify(
            order.user,
            title="Подписка продлена",
            body=f"Партнёрская активность продлена на {months} мес.",
            metadata={"order_id": order.id, "months": months},
        )

    @staticmethod
    def _credit_tariff_tokens(user, product, order) -> None:
        from apps.ibox.constants import REASON_TARIFF
        from apps.ibox.tokens import TokenService

        amount = getattr(getattr(product, "tariff_plan", None), "initial_tokens", 0) or 0
        if amount > 0:
            TokenService.credit(user, amount, reason=REASON_TARIFF, order=order)

    @staticmethod
    def _credit_token_pack(user, product, order) -> None:
        from apps.ibox.constants import REASON_PURCHASE
        from apps.ibox.tokens import TokenService

        amount = int((product.metadata or {}).get("amount") or 0)
        if amount > 0:
            TokenService.credit(user, amount, reason=REASON_PURCHASE, order=order)

    @staticmethod
    def _notify(user: User, *, title: str, body: str, metadata: dict) -> None:
        Notification.objects.create(
            user=user,
            type="access",
            title=title,
            body=body,
            metadata=metadata,
        )


class PaymentConfirmationService:
    @staticmethod
    @transaction.atomic
    def confirm(payment: Payment, *, paid_at=None) -> Order:
        payment = Payment.objects.select_for_update().select_related("order", "order__product", "order__user").get(
            pk=payment.pk
        )
        if payment.status == Payment.STATUS_PAID:
            return payment.order

        if payment.order.status == Order.STATUS_PAID:
            payment.status = Payment.STATUS_PAID
            payment.paid_at = payment.paid_at or paid_at or timezone.now()
            payment.save(update_fields=["status", "paid_at", "updated_at"])
            return payment.order

        # Manual/crypto confirm = внешняя оплата. Списание с кошелька только
        # через create_order → provider=wallet. Иначе двойное списание.
        payment.status = Payment.STATUS_PAID
        payment.paid_at = paid_at or timezone.now()
        payment.save(update_fields=["status", "paid_at", "updated_at"])
        return OrderFulfillmentService.fulfill(payment.order)
