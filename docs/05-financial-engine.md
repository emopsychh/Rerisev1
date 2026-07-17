# ReRise — Этап 5: Financial Engine

**Статус:** черновик на утверждение  
**Источник правил:** `marketingplan.md` (раздел «Утверждено»)  
**Версия:** 0.1 · 15.07.2026

---

## 1. Архитектура движка

### Принцип: события, а не пересчёт дерева

Любое финансовое действие — **событие**, которое порождает одну или несколько записей в `ledger_entry`. Балансы и кэши — производные.

```
                    ┌─────────────────┐
  Order Paid ──────►│  Event Handler  │
  Renewal    ──────►│  (Commerce)     │
  Admin Adj  ──────►└────────┬────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │  BonusEngine    │
                    │  (оркестратор)  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  PersonalBonusSvc    PvDistributionSvc    BinaryCollapseSvc
         │                   │                   │
         ▼                   ▼                   ▼
  MatchingBonusSvc    StatusQualificationSvc   FastStartSvc
         │                   │                   │
         └───────────────────┴───────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  LedgerWriter   │  ← append-only
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  WalletUpdater  │  ← кэш баланса
                    └─────────────────┘
```

### Сервисы (Python / Django)

| Сервис | Ответственность |
|---|---|
| `BonusEngine` | Оркестратор: вызывает нужные сервисы по типу события |
| `PersonalBonusService` | Личный бонус прямому спонсору |
| `PvDistributionService` | Распространение PV вверх по бинару |
| `BinaryCollapseService` | Схлоп PV, бинарный доход |
| `MatchingBonusService` | 10% от бинара нижестоящих |
| `StatusQualificationService` | Проверка и присвоение статусов |
| `FastStartService` | Отслеживание 4 Pro/Max за 30 дней |
| `ActivityService` | Активность / неактивность / 12 мес |
| `LedgerWriter` | Единственная точка записи в ledger |
| `WalletUpdater` | Пересчёт `wallet_balance` из ledger |
| `AdjustmentService` | Отмены, корректировочный долг |

### Идемпотентность

Каждое событие имеет `idempotency_key`:

```
order:{order_id}:paid
renewal:{order_id}:paid
upgrade:{order_id}:paid
```

Повторный webhook не создаёт дубликатов в ledger.

---

## 2. Справочник тарифов (константы v1)

```python
TARIFF_CAPS = {
    "rise":         {"bonus_usd": 30,  "pv": 30,  "binary_depth": 3,  "matching_lines": 1},
    "rise-pro":     {"bonus_usd": 90,  "pv": 90,  "binary_depth": 9,  "matching_lines": 2},
    "rise-pro-max": {"bonus_usd": 300, "pv": 300, "binary_depth": 15, "matching_lines": 3},
}

BINARY_PV_PER_USD = 10          # 10 схлопнутых PV = $1
SUBSCRIPTION_PRICE = 30         # USD
SUBSCRIPTION_SPONSOR_BONUS = 9  # USD
SUBSCRIPTION_PV = 9
FAST_START_WINDOW_DAYS = 30
FAST_START_REQUIRED = 4
FAST_START_REWARD = 90
INACTIVITY_TARIFF_LOSS_MONTHS = 12
```

Начисление по покупке = `min(тариф_пригласившего, тариф_покупки)`:

```python
def calc_purchase_bonus(sponsor_tariff: str, buyer_tariff: str) -> tuple[int, int]:
    sponsor = TARIFF_CAPS[sponsor_tariff]
    buyer = TARIFF_CAPS[buyer_tariff]
    return (
        min(sponsor["bonus_usd"], buyer["bonus_usd"]),
        min(sponsor["pv"], buyer["pv"]),
    )
```

---

## 3. Главный поток: покупка тарифа

### Триггер

`commerce_order.status` → `paid`, `order_type = purchase`

### Последовательность

