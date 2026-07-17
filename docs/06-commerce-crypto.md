# ReRise — Этап 6: Commerce + Crypto

**Статус:** черновик на утверждение  
**Версия:** 0.1 · 15.07.2026

---

## 1. Обзор

Commerce-модуль отвечает за:

- каталог продуктов (тарифы, подписка, токены);
- создание заказов;
- приём оплаты через крипто-провайдера;
- выдачу доступов и запуск Financial Engine.

**Принцип:** бэкенд не привязан к конкретному провайдеру. CryptoBot — первая реализация, но можно подключить другой.

---

## 2. Типы продуктов и заказов

### Продукты (MVP)

| product.type | slug | Цена | order_type |
|---|---|---:|---|
| tariff | rise | $90 | purchase |
| tariff | rise-pro | $300 | purchase |
| tariff | rise-pro-max | $900 | purchase |
| subscription | subscription | $30 | renewal |
| tokens | tokens-1000 | TBD | purchase |
| tokens | tokens-5000 | TBD | purchase |

### Типы заказов

| order_type | Когда | Что происходит после оплаты |
|---|---|---|
| `purchase` | Первая покупка тарифа или токенов | Тариф + 1 мес + токены + PV + бонусы |
| `upgrade` | Повышение тарифа | Разница PV/бонусов, смена тарифа |
| `renewal` | Продление $30 | +1 мес активности + $9 спонсору + 9 PV |

### Правила

- Один `pending` заказ на пользователя на один продукт (не плодить дубликаты).
- Заказ `expired` через 60 минут без оплаты (настраиваемо).
- Повторная оплата того же `external_id` — идемпотентно (не дублировать side effects).

---

## 3. Жизненный цикл заказа

```
                    ┌──────────┐
         create     │ pending  │
        ──────────► │          │
                    └────┬─────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
       ┌─────────┐ ┌─────────┐ ┌───────────┐
       │  paid   │ │ expired │ │ cancelled │
       └────┬────┘ └─────────┘ └───────────┘
            │
            ▼
   OrderFulfillmentService
   (access + tokens + BonusEngine)
```

### Статусы `commerce_order`

| status | Описание |
|---|---|
| `pending` | Создан, ждёт оплату |
| `paid` | Оплачен, fulfillment выполнен |
| `expired` | Не оплачен в срок |
| `cancelled` | Отменён админом / fraud |

### Статусы `commerce_payment`

| status | Описание |
|---|---|
| `pending` | Invoice создан |
| `paid` | Webhook подтвердил |
| `expired` | Invoice истёк у провайдера |
| `failed` | Ошибка |

---

## 4. Абстракция платёжного провайдера

### Интерфейс (Python Protocol)

```python
# commerce/providers/base.py

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass
class PaymentIntent:
    external_id: str          # invoice_id провайдера
    payment_url: str          # ссылка для пользователя
    amount_usd: Decimal
    asset: str                # USDT
    expires_at: datetime


@dataclass
class PaymentEvent:
    external_id: str
    status: str               # paid / expired
    paid_at: datetime | None
    raw_payload: dict


class PaymentProvider(Protocol):
    provider_name: str

    def create_invoice(
        self,
        order: Order,
        amount_usd: Decimal,
        description: str,
    ) -> PaymentIntent: ...

    def verify_webhook(
        self,
        raw_body: bytes,
        headers: dict,
    ) -> PaymentEvent: ...

    def get_invoice_status(self, external_id: str) -> str: ...
```

### Реализации

| Класс | Назначение |
|---|---|
| `CryptoBotProvider` | Продакшн (Telegram Crypto Pay API) |
| `ManualCryptoProvider` | Dev/staging: админ подтверждает вручную |
| `MockProvider` | Тесты: мгновенная «оплата» |

Выбор через `settings.PAYMENT_PROVIDER`:

```python
PAYMENT_PROVIDER=cryptobot   # production
PAYMENT_PROVIDER=manual        # dev
PAYMENT_PROVIDER=mock          # tests
```

---

## 5. CryptoBot — первая реализация

### Настройки (env / VPS)

```env
CRYPTOBOT_API_TOKEN=xxx:xxx
CRYPTOBOT_TESTNET=false          # true для тестов
CRYPTOBOT_WEBHOOK_SECRET_PATH=wh_abc123   # секретный сегмент URL
CRYPTOBOT_ASSET=USDT
CRYPTOBOT_INVOICE_TTL_MINUTES=60
```

### Создание invoice

```python
# commerce/providers/cryptobot.py

def create_invoice(self, order, amount_usd, description):
    invoice = client.create_invoice(
        asset="USDT",
        amount=str(amount_usd),
        description=description,
        payload=json.dumps({"order_id": order.id}),
        paid_btn_name="callback",
        paid_btn_url=f"https://rerise.app/market?order={order.id}",
        expires_in=3600,
    )
    return PaymentIntent(
        external_id=str(invoice.invoice_id),
        payment_url=invoice.bot_invoice_url or invoice.pay_url,
        amount_usd=amount_usd,
        asset="USDT",
        expires_at=invoice.expiration_date,
    )
```

