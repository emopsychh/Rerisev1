# ReRise — Этап 4: API-контракты

**Статус:** черновик на утверждение  
**Base URL:** `/api/v1/`  
**Auth:** JWT (Bearer token)  
**Язык:** `Accept-Language: ru` (позже en, es)  
**Формат:** JSON  
**Версия:** 0.1 · 15.07.2026

---

## Общие соглашения

### Аутентификация

```
Authorization: Bearer <access_token>
```

Публичные эндпоинты (без токена): `auth/*`, `store/tariffs` (список тарифов).

### Стандартный формат ответа

**Успех (один объект):**
```json
{
  "data": { ... }
}
```

**Успех (список + пагинация):**
```json
{
  "data": [ ... ],
  "meta": {
    "total": 12,
    "page": 1,
    "per_page": 20
  }
}
```

**Ошибка:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Описание ошибки",
    "details": { "field": ["сообщение"] }
  }
}
```

### Коды ошибок

| HTTP | code | Когда |
|---:|---|---|
| 400 | VALIDATION_ERROR | Невалидные данные |
| 401 | UNAUTHORIZED | Нет / просрочен токен |
| 403 | FORBIDDEN | Нет доступа (тариф, роль) |
| 404 | NOT_FOUND | Сущность не найдена |
| 409 | CONFLICT | Дубликат, неверный статус |
| 422 | BUSINESS_RULE_ERROR | Нарушение бизнес-правила |
| 429 | RATE_LIMITED | Слишком много запросов |
| 500 | INTERNAL_ERROR | Серверная ошибка |

### Пагинация

Query-параметры: `?page=1&per_page=20`

### Фильтрация и поиск

Query-параметр `?search=текст` — полнотекстовый поиск где указано.

---

# 0. Auth & Common

## POST /auth/register

Регистрация. Опционально — реферальный код.

**Request:**
```json
{
  "email": "user@example.com",
  "phone": "+79000000000",
  "password": "securePassword1",
  "first_name": "Александр",
  "last_name": "Левес",
  "referral_code": "RERISE-1842"
}
```

**Response 201:**
```json
{
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "public_id": "RERISE-2048"
    }
  }
}
```

**Side effects:** если `referral_code` — создать `partner_sponsor_link` (после покупки тарифа — бинарное размещение).

---

## POST /auth/login

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword1"
}
```

**Response 200:** аналогично register.

---

## POST /auth/refresh

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response 200:**
```json
{
  "data": {
    "access_token": "eyJ..."
  }
}
```

---

## GET /me

Текущий пользователь. Используется глобально (хедер, сайдбар).

**Response 200:**
```json
{
  "data": {
    "id": 1,
    "email": "aleksandr@rerise.ai",
    "phone": "+79000000000",
    "public_id": "RERISE-1842",
    "first_name": "Александр",
    "last_name": "Левес",
    "avatar_url": null,
    "language": "ru",
    "is_partner": true,
    "subscription": {
      "tariff_id": "rise-pro",
      "tariff_name": "Rise Pro",
      "is_active": true,
      "activity_until": "2026-07-24T00:00:00Z"
    },
    "unread_notifications": 3
  }
}
```

---

## GET /me/summary

Компактные данные для сайдбара и хедера.

**Response 200:**
```json
{
  "data": {
    "subscription": {
      "tariff_name": "Rise Pro",
      "activity_until": "2026-07-24T00:00:00Z",
      "can_renew": true
    },
    "unread_notifications": 3,
    "referral_code": "RERISE-1842"
  }
}
```

---

## POST /me/invite-link

Генерация / получение реферальной ссылки (кнопка «Пригласить»).

**Response 200:**
```json
{
  "data": {
    "referral_code": "RERISE-1842",
    "referral_url": "https://rerise.ai/join/RERISE-1842"
  }
}
```

---

## GET /notifications

**Query:** `?unread_only=true&page=1`

