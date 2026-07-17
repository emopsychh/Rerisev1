# ReRise — Этап 7: План реализации

**Статус:** черновик на утверждение  
**Разработчик:** 1 человек (Python/Django)  
**Деплой:** VPS  
**Версия:** 0.1 · 15.07.2026

---

## 1. Структура проекта

```
rerise/
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── apps/
│   ├── users/
│   ├── partner/
│   ├── ledger/
│   ├── wallet/
│   ├── commerce/
│   ├── academy/
│   ├── ibox/
│   ├── content/
│   ├── crm/
│   └── admin_ops/
├── core/
│   ├── exceptions.py
│   ├── permissions.py
│   └── pagination.py
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
├── docs/                    # ← уже есть
├── fixtures/                # seed data
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
└── tests/
    └── integration/
```

### Зависимости (requirements/base.txt)

```
Django>=5.0
djangorestframework>=3.15
djangorestframework-simplejwt>=5.3
django-cors-headers>=4.3
drf-spectacular>=0.27
psycopg[binary]>=3.1
celery>=5.3
redis>=5.0
django-storages>=1.14
boto3>=1.34
Pillow>=10.0
python-dateutil>=2.8
pytz>=2024.1
```

Опционально позже: `cryptobot` / `httpx` для CryptoBot API.

---

## 2. Спринты

Оценка для **одного разработчика**, full-time. С буфером ~20%.

| Спринт | Название | Дней | Результат |
|---:|---|---:|---|
| 0 | Инициализация | 2 | Проект, Docker, CI skeleton |
| 1 | Auth + Users | 3 | Регистрация, вход, профиль |
| 2 | Commerce core | 4 | Заказы, manual payment |
| 3 | Partner structure | 4 | Спонсор, бинар, размещение |
| 4 | Ledger + Wallet | 5 | Financial Engine v1 |
| 5 | Bonus engine | 5 | Все начисления + тесты |
| 6 | Academy | 4 | Программы, модули, уроки |
| 7 | Content + Home | 3 | Баннеры, материалы, чаты |
| 8 | iBox | 4 | AI-чат, токены, сценарии |
| 9 | CRM + Dashboard API | 3 | Кабинет, лиды |
| 10 | CryptoBot + Deploy | 4 | Webhook, VPS, HTTPS |
| 11 | Admin + Polish | 3 | Audit, корректировки, seed |
| | **Итого** | **~44** | **MVP backend** |

---

## 3. Спринт 0: Инициализация (2 дня)

### День 1

- [ ] `django-admin startproject` + структура apps
- [ ] `docker-compose.yml`: postgres, redis, minio (файлы)
- [ ] settings: base / development / production
- [ ] DRF + JWT + CORS + drf-spectacular
- [ ] Базовые `core/` utilities (exceptions, pagination)
- [ ] `.env.example`

### День 2

- [ ] Celery + Redis подключение
- [ ] Базовый `Makefile` или `scripts/dev.sh`
- [ ] Pre-commit: ruff, mypy (базово)
- [ ] README с инструкцией запуска
- [ ] Первый `docker compose up` — всё стартует

**Критерий готовности:** `docker compose up` → API отвечает `GET /api/v1/health/` → 200.

---

## 4. Спринт 1: Auth + Users (3 дня)

### Модели

- `users_user`, `users_profile`, `users_referral_code`
- `users_notification_settings`, `users_notification`

### API

