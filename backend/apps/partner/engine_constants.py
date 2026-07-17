from decimal import Decimal

from apps.partner.constants import LEG_LEFT, LEG_RIGHT

# --- Финансовые константы движка (v1, из marketingplan.md) ---
BINARY_PV_PER_USD = 10
MATCHING_RATE = Decimal("0.10")
SUBSCRIPTION_SPONSOR_BONUS = Decimal("9")
SUBSCRIPTION_PV = 9
FAST_START_WINDOW_DAYS = 30
FAST_START_REQUIRED = 4
FAST_START_REWARD = Decimal("90")
INACTIVITY_TARIFF_LOSS_MONTHS = 12

FAST_START_TARIFFS = ("rise-pro", "rise-pro-max")

MSK_TIMEZONE = "Europe/Moscow"

LEG_KEYS = (LEG_LEFT, LEG_RIGHT)

# --- Лестница статусов ---
RANK_NAMES = {
    "partner_1": "Партнёр I",
    "partner_2": "Партнёр II",
    "partner_3": "Партнёр III",
    "expert_1": "Эксперт I",
    "expert_2": "Эксперт II",
    "expert_3": "Эксперт III",
    "master_1": "Мастер I",
    "master_2": "Мастер II",
    "grand_master": "Гранд Мастер",
    "leader_1": "Лидер I",
    "leader_2": "Лидер II",
    "top_leader": "Топ-Лидер",
    "mentor_1": "Ментор I",
    "mentor_2": "Ментор II",
    "premier_mentor": "Премьер-Ментор",
    "visioner": "Визионер",
}

RANKS = [
    {"rank": "partner_1", "pv": 0, "personals": 0, "premium": Decimal("0"), "leg_req": None},
    {"rank": "partner_2", "pv": 100, "personals": 2, "premium": Decimal("10"), "leg_req": None},
    {"rank": "partner_3", "pv": 200, "personals": 4, "premium": Decimal("20"), "leg_req": None},
    {"rank": "expert_1", "pv": 300, "personals": 6, "premium": Decimal("30"), "leg_req": None},
    {"rank": "expert_2", "pv": 400, "personals": 8, "premium": Decimal("40"), "leg_req": None},
    {"rank": "expert_3", "pv": 500, "personals": 10, "premium": Decimal("50"), "leg_req": None},
    {"rank": "master_1", "pv": 600, "personals": 0, "premium": Decimal("60"), "leg_req": "expert_1"},
    {"rank": "master_2", "pv": 700, "personals": 0, "premium": Decimal("70"), "leg_req": "expert_2"},
    {"rank": "grand_master", "pv": 800, "personals": 0, "premium": Decimal("80"), "leg_req": "expert_3"},
    {"rank": "leader_1", "pv": 1000, "personals": 0, "premium": Decimal("100"), "leg_req": "master_1"},
    {"rank": "leader_2", "pv": 1500, "personals": 0, "premium": Decimal("150"), "leg_req": "master_2"},
    {"rank": "top_leader", "pv": 2000, "personals": 0, "premium": Decimal("200"), "leg_req": "grand_master"},
    {"rank": "mentor_1", "pv": 3000, "personals": 0, "premium": Decimal("300"), "leg_req": "leader_1"},
    {"rank": "mentor_2", "pv": 4000, "personals": 0, "premium": Decimal("400"), "leg_req": "leader_2"},
    {"rank": "premier_mentor", "pv": 5000, "personals": 0, "premium": Decimal("500"), "leg_req": "top_leader"},
    {"rank": "visioner", "pv": 10000, "personals": 0, "premium": Decimal("10000"), "leg_req": "mentor_1"},
]

RANK_ORDER = [rank_def["rank"] for rank_def in RANKS]
RANK_INDEX = {rank: index for index, rank in enumerate(RANK_ORDER)}
RANK_BY_ID = {rank_def["rank"]: rank_def for rank_def in RANKS}


def rank_index(rank_id: str) -> int:
    return RANK_INDEX.get(rank_id, 0)


def next_rank_id(rank_id: str) -> str | None:
    index = rank_index(rank_id)
    if index + 1 < len(RANK_ORDER):
        return RANK_ORDER[index + 1]
    return None


def rank_name(rank_id: str) -> str:
    return RANK_NAMES.get(rank_id, rank_id)


def rank_requirement_text(rank_def: dict) -> str:
    if rank_def["rank"] == "partner_1":
        return "Покупка любого партнёрского тарифа"

    parts = [f"{rank_def['pv']} PV схлопа за неделю"]
    if rank_def["personals"]:
        parts.append(f"{rank_def['personals']} активных личных партнёров")
    if rank_def["leg_req"]:
        parts.append(f"квалификатор «{rank_name(rank_def['leg_req'])}» в каждой ноге")
    return ", ".join(parts)