```
1. ActivityService.grant_initial_month(buyer)
2. UserAccessService.grant_tariff(buyer, tariff)
3. TokenService.credit_initial_tokens(buyer, tariff)
4. BinaryPlacementService.place_in_tree(buyer)        # если ещё не размещён
5. PersonalBonusService.process(buyer, order)         # $ спонсору
6. PvDistributionService.process(buyer, order)      # PV вверх по бинару
7. StatusQualificationService.check(buyer)            # Партнёр I
8. FastStartService.track_invite(sponsor, buyer)      # если Pro/Max
9. NotificationService.notify(...)
```

### Псевдокод: PersonalBonusService

```python
def process_purchase(buyer: Partner, order: Order):
    sponsor = buyer.direct_sponsor
    if not sponsor:
        return

    # Нет тарифа у спонсора (12+ мес неактивности)
    if not sponsor.tariff_id:
        return

    bonus_usd, pv_cap = calc_purchase_bonus(sponsor.tariff_id, buyer.tariff_id)

    # Денежный бонус — только прямому спонсору
    if sponsor.is_active or sponsor.is_within_12m_inactivity():
        LedgerWriter.credit(
            user=sponsor.user,
            entry_type="personal_bonus",
            amount=bonus_usd,
            currency="USD",
            source=order,
            metadata={"buyer_id": buyer.id, "buyer_tariff": buyer.tariff_id},
        )
        WalletUpdater.refresh(sponsor.user)
        # Триггер матчинга НЕ нужен — матчинг только от бинара

    # PV — отдельно, через PvDistributionService
```

### Псевдокод: PvDistributionService

```python
def process_purchase(buyer: Partner, order: Order, pv_amount: int):
    """
    PV поднимается вверх по бинарному дереву (физические уровни).
    На каждом узле — начисляется в соответствующую ногу.
    Глубина ограничена тарифом каждого вышестоящего.
    """
    current = buyer.binary_placement
    pv_remaining = pv_amount  # полный PV покупки (30/90/300)

    for physical_level in range(1, MAX_DEPTH + 1):
        parent = current.parent
        if not parent:
            break

        # Неактивный не получает PV
        if not parent.is_active:
            current = parent.binary_placement
            continue

        # Глубина по тарифу родителя
        parent_depth_limit = TARIFF_CAPS[parent.tariff_id]["binary_depth"]
        if physical_level > parent_depth_limit:
            current = parent.binary_placement
            continue

        # PV доступный по тарифу родителя
        _, parent_pv_cap = calc_purchase_bonus(parent.tariff_id, buyer.tariff_id)
        pv_for_parent = min(pv_remaining, parent_pv_cap)

        leg = current.leg  # left / right
        BinaryCollapseService.add_pv(parent, leg, pv_for_parent, source=order)

        current = parent.binary_placement

    LedgerWriter.credit(
        user=buyer.user,
        entry_type="purchase_pv",
        amount=pv_amount,
        currency="PV",
        source=order,
    )
```

---

## 4. Бинарный схлоп (BinaryCollapseService)

### Правила

- У каждого партнёра: `left_pv`, `right_pv` (кэш + ledger)
- Схлоп = `min(left, right)` — в реальном времени
- Бинарный доход = `collapsed_pv / 10` USD
- Остаток в сильной ноге переносится
- При неактивности — PV заморожен (`is_frozen = true`)
- После 12 мес неактивности — обнуление

### Псевдокод