- `POST /auth/register` (с referral_code)
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /me`
- `GET /me/summary`
- `GET/PATCH /me/profile`
- `POST /me/invite-link`

### Задачи

- [ ] Кастомная User model
- [ ] JWT через simplejwt
- [ ] Автогенерация `public_id` (RERISE-XXXX) и referral_code
- [ ] При регистрации с referral_code — сохранить `invited_by_id` (без бинара пока)
- [ ] Базовые тесты auth

**Критерий:** можно зарегистрироваться, войти, получить профиль.

---

## 5. Спринт 2: Commerce core (4 дня)

### Модели

- `commerce_product`, `commerce_tariff_plan`
- `commerce_order`, `commerce_payment`
- `commerce_user_access`, `commerce_subscription`

### API

- `GET /store/tariffs`
- `GET /store/tokens`
- `POST /store/orders`
- `GET /store/orders/{id}`

### Задачи

- [ ] Seed: 3 тарифа + subscription + token packs
- [ ] `OrderService.create_order`
- [ ] `ManualCryptoProvider` (dev)
- [ ] Admin action: Confirm Payment
- [ ] `OrderFulfillmentService` — скелет (без бонусов пока)
- [ ] `AccessService.grant_tariff`
- [ ] `ActivityService.grant_initial_month`

**Критерий:** купить тариф через admin confirm → доступ выдан, subscription создан.

---

## 6. Спринт 3: Partner structure (4 дня)

### Модели

- `partner_profile`, `partner_sponsor_link`
- `partner_binary_placement`, `partner_binary_balance`

### Сервисы

- [ ] `BinaryPlacementService` (BFS-заглушка)
- [ ] Правило первого личного → нога спонсора
- [ ] Spillover
- [ ] `ActivityService` (active / inactive states)
- [ ] При покупке тарифа → размещение в бинаре

### API (базово)

- `GET /partner/invited`

**Критерий:** 3 тестовых юзера в цепочке спонсорства, размещены в бинаре.

---

## 7. Спринт 4: Ledger + Wallet (5 дней)

### Модели

- `ledger_rule_version`, `ledger_entry`
- `ledger_adjustment_debt`
- `wallet_balance`, `wallet_withdrawal_request`, `wallet_saved_address`

### Сервисы

- [x] `LedgerWriter` (credit / debit, append-only)
- [x] `WalletUpdater` (пересчёт из ledger)
- [x] Seed `rule_version` v1.0 с формулами
- [x] `AdjustmentService` (скелет)

### API

- [x] `GET /wallet`
- [x] `GET /wallet/transactions`
- [x] `POST /wallet/withdraw`
- [x] `PUT /wallet/address`

**Критерий:** ledger записи создаются, баланс пересчитывается, вывод создаёт заявку.

---

## 8. Спринт 5: Bonus Engine (5 дней)

**Самый важный спринт.** Реализовать по `docs/05-financial-engine.md`.

### Порядок внутри спринта

| День | Сервис | Тест-кейсы |
|---:|---|---|
| 1 | `PersonalBonusService` | TC-PUR-01..06 |
| 2 | `PvDistributionService` + `BinaryCollapseService` | TC-BIN-01..03 |
| 3 | `MatchingBonusService` | TC-MATCH-01 |
| 4 | `StatusQualificationService` + `QualificationWeekService` | TC-RANK-01..02 |
| 5 | `FastStartService` + upgrade + renewal | TC-UPG, TC-REN, TC-FS |

### Задачи

- [x] `BonusEngine` — оркестратор
- [x] Подключить к `OrderFulfillmentService`
- [~] Celery: `reset_qualification_week` — не нужен (недели = строки по `week_start`)
- [x] `check_activity_expiration` — management command (Celery-ready)
- [x] Integration tests: полная цепочка покупки

### API

- [x] `GET /partner/dashboard`
- [x] `GET /partner/ranks`
- [x] `GET /partner/structure`

**Критерий:** покупка Rise Pro → личный бонус + PV + бинар + уведомления. Все TC-PUR, TC-BIN проходят. **Выполнен (53/53 тестов).**

---

## 9. Спринт 6: Academy (4 дня)

### Модели

- `academy_program`, `academy_module`, `academy_lesson`
- `academy_lesson_resource`
- `academy_user_progress`, `academy_module_progress`, `academy_lesson_progress`

### API

- [x] `GET /programs` (с фильтрами)
- [x] `GET /programs/{slug}`
- [x] `GET /lessons/{id}`
- [x] `POST /lessons/{id}/start`
- [x] `PATCH /lessons/{id}/progress`
- [x] `POST /lessons/{id}/complete`

### Задачи

- [x] Seed: 2–3 программы (GPT-NOW с 6 модулями / 21 урок — mock)
- [x] Пересчёт progress_percent
- [x] Проверка доступа по тарифу
- [~] Загрузка видео в MinIO/S3 — placeholder URL (инфра Спринт 0)

**Критерий:** открыть курс → пройти урок → прогресс обновился. **Выполнен (60/60 тестов).**

---

## 10. Спринт 7: Content + Home (3 дня) ✅

### Модели

- `content_banner`, `content_material_*`, `content_telegram_chat`

### API

- [x] `GET /home`
- [x] `GET /materials`, `GET /materials/groups/{id}`
- [x] `GET /chats`
- [x] `GET /notifications` (если не в спринте 1)

### Задачи

- [x] Seed: баннеры, 8 разделов материалов, 5 чатов
- [~] Файловое хранилище (MinIO) — placeholder URLs
- [x] Проверка доступа к материалам по тарифу

**Критерий:** главная отдаёт баннеры + программы, материалы фильтруются.

---

## 11. Спринт 8: iBox (4 дня) ✅

### Модели

- `ibox_scenario`, `ibox_chat_session`, `ibox_chat_message`
- `ibox_token_balance`, `ibox_token_transaction`

### API

- [x] `GET /ibox/scenarios`
- [x] `POST /ibox/sessions`
- [x] `POST /ibox/sessions/{id}/messages`
- [x] `GET /ibox/sessions`, `GET /ibox/sessions/{id}`

### Задачи

- [x] Seed: 10 сценариев
- [x] AI Gateway: абстракция провайдера (Mock + OpenAI)
- [x] Списание токенов через `TokenService`
- [x] Начисление токенов при покупке тарифа (из спринта 2)

**Критерий:** запустить сценарий → получить ответ → токены списались.

---

## 12. Спринт 9: CRM + Dashboard polish (3 дня) ✅

### Модели

- `crm_lead_stage`, `crm_lead`, `crm_lead_activity`

### API

- [x] CRUD `/crm/leads`
- [x] Доработка `/partner/dashboard` (все виджеты + `can_renew`)
- [x] `POST /partner/renew`

### Задачи

- [x] Seed: 4 стадии CRM
- [x] Канбан-ответ (группировка по stage)
- [x] `GET /home` — финальная сборка

**Критерий:** кабинет на фронте можно полностью накатить на API.

---

## 13. Спринт 10: CryptoBot + Deploy (4 дня)

### День 1–2: CryptoBot

- [ ] `CryptoBotProvider` реализация
- [ ] Webhook view + signature verification
- [ ] Replay protection (Redis)
- [ ] Celery `fulfill_order`
- [ ] Celery beat: sync pending payments
- [ ] Тесты TC-ORD-03..05

### День 3–4: VPS Deploy

- [ ] Dockerfile (production)
- [ ] docker-compose.prod.yml (api, celery, beat, postgres, redis, nginx)
- [ ] Nginx reverse proxy + HTTPS (Let's Encrypt)
- [ ] Env secrets на сервере
- [ ] `collectstatic`, media volume
- [ ] CryptoBot webhook URL → production
- [ ] Health check + basic monitoring

**Критерий:** реальная оплата USDT через CryptoBot → тариф выдан.

---

## 14. Спринт 11: Admin + Polish (3 дня)

- [ ] Django Admin: все модели с фильтрами
- [ ] Admin: Confirm Payment, Approve Withdrawal
- [ ] Admin: Create Adjustment, Block User
- [ ] `admin_ops_audit_log` — автозапись действий
- [ ] OpenAPI docs (`/api/schema/`)
- [ ] Seed-скрипт полного demo-окружения
- [ ] Integration test: end-to-end user journey
- [ ] README: deployment guide

**Критерий:** руководитель может управлять системой через Admin.

---

## 15. Диаграмма зависимостей спринтов

```
S0 Init
 └── S1 Auth
      └── S2 Commerce
           └── S3 Partner
                └── S4 Ledger
                     └── S5 Bonus Engine ★
                          ├── S6 Academy
                          ├── S7 Content
                          ├── S8 iBox
                          └── S9 CRM
                               └── S10 Crypto + Deploy
                                    └── S11 Admin