### Webhook

**URL на VPS:** `https://api.rerise.app/api/v1/store/webhook/cryptobot/{CRYPTOBOT_WEBHOOK_SECRET_PATH}/`

**Событие:** `invoice_paid`

**Верификация:** заголовок `crypto-pay-api-signature` = HMAC-SHA256(SHA256(api_token), raw_body)

```python
def verify_webhook(self, raw_body: bytes, headers: dict) -> PaymentEvent:
    if not check_signature(self.api_token, raw_body.decode(), headers):
        raise InvalidSignatureError()

    data = json.loads(raw_body)
    if data["update_type"] != "invoice_paid":
        raise IgnoredWebhookError()

    payload = data["payload"]
    return PaymentEvent(
        external_id=str(payload["invoice_id"]),
        status="paid",
        paid_at=parse_dt(payload.get("paid_at")),
        raw_payload=data,
    )
```

### Безопасность webhook

| Мера | Реализация |
|---|---|
| Подпись | `check_signature` на raw body |
| Replay protection | Redis: `webhook:seen:{invoice_id}` TTL 24h |
| Secret path | Случайный сегмент в URL |
| HTTPS | Nginx + Let's Encrypt на VPS |
| Быстрый ответ | 200 OK сразу, fulfillment в Celery |

---

## 6. OrderService — создание заказа

```python
# commerce/services/order_service.py

class OrderService:

    @transaction.atomic
    def create_order(self, user, product_slug: str, order_type: str) -> Order:
        product = Product.objects.get(slug=product_slug, is_active=True)

        # Валидация
        self._validate(user, product, order_type)

        # Отменить старые pending на тот же продукт
        Order.objects.filter(
            user=user, product=product, status="pending"
        ).update(status="expired")

        order = Order.objects.create(
            user=user,
            product=product,
            amount_usd=product.price_usd,
            status="pending",
            order_type=order_type,
            previous_tariff_id=user.partner.tariff_id if order_type == "upgrade" else None,
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
            status="pending",
            payment_url=intent.payment_url,
        )

        return order
```

### Валидация

| order_type | Проверка |
|---|---|
| `purchase` (tariff) | Нет активного тарифа ИЛИ 12м+ без тарифа |
| `upgrade` | Есть тариф ниже целевого |
| `renewal` | Есть тариф, активность истекает или истекла |
| `purchase` (tokens) | Любой авторизованный |

---

## 7. OrderFulfillmentService — после оплаты

```python
# commerce/services/fulfillment_service.py

class OrderFulfillmentService:

    @transaction.atomic
    def fulfill(self, order: Order):
        key = f"order:{order.id}:paid"
        if IdempotencyStore.exists(key):
            return
        IdempotencyStore.set(key)

        order.status = "paid"
        order.paid_at = now()
        order.save()

        if order.order_type == "purchase":
            self._fulfill_purchase(order)
        elif order.order_type == "upgrade":
            self._fulfill_upgrade(order)
        elif order.order_type == "renewal":
            self._fulfill_renewal(order)

        AnalyticsEvent.track(order.user, "order_paid", {"product": order.product.slug})


    def _fulfill_purchase(self, order):
        product = order.product
        user = order.user

        if product.type == "tariff":
            ActivityService.grant_initial_month(user.partner)
            AccessService.grant_tariff(user, product)
            TokenService.credit_initial(user, product)
            BinaryPlacementService.place_if_needed(user.partner)
            BonusEngine.on_tariff_purchase(user.partner, order)

        elif product.type == "tokens":
            TokenService.credit_pack(user, product)
            # PV за токены — TBD, пока без PV


    def _fulfill_upgrade(self, order):
        old_tariff = order.previous_tariff_id
        new_tariff = order.product.slug
        user.partner.tariff_id = new_tariff
        user.partner.save()
        AccessService.upgrade(user, new_tariff)
        BonusEngine.on_tariff_upgrade(user.partner, order, old_tariff, new_tariff)


    def _fulfill_renewal(self, order):
        ActivityService.extend(user.partner, months=1)
        BonusEngine.on_renewal(user.partner, order)
```

---

## 8. Webhook handler (Django view)

```python
# commerce/views/webhook.py

@csrf_exempt
def cryptobot_webhook(request, secret_path):
    if secret_path != settings.CRYPTOBOT_WEBHOOK_SECRET_PATH:
        return HttpResponse(status=404)

    raw_body = request.body
    provider = CryptoBotProvider()

    try:
        event = provider.verify_webhook(raw_body, request.headers)
    except InvalidSignatureError:
        return HttpResponse(status=400)
    except IgnoredWebhookError:
        return HttpResponse("ok")

    payment = Payment.objects.filter(
        external_id=event.external_id,
        status="pending",
    ).select_related("order").first()

    if not payment:
        return HttpResponse("ok")

    payment.status = "paid"
    payment.paid_at = event.paid_at
    payment.webhook_payload = event.raw_payload
    payment.save()

    # Тяжёлую работу — в Celery
    fulfill_order.delay(payment.order_id)

    return HttpResponse("ok")
```

