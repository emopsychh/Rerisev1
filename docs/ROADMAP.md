# ReRise — Roadmap

**Обновлено:** 16.07.2026  
**Разработчик:** 1 человек (Python/Django)  
**Стек:** Django 5 + DRF + PostgreSQL (+ Celery/Redis позже)

> Живой документ: отмечаем `[x]` по мере выполнения. Детальный план спринтов — в [`07-implementation-plan.md`](./07-implementation-plan.md).

---

## Прогресс (сводка)

| Блок | Статус | Прогресс |
|---|---|---|
| Планирование (этапы 1–7) | ✅ Готово | 7/7 |
| Спринт 0 — Инфраструктура | ⏸ Отложен | ~15% |
| Спринт 1 — Auth + Users | ✅ Готово | 100% |
| Спринт 2 — Commerce | ✅ Готово | 100% |
| Спринт 3 — Partner structure | ✅ Готово | 100% |
| Спринт 4 — Ledger + Wallet | ✅ Готово | 100% |
| Спринт 5 — Bonus engine | ✅ Готово | 100% |
| Спринт 6 — Academy | ✅ Готово | 100% |
| Спринт 7 — Content + Home | ✅ Готово | 100% |
| Спринт 8 — AI Hub | ✅ Готово | 100% |
| Спринт 9 — CRM + Dashboard polish | ✅ Готово | 100% |
| Спринт 10 — CryptoBot + Deploy | ✅ Оплата готова · деплой ⏸ | ~70% |
| Спринт 11 — Admin + Polish | ✅ Готово | 100% |

**Код:** 10 Django-приложений (`users`, `commerce`, `partner`, `ledger`, `wallet`, `academy`, `content`, `ibox`, `crm`, `admin_ops`), PostgreSQL, Swagger, CryptoBot webhook + Celery.  
**Документация:** 7 файлов в `docs/`.

---

## Легенда

- `[x]` — сделано и проверено
- `[~]` — частично (скелет / заглушка / отложено осознанно)
- `[ ]` — ещё не начато

---

## Этап 0. Планирование ✅

Вся архитектура и контракты согласованы до написания кода.

| # | Документ | Статус | Содержание |
|---|---|---|---|
| 1 | Стек и архитектура (в чате) | `[x]` | Django 5, DRF, PostgreSQL, VPS, RU-first |
| 2 | Domain map — 10 apps | `[x]` | users, partner, ledger, wallet, commerce, academy, ibox, content, crm, admin_ops |
| 3 | [`03-database-schema-draft.md`](./03-database-schema-draft.md) v0.2 | `[x]` | 48 таблиц, Academy: Program → Module → Lesson |
| 4 | [`04-api-contracts.md`](./04-api-contracts.md) | `[x]` | ~48 эндпоинтов, форматы запросов/ответов |
| 5 | [`05-financial-engine.md`](./05-financial-engine.md) | `[x]` | Бонусы, бинар, matching, fast start, 22 тест-кейса |
| 6 | [`06-commerce-crypto.md`](./06-commerce-crypto.md) | `[x]` | Заказы, manual/crypto провайдеры, fulfillment |
| 7 | [`07-implementation-plan.md`](./07-implementation-plan.md) | `[x]` | 12 спринтов, ~44 дня |

**Ревью:** финансовый движок — на проверку у лида (позже).

---

## Спринт 0 — Инициализация ⏸ (~15%)

> Отложен по решению: сначала бизнес-логика, Docker/Celery/CI — ближе к деплою.

### Сделано

- `[x]` Django-проект: `config/`, `manage.py`, `apps/users/`
- `[x]` DRF + JWT (simplejwt) + CORS + drf-spectacular
- `[x]` `core/`: `exceptions.py`, `pagination.py`, `responses.py`
- `[x]` `.env.example`, `python-dotenv`, PostgreSQL через env
- `[x]` `docker-compose.yml` — только PostgreSQL 16
- `[x]` `requirements.txt`
- `[x]` `README.md` — quick start

### Не сделано (отложено)

- `[ ]` settings: `base` / `development` / `production` (сейчас один `settings.py`)
- `[ ]` Redis, MinIO в docker-compose
- `[ ]` Celery + beat
- `[ ]` `GET /api/v1/health/`
- `[ ]` Dockerfile, nginx, CI
- `[ ]` Pre-commit (ruff, mypy)
- `[ ]` Makefile / dev-скрипты

**Критерий готовности:** `docker compose up` → health 200, Celery worker жив.

---

## Спринт 1 — Auth + Users ✅