**Response 200:**
```json
{
  "data": [
    {
      "id": 1,
      "type": "bonus",
      "title": "Начислен бинарный бонус",
      "body": "+$6",
      "is_read": false,
      "created_at": "2026-07-15T10:00:00Z"
    }
  ],
  "meta": { "total": 3, "unread": 3 }
}
```

---

## PATCH /notifications/{id}/read

**Response 200:** `{ "data": { "is_read": true } }`

---

## PATCH /notifications/read-all

**Response 200:** `{ "data": { "marked": 3 } }`

---

# 1. Главная (Home)

## GET /home

Всё для главной страницы одним запросом (баннеры + виджеты).

**Response 200:**
```json
{
  "data": {
    "banners": [
      {
        "id": 1,
        "title": "2 ЧАСТЬ ChatGPT New",
        "subtitle": "Новые сценарии для контента и продаж",
        "image_url": "/media/banners/gpt-new.jpg",
        "tags": ["Контент", "Продажи", "Автоматизация"],
        "link_url": "/programs/gpt-new"
      }
    ],
    "ai_box_widget": {
      "title": "RE:RISE AI — AI Hub",
      "description": "Выберите сценарий или напишите задачу",
      "is_available": true
    },
    "programs_count": 12
  }
}
```

---

## GET /programs

Список программ (курсов) с фильтрами.

**Query:**
| Параметр | Значения | Описание |
|---|---|---|
| `filter` | all / owned / available / completed | Кнопки фильтрации |
| `search` | строка | Поиск по названию |
| `page` | int | Пагинация |

**Response 200:**
```json
{
  "data": [
    {
      "id": 1,
      "slug": "gpt-new",
      "title": "GPT - NEW",
      "description": "ChatGPT с нуля до коммерческого применения",
      "lesson_count": 21,
      "module_count": 6,
      "icon": "chat",
      "tags": ["HIT"],
      "access_status": "owned",
      "progress": {
        "status": "completed",
        "completed_lessons": 21,
        "percent": 100
      },
      "action": "open"
    },
    {
      "id": 2,
      "slug": "ai-design",
      "title": "AI Design",
      "description": "Дизайн с помощью нейросетей",
      "lesson_count": 13,
      "module_count": 4,
      "tags": [],
      "access_status": "in_progress",
      "progress": {
        "status": "in_progress",
        "completed_lessons": 2,
        "percent": 15
      },
      "action": "continue"
    },
    {
      "id": 3,
      "slug": "ai-video",
      "title": "AI Video",
      "access_status": "locked",
      "progress": null,
      "action": "details"
    }
  ],
  "meta": { "total": 12, "page": 1, "per_page": 20 }
}
```

**Поле `action`:** `open` | `continue` | `details` — текст кнопки на карточке.

**Поле `access_status`:** `owned` | `in_progress` | `completed` | `locked` | `available_for_purchase`

---

# 2. Academy — программа / модули / уроки

## GET /programs/{slug}

Страница курса: шапка + программа + прогресс.