```python
# commerce/tasks.py

@shared_task
def fulfill_order(order_id):
    order = Order.objects.get(id=order_id)
    if order.status == "paid":
        return  # уже обработан
    OrderFulfillmentService().fulfill(order)
```

---

## 9. Polling (запасной вариант)

Если webhook не дошёл — фронт поллит `GET /store/orders/{id}`.

Бэкенд при polling может опросить провайдера:

```python
def sync_payment_status(order):
    payment = order.payments.last()
    if payment.status != "pending":
        return

    provider = get_payment_provider()
    status = provider.get_invoice_status(payment.external_id)
    if status == "paid":
        fulfill_order.delay(order.id)
```

Celery beat: каждые 5 минут проверять `pending` заказы старше 2 минут.

---

## 10. Выдача доступов

### AccessService

```python
def grant_tariff(user, product):
    UserAccess.objects.create(
        user=user,
        product=product,
        granted_at=now(),
        expires_at=None,  # тариф бессрочен, активность отдельно
        source_order_id=order.id,
    )
    Subscription.objects.update_or_create(
        user=user,
        defaults={
            "tariff_id": product.slug,
            "active_until": now() + timedelta(days=30),
        },
    )
```

### Что открывается по тарифу (предварительно)

| Доступ | Rise | Rise Pro | Rise Pro Max |
|---|---|---|---|
| iBox (базовый) | ✅ огранич. | ✅ полный | ✅ полный |
| Academy (базовые) | ✅ 2–5 | ✅ основная | ✅ всё |
| Materials | ❌ | ✅ | ✅ |
| CRM | ❌ | ✅ Lite | ✅ полная |
| Partner OS | ✅ Lite | ✅ | ✅ |
| Токены стартовые | TBD | TBD | TBD |

Точные лимиты — в `commerce_tariff_plan` + `SystemConfig`. **Не хардкодить в коде.**

---

## 11. Manual Provider (для разработки)

Пока CryptoBot не подключён — ручное подтверждение через Django Admin:

```
Admin → Payments → [Confirm Payment]
  → fulfill_order(order_id)
```

Или API (только staff):

```
POST /admin/orders/{id}/confirm-payment
```

Это позволяет тестировать весь Financial Engine без реальных денег.

---

## 12. Вывод USDT (Wallet)

Отдельный от приёма платежей, но в том же домене `wallet`.

### MVP: ручной вывод

```
1. Пользователь: POST /wallet/withdraw ($100+, USDT address)
2. WithdrawalRequest status = pending
3. Админ в Django Admin: Approve → Mark Paid (вводит tx_hash)
4. LedgerWriter.debit(user, "withdrawal", amount)
5. WalletUpdater.refresh(user)
```

### Позже: автоматический вывод

- Интеграция с CryptoBot Transfer API или другим сервисом
- KYC, 2FA, лимиты — по `marketingplan.md` раздел V.6

---

## 13. Структура Django-приложения commerce

```
commerce/
├── models/
│   ├── product.py
│   ├── order.py
│   ├── payment.py
│   ├── user_access.py
│   └── subscription.py
├── providers/
│   ├── base.py
│   ├── cryptobot.py
│   ├── manual.py
│   └── mock.py
├── services/
│   ├── order_service.py
│   ├── fulfillment_service.py
│   └── access_service.py
├── views/
│   ├── store.py          # API для фронта
│   └── webhook.py
├── tasks.py
├── admin.py
└── tests/
    ├── test_order_service.py
    ├── test_fulfillment.py
    └── test_cryptobot_webhook.py
```

---

## 14. Тест-кейсы Commerce

| ID | Сценарий | Ожидание |
|---|---|---|
| TC-ORD-01 | Создать заказ Rise | pending + payment_url |
| TC-ORD-02 | Два pending на один продукт | старый → expired |
| TC-ORD-03 | Webhook paid | order paid + fulfillment |
| TC-ORD-04 | Повторный webhook | идемпотентно, без дублей |
| TC-ORD-05 | Невалидная подпись | 400 |
| TC-ORD-06 | Upgrade Rise→Pro | previous_tariff сохранён |
| TC-ORD-07 | Renewal без тарифа | 422 ошибка |
| TC-ORD-08 | Manual confirm (dev) | fulfillment срабатывает |
| TC-ORD-09 | Order expired (60 мин) | status expired |
| TC-WD-01 | Withdraw < $100 | 422 |
| TC-WD-01 | Withdraw > balance | 422 |

---

## 15. Открытые вопросы

| # | Вопрос | Влияние |
|---|---|---|
| 1 | Провайдер: CryptoBot или другой? | `cryptobot.py` |
| 2 | Сеть USDT: TRC20 / ERC20? | withdrawal, invoice |
| 3 | Цены пакетов токенов | products seed |
| 4 | PV за покупку токенов | fulfillment |
| 5 | Комиссия провайдера — кто платит? | amount в invoice |

---

## 16. Следующий этап

**Этап 7:** План реализации по спринтам.