```

**S5 — блокер.** До него не трогаем dashboard с реальными цифрами.  
**S6, S7, S8, S9** — можно частично параллелить после S5.

---

## 16. Что НЕ входит в MVP

| Функция | Когда |
|---|---|
| Биржа труда | После MVP |
| Creator Marketplace | Этап 2 |
| Telegram Mini App auth | Позже |
| Авто-вывод USDT | После MVP |
| Внутренние переводы | После утверждения правил |
| i18n EN/ES | После MVP |
| KYC / 2FA | После MVP |
| AI image/video generation | После MVP (только chat) |

---

## 17. Риски и митигация

| Риск | Вероятность | Митигация |
|---|---|---|
| Ошибки в bonus engine | Высокая | 22 тест-кейса, ledger, ревью руководителя |
| CryptoBot API изменится | Средняя | Абстракция провайдера |
| Алгоритм бинара не утверждён | Средняя | Заглушка BFS, легко заменить |
| Один разработчик — bottleneck | Высокая | Чёткие спринты, docs-first |
| Продуктовые лимиты не утверждены | Высокая | SystemConfig + seed, не хардкод |
| VPS без опыта деплоя | Средняя | Docker, пошаговый README |

---

## 18. Definition of Done (MVP)

MVP backend считается готовым, когда:

1. ✅ Пользователь регистрируется с реферальным кодом
2. ✅ Покупает тариф через CryptoBot (USDT)
3. ✅ Получает доступ, токены, партнёрский кабинет
4. ✅ Спонсор получает личный бонус, PV, бинар
5. ✅ Проходит урок в Academy, прогресс сохраняется
6. ✅ Использует AI Box, токены списываются
7. ✅ Видит материалы, чаты, главную
8. ✅ Создаёт лиды в CRM
9. ✅ Подаёт заявку на вывод USDT
10. ✅ Админ управляет через Django Admin
11. ✅ Все финансовые операции в ledger
12. ✅ Деплой на VPS с HTTPS

---

## 19. Документация проекта (итог)

| Файл | Этап | Содержание |
|---|---|---|
| `productcore.md` | — | Продуктовое ядро |
| `marketingplan.md` | — | Бизнес-правила |
| `docs/03-database-schema-draft.md` | 3 | 48 таблиц |
| `docs/04-api-contracts.md` | 4 | ~48 эндпоинтов |
| `docs/05-financial-engine.md` | 5 | Bonus engine |
| `docs/06-commerce-crypto.md` | 6 | Платежи |
| `docs/07-implementation-plan.md` | 7 | Спринты |

---

## 20. Следующий шаг

**Начать Спринт 0:** инициализация Django-проекта.

Команда для старта:
```bash
# После утверждения плана:
docker compose up -d
python manage.py migrate
python manage.py seed
python manage.py runserver
```

Готов начать код, когда скажешь.