**Response 200:**
```json
{
  "data": {
    "id": 1,
    "slug": "gpt-new",
    "title": "GPT - NEW",
    "description": "Полный курс по ChatGPT: от основ до коммерческого применения в печати, ивентах, соцсетях и других нишах.",
    "lesson_count": 21,
    "module_count": 6,
    "progress": {
      "percent": 100,
      "completed_lessons": 21,
      "completed_modules": 6,
      "status": "completed",
      "last_lesson": {
        "id": 21,
        "title": "Как быстро и стабильно выполнять заказы",
        "module_title": "Модуль 6",
        "duration_minutes": 36
      }
    },
    "modules": [
      {
        "id": 1,
        "order": 0,
        "title": "Введение в ChatGPT",
        "description": "Как устроена программа, что понадобится и с чего начать",
        "is_intro": true,
        "lesson_count": 1,
        "progress": {
          "completed_lessons": 1,
          "status": "completed"
        },
        "lessons": [
          {
            "id": 1,
            "order": 1,
            "title": "Введение в ChatGPT",
            "duration_minutes": 9,
            "type": "video",
            "status": "completed"
          }
        ]
      },
      {
        "id": 2,
        "order": 1,
        "title": "Знакомство с ChatGPT",
        "description": "Первые шаги и базовые принципы работы",
        "is_intro": false,
        "lesson_count": 2,
        "progress": {
          "completed_lessons": 2,
          "status": "completed"
        },
        "lessons": [
          {
            "id": 2,
            "order": 1,
            "title": "Что такое ChatGPT и как он работает",
            "duration_minutes": 15,
            "type": "video",
            "status": "completed"
          },
          {
            "id": 3,
            "order": 2,
            "title": "Первый диалог с ChatGPT",
            "duration_minutes": 12,
            "type": "video",
            "status": "completed"
          }
        ]
      },
      {
        "id": 7,
        "order": 6,
        "title": "Модуль 6",
        "description": "Финальные техники и коммерческое применение",
        "lesson_count": 3,
        "progress": {
          "completed_lessons": 3,
          "status": "completed"
        },
        "lessons": [ "..." ]
      }
    ]
  }
}
```

**Примечание:** уроки в списке модулей — краткие. Полные данные — через `GET /lessons/{id}`.

**Поле `status` урока:** `not_started` | `in_progress` | `completed`

**Поле `status` модуля:** `not_started` | `in_progress` | `completed` | `current` (текущий модуль)

---

## GET /lessons/{id}

Модалка урока: видео, результат, ресурсы.

**Response 200:**
```json
{
  "data": {
    "id": 1,
    "title": "Введение в ChatGPT",
    "description": "Как устроена программа, что понадобится и с чего начать",
    "result_description": "Вы разберёте ключевые принципы, увидите рабочий пример и соберёте собственный результат по готовой структуре RE:RISE.",
    "type": "video",
    "duration_minutes": 9,
    "video": {
      "url": "/media/lessons/gpt-intro.mp4",
      "quality": "HD"
    },
    "resources": [
      { "type": "summary", "title": "Краткий конспект", "file_url": "/media/lessons/gpt-intro-summary.pdf" },
      { "type": "template", "title": "Рабочий шаблон", "file_url": "/media/lessons/gpt-intro-template.docx" },
      { "type": "practice", "title": "Практическое задание", "file_url": null, "ibox_scenario_id": 5 }
    ],
    "program": {
      "slug": "gpt-new",
      "title": "GPT - NEW"
    },
    "module": {
      "id": 1,
      "title": "ВВОДНЫЙ МАТЕРИАЛ"
    },
    "progress": {
      "status": "not_started",
      "video_position_sec": 0
    }
  }
}
```

---

## POST /lessons/{id}/start

Кнопка «Начать урок». Переводит урок в `in_progress`.

**Response 200:**
```json
{
  "data": {
    "lesson_id": 1,
    "status": "in_progress",
    "started_at": "2026-07-15T12:00:00Z"
  }
}
```

**Side effects:**
- `academy_lesson_progress.status` → `in_progress`
- `academy_user_progress.status` → `in_progress` (если первый урок)
- `analytics_event`: `lesson_started`

---

## PATCH /lessons/{id}/progress

Сохранение позиции видео (периодически с фронта).

**Request:**
```json
{
  "video_position_sec": 142
}
```

**Response 200:**
```json
{
  "data": {
    "lesson_id": 1,
    "video_position_sec": 142
  }
}
```

---

## POST /lessons/{id}/complete

Урок пройден.

**Response 200:**
```json
{
  "data": {
    "lesson_id": 1,
    "status": "completed",
    "completed_at": "2026-07-15T12:30:00Z",
    "program_progress": {
      "completed_lessons": 5,
      "percent": 24,
      "status": "in_progress"
    },
    "module_progress": {
      "completed_lessons": 2,
      "status": "completed"
    },
    "next_lesson": {
      "id": 6,
      "title": "Следующий урок...",
      "module_title": "Модуль 2"
    }
  }
}
```

