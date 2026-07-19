from decimal import Decimal

from django.core.management import call_command
from django.db.models import Sum
from django.test import TestCase
from rest_framework.test import APIClient

from apps.commerce.models import Order
from apps.ledger.constants import (
    ENTRY_TYPE_BINARY_BONUS,
    ENTRY_TYPE_BINARY_COLLAPSE,
    ENTRY_TYPE_FAST_START_BONUS,
    ENTRY_TYPE_MATCHING_BONUS,
    ENTRY_TYPE_PERSONAL_BONUS,
    ENTRY_TYPE_PURCHASE_PV,
    ENTRY_TYPE_RENEWAL_BONUS,
    ENTRY_TYPE_STATUS_PREMIUM,
)
from apps.ledger.models import Entry
from apps.partner.engine import (
    BinaryCollapseService,
    MatchingBonusService,
    QualificationWeekService,
    StatusQualificationService,
)
from apps.partner.models import BinaryBalance, FastStart, PartnerProfile
from apps.users.models import User
from tests.support import AuthStoreTestMixin


class BonusEngineTestMixin(AuthStoreTestMixin):
    def _seed(self):
        self.client = APIClient()
        self.seed_store()
        call_command("seed_ledger_rules")

    def join(self, email, tariff, *, sponsor_code=None, first_name="Тест", last_name="Партнёр"):
        self.client.credentials()
        extra = {"first_name": first_name, "last_name": last_name}
        if sponsor_code:
            extra["referral_code"] = sponsor_code
        self.register_user(email, **extra)
        self.login_user(email)
        self.buy_tariff(tariff)
        return PartnerProfile.objects.get(user__email=email)

    def referral_code(self, partner: PartnerProfile) -> str:
        return partner.user.referral_code.code

    def sum_entries(self, user, entry_type, currency="USD") -> Decimal:
        total = Entry.objects.filter(
            user=user, entry_type=entry_type, currency=currency
        ).aggregate(total=Sum("amount"))["total"]
        return total or Decimal("0")


class PurchaseBonusTests(BonusEngineTestMixin, TestCase):
    def setUp(self):
        self._seed()

    def test_tc_pur_01_rise_invites_rise(self):
        sponsor = self.join("a@t.ai", "rise")
        buyer = self.join("b@t.ai", "rise", sponsor_code=self.referral_code(sponsor))

        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_PERSONAL_BONUS), Decimal("30"))
        self.assertEqual(
            self.sum_entries(buyer.user, ENTRY_TYPE_PURCHASE_PV, currency="PV"), Decimal("30")
        )

    def test_tc_pur_02_max_invites_rise_min_applies(self):
        sponsor = self.join("a@t.ai", "rise-pro-max")
        self.join("b@t.ai", "rise", sponsor_code=self.referral_code(sponsor))

        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_PERSONAL_BONUS), Decimal("30"))

    def test_tc_pur_03_max_invites_max(self):
        sponsor = self.join("a@t.ai", "rise-pro-max")
        self.join("b@t.ai", "rise-pro-max", sponsor_code=self.referral_code(sponsor))

        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_PERSONAL_BONUS), Decimal("300"))

    def test_tc_pur_04_rise_sponsor_cap_on_max_buyer(self):
        sponsor = self.join("a@t.ai", "rise")
        buyer = self.join("b@t.ai", "rise-pro-max", sponsor_code=self.referral_code(sponsor))

        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_PERSONAL_BONUS), Decimal("30"))
        self.assertEqual(
            self.sum_entries(buyer.user, ENTRY_TYPE_PURCHASE_PV, currency="PV"), Decimal("300")
        )

    def test_tc_pur_05_inactive_sponsor_gets_money_no_pv(self):
        sponsor = self.join("a@t.ai", "rise")
        PartnerProfile.objects.filter(pk=sponsor.pk).update(is_active=False)

        self.join("b@t.ai", "rise", sponsor_code=self.referral_code(sponsor))

        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_PERSONAL_BONUS), Decimal("30"))
        balance = BinaryBalance.objects.get(partner=sponsor)
        self.assertEqual(balance.left_pv, 0)
        self.assertEqual(balance.right_pv, 0)

    def test_tc_pur_06_sponsor_without_tariff_gets_nothing(self):
        sponsor = self.join("a@t.ai", "rise")
        PartnerProfile.objects.filter(pk=sponsor.pk).update(is_active=False, tariff_id=None)

        self.join("b@t.ai", "rise", sponsor_code=self.referral_code(sponsor))

        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_PERSONAL_BONUS), Decimal("0"))

    def test_second_personal_defaults_to_opposite_leg_and_collapses(self):
        from apps.partner.models import BinaryPlacement

        sponsor = self.join("root@t.ai", "rise")
        first = self.join("left@t.ai", "rise", sponsor_code=self.referral_code(sponsor))
        second = self.join("right@t.ai", "rise", sponsor_code=self.referral_code(sponsor))

        first_leg = BinaryPlacement.objects.get(partner=first).leg
        second_leg = BinaryPlacement.objects.get(partner=second).leg
        self.assertNotEqual(first_leg, second_leg)

        balance = BinaryBalance.objects.get(partner=sponsor)
        # Both rise purchases → 30 PV each leg → full collapse, no remainder
        self.assertEqual(balance.left_pv, 0)
        self.assertEqual(balance.right_pv, 0)
        self.assertEqual(
            self.sum_entries(sponsor.user, ENTRY_TYPE_BINARY_COLLAPSE, currency="PV"),
            Decimal("30"),
        )