```python
def add_pv(partner: Partner, leg: str, amount: int, source):
    if not partner.is_active:
        return  # неактивный не накапливает

    balance = partner.binary_balance
    if balance.is_frozen:
        return

    if leg == "left":
        balance.left_pv += amount
    else:
        balance.right_pv += amount
    balance.save()

    LedgerWriter.credit(
        user=partner.user,
        entry_type="pv_received",
        amount=amount,
        currency="PV",
        source=source,
        metadata={"leg": leg, "partner_id": partner.id},
    )

    collapse(partner, source)


def collapse(partner: Partner, source):
    if not partner.is_active:
        return

    balance = partner.binary_balance
    collapsed = min(balance.left_pv, balance.right_pv)
    if collapsed == 0:
        return

    balance.left_pv -= collapsed
    balance.right_pv -= collapsed
    balance.save()

    income_usd = collapsed / BINARY_PV_PER_USD

    LedgerWriter.credit(
        user=partner.user,
        entry_type="binary_collapse",
        amount=collapsed,
        currency="PV",
        source=source,
        metadata={"collapsed_pv": collapsed},
    )

    LedgerWriter.credit(
        user=partner.user,
        entry_type="binary_bonus",
        amount=income_usd,
        currency="USD",
        source=source,
    )
    WalletUpdater.refresh(partner.user)

    # Записать в квалификационную неделю
    QualificationWeekService.add_collapsed_pv(partner, collapsed)

    # Матчинг для спонсоров
    MatchingBonusService.process(partner, income_usd, source)

    # Проверить статус
    StatusQualificationService.check(partner)
```

### Тест-кейс TC-BIN-01

```
Дано:  партнёр P, left=300, right=220
Когда: add_pv не вызывается, вызываем collapse напрямую
Тогда: collapsed=220, income=$22, left=80, right=0
```

### Тест-кейс TC-BIN-02 (из marketingplan.md)

```
Дано:  P: left=300, right=220
Когда: collapse
Тогда: income=$22, carryover left=80
Когда: позже right получает 80 PV → collapse снова
Тогда: collapsed=80, income=$8, left=0, right=0
```

---

## 5. Матчинг (MatchingBonusService)

### Правила

- 10% от **бинарного дохода** нижестоящих
- Спонсорские линии (не бинарные уровни):
  - 1-я: лично приглашённые
  - 2-я: их лично приглашённые
  - 3-я: следующая генерация
- Без компрессии неактивных
- Неактивный получатель — не получает

### Псевдокод

```python
def process(earner: Partner, binary_income_usd: Decimal, source):
    """
    Когда earner получает бинарный доход,
    его спонсоры (до 3 линий) получают 10%.
    """
    current_sponsor = earner.direct_sponsor
    for line in range(1, 4):
        if not current_sponsor:
            break

        if not current_sponsor.is_active:
            # Неактивный не получает, но линия не сжимается
            current_sponsor = current_sponsor.direct_sponsor
            continue

        max_lines = TARIFF_CAPS[current_sponsor.tariff_id]["matching_lines"]
        if line > max_lines:
            break

        matching_usd = binary_income_usd * Decimal("0.10")

        LedgerWriter.credit(
            user=current_sponsor.user,
            entry_type="matching_bonus",
            amount=matching_usd,
            currency="USD",
            source=source,
            metadata={
                "from_partner": earner.id,
                "line": line,
                "binary_income": str(binary_income_usd),
            },
        )
        WalletUpdater.refresh(current_sponsor.user)

        current_sponsor = current_sponsor.direct_sponsor
```

### Тест-кейс TC-MATCH-01

```
Дано:  A (Pro Max) → B (Pro) → C (Rise)
       C получает бинар $22
Когда: matching для C
Тогда: B (1-я линия, matching_lines=2) получает $2.20
       A (2-я линия, matching_lines=3) получает $2.20
```

---

## 6. Апгрейд тарифа

### Триггер

`order_type = upgrade`

### Правило

Начисляется **только разница** между старым и новым уровнем. Без пересчёта прошлого.

```python
UPGRADE_DIFF = {
    ("rise", "rise-pro"):      (60, 60),
    ("rise-pro", "rise-pro-max"): (210, 210),
    ("rise", "rise-pro-max"):  (270, 270),
}

def process_upgrade(buyer, order, old_tariff, new_tariff):
    diff = UPGRADE_DIFF.get((old_tariff, new_tariff))
    if not diff:
        return

    bonus_diff, pv_diff = diff
    sponsor = buyer.direct_sponsor
    if not sponsor or not sponsor.tariff_id:
        return

    # Проверка: спонсор должен иметь достаточный тариф
    sponsor_bonus_cap = TARIFF_CAPS[sponsor.tariff_id]["bonus_usd"]
    if sponsor_bonus_cap < bonus_diff:
        bonus_diff = 0  # Rise-спонсор не получает при Rise→Pro
        pv_diff = 0

    if bonus_diff > 0 and sponsor.is_active:
        LedgerWriter.credit(sponsor.user, "personal_bonus", bonus_diff, "USD", order)
        PvDistributionService.process(buyer, order, pv_diff)
        WalletUpdater.refresh(sponsor.user)

    buyer.tariff_id = new_tariff
    buyer.save()
```