**Side effects:**
- пересчёт `academy_user_progress`, `academy_module_progress`
- обновление `last_lesson_id`
- `analytics_event`: `lesson_completed`

---

# 3. Кабинет (Cabinet)

Кабинет — 4 подраздела: Дашборд, CRM, Структура, Кошелёк.

## GET /partner/dashboard

Главный дашборд партнёра.

**Response 200:**
```json
{
  "data": {
    "member_label": "RE:RISE MEMBER 01 / 16",
    "balance": {
      "total_usd": 12350.00,
      "available_usd": 12350.00
    },
    "partner": {
      "tariff_id": "rise-pro",
      "tariff_name": "Rise Pro",
      "is_active": true,
      "activity_until": "2026-07-24T00:00:00Z",
      "current_rank": "partner_1",
      "current_rank_name": "Партнёр I",
      "next_rank": "partner_2",
      "next_rank_name": "Партнёр II"
    },
    "team_depth": {
      "tariff_depth_limit": 9,
      "levels": [
        { "level": "L1", "total": 35, "active": 15, "pv": 3600 },
        { "level": "L2", "total": 48, "active": 18, "pv": 4200 },
        { "level": "L3", "total": 41, "active": 11, "pv": 3100 },
        { "level": "L4", "total": 29, "active": 7, "pv": 2400 },
        { "level": "L5", "total": 23, "active": 2, "pv": 1700 }
      ]
    },
    "metrics": {
      "weekly_collapsed_pv": { "current": 60, "required": 100, "next_rank": "Партнёр II" },
      "active_personal_partners": { "current": 1, "required": 2, "next_rank": "Партнёр II" },
      "fast_start": { "current": 4, "required": 4, "reward_usd": 90, "reward_paid": true },
      "available_to_withdraw": { "amount_usd": 12350.00 }
    },
    "qualification_week": {
      "title": "Движение к Партнёру II",
      "period": "13–19 июля · МСК",
      "week_start": "2026-07-13",
      "week_end": "2026-07-19",
      "rows": [
        { "label": "Схлоп за неделю", "current": 60, "required": 100, "unit": "PV" },
        { "label": "Активные личные", "current": 1, "required": 2, "hint": "нужен ещё 1" },
        { "label": "Бинарный доход", "current": 6, "unit": "USD", "formula": "10 PV = $1" }
      ]
    },
    "updates": [
      {
        "id": 1,
        "type": "binary_bonus",
        "title": "Начислен бинарный бонус",
        "amount_usd": 6.00,
        "created_at": "2026-07-15T09:00:00Z"
      },
      {
        "id": 2,
        "type": "personal_bonus",
        "title": "Личный бонус Rise Pro",
        "amount_usd": 90.00,
        "from_user": "Мария К.",
        "created_at": "2026-07-15T08:00:00Z"
      },
      {
        "id": 3,
        "type": "renewal_bonus",
        "title": "Бонус за продление",
        "amount_usd": 9.00,
        "from_user": "Олег Н.",
        "created_at": "2026-07-15T07:00:00Z"
      }
    ]
  }
}
```

---

## GET /partner/ranks

Список всех статусов (кнопка «Все статусы»).

**Response 200:**
```json
{
  "data": [
    {
      "rank": "partner_1",
      "name": "Партнёр I",
      "weekly_collapsed_pv": 0,
      "requirement": "Покупка любого партнёрского тарифа",
      "reward_usd": 0,
      "is_achieved": true,
      "achieved_at": "2026-06-24T00:00:00Z"
    },
    {
      "rank": "partner_2",
      "name": "Партнёр II",
      "weekly_collapsed_pv": 100,
      "requirement": "2 активных личных партнёра",
      "reward_usd": 10,
      "is_achieved": false,
      "progress": {
        "collapsed_pv": { "current": 60, "required": 100 },
        "active_personals": { "current": 1, "required": 2 }
      }
    }
  ]
}
```