class UpgradeRenewalTests(BonusEngineTestMixin, TestCase):
    def setUp(self):
        self._seed()

    def test_tc_upg_01_rise_sponsor_no_upgrade_bonus(self):
        sponsor = self.join("a@t.ai", "rise")
        buyer = self.join("b@t.ai", "rise", sponsor_code=self.referral_code(sponsor))

        self.buy_tariff("rise-pro", order_type="upgrade")

        # Только первичный бонус $30, без апгрейд-разницы (спонсор Rise, cap 30 < 60)
        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_PERSONAL_BONUS), Decimal("30"))

    def test_tc_upg_02_pro_sponsor_gets_diff(self):
        sponsor = self.join("a@t.ai", "rise-pro")
        buyer = self.join("b@t.ai", "rise", sponsor_code=self.referral_code(sponsor))

        # Первичный бонус min(90,30)=30
        self.buy_tariff("rise-pro", order_type="upgrade")

        # +$60 разницы → всего 90
        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_PERSONAL_BONUS), Decimal("90"))

    def test_tc_upg_03_pro_sponsor_rise_to_max_gets_matrix_delta(self):
        """Спонсор Pro, байер Rise→Max: delta = min(90,300)-min(90,30) = 60, не «всё или ничего»."""
        sponsor = self.join("a@t.ai", "rise-pro")
        self.join("b@t.ai", "rise", sponsor_code=self.referral_code(sponsor))

        self.buy_tariff("rise-pro-max", order_type="upgrade")

        # 30 (покупка Rise) + 60 (апгрейд) = 90
        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_PERSONAL_BONUS), Decimal("90"))

    def test_upgrade_bonus_paid_to_inactive_sponsor_within_12m(self):
        sponsor = self.join("a@t.ai", "rise-pro")
        self.join("b@t.ai", "rise", sponsor_code=self.referral_code(sponsor))
        # Спонсор неактивен, но тариф сохраняется (<12 мес) → бонус по матрице платится
        PartnerProfile.objects.filter(pk=sponsor.pk).update(is_active=False)

        self.buy_tariff("rise-pro", order_type="upgrade")

        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_PERSONAL_BONUS), Decimal("90"))

    def test_tc_ren_01_active_sponsor_gets_nine(self):
        from datetime import timedelta

        from django.utils import timezone

        from apps.commerce.models import Subscription

        sponsor = self.join("a@t.ai", "rise-pro")
        buyer = self.join("b@t.ai", "rise", sponsor_code=self.referral_code(sponsor))
        Subscription.objects.filter(user=buyer.user).update(
            active_until=timezone.now() + timedelta(days=3)
        )

        self.buy_tariff("subscription", order_type="renewal")

        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_RENEWAL_BONUS), Decimal("9"))

    def test_tc_ren_02_inactive_sponsor_gets_nothing(self):
        from datetime import timedelta

        from django.utils import timezone

        from apps.commerce.models import Subscription

        sponsor = self.join("a@t.ai", "rise-pro")
        buyer = self.join("b@t.ai", "rise", sponsor_code=self.referral_code(sponsor))
        PartnerProfile.objects.filter(pk=sponsor.pk).update(is_active=False)
        Subscription.objects.filter(user=buyer.user).update(
            active_until=timezone.now() + timedelta(days=3)
        )

        self.buy_tariff("subscription", order_type="renewal")

        self.assertEqual(self.sum_entries(sponsor.user, ENTRY_TYPE_RENEWAL_BONUS), Decimal("0"))