**Критерий:** регистрация → вход → профиль → уведомления. **Выполнен.**

### Модели (`apps/users/models.py`)

| Модель | Таблица | Статус |
|---|---|---|
| `User` (email, phone, invited_by) | `users_user` | `[x]` |
| `Profile` (public_id RERISE-XXXX, язык) | `users_profile` | `[x]` |
| `ReferralCode` | `users_referral_code` | `[x]` |
| `NotificationSettings` | `users_notification_settings` | `[x]` |
| `Notification` | `users_notification` | `[x]` |

### Сервисный слой

| Компонент | Статус | Что делает |
|---|---|---|
| `UserRegistrationService` | `[x]` | Регистрация, referral → `invited_by`, автогенерация profile/code |
| `AuthenticationService` | `[x]` | Login, refresh, `last_login_at` |
| `ProfileUpdateService` | `[x]` | PATCH профиля, уникальность phone |
| `selectors.py` | `[x]` | Read-запросы с prefetch |
| `utils.py` | `[x]` | Генераторы `public_id`, referral code |

### API (все в Swagger: `/api/docs/`)

| Метод | Путь | Статус |
|---|---|---|
| POST | `/api/v1/auth/register` | `[x]` |
| POST | `/api/v1/auth/login` | `[x]` |
| POST | `/api/v1/auth/refresh` | `[x]` |
| GET | `/api/v1/me` | `[x]` |
| GET | `/api/v1/me/summary` | `[x]` |
| GET/PATCH | `/api/v1/me/profile` | `[x]` |
| POST | `/api/v1/me/invite-link` | `[x]` |
| GET | `/api/v1/notifications` | `[x]` |
| PATCH | `/api/v1/notifications/{id}/read` | `[x]` |
| PATCH | `/api/v1/notifications/read-all` | `[x]` |
| PATCH | `/api/v1/me/notifications` | `[x]` |

### Тесты и инфра

- `[x]` 6 тестов в `apps/users/tests.py` — все проходят
- `[x]` Миграции `0001_initial` применены
- `[x]` Django Admin: User, Profile, ReferralCode, Notification*
- `[x]` PostgreSQL (локально, БД `Rerise`)

### Заглушки (осознанно — следующие спринты)

| Поле / блок | Где | Когда |
|---|---|---|
| `subscription` в `/me`, `/me/summary` | `serializers.py` | Спринт 2 |
| `is_partner` в `/me` | `serializers.py` | Спринт 3 |
| `partner` в profile | `serializers.py` | Спринт 3 |
| Бинарное размещение при регистрации | — | Спринт 3 |
| Telegram auth | — | После MVP |

---

## Спринт 2 — Commerce core ✅

**Критерий:** купить тариф через admin confirm → доступ + subscription. **Выполнен.**

### Модели (`apps/commerce/`)

| Модель | Таблица | Статус |
|---|---|---|
| `Product` | `commerce_product` | `[x]` |
| `TariffPlan` | `commerce_tariff_plan` | `[x]` |
| `Order` | `commerce_order` | `[x]` |
| `Payment` | `commerce_payment` | `[x]` |
| `UserAccess` | `commerce_user_access` | `[x]` |
| `Subscription` | `commerce_subscription` | `[x]` |

### Seed (`python manage.py seed_commerce`)

- `[x]` Rise $90, Rise Pro $300, Rise Pro Max $900
- `[x]` Subscription $30
- `[x]` Token packs: 1000 ($10), 5000 ($40)

### API

| Метод | Путь | Статус |
|---|---|---|
| GET | `/api/v1/store/tariffs` | `[x]` публичный |
| GET | `/api/v1/store/tokens` | `[x]` |
| POST | `/api/v1/store/orders` | `[x]` |
| GET | `/api/v1/store/orders/{id}` | `[x]` |

### Сервисы и провайдеры

| Компонент | Статус |
|---|---|
| `ManualCryptoProvider` | `[x]` |
| `OrderService.create_order` | `[x]` |
| `PaymentConfirmationService` (Admin Confirm) | `[x]` |
| `OrderFulfillmentService` — скелет | `[x]` access + subscription, без бонусов |
| `AccessService.grant_tariff` / `upgrade` / `extend` | `[x]` |
| `subscription` в `/me` и `/me/summary` | `[x]` |

### Тесты

- `[x]` 10 commerce-тестов (заказ, confirm, upgrade, renewal validation, /me subscription)
- `[x]` 16/16 тестов всего

### Отложено (следующие спринты)

