# ReRise — Этап 3: Черновик схемы БД

**Статус:** черновик на утверждение  
**СУБД:** PostgreSQL 16  
**ORM:** Django  
**Версия:** 0.2 · 15.07.2026

---

## Принципы проектирования

1. **Деньги и PV — только через журнал.** Балансы — производные от `ledger_entries` (кэш в `wallet_balances` допустим, но пересчитываемый).
2. **Правила начислений versioned.** Формулы не хардкодятся — хранятся в `rule_versions`.
3. **Спонсор и бинар неизменяемы** после размещения (DB constraint + бизнес-логика).
4. **Soft delete не используем для финансов.** Отмена = новая запись `adjustment` в ledger.
5. **UUID для публичных ID** (referral, order), **bigint PK** внутри.
6. **Все timestamps в UTC**, квалификационная неделя — MSK (Europe/Moscow) на уровне сервиса.

---

## Общие поля (миксин)

Все таблицы (кроме ledger) содержат:

```
id          BIGSERIAL PRIMARY KEY
created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
```

`ledger_entries` — только `created_at` (immutable).

---

# 1. users

## users_user

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| email | VARCHAR(255) UNIQUE NOT NULL | |
| phone | VARCHAR(20) UNIQUE NULL | |
| password_hash | VARCHAR(255) NOT NULL | |
| is_active | BOOLEAN DEFAULT true | |
| is_staff | BOOLEAN DEFAULT false | |
| last_login_at | TIMESTAMPTZ NULL | |

**Индексы:** `email`, `phone`

---

## users_profile

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT UNIQUE FK → users_user | |
| first_name | VARCHAR(100) | |
| last_name | VARCHAR(100) | |
| avatar_url | VARCHAR(500) NULL | |
| country | VARCHAR(100) NULL | |
| city | VARCHAR(100) NULL | |
| language | VARCHAR(5) DEFAULT 'ru' | ru / en / es |
| public_id | VARCHAR(20) UNIQUE | RERISE-1842 |

**Индексы:** `public_id`

---

## users_referral_code

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT UNIQUE FK → users_user | |
| code | VARCHAR(32) UNIQUE NOT NULL | |
| is_active | BOOLEAN DEFAULT true | |

---

## users_notification_settings

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT UNIQUE FK → users_user | |
| email_enabled | BOOLEAN DEFAULT true | |
| push_enabled | BOOLEAN DEFAULT true | |

---

## users_notification

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | |
| type | VARCHAR(50) | bonus / access / system / crm |
| title | VARCHAR(255) | |
| body | TEXT | |
| is_read | BOOLEAN DEFAULT false | |
| metadata | JSONB DEFAULT '{}' | |

**Индексы:** `(user_id, is_read)`, `(user_id, created_at DESC)`

---

# 2. partner

## partner_profile

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT UNIQUE FK → users_user | |
| tariff_id | VARCHAR(20) NULL | rise / rise-pro / rise-pro-max |
| is_active | BOOLEAN DEFAULT false | |
| activity_until | TIMESTAMPTZ NULL | до 24.07.2026 |
| tariff_lost_at | TIMESTAMPTZ NULL | после 12 мес неактивности |
| current_rank | VARCHAR(50) DEFAULT 'partner_1' | Партнёр I … Визионер |
| highest_rank | VARCHAR(50) DEFAULT 'partner_1' | навсегда |
| invited_by_id | BIGINT FK → users_user NULL | прямой спонсор |
| placed_at | TIMESTAMPTZ NULL | дата размещения в структуре |

**Индексы:** `invited_by_id`, `tariff_id`, `is_active`, `current_rank`

---

## partner_sponsor_link

Неизменяемая связь спонсорства.

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| partner_id | BIGINT UNIQUE FK → partner_profile | |
| sponsor_id | BIGINT FK → partner_profile | |
| placed_at | TIMESTAMPTZ NOT NULL | |

**Constraint:** нет UPDATE sponsor_id после INSERT.

---

## partner_binary_placement

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| partner_id | BIGINT UNIQUE FK → partner_profile | |
| parent_id | BIGINT FK → partner_profile | |
| leg | VARCHAR(5) NOT NULL | left / right |
| depth | SMALLINT NOT NULL | физический уровень |
| placed_at | TIMESTAMPTZ NOT NULL | |