class BinaryCollapseTests(BonusEngineTestMixin, TestCase):
    def setUp(self):
        self._seed()

    def test_tc_bin_01_collapse_weak_leg(self):
        partner = self.join("p@t.ai", "rise")
        balance, _ = BinaryBalance.objects.get_or_create(partner=partner)
        balance.left_pv = 300
        balance.right_pv = 220
        balance.save()

        income = BinaryCollapseService.collapse(partner, None)

        balance.refresh_from_db()
        self.assertEqual(income, Decimal("22.00"))
        self.assertEqual(balance.left_pv, 80)
        self.assertEqual(balance.right_pv, 0)
        self.assertEqual(self.sum_entries(partner.user, ENTRY_TYPE_BINARY_BONUS), Decimal("22"))
        self.assertEqual(
            self.sum_entries(partner.user, ENTRY_TYPE_BINARY_COLLAPSE, currency="PV"),
            Decimal("220"),
        )

    def test_tc_bin_02_carryover_then_collapse(self):
        partner = self.join("p@t.ai", "rise")
        balance, _ = BinaryBalance.objects.get_or_create(partner=partner)
        balance.left_pv = 300
        balance.right_pv = 220
        balance.save()

        BinaryCollapseService.collapse(partner, None)
        BinaryCollapseService.add_pv(partner, "right", 80, None)

        balance.refresh_from_db()
        self.assertEqual(balance.left_pv, 0)
        self.assertEqual(balance.right_pv, 0)
        self.assertEqual(self.sum_entries(partner.user, ENTRY_TYPE_BINARY_BONUS), Decimal("30"))

    def test_tc_bin_03_inactive_partner_frozen(self):
        partner = self.join("p@t.ai", "rise")
        PartnerProfile.objects.filter(pk=partner.pk).update(is_active=False)
        partner.refresh_from_db()

        BinaryCollapseService.add_pv(partner, "left", 100, None)

        balance = BinaryBalance.objects.get(partner=partner)
        self.assertEqual(balance.left_pv, 0)
        self.assertEqual(self.sum_entries(partner.user, ENTRY_TYPE_BINARY_BONUS), Decimal("0"))


class MatchingBonusTests(BonusEngineTestMixin, TestCase):
    def setUp(self):
        self._seed()

    def test_tc_match_01_two_lines_get_ten_percent(self):
        a = self.join("a@t.ai", "rise-pro-max")
        b = self.join("b@t.ai", "rise-pro", sponsor_code=self.referral_code(a))
        c = self.join("c@t.ai", "rise", sponsor_code=self.referral_code(b))

        MatchingBonusService.process(c, Decimal("22"), None)

        self.assertEqual(self.sum_entries(b.user, ENTRY_TYPE_MATCHING_BONUS), Decimal("2.20"))
        self.assertEqual(self.sum_entries(a.user, ENTRY_TYPE_MATCHING_BONUS), Decimal("2.20"))


class FastStartTests(BonusEngineTestMixin, TestCase):
    def setUp(self):
        self._seed()

    def test_tc_fs_01_four_pro_invites_pay_once(self):
        sponsor = self.join("a@t.ai", "rise-pro")
        code = self.referral_code(sponsor)

        for index in range(5):
            self.join(f"inv{index}@t.ai", "rise-pro", sponsor_code=code)

        self.assertEqual(
            self.sum_entries(sponsor.user, ENTRY_TYPE_FAST_START_BONUS), Decimal("90")
        )
        fast_start = FastStart.objects.get(partner=sponsor)
        self.assertTrue(fast_start.reward_paid)

    def test_tc_fs_02_rise_sponsor_no_fast_start(self):
        sponsor = self.join("a@t.ai", "rise")
        code = self.referral_code(sponsor)

        for index in range(4):
            self.join(f"inv{index}@t.ai", "rise-pro", sponsor_code=code)

        self.assertEqual(
            self.sum_entries(sponsor.user, ENTRY_TYPE_FAST_START_BONUS), Decimal("0")
        )
        self.assertFalse(FastStart.objects.filter(partner=sponsor).exists())