### Тест-кейс TC-UPG-01

```
Дано:  покупатель апгрейд Rise → Pro
       спонсор на Rise
Тогда: дополнительного начисления нет

Дано:  спонсор на Pro
Тогда: +$60 + 60 PV
```

---

## 7. Ежемесячное продление ($30)

### Триггер

`order_type = renewal`, amount = $30

```python
def process_renewal(buyer: Partner, order: Order):
    # 1. Продлить активность
    ActivityService.extend(buyer, months=1)

    sponsor = buyer.direct_sponsor

    # 2. $9 прямому спонсору (только если активен)
    if sponsor and sponsor.is_active:
        LedgerWriter.credit(sponsor.user, "renewal_bonus", 9, "USD", order)
        WalletUpdater.refresh(sponsor.user)

    # 3. 9 PV вверх по бинару
    PvDistributionService.process(buyer, order, SUBSCRIPTION_PV)
```

### Тест-кейс TC-REN-01

```
Дано:  партнёр P продлевает, спонсор S (Pro, активен)
Тогда: S получает $9
       9 PV поднимаются вверх (глубина по тарифу каждого)
       PV участвуют в бинарном схлопе
```

### Тест-кейс TC-REN-02

```
Дано:  спонсор S неактивен
Тогда: S не получает $9, PV не начисляются S
       (перераспределение $9 не утверждено — теряется)
```

---

## 8. Быстрый старт

### Условия

- Только Pro / Pro Max
- 30 дней с **первой покупки** любого партнёрского тарифа
- 4 личных приглашённых купили Pro или Pro Max
- $90 один раз
- Апгрейд Rise → Pro не перезапускает окно
- Действия до получения права не пересчитываются

```python
def track_invite(sponsor: Partner, invited: Partner, order: Order):
    fs = sponsor.fast_start
    if not fs:
        return

    # Только Pro/Pro Max спонсоры
    if sponsor.tariff_id == "rise":
        return

    # Окно
    if now() > fs.window_end:
        return

    # Уже выплачено
    if fs.reward_paid:
        return

    # Приглашённый купил Pro или Pro Max
    if invited.tariff_id not in ("rise-pro", "rise-pro-max"):
        return

    fs.qualified_count += 1
    fs.save()

    if fs.qualified_count >= FAST_START_REQUIRED:
        pay_fast_start(sponsor, fs)


def pay_fast_start(sponsor, fs):
    LedgerWriter.credit(sponsor.user, "fast_start_bonus", 90, "USD", fs)
    WalletUpdater.refresh(sponsor.user)
    fs.reward_paid = True
    fs.reward_paid_at = now()
    fs.save()
```

### Тест-кейс TC-FS-01

```
Дано:  спонсор Pro, fast_start окно активно
Когда: 4 личных покупают Pro/Pro Max
Тогда: +$90, reward_paid=true

Дано:  5-й личный покупает Pro
Тогда: без доп. выплаты
```

---

## 9. Статусная квалификация

### Квалификационная неделя

- Пн 00:00 — Вс 23:59:59 **МСК** (Europe/Moscow)
- Счётчик `collapsed_pv` за неделю **обнуляется** в понедельник
- Несхлопнутый остаток PV **сохраняется**
- Заработанный бинар **сохраняется**
- Достигнутый статус **сохраняется навсегда**

### Лестница статусов