**Индексы:** `(parent_id, leg)`, `depth`  
**Constraint:** нет UPDATE parent_id / leg после INSERT.

---

## partner_binary_balance

Текущий несхлопнутый остаток (кэш; источник истины — ledger).

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| partner_id | BIGINT UNIQUE FK → partner_profile | |
| left_pv | INTEGER DEFAULT 0 | |
| right_pv | INTEGER DEFAULT 0 | |
| is_frozen | BOOLEAN DEFAULT false | при неактивности |

---

## partner_qualification_week

Снимок текущей квалификационной недели.

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| partner_id | BIGINT FK → partner_profile | |
| week_start | DATE NOT NULL | понедельник МСК |
| collapsed_pv | INTEGER DEFAULT 0 | схлоп за неделю |
| active_personal_count | SMALLINT DEFAULT 0 | |
| binary_income_usd | DECIMAL(12,2) DEFAULT 0 | |

**Индексы:** `(partner_id, week_start)` UNIQUE

---

## partner_fast_start

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| partner_id | BIGINT UNIQUE FK → partner_profile | |
| window_start | TIMESTAMPTZ NOT NULL | |
| window_end | TIMESTAMPTZ NOT NULL | +30 дней |
| qualified_count | SMALLINT DEFAULT 0 | 0–4 |
| reward_paid | BOOLEAN DEFAULT false | |
| reward_paid_at | TIMESTAMPTZ NULL | |

---

## partner_team_depth_cache

Кэш глубины команды (пересчитывается при PV-событиях).

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| partner_id | BIGINT FK → partner_profile | |
| level | SMALLINT NOT NULL | L1–L15 |
| total_members | INTEGER DEFAULT 0 | |
| active_members | INTEGER DEFAULT 0 | |
| pv | INTEGER DEFAULT 0 | |
| calculated_at | TIMESTAMPTZ NOT NULL | |

**Индексы:** `(partner_id, level)` UNIQUE

---

## partner_rank_history

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| partner_id | BIGINT FK → partner_profile | |
| rank | VARCHAR(50) NOT NULL | |
| premium_usd | DECIMAL(12,2) | |
| achieved_at | TIMESTAMPTZ NOT NULL | |
| week_start | DATE NOT NULL | |

---

# 3. ledger

## ledger_rule_version

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| version | VARCHAR(20) UNIQUE | v1.0 |
| rules | JSONB NOT NULL | все формулы и лимиты |
| effective_from | TIMESTAMPTZ NOT NULL | |
| created_by_id | BIGINT FK → users_user NULL | |

Пример `rules`:
```json
{
  "binary": {"collapsed_pv_per_usd": 10},
  "subscription": {"price_usd": 30, "sponsor_reward_usd": 9, "pv": 9},
  "fast_start": {"window_days": 30, "required_partners": 4, "reward_usd": 90},
  "withdrawal": {"min_usd": 100, "currency": "USDT"},
  "tariffs": { ... }
}
```

---

## ledger_entry

**Append-only. Без UPDATE/DELETE.**

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | получатель |
| entry_type | VARCHAR(50) NOT NULL | см. список ниже |
| amount | DECIMAL(14,4) NOT NULL | |
| currency | VARCHAR(5) NOT NULL | USD / PV |
| direction | VARCHAR(10) NOT NULL | credit / debit |
| source_type | VARCHAR(50) NULL | order / partner / admin |
| source_id | BIGINT NULL | |
| rule_version_id | BIGINT FK → ledger_rule_version | |
| description | TEXT NULL | |
| metadata | JSONB DEFAULT '{}' | depth, leg, rank и т.д. |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |

**entry_type:**
```
purchase_pv, subscription_pv, upgrade_pv,
binary_collapse, personal_bonus, renewal_bonus,
binary_bonus, matching_bonus, status_premium,
fast_start_bonus, adjustment, withdrawal
```

**Индексы:**
- `(user_id, created_at DESC)`
- `(entry_type, created_at DESC)`
- `(source_type, source_id)`
- `(currency, user_id)`

---

## ledger_adjustment_debt

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | |
| amount_usd | DECIMAL(12,2) NOT NULL | |
| remaining_usd | DECIMAL(12,2) NOT NULL | |
| reason | TEXT NOT NULL | |
| status | VARCHAR(20) | open / paid / cancelled |
| created_by_id | BIGINT FK → users_user | |
| resolved_at | TIMESTAMPTZ NULL | |