class StatusQualificationTests(BonusEngineTestMixin, TestCase):
    def setUp(self):
        self._seed()

    def test_tc_rank_01_skips_intermediate_premium(self):
        partner = self.join("p@t.ai", "rise")
        code = self.referral_code(partner)
        for index in range(4):
            self.join(f"inv{index}@t.ai", "rise", sponsor_code=code)

        week = QualificationWeekService.current(partner)
        week.collapsed_pv = 250
        week.save()

        StatusQualificationService.check(partner)

        partner.refresh_from_db()
        self.assertEqual(partner.current_rank, "partner_3")
        self.assertEqual(self.sum_entries(partner.user, ENTRY_TYPE_STATUS_PREMIUM), Decimal("20"))


class ActivityExpirationTests(BonusEngineTestMixin, TestCase):
    def setUp(self):
        self._seed()

    def test_expire_due_deactivates_and_freezes(self):
        from django.utils import timezone

        partner = self.join("p@t.ai", "rise")
        PartnerProfile.objects.filter(pk=partner.pk).update(
            activity_until=timezone.now() - timezone.timedelta(days=1)
        )

        from apps.partner.services import ActivityService

        count = ActivityService.expire_due()

        partner.refresh_from_db()
        self.assertEqual(count, 1)
        self.assertFalse(partner.is_active)
        self.assertTrue(BinaryBalance.objects.get(partner=partner).is_frozen)

    def test_expire_due_clears_tariff_after_12_months(self):
        from django.utils import timezone

        partner = self.join("p@t.ai", "rise")
        PartnerProfile.objects.filter(pk=partner.pk).update(
            is_active=False,
            activity_until=timezone.now() - timezone.timedelta(days=400),
        )
        BinaryBalance.objects.filter(partner=partner).update(left_pv=50, right_pv=20, is_frozen=True)

        from apps.partner.services import ActivityService

        ActivityService.expire_due()

        partner.refresh_from_db()
        self.assertIsNone(partner.tariff_id)
        self.assertIsNotNone(partner.tariff_lost_at)
        bal = BinaryBalance.objects.get(partner=partner)
        self.assertEqual(bal.left_pv, 0)
        self.assertEqual(bal.right_pv, 0)


class PartnerDashboardApiTests(BonusEngineTestMixin, TestCase):
    def setUp(self):
        self._seed()

    def test_dashboard_ranks_structure_endpoints(self):
        sponsor = self.join("a@t.ai", "rise-pro")
        self.join("b@t.ai", "rise", sponsor_code=self.referral_code(sponsor))

        self.login_user("a@t.ai")

        dashboard = self.client.get("/api/v1/partner/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertTrue(dashboard.data["data"]["is_partner"])
        self.assertEqual(dashboard.data["data"]["partner"]["tariff_id"], "rise-pro")

        ranks = self.client.get("/api/v1/partner/ranks")
        self.assertEqual(ranks.status_code, 200)
        self.assertEqual(len(ranks.data["data"]), 16)
        self.assertTrue(ranks.data["data"][0]["is_achieved"])
        self.assertIn("achieved_at", ranks.data["data"][0])
        self.assertNotIn("achieved_at", ranks.data["data"][-1])

        structure = self.client.get("/api/v1/partner/structure")
        self.assertEqual(structure.status_code, 200)
        self.assertEqual(len(structure.data["data"]["legs"]), 2)
        self.assertEqual(structure.data["data"]["summary"]["personal_invites"], 1)

        tree = structure.data["data"]["tree"]
        self.assertEqual(tree["root_id"], "self")
        directory = tree["directory"]
        self.assertIn("self", directory)
        self.assertEqual(directory["self"]["id"], "self")
        children = directory["self"]["children"]
        self.assertEqual(len(children), 2)
        child_ids = [item for item in children if item]
        self.assertEqual(len(child_ids), 1)
        child = directory[child_ids[0]]
        self.assertEqual(child["parentId"], "self")
        self.assertIn(child["branchId"], ("left", "right"))
        self.assertEqual(child["level"], "L1")
        self.assertTrue(any(member.get("id") == child_ids[0] for member in structure.data["data"]["members"]))