---

## GET /partner/structure

Бинарная структура (вкладка «Структура»).

**Query:** `?leg=left|right&depth=3`

**Response 200:**
```json
{
  "data": {
    "legs": [
      {
        "id": "left",
        "title": "Левая ветка",
        "lead": "Мария К.",
        "pv": 9000,
        "members": 98,
        "active": 31,
        "recent": ["Мария К.", "Дмитрий В.", "Сергей Б."]
      },
      {
        "id": "right",
        "title": "Правая ветка",
        "lead": "Олег Н.",
        "pv": 6000,
        "members": 78,
        "active": 22,
        "recent": ["Олег Н.", "Елена К."]
      }
    ],
    "summary": {
      "total_members": 176,
      "active_members": 53,
      "personal_invites": 5,
      "total_pv": 15000
    },
    "members": [
      {
        "name": "Мария К.",
        "branch": "Левая ветка",
        "branch_id": "left",
        "level": "L1",
        "pv": 4200,
        "status": "Активен",
        "activity": "Активен до 24.07.2026"
      }
    ]
  }
}
```

---

## GET /partner/invited

Лично приглашённые партнёры.

**Response 200:**
```json
{
  "data": [
    {
      "id": 5,
      "name": "Мария К.",
      "tariff": "Rise Pro",
      "is_active": true,
      "joined_at": "2026-07-01T00:00:00Z"
    }
  ]
}
```

---

### CRM (вкладка в кабинете)

## GET /crm/leads

Канбан: все лиды пользователя.

**Query:** `?stage=new|contact|meeting|deal&search=`

**Response 200:**
```json
{
  "data": {
    "stages": [
      {
        "slug": "new",
        "name": "Новые",
        "color": "blue",
        "leads": [
          {
            "id": 1,
            "name": "Марина К.",
            "source": "Instagram",
            "task": "Созвон завтра",
            "time": "Завтра в 15:00",
            "value_usd": 300,
            "phone": "+79002145511",
            "contact": "@marina.ai",
            "note": "Интересуется AI Hub для контента"
          }
        ]
      },
      { "slug": "contact", "name": "Контакты", "color": "green", "leads": [] },
      { "slug": "meeting", "name": "Встречи", "color": "orange", "leads": [] },
      { "slug": "deal", "name": "Сделки", "color": "violet", "leads": [] }
    ]
  }
}
```

---

## POST /crm/leads

**Request:**
```json
{
  "name": "Марина К.",
  "source": "Instagram",
  "phone": "+79002145511",
  "contact": "@marina.ai",
  "stage": "new",
  "task": "Созвон завтра",
  "value_usd": 300,
  "note": "Интересуется AI Hub"
}
```

**Response 201:** `{ "data": { "id": 1, ... } }`

---

## PATCH /crm/leads/{id}

Обновление лида (смена стадии, заметки).

**Request:**
```json
{
  "stage": "contact",
  "task": "Отправить презентацию",
  "note": "Обновлённая заметка"
}
```

---

## DELETE /crm/leads/{id}

**Response 204:** No content.

---

### Кошелёк (вкладка в кабинете)

## GET /wallet

**Response 200:**
```json
{
  "data": {
    "balance": {
      "available_usd": 12350.00,
      "pending_usd": 0.00,
      "total_earned_usd": 15000.00
    },
    "adjustment_debt_usd": 0.00,
    "withdrawal_limits": {
      "min_usd": 100,
      "max_per_request_usd": 10000,
      "currency": "USDT"
    },
    "saved_address": {
      "address": "TXyz...",
      "network": "TRC20"
    },
    "recent_transactions": [
      {
        "id": 1,
        "type": "binary_bonus",
        "title": "Бинарный бонус",
        "amount_usd": 6.00,
        "direction": "credit",
        "created_at": "2026-07-15T09:00:00Z"
      }
    ]
  }
}
```

