# Code - Architecture v0.1

## Target Repository Shape

```txt
code-platform/
├─ apps/
│  ├─ web/
│  ├─ admin/
│  └─ mini-app/
├─ packages/
│  ├─ ui/
│  ├─ config/
│  ├─ db/
│  ├─ auth/
│  ├─ ai/
│  ├─ academy/
│  ├─ commerce/
│  ├─ partner-engine/
│  ├─ payments/
│  ├─ notifications/
│  ├─ storage/
│  ├─ analytics/
│  └─ shared/
├─ docs/
├─ scripts/
├─ docker/
├─ .env.example
├─ package.json
├─ turbo.json
└─ README.md
```

## Suggested Stack

| Layer | Stack |
| --- | --- |
| Frontend | Next.js, TypeScript |
| UI | Tailwind CSS, shadcn/ui or internal UI kit |
| Backend | Next.js API/server actions first, separate API later if needed |
| DB | PostgreSQL |
| ORM | Prisma |
| Cache/Queue | Redis, BullMQ |
| Storage | S3-compatible storage |
| Auth | Credentials first, Telegram auth later |
| Payments | Provider abstraction layer |
| AI | AI Gateway with provider adapters |
| Deploy | Docker |
| Monorepo | Turborepo |

## Package Responsibilities

- `packages/ui`: shared components, tokens, icons, layouts.
- `packages/db`: Prisma schema, migrations, seed.
- `packages/auth`: auth services, roles, guards.
- `packages/ai`: provider adapters, token usage, prompt utilities.
- `packages/commerce`: products, prices, orders, access grants.
- `packages/academy`: programs, modules, lessons, progress.
- `packages/partner-engine`: referral codes, sponsor relation, bonus logic.
- `packages/payments`: payment provider abstraction and webhooks.
- `packages/notifications`: in-app/email/Telegram notifications.
- `packages/shared`: shared types, constants, utilities.

## First Implementation Rule

Start with a clean modular monorepo, but keep MVP behavior simple:

- mocked AI response before real provider;
- mock payment success before real payment provider;
- direct referral bonus before binary/matching bonus;
- manual admin flows before automation.