---

# 4. wallet

## wallet_balance

Кэш баланса (пересчитывается из ledger).

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT UNIQUE FK → users_user | |
| available_usd | DECIMAL(12,2) DEFAULT 0 | доступно к выводу |
| pending_usd | DECIMAL(12,2) DEFAULT 0 | в обработке |
| total_earned_usd | DECIMAL(12,2) DEFAULT 0 | за всё время |

---

## wallet_withdrawal_request

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | |
| amount_usd | DECIMAL(12,2) NOT NULL | min 100 |
| usdt_address | VARCHAR(128) NOT NULL | |
| network | VARCHAR(20) NOT NULL | TRC20 / ERC20 (TBD) |
| status | VARCHAR(20) | pending / approved / paid / rejected |
| fee_usd | DECIMAL(12,2) DEFAULT 0 | |
| tx_hash | VARCHAR(128) NULL | |
| reviewed_by_id | BIGINT FK → users_user NULL | |
| paid_at | TIMESTAMPTZ NULL | |
| rejection_reason | TEXT NULL | |

**Индексы:** `(user_id, status)`, `(status, created_at)`

---

## wallet_saved_address

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | |
| address | VARCHAR(128) NOT NULL | |
| network | VARCHAR(20) NOT NULL | |
| is_default | BOOLEAN DEFAULT false | |

**Индексы:** `(user_id, is_default)`

---

# 5. commerce

## commerce_product

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| slug | VARCHAR(50) UNIQUE | rise / rise-pro / tokens-1000 |
| type | VARCHAR(20) | tariff / subscription / tokens / program |
| name | VARCHAR(255) | |
| description | TEXT NULL | |
| price_usd | DECIMAL(12,2) NOT NULL | |
| is_active | BOOLEAN DEFAULT true | |
| metadata | JSONB DEFAULT '{}' | |

---

## commerce_tariff_plan

Расширение для type=tariff.

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| product_id | BIGINT UNIQUE FK → commerce_product | |
| tariff_id | VARCHAR(20) UNIQUE | rise / rise-pro / rise-pro-max |
| included_months | SMALLINT DEFAULT 1 | |
| personal_bonus_cap_usd | DECIMAL(12,2) | 30 / 90 / 300 |
| purchase_pv_cap | INTEGER | 30 / 90 / 300 |
| binary_depth | SMALLINT | 3 / 9 / 15 |
| matching_lines | SMALLINT | 1 / 2 / 3 |
| quick_start_eligible | BOOLEAN | |
| initial_tokens | INTEGER DEFAULT 0 | стартовые токены |

---

## commerce_order

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | покупатель |
| product_id | BIGINT FK → commerce_product | |
| amount_usd | DECIMAL(12,2) NOT NULL | |
| status | VARCHAR(20) | pending / paid / cancelled / refunded |
| order_type | VARCHAR(20) | purchase / upgrade / renewal |
| previous_tariff_id | VARCHAR(20) NULL | для upgrade |
| paid_at | TIMESTAMPTZ NULL | |

**Индексы:** `(user_id, status)`, `(status, created_at)`

---

## commerce_payment

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| order_id | BIGINT FK → commerce_order | |
| provider | VARCHAR(50) | cryptobot / manual |
| external_id | VARCHAR(255) NULL | invoice id провайдера |
| amount_usd | DECIMAL(12,2) | |
| currency_crypto | VARCHAR(10) NULL | USDT |
| status | VARCHAR(20) | pending / paid / expired / failed |
| payment_url | TEXT NULL | ссылка на оплату |
| webhook_payload | JSONB NULL | сырой webhook |
| paid_at | TIMESTAMPTZ NULL | |

**Индексы:** `external_id`, `(provider, status)`

---

## commerce_user_access

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | |
| product_id | BIGINT FK → commerce_product | |
| granted_at | TIMESTAMPTZ NOT NULL | |
| expires_at | TIMESTAMPTZ NULL | |
| is_active | BOOLEAN DEFAULT true | |
| source_order_id | BIGINT FK → commerce_order NULL | |

**Индексы:** `(user_id, is_active)`, `(user_id, product_id)`

---