```python
RANKS = [
    {"rank": "partner_1",     "pv": 0,     "personals": 0,  "premium": 0,     "leg_req": None},
    {"rank": "partner_2",     "pv": 100,   "personals": 2,  "premium": 10,    "leg_req": None},
    {"rank": "partner_3",     "pv": 200,   "personals": 4,  "premium": 20,    "leg_req": None},
    {"rank": "expert_1",      "pv": 300,   "personals": 6,  "premium": 30,    "leg_req": None},
    {"rank": "expert_2",      "pv": 400,   "personals": 8,  "premium": 40,    "leg_req": None},
    {"rank": "expert_3",      "pv": 500,   "personals": 10, "premium": 50,    "leg_req": None},
    {"rank": "master_1",      "pv": 600,   "personals": 0,  "premium": 60,    "leg_req": "expert_1"},
    {"rank": "master_2",      "pv": 700,   "personals": 0,  "premium": 70,    "leg_req": "expert_2"},
    {"rank": "grand_master",  "pv": 800,   "personals": 0,  "premium": 80,    "leg_req": "expert_3"},
    {"rank": "leader_1",      "pv": 1000,  "personals": 0,  "premium": 100,   "leg_req": "master_1"},
    {"rank": "leader_2",      "pv": 1500,  "personals": 0,  "premium": 150,   "leg_req": "master_2"},
    {"rank": "top_leader",    "pv": 2000,  "personals": 0,  "premium": 200,   "leg_req": "grand_master"},
    {"rank": "mentor_1",      "pv": 3000,  "personals": 0,  "premium": 300,   "leg_req": "leader_1"},
    {"rank": "mentor_2",      "pv": 4000,  "personals": 0,  "premium": 400,   "leg_req": "leader_2"},
    {"rank": "premier_mentor","pv": 5000,  "personals": 0,  "premium": 500,   "leg_req": "top_leader"},
    {"rank": "visioner",      "pv": 10000, "personals": 0,  "premium": 10000, "leg_req": "mentor_1"},
]
```

### Псевдокод

```python
def check(partner: Partner):
    if not partner.is_active:
        return

    week = QualificationWeekService.current(partner)
    collapsed_pv = week.collapsed_pv
    active_personals = count_active_direct_invites(partner)
    current_rank = partner.current_rank

    # Найти все новые статусы, которые выполнены
    achievable = []
    for rank_def in RANKS:
        if rank_def["rank"] <= current_rank:
            continue  # уже достигнут

        if collapsed_pv < rank_def["pv"]:
            break  # лестница последовательна

        # Проверка личных (Партнёр II — Эксперт III)
        if rank_def["personals"] > 0:
            if active_personals < rank_def["personals"]:
                continue

        # Проверка квалификаторов в ногах (Мастер I+)
        if rank_def["leg_req"]:
            if not has_qualifier_in_each_leg(partner, rank_def["leg_req"]):
                continue

        achievable.append(rank_def)

    if not achievable:
        return

    # Только самый высокий за неделю
    best = achievable[-1]

    partner.current_rank = best["rank"]
    partner.highest_rank = best["rank"]
    partner.save()

    PartnerRankHistory.create(partner, best["rank"], best["premium"])

    if best["premium"] > 0:
        LedgerWriter.credit(
            partner.user, "status_premium", best["premium"], "USD",
            metadata={"rank": best["rank"]},
        )
        WalletUpdater.refresh(partner.user)
```

### Тест-кейс TC-RANK-01

```
Дано:  партнёр I, collapsed_pv=250, 4 активных личных
Когда: check
Тогда: статус остаётся partner_1 (250 < 300 для Эксперт I)
       НО partner_3 (200 PV, 4 personals) — выполнен
Тогда: статус → partner_3, премия $20 (пропущенная partner_2 НЕ выплачивается)
```

### Тест-кейс TC-RANK-02

```
Дано:  за неделю collapsed_pv скачет 0 → 800
Когда: check после схлопа 800 PV
Тогда: присваивается только grand_master ($80)
       пропущенные master_1, master_2 — не компенсируются
```

---

## 10. Активность и неактивность

### Состояния

```
ACTIVE          — первый месяц или продление $30
INACTIVE_<12M   — не продлил, но < 12 мес
INACTIVE_12M+   — 12 мес без продления, тариф обнулён
```