---

## GET /wallet/transactions

История операций с фильтрами.

**Query:** `?type=all|bonus|withdrawal&period=today|yesterday|week|month&page=1`

**Response 200:**
```json
{
  "data": [
    {
      "id": 1,
      "entry_type": "binary_bonus",
      "title": "Бинарный бонус",
      "amount_usd": 6.00,
      "direction": "credit",
      "created_at": "2026-07-15T09:00:00Z"
    }
  ],
  "meta": { "total": 45 }
}
```

---

## POST /wallet/withdraw

Заявка на вывод USDT.

**Request:**
```json
{
  "amount_usd": 500.00,
  "usdt_address": "TXyz123...",
  "network": "TRC20"
}
```

**Response 201:**
```json
{
  "data": {
    "id": 1,
    "amount_usd": 500.00,
    "fee_usd": 0.00,
    "status": "pending",
    "created_at": "2026-07-15T12:00:00Z"
  }
}
```

**Валидация:**
- `amount_usd` >= 100
- `amount_usd` <= available_usd
- адрес не пустой
- `network` из списка поддерживаемых

---

## PUT /wallet/address

Сохранение USDT-адреса.

**Request:**
```json
{
  "address": "TXyz123...",
  "network": "TRC20"
}
```

---

# 4. Материалы

## GET /materials

**Query:** `?category=all|ai-box|sales|content|partner&search=`

**Response 200:**
```json
{
  "data": {
    "stats": {
      "total_files": 245,
      "total_sections": 8,
      "last_updated": "2026-07-15T00:00:00Z"
    },
    "categories": [
      {
        "slug": "ai-box",
        "name": "AI Hub",
        "groups": [
          {
            "id": 1,
            "title": "Промпты",
            "description": "Готовые промпты для ежедневной работы",
            "file_type": "PROMPT",
            "file_count": 64,
            "last_updated": "2026-07-15T00:00:00Z"
          }
        ]
      }
    ]
  }
}
```

---

## GET /materials/groups/{id}

Файлы внутри группы.

**Response 200:**
```json
{
  "data": {
    "id": 1,
    "title": "Промпты",
    "files": [
      {
        "id": 1,
        "title": "Промпт для продающего поста",
        "format": "TXT",
        "file_url": "/media/materials/prompt-sales-post.txt",
        "file_size": 2048
      }
    ]
  }
}
```

---

## GET /materials/files/{id}/download

**Response 302:** Redirect на file_url (или signed URL).

**403:** если нет доступа по тарифу.

---

# 5. Чаты

## GET /chats

**Response 200:**
```json
{
  "data": {
    "community_active": true,
    "chats": [
      {
        "id": 1,
        "title": "Чат партнёров",
        "description": "Общение, вопросы, кейсы и обмен опытом",
        "chat_type": "open",
        "telegram_url": "https://t.me/rerise_partners",
        "is_accessible": true
      },
      {
        "id": 2,
        "title": "Чат лидеров",
        "description": "Стратегия, метрики, координация запусков",
        "chat_type": "invite",
        "telegram_url": "https://t.me/rerise_leaders",
        "is_accessible": false,
        "access_requirement": "Партнёр II и выше"
      }
    ]
  }
}
```

---

# 6. Маркет (Store)

## GET /store/tariffs

Публичный список тарифов.