| Что | Когда |
|---|---|
| `BonusEngine`, PV, бинар | Спринт 5 |
| `TokenService` (начисление токенов) | Спринт 8 |
| `ActivityService` (partner active/inactive) | Спринт 3 |
| `CryptoBotProvider` + webhook | Спринт 10 |
| Авто-expire pending заказов (60 мин) | Celery, спринт 0/10 |

---

## Спринт 3 — Partner structure ✅

**Критерий:** 3 юзера в цепочке спонсорства, размещены в бинаре. **Выполнен.**

### Модели (`apps/partner/`)

| Модель | Таблица | Статус |
|---|---|---|
| `PartnerProfile` | `partner_profile` | `[x]` |
| `SponsorLink` | `partner_sponsor_link` | `[x]` |
| `BinaryPlacement` | `partner_binary_placement` | `[x]` |
| `BinaryBalance` | `partner_binary_balance` | `[x]` |

### Сервисы

| Компонент | Статус |
|---|---|
| `BinaryPlacementService` (BFS) | `[x]` |
| Первый личный → нога спонсора | `[x]` |
| Spillover (BFS по ноге) | `[x]` |
| `ActivityService` — sync из subscription | `[x]` |
| `PartnerActivationService` — при покупке тарифа | `[x]` |
| Хук в `OrderFulfillmentService` | `[x]` |

### API

| Метод | Путь | Статус |
|---|---|---|
| GET | `/api/v1/partner/invited` | `[x]` |
| `is_partner` в `/me` | `[x]` |
| `partner` блок в `/me/profile` | `[x]` |

### Тесты

- `[x]` 4 partner-теста (цепочка 3 юзеров, invited, /me, profile)
- `[x]` 22/22 тестов всего (~26 сек)

### Исправлено в процессе

- Root в бинаре: `parent=None` (раньше `parent=self` блокировал слот `(parent, leg)`)

---

## Спринт 4 — Ledger + Wallet ✅

**Критерий:** ledger append-only, баланс пересчитывается, заявка на вывод.

**Спека:** [`05-financial-engine.md`](./05-financial-engine.md) § Ledger.

### Модели

- `[x]` `ledger_rule_version`, `ledger_entry`, `ledger_adjustment_debt`
- `[x]` `wallet_balance`, `wallet_withdrawal_request`, `wallet_saved_address`

### Сервисы

- `[x]` `LedgerWriter` (credit/debit, immutable, idempotency_key)
- `[x]` `WalletUpdater`
- `[x]` Seed `rule_version` v1.0 (`seed_ledger_rules`)
- `[x]` `AdjustmentService` (скелет)

### API

- `[x]` `GET /api/v1/wallet`
- `[x]` `GET /api/v1/wallet/transactions`
- `[x]` `POST /api/v1/wallet/withdraw`
- `[x]` `PUT /api/v1/wallet/address`

### Тесты

- `[x]` 34/34 тестов всего (~30 сек)

---

## Спринт 5 — Bonus Engine ✅ ⚠️ Критический

**Критерий:** покупка Rise Pro → личный бонус + PV + бинар + уведомления. TC-PUR, TC-BIN проходят. **Выполнен.**

**Спека:** [`05-financial-engine.md`](./05-financial-engine.md) — 22 тест-кейса.

### Сервисы (`apps/partner/engine.py`)

- `[x]` `PersonalBonusService` — личный бонус `min(тариф спонсора, тариф покупки)`
- `[x]` `PvDistributionService` — PV вверх по бинару, глубина по тарифу
- `[x]` `BinaryCollapseService` — схлоп `min(left,right)`, доход `PV/10`
- `[x]` `MatchingBonusService` — 10% по 1/2/3 спонсорским линиям
- `[x]` `QualificationWeekService` — недельный счётчик схлопа (пн MSK)
- `[x]` `StatusQualificationService` — 16 рангов, лестница, премии
- `[x]` `FastStartService` — 4 Pro/Max за 30 дней → $90
- `[x]` `BonusEngine` — оркестратор (purchase / upgrade / renewal)
- `[x]` Подключён к `OrderFulfillmentService`
- `[x]` `check_activity_expiration` (management command; Celery-ready)
- `[~]` `reset_qualification_week` — не нужен: недели хранятся отдельными строками (`week_start`), новый период стартует с 0 автоматически

### Модели

- `[x]` `partner_qualification_week`, `partner_rank_history`, `partner_fast_start`

### API

- `[x]` `GET /api/v1/partner/dashboard`
- `[x]` `GET /api/v1/partner/ranks`
- `[x]` `GET /api/v1/partner/structure`