### Права по состоянию

| Действие | ACTIVE | INACTIVE <12M | INACTIVE 12M+ |
|---|:---:|:---:|:---:|
| Личный $ бонус | ✅ | ✅ | ❌ |
| PV | ✅ | ❌ | ❌ |
| Бинар | ✅ | ❌ (frozen) | ❌ |
| Матчинг | ✅ | ❌ | ❌ |
| $9 продление | ✅ | ❌ | ❌ |
| Новые статусы | ✅ | ❌ | ❌ |
| Вывод баланса | ✅ | ✅ | ✅ |
| Приглашать | ✅ | ✅ | ✅ |
| Реферальная ссылка | ✅ | ✅ | ✅ |

### Celery-задачи (периодические)

```python
# Ежедневно
@celery.task
def check_activity_expiration():
    """Партнёры, у которых activity_until < now() → is_active = False"""
    ...

@celery.task
def check_12m_inactivity():
    """12 мес без продления → tariff_id = None, PV обнулить"""
    ...

# Каждый понедельник 00:00 MSK
@celery.task
def reset_qualification_week():
    """Обнулить weekly collapsed_pv счётчик"""
    ...
```

---

## 11. Размещение в бинаре

### Правила (утверждено)

1. Спонсор неизменяем
2. Первый личный → внешняя нога спонсора (та же, что у спонсора у его наставника)
3. Со 2-го личного → спонсор выбирает left/right
4. Позиция внутри ноги — автоматически (алгоритм TBD)
5. Spillover возможен

### Предварительный алгоритм (⚠️ требует утверждения владельца)

```python
def place_in_tree(new_partner: Partner, sponsor: Partner, leg: str | None = None):
    personal_count = sponsor.personal_invite_count

    if personal_count == 0:
        # Первый личный → нога спонсора = нога спонсора в бинаре
        sponsor_placement = sponsor.binary_placement
        leg = sponsor_placement.leg  # left или right
    elif leg is None:
        raise ValueError("leg required for 2+ personal invite")

    # Найти свободную позицию: BFS по выбранной ноге, слева направо
    position = find_first_free_slot(sponsor, leg)

    BinaryPlacement.create(
        partner=new_partner,
        parent=position.parent,
        leg=position.leg,
        depth=position.depth,
    )
```

---

## 12. Корректировки и отмены

### Триггер

Админ: мошенничество, отмена платежа, ошибка.

```python
def reverse_order(order: Order, reason: str, admin: User):
    with transaction.atomic():
        entries = LedgerEntry.filter(source=order)

        for entry in entries:
            LedgerWriter.debit(
                user=entry.user,
                entry_type="adjustment",
                amount=entry.amount,
                currency=entry.currency,
                metadata={"reversed_entry": entry.id, "reason": reason},
            )

            # Пересчитать binary balance если PV
            if entry.currency == "PV":
                BinaryCollapseService.reverse_pv(entry)

        # Корректировочный долг если уже выведено
        for user in affected_users:
            if WalletUpdater.available(user) < 0:
                AdjustmentDebtService.create(user, abs(balance), reason)

        order.status = "cancelled"
        order.save()

        AuditLog.record(admin, "order_reversed", order, reason)
```

---

## 13. Полная цепочка: пример

```
Мария (Pro Max, активна) пригласила Олега (купил Rise Pro, $300)
Олег размещён в правой ноге Марии на L1
Спонсор Марии — Александр (Pro, активен)

Шаг 1: Олег покупает Rise Pro
  → Олег: activity_until +1 мес, тариф rise-pro, Партнёр I
  → Мария: personal_bonus +$90 (min(90,90))
  → PV 90 поднимается вверх:
      Олег L0 → Мария right_leg +90 → collapse? → binary?
      → Александр L1: получает 90 PV? (глубина Pro=9, min(90,90)=90)

Шаг 2: PV на Марии (right +90)
  → если left >= 90: collapse, binary_bonus
  → qualification_week.collapsed_pv += collapsed
  → matching для спонсоров Марии

Шаг 3: StatusQualificationService.check(Мария)
  → если условия выполнены → новый статус + премия

Шаг 4: FastStartService.track(Mария, Олег)
  → qualified_count += 1 (Pro считается)

Шаг 5: NotificationService
  → Мария: "Личный бонус Rise Pro +$90 от Олега Н."
  → Олег: "Доступ Rise Pro активирован"
```