## commerce_subscription

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT UNIQUE FK → users_user | |
| tariff_id | VARCHAR(20) | |
| active_until | TIMESTAMPTZ NOT NULL | |
| last_renewal_at | TIMESTAMPTZ NULL | |
| auto_renew | BOOLEAN DEFAULT false | |

---

# 6. academy

Иерархия контента (как в UI):

```
Program (курс)  →  Module (модуль)  →  Lesson (урок)  →  LessonResource (видео, конспект, шаблон…)
```

Пример из UI: **GPT - NEW** → 6 модулей → 21 урок → видео «Введение в ChatGPT» (9 мин, HD).

---

## academy_program

Карточка на главной + шапка страницы курса.

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| slug | VARCHAR(100) UNIQUE | gpt-new |
| title | VARCHAR(255) | GPT - NEW |
| description | TEXT | |
| module_count | SMALLINT DEFAULT 0 | кэш: 6 модулей |
| lesson_count | SMALLINT DEFAULT 0 | кэш: 21 урок |
| icon | VARCHAR(50) NULL | |
| tags | JSONB DEFAULT '[]' | HIT, Завершено и т.д. |
| required_tariff | VARCHAR(20) NULL | NULL = все |
| required_product_id | BIGINT FK NULL | отдельная покупка |
| is_published | BOOLEAN DEFAULT false | |
| sort_order | SMALLINT DEFAULT 0 | |

---

## academy_module

Модули внутри программы. «Вводный материал» — модуль с `is_intro = true`.

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| program_id | BIGINT FK → academy_program | |
| order | SMALLINT NOT NULL | 0 = вводный, 1..N = модули |
| title | VARCHAR(255) | Знакомство с ChatGPT |
| description | TEXT NULL | |
| is_intro | BOOLEAN DEFAULT false | ВВОДНЫЙ МАТЕРИАЛ |
| lesson_count | SMALLINT DEFAULT 0 | кэш: 4 урока |
| is_published | BOOLEAN DEFAULT true | |

**Индексы:** `(program_id, order)` UNIQUE

---

## academy_lesson

Урок внутри модуля. Открывается в модальном окне / отдельной странице.

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| module_id | BIGINT FK → academy_module | |
| order | SMALLINT NOT NULL | порядок внутри модуля |
| title | VARCHAR(255) | Введение в ChatGPT |
| description | TEXT NULL | краткое описание в списке |
| result_description | TEXT NULL | «Результат урока» в модалке |
| type | VARCHAR(20) | video / practice / reading |
| duration_minutes | SMALLINT NULL | 9 мин |
| video_url | TEXT NULL | URL видео |
| video_quality | VARCHAR(10) NULL | HD / SD |
| ibox_scenario_id | BIGINT FK NULL | практика в AI Box |
| is_published | BOOLEAN DEFAULT true | |

**Индексы:** `(module_id, order)` UNIQUE

---

## academy_lesson_resource

Материалы урока: конспект, шаблон, практическое задание (чекбоксы в модалке).

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| lesson_id | BIGINT FK → academy_lesson | |
| resource_type | VARCHAR(30) | summary / template / practice / file |
| title | VARCHAR(255) | Краткий конспект |
| file_url | TEXT NULL | ссылка на файл |
| content | TEXT NULL | inline-контент |
| sort_order | SMALLINT DEFAULT 0 | |

**Индексы:** `(lesson_id, resource_type)`

---

## academy_user_progress

Прогресс по программе целиком. Сайдбар «Ваш прогресс: 100%, 21 из 21».

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | |
| program_id | BIGINT FK → academy_program | |
| completed_lessons | SMALLINT DEFAULT 0 | |
| completed_modules | SMALLINT DEFAULT 0 | |
| progress_percent | SMALLINT DEFAULT 0 | 0–100 |
| status | VARCHAR(20) | not_started / in_progress / completed |
| last_lesson_id | BIGINT FK → academy_lesson NULL | «Продолжить с места остановки» |
| started_at | TIMESTAMPTZ NULL | |
| completed_at | TIMESTAMPTZ NULL | |

**Индексы:** `(user_id, program_id)` UNIQUE, `(user_id, status)`

---

## academy_module_progress

Прогресс по модулю. Счётчик «4/4», «2/2» на карточке модуля.

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | |
| module_id | BIGINT FK → academy_module | |
| completed_lessons | SMALLINT DEFAULT 0 | |
| status | VARCHAR(20) | not_started / in_progress / completed |
| completed_at | TIMESTAMPTZ NULL | |