**Response 200:**
```json
{
  "data": [
    {
      "id": "rise",
      "name": "Rise",
      "price_usd": 90,
      "description": "Партнёрский тариф с физической PV-глубиной 3 уровня",
      "included": ["Первый месяц партнёрской активности включён"],
      "terms": {
        "personal_bonus_cap_usd": 30,
        "purchase_pv_cap": 30,
        "binary_depth": 3,
        "matching_lines": 1,
        "matching_percent": 10
      },
      "quick_start_eligible": false
    },
    {
      "id": "rise-pro",
      "name": "Rise Pro",
      "price_usd": 300,
      "terms": {
        "personal_bonus_cap_usd": 90,
        "purchase_pv_cap": 90,
        "binary_depth": 9,
        "matching_lines": 2,
        "matching_percent": 10
      },
      "quick_start_eligible": true,
      "quick_start": "4 личных Pro/Max · 30 дней · $90"
    },
    {
      "id": "rise-pro-max",
      "name": "Rise Pro Max",
      "price_usd": 900,
      "terms": {
        "personal_bonus_cap_usd": 300,
        "purchase_pv_cap": 300,
        "binary_depth": 15,
        "matching_lines": 3,
        "matching_percent": 10
      },
      "quick_start_eligible": true
    }
  ]
}
```

---

## GET /store/tokens

Пакеты токенов.

**Response 200:**
```json
{
  "data": {
    "balance": 7540,
    "packs": [
      { "id": "tokens-1000", "amount": 1000, "price_usd": 10 },
      { "id": "tokens-5000", "amount": 5000, "price_usd": 40 }
    ]
  }
}
```

---

## POST /store/orders

Создание заказа → получение ссылки на оплату.

**Request:**
```json
{
  "product_id": "rise-pro",
  "order_type": "purchase"
}
```

Для апгрейда:
```json
{
  "product_id": "rise-pro-max",
  "order_type": "upgrade"
}
```

Для продления:
```json
{
  "product_id": "subscription",
  "order_type": "renewal"
}
```

**Response 201:**
```json
{
  "data": {
    "order_id": 42,
    "product_name": "Rise Pro",
    "amount_usd": 300.00,
    "status": "pending",
    "payment": {
      "provider": "cryptobot",
      "payment_url": "https://t.me/CryptoBot?start=inv_xxx",
      "expires_at": "2026-07-15T13:00:00Z"
    }
  }
}
```

---

## GET /store/orders/{id}

Статус заказа (polling после оплаты).

**Response 200:**
```json
{
  "data": {
    "order_id": 42,
    "status": "paid",
    "paid_at": "2026-07-15T12:05:00Z",
    "granted_access": {
      "tariff": "rise-pro",
      "activity_until": "2026-08-15T00:00:00Z",
      "tokens_credited": 7540
    }
  }
}
```

---

## POST /store/webhook/{provider}

Webhook от платёжного провайдера (CryptoBot). Внутренний.

**Не вызывается фронтом.** Провайдер → backend.

**Side effects при `paid`:**
1. `commerce_order.status` → paid
2. `commerce_user_access` — выдать доступ
3. `ibox_token_transaction` — начислить токены
4. `ledger_entry` — PV
5. `BonusEngine` — личный бонус, бинар, матчинг
6. `partner_profile` — обновить тариф/активность
7. `users_notification` — уведомление покупателю и спонсору

---

# 7. Профиль

## GET /me/profile

**Response 200:**
```json
{
  "data": {
    "first_name": "Александр",
    "last_name": "Левес",
    "email": "aleksandr@rerise.ai",
    "phone": "+79000000000",
    "country": "Россия",
    "city": "Москва",
    "language": "ru",
    "avatar_url": null,
    "public_id": "RERISE-1842",
    "partner": {
      "tariff_name": "Rise Pro",
      "is_active": true,
      "activity_until": "2026-07-24T00:00:00Z",
      "historical_rank": "Партнёр I",
      "historical_rank_note": "Сохраняется независимо от активности",
      "inactivity_info": "После окончания активности тариф сохраняется 12 месяцев..."
    },
    "notifications": {
      "email_enabled": true,
      "push_enabled": true
    }
  }
}
```

---

## PATCH /me/profile

**Request:**
```json
{
  "first_name": "Александр",
  "last_name": "Левес",
  "phone": "+79000000000",
  "country": "Россия",
  "city": "Москва",
  "language": "ru"
}
```

---