### Тесты (19 в `test_engine.py`)

- `[x]` TC-PUR-01..06, TC-UPG-01/02, TC-REN-01/02
- `[x]` TC-BIN-01..03, TC-MATCH-01, TC-FS-01/02, TC-RANK-01
- `[x]` Активность (expire), dashboard/ranks/structure API
- `[x]` 54/54 тестов всего (~72 сек)

### Отложено (не утверждено / инфраструктура)

- Celery-планировщик (Спринт 0) — логика готова как management-команды
- `check_12m_inactivity` (обнуление PV/тарифа) — модели готовы, включим с Celery
- Автопозиционирование left/right со 2-го личного — заглушка BFS слева

---

## Спринт 6 — Academy ✅

**Критерий:** открыть курс → пройти урок → прогресс обновился. **Выполнен.**

### Модели (`apps/academy/`)

- `[x]` `academy_program`, `academy_module`, `academy_lesson`
- `[x]` `academy_lesson_resource`
- `[x]` `academy_user_progress`, `academy_module_progress`, `academy_lesson_progress`

### Сервисы

- `[x]` `ProgressService` — start / video position / complete + пересчёт %
- `[x]` `ProgramCatalogService` — кэш module_count / lesson_count
- `[x]` Доступ по тарифу (`access.py` + `required_tariff`)

### API

- `[x]` `GET /api/v1/programs` (filter, search, pagination)
- `[x]` `GET /api/v1/programs/{slug}`
- `[x]` `GET /api/v1/lessons/{id}`
- `[x]` `POST /api/v1/lessons/{id}/start`
- `[x]` `PATCH /api/v1/lessons/{id}/progress`
- `[x]` `POST /api/v1/lessons/{id}/complete`

### Seed

- `[x]` `seed_academy` — GPT-NOW (6 модулей / 21 урок) + AI Design + AI Video
- `[~]` MinIO/S3 для видео — placeholder URL `/media/lessons/...` (инфра в Спринте 0)

### Тесты

- `[x]` 63/63 тестов всего (~104 сек)

---

## Спринт 7 — Content + Home ✅

**Критерий:** главная отдаёт баннеры + программы, материалы фильтруются по тарифу. **Выполнен.**

### Модели (`apps/content/`)

- `[x]` `content_banner`
- `[x]` `content_material_category`, `content_material_group`, `content_material_file`
- `[x]` `content_telegram_chat`

### Сервисы / доступ

- `[x]` Материалы — доступ по `required_tariff` (rise / rise-pro / rise-pro-max)
- `[x]` Чаты — open/service всем; invite по `min_rank` (highest_rank)
- `[x]` `MaterialCatalogService.refresh_group_file_count`

### API

- `[x]` `GET /api/v1/home` — баннеры, AI Hub widget, programs_count
- `[x]` `GET /api/v1/materials` (category, search)
- `[x]` `GET /api/v1/materials/groups/{id}`
- `[x]` `GET /api/v1/materials/files/{id}/download` → 302
- `[x]` `GET /api/v1/chats`

### Seed

- `[x]` `seed_content` — 2 баннера, 4 категории / 8 групп / 17 файлов, 5 чатов
- `[~]` MinIO/S3 — placeholder URL `/media/...` (инфра в Спринте 0)

### Тесты

- `[x]` 72/72 тестов всего

### Отложено на Спринт 9

- `[x]` Финальная сборка `/home` (next action, continue learning, partner widget) — сделано в Sprint 9

---

## Спринт 8 — AI Hub ✅

**Критерий:** запустить сценарий → получить ответ → токены списались. **Выполнен** (каркас + MockProvider).

### Модели (`apps/ibox/`)

- `[x]` `ibox_scenario`, `ibox_chat_session`, `ibox_chat_message`
- `[x]` `ibox_token_balance`, `ibox_token_transaction`

### Сервисы

- `[x]` `TokenService` — credit / debit + `INSUFFICIENT_TOKENS`
- `[x]` `ChatService` — start session / send message
- `[x]` AI Gateway: `MockAIProvider` (default) + `OpenAIProvider` (`IBOX_AI_PROVIDER`)
- `[x]` Начисление токенов при покупке тарифа / token pack (commerce fulfill)

### API

- `[x]` `GET /api/v1/ibox/scenarios`
- `[x]` `POST /api/v1/ibox/sessions`
- `[x]` `POST /api/v1/ibox/sessions/{id}/messages`
- `[x]` `GET /api/v1/ibox/sessions`, `GET /api/v1/ibox/sessions/{id}`

### Seed