**Индексы:** `(user_id, module_id)` UNIQUE

---

## academy_lesson_progress

Прогресс по уроку. Статус «Пройден», возобновление видео.

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | |
| lesson_id | BIGINT FK → academy_lesson | |
| status | VARCHAR(20) | not_started / in_progress / completed |
| video_position_sec | INTEGER DEFAULT 0 | позиция в видео |
| started_at | TIMESTAMPTZ NULL | |
| completed_at | TIMESTAMPTZ NULL | |

**Индексы:** `(user_id, lesson_id)` UNIQUE

---

# 7. ibox

## ibox_scenario

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| slug | VARCHAR(100) UNIQUE | |
| title | VARCHAR(255) | |
| description | TEXT NULL | |
| category | VARCHAR(50) | content / sales / design |
| prompt_template | TEXT | |
| default_model | VARCHAR(50) | gpt-4o и т.д. |
| token_cost | INTEGER DEFAULT 10 | списание за запуск |
| required_tariff | VARCHAR(20) NULL | |
| is_active | BOOLEAN DEFAULT true | |
| sort_order | SMALLINT DEFAULT 0 | |

---

## ibox_chat_session

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | |
| scenario_id | BIGINT FK → ibox_scenario NULL | |
| model | VARCHAR(50) | |
| title | VARCHAR(255) NULL | |
| tokens_spent | INTEGER DEFAULT 0 | |

**Индексы:** `(user_id, created_at DESC)`

---

## ibox_chat_message

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| session_id | BIGINT FK → ibox_chat_session | |
| role | VARCHAR(20) | user / assistant / system |
| content | TEXT NOT NULL | |
| tokens_used | INTEGER DEFAULT 0 | |

**Индексы:** `(session_id, created_at)`

---

## ibox_token_balance

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT UNIQUE FK → users_user | |
| available | INTEGER DEFAULT 0 | |
| used_this_month | INTEGER DEFAULT 0 | |
| month_reset_at | TIMESTAMPTZ NULL | |

---

## ibox_token_transaction

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK → users_user | |
| amount | INTEGER NOT NULL | + или - |
| reason | VARCHAR(50) | purchase / generation / bonus / admin |
| session_id | BIGINT FK NULL | |
| order_id | BIGINT FK NULL | |

**Индексы:** `(user_id, created_at DESC)`

---

# 8. content

## content_banner

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| title | VARCHAR(255) | |
| subtitle | TEXT NULL | |
| image_url | VARCHAR(500) | |
| link_url | VARCHAR(500) NULL | |
| tags | JSONB DEFAULT '[]' | |
| is_active | BOOLEAN DEFAULT true | |
| sort_order | SMALLINT DEFAULT 0 | |
| active_from | TIMESTAMPTZ NULL | |
| active_until | TIMESTAMPTZ NULL | |

---

## content_material_category

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| slug | VARCHAR(50) UNIQUE | ai-box / sales / content |
| name | VARCHAR(100) | |
| icon | VARCHAR(50) NULL | |
| sort_order | SMALLINT DEFAULT 0 | |

---

## content_material_group

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| category_id | BIGINT FK → content_material_category | |
| title | VARCHAR(255) | |
| description | TEXT NULL | |
| file_type | VARCHAR(20) | PROMPT / PDF / DOC / VIDEO / FLOW |
| file_count | INTEGER DEFAULT 0 | кэш |
| required_tariff | VARCHAR(20) NULL | |
| sort_order | SMALLINT DEFAULT 0 | |

---

## content_material_file

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| group_id | BIGINT FK → content_material_group | |
| title | VARCHAR(255) | |
| file_url | VARCHAR(500) | |
| file_size | INTEGER NULL | bytes |
| format | VARCHAR(20) | |

**Индексы:** `group_id`

---

## content_telegram_chat

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| title | VARCHAR(255) | |
| description | TEXT | |
| chat_type | VARCHAR(20) | open / invite / service |
| telegram_url | VARCHAR(500) | |
| min_rank | VARCHAR(50) NULL | для invite-чатов |
| is_active | BOOLEAN DEFAULT true | |
| sort_order | SMALLINT DEFAULT 0 | |

---

# 9. crm