## PATCH /me/notifications

**Request:**
```json
{
  "email_enabled": true,
  "push_enabled": false
}
```

---

## POST /me/avatar

**Request:** `multipart/form-data`, поле `avatar`.

**Response 200:**
```json
{
  "data": { "avatar_url": "/media/avatars/user-1.jpg" }
}
```

---

## POST /partner/renew

Кнопка «Продлить активность» / «Продлить».

Создаёт order на $30 subscription.

**Response 201:** аналогично `POST /store/orders` с `order_type: renewal`.

---

# 8. AI Hub (дополнительно — не отдельный пункт меню, но нужен)

## GET /ibox/scenarios

**Query:** `?category=content|sales|design`

**Response 200:**
```json
{
  "data": {
    "token_balance": 7540,
    "scenarios": [
      {
        "id": 1,
        "slug": "selling-post",
        "title": "Создать продающий пост",
        "category": "content",
        "token_cost": 10
      }
    ],
    "recent_tasks": [
      "Контент-план на 7 дней",
      "Презентация продукта"
    ]
  }
}
```

---

## POST /ibox/sessions

Новая сессия (запуск сценария или свободный чат).

**Request:**
```json
{
  "scenario_id": 1,
  "model": "gpt-4o",
  "message": "Напиши пост про запуск AI-курса"
}
```

**Response 201:**
```json
{
  "data": {
    "session_id": 10,
    "message": {
      "role": "assistant",
      "content": "Вот вариант продающего поста...",
      "tokens_used": 18
    },
    "token_balance": 7522
  }
}
```

---

## POST /ibox/sessions/{id}/messages

Продолжение диалога.

**Request:**
```json
{
  "message": "Сделай короче и добавь CTA"
}
```

---

## GET /ibox/sessions

История сессий.

**Query:** `?page=1`

---

## GET /ibox/sessions/{id}

Сессия с полной историей сообщений.

---

# 9. Admin (Django Admin + API для операций)

Админка — в основном через **Django Admin**. Критичные API-операции:

| Метод | Путь | Действие |
|---|---|---|
| POST | `/admin/ledger/adjustments` | Корректировка PV/бонусов |
| POST | `/admin/users/{id}/block` | Блокировка аккаунта |
| PATCH | `/admin/withdrawals/{id}` | Одобрить/отклонить вывод |
| GET | `/admin/audit-log` | Журнал действий |

Детализация — на этапе реализации admin_ops.

---

# Сводка эндпоинтов

| Раздел | Эндпоинтов | Ключевые |
|---|---:|---|
| Auth & Common | 8 | register, login, me, notifications |
| Главная | 2 | home, programs |
| Academy | 5 | program detail, lesson, start, progress, complete |
| Кабинет | 10 | dashboard, structure, CRM CRUD, wallet |
| Материалы | 3 | list, group, download |
| Чаты | 1 | list |
| Маркет | 5 | tariffs, tokens, orders, webhook |
| Профиль | 5 | profile, avatar, renew |
| AI Hub | 5 | scenarios, sessions, messages |
| Admin | 4 | adjustments, block, withdrawals |
| **Итого** | **~48** | |

---

# Приоритет реализации API (для этапа 7)

| Фаза | Эндпоинты | Зачем |
|---|---|---|
| **A** | auth, me, me/profile | Вход в систему |
| **B** | store/tariffs, store/orders, webhook | Покупка тарифа |
| **C** | partner/dashboard, wallet | Кабинет после покупки |
| **D** | programs, lessons | Academy |
| **E** | ibox/scenarios, sessions | AI Hub |
| **F** | materials, chats, home | Контент |
| **G** | crm/leads | CRM |
| **H** | partner/structure, ranks | Структура |
| **I** | admin | Операции |

---

# Следующий этап

**Этап 5:** Financial Engine — детальная спецификация расчётов (PV, бинар, матчинг, статусы, быстрый старт) с псевдокодом и тест-кейсами.