- `[x]` `seed_ibox` — 10 сценариев
- `[x]` Тарифы: rise 1000 / pro 5000 / max 15000 initial tokens

### Тесты

- `[x]` 79/79 тестов всего

### Не в scope (осознанно)

- `[ ]` Стриминг, мультимодальность, роутинг моделей
- `[ ]` Прод-тюнинг промптов / Projects

---

## Спринт 9 — CRM + Dashboard polish ✅

**Критерий:** кабинет на фронте можно полностью накатить на API. **Выполнен.**

### CRM (`apps/crm/`)

- `[x]` `crm_lead_stage`, `crm_lead`, `crm_lead_activity`
- `[x]` Seed: 4 стадии (new / contact / meeting / deal)
- `[x]` `GET /api/v1/crm/leads` — канбан
- `[x]` `POST /api/v1/crm/leads`
- `[x]` `PATCH /api/v1/crm/leads/{id}`
- `[x]` `DELETE /api/v1/crm/leads/{id}` → 204

### Partner / Home

- `[x]` `POST /api/v1/partner/renew` — order на subscription $30
- `[x]` Dashboard: `can_renew` (+ уже готовые виджеты Sprint 5)
- `[x]` `GET /home` — next_action, continue_learning, partner_summary, token_balance

### Тесты

- `[x]` 86/86 тестов всего

---

## Спринт 10 — CryptoBot + Deploy ⏳

### Оплата (сделано, без прод-деплоя)

- `[x]` `CryptoBotProvider` + `MockCryptoProvider` + registry (`manual` / `mock` / `cryptobot`)
- `[x]` Webhook `POST /api/v1/store/webhook/cryptobot/<secret>/` + HMAC-подпись
- `[x]` Replay protection (Django cache / Redis)
- `[x]` Celery `fulfill_order` + beat `sync_pending_payments` (локально eager без брокера)
- `[x]` Тесты TC-ORD-03..05 (+ expire sync, mock payment_url)

### Деплой (отложено — нет фронта)

- `[ ]` Dockerfile / docker-compose.prod / nginx / HTTPS
- `[ ]` CryptoBot webhook URL → production
- `[ ]` Health check + monitoring

---

## Спринт 11 — Admin + Polish ✅

- `[x]` Admin: все модели с фильтрами; Confirm Payment, Approve/Reject/Mark Paid
- `[x]` Admin: Create Adjustment (debt + staff API), Block/Unblock User
- `[x]` `admin_ops` — `AuditLog`, `SystemConfig`, автозапись ключевых действий
- `[x]` Staff API: `/api/v1/admin/ledger/adjustments`, `/users/{id}/block`, `/withdrawals/{id}`, `/audit-log`
- `[x]` OpenAPI polish (`SPECTACULAR_SETTINGS`), `seed_demo`, e2e journey test
- `[x]` README: quick start + deployment draft

### Тесты

- `[x]` `apps.admin_ops` — 7/7 (adjustments, block, withdrawals, audit, seed_demo, e2e)

---

## Вне MVP (backlog)

| Фича | Приоритет |
|---|---|
| Job board (`/labor`) | Низкий |
| Creator marketplace | Низкий |
| Telegram Mini App auth | После MVP |
| Автовывод USDT | После MVP |
| i18n EN/ES (контент) | После RU launch |
| Полный Docker/Celery/CI (спринт 0) | Перед прод-деплоем |

---

## Ключевые бизнес-правила (напоминание)

Из [`marketingplan.md`](./marketingplan.md):

- Тарифы: **Rise $90**, **Rise Pro $300**, **Rise Pro Max $900**; продление **$30/мес**
- Личный бонус = `min(тариф спонсора, тариф покупателя)`
- Бинар: 10 collapsed PV = $1
- Matching: 10% от бинарного дохода, 1/2/3 линии спонсора
- Fast start: Pro/Max, 30 дней, 4 личных Pro/Max → $90
- Спонсор и бинарное место **неизменяемы** после регистрации

---

## Как обновлять этот файл

1. Закончили задачу в спринте → `[ ]` → `[x]`
2. Сделали заглушку → `[~]` + комментарий «когда доделаем»
3. Завершили спринт → обновить таблицу «Прогресс» вверху
4. Крупные решения (отложили/изменили scope) → запись в секцию спринта

---

## Следующий шаг

**Деплой (хвост спринта 10)** — когда будет фронт/staging.  
Сейчас: `PAYMENT_PROVIDER=cryptobot` + токен testnet для проверки оплаты; иначе `manual` / `mock`.