## crm_lead_stage

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| slug | VARCHAR(20) UNIQUE | new / contact / meeting / deal |
| name | VARCHAR(100) | |
| color | VARCHAR(20) | |
| sort_order | SMALLINT | |

---

## crm_lead

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| owner_id | BIGINT FK → users_user | |
| name | VARCHAR(255) | |
| source | VARCHAR(100) NULL | Instagram / Telegram |
| phone | VARCHAR(20) NULL | |
| contact | VARCHAR(100) NULL | @username |
| stage_id | BIGINT FK → crm_lead_stage | |
| task | VARCHAR(255) NULL | |
| note | TEXT NULL | |
| value_usd | DECIMAL(12,2) NULL | |
| scheduled_at | TIMESTAMPTZ NULL | |

**Индексы:** `(owner_id, stage_id)`, `(owner_id, created_at DESC)`

---

## crm_lead_activity

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| lead_id | BIGINT FK → crm_lead | |
| action | VARCHAR(100) | |
| details | TEXT NULL | |
| created_by_id | BIGINT FK → users_user | |

---

# 10. admin_ops

## admin_ops_audit_log

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| actor_id | BIGINT FK → users_user | |
| action | VARCHAR(100) | |
| target_type | VARCHAR(50) | |
| target_id | BIGINT NULL | |
| old_value | JSONB NULL | |
| new_value | JSONB NULL | |
| ip_address | INET NULL | |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |

**Индексы:** `(target_type, target_id)`, `(actor_id, created_at DESC)`

---

## admin_ops_system_config

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| key | VARCHAR(100) UNIQUE | |
| value | JSONB NOT NULL | |
| description | TEXT NULL | |

---

## admin_ops_analytics_event

| Поле | Тип | Описание |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK NULL | |
| event_type | VARCHAR(100) | first_result / project_saved / lesson_completed |
| metadata | JSONB DEFAULT '{}' | |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |

**Индексы:** `(event_type, created_at)`, `(user_id, event_type)`

---

# ER-диаграмма (ключевые связи)

```
users_user
  ├──1:1── users_profile
  ├──1:1── users_referral_code
  ├──1:1── partner_profile
  ├──1:1── wallet_balance
  ├──1:1── ibox_token_balance
  ├──1:1── commerce_subscription
  ├──1:N── commerce_order
  ├──1:N── commerce_user_access
  ├──1:N── academy_user_progress
  ├──1:N── ibox_chat_session
  ├──1:N── crm_lead
  ├──1:N── ledger_entry
  └──1:N── users_notification

partner_profile
  ├──1:1── partner_sponsor_link
  ├──1:1── partner_binary_placement
  ├──1:1── partner_binary_balance
  ├──1:1── partner_fast_start
  ├──1:N── partner_qualification_week
  ├──1:N── partner_team_depth_cache
  └──1:N── partner_rank_history

commerce_order
  ├──1:N── commerce_payment
  └──triggers── ledger_entry, commerce_user_access, ibox_token_transaction

academy_program
  └──1:N── academy_module
            └──1:N── academy_lesson
                      ├──1:N── academy_lesson_resource
                      └──links── ibox_scenario (optional, для практики)
```

---

# Сводка: таблицы по доменам

| Домен | Таблиц | MVP |
|---|---:|---|
| users | 5 | ✅ |
| partner | 8 | ✅ |
| ledger | 3 | ✅ |
| wallet | 3 | ✅ |
| commerce | 6 | ✅ |
| academy | 7 | ✅ |
| ibox | 5 | ✅ |
| content | 5 | ✅ |
| crm | 3 | ✅ |
| admin_ops | 3 | ✅ |
| **Итого** | **48** | |

---

# Открытые вопросы (для этапа 4–5)

1. **Алгоритм автопозиционирования в бинаре** — влияет на `partner_binary_placement` (поиск свободной позиции).
2. **Сеть USDT** — TRC20 / ERC20 в `wallet_withdrawal_request.network`.
3. **Состав токенов по тарифам** — `commerce_tariff_plan.initial_tokens` (не утверждено).
4. **Проекты (Projects)** — отдельный модуль позже; пока результаты iBox → `ibox_chat_session`.
5. **Внутренние переводы** — таблица `wallet_internal_transfer` добавим, когда утвердят правила.

---

# Следующий этап

**Этап 4:** API-контракты по экранам — эндпоинты, request/response для каждого из 7 разделов UI.