---

## 14. Тест-кейсы (сводка)

| ID | Сценарий | Ожидание |
|---|---|---|
| TC-PUR-01 | Rise пригласил Rise | $30 спонсору, 30 PV вверх |
| TC-PUR-02 | Pro Max пригласил Rise | $30 спонсору, 30 PV (min) |
| TC-PUR-03 | Pro Max пригласил Pro Max | $300, 300 PV |
| TC-PUR-04 | Rise спонсор, покупка Pro Max | $30, 30 PV (cap спонсора) |
| TC-PUR-05 | Неактивный спонсор <12м | $ да, PV нет |
| TC-PUR-06 | Спонсор 12м+ без тарифа | ничего |
| TC-UPG-01 | Rise→Pro, спонсор Rise | $0 |
| TC-UPG-02 | Rise→Pro, спонсор Pro | +$60, +60 PV |
| TC-UPG-03 | Pro→Max, спонсор Max | +$210, +210 PV |
| TC-REN-01 | Продление, активный спонсор | +$9, +9 PV |
| TC-REN-02 | Продление, неактивный спонсор | $0, PV нет |
| TC-BIN-01 | left=300, right=220 | collapse 220, $22 |
| TC-BIN-02 | carryover 80 + 80 | collapse 80, $8 |
| TC-BIN-03 | Неактивный партнёр | PV frozen, нет collapse |
| TC-MATCH-01 | Pro Max спонсор, бинар $22 у нижн. | 10% = $2.20 |
| TC-FS-01 | 4 Pro/Max за 30 дней | $90 один раз |
| TC-FS-02 | Rise спонсор | fast start недоступен |
| TC-RANK-01 | Пропуск статуса | только высший, промежуточные сгорают |
| TC-RANK-02 | Мастер I, квалификаторы в ногах | Эксперт I active в left AND right |
| TC-ACT-01 | Реактивация до 12м | PV разморозка, пропущенное не восстанавливается |
| TC-ACT-02 | 12м неактивности | tariff=null, PV=0, статус сохранён |
| TC-ADJ-01 | Отмена заказа | reversal entries + adjustment debt |

---

## 15. Не утверждено — заглушки

| Вопрос | Текущее поведение в коде |
|---|---|
| Алгоритм автопозиционирования | BFS слева-направо (заглушка) |
| Апгрейд и быстрый старт | Апгрейд НЕ считается как квалиф. покупка для FS |
| PV при неактивных позициях | PV проходит сквозь, не сжимается |
| Отмена статуса при fraud | Статус НЕ отбирается (до решения владельца) |
| Перераспределение $9 | Теряется |

---

## 16. Порядок реализации движка

| Шаг | Сервис | Зависит от |
|---|---|---|
| 1 | `LedgerWriter` + `WalletUpdater` | БД |
| 2 | `ActivityService` | partner_profile |
| 3 | `BinaryPlacementService` | partner_binary_placement |
| 4 | `PersonalBonusService` | ledger |
| 5 | `PvDistributionService` + `BinaryCollapseService` | placement, ledger |
| 6 | `MatchingBonusService` | binary |
| 7 | `QualificationWeekService` | celery |
| 8 | `StatusQualificationService` | week, personals |
| 9 | `FastStartService` | purchases |
| 10 | `AdjustmentService` | все выше |
| 11 | Интеграционные тесты TC-* | все |

---

## 17. Следующий этап

**Этап 6:** Commerce + Crypto — детали заказов, абстракция провайдера, webhook-flow.

**Этап 7:** План реализации по спринтам — что кодим в каком порядке, оценка по дням.
