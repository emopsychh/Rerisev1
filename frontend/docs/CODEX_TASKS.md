# Code - Codex Tasks

## Task 001 - Project foundation

Create a Turborepo monorepo for Code Platform.

Apps:

- `apps/web`
- `apps/admin`
- `apps/mini-app`

Packages:

- `packages/ui`
- `packages/db`
- `packages/auth`
- `packages/ai`
- `packages/commerce`
- `packages/academy`
- `packages/partner-engine`
- `packages/shared`
- `packages/config`

Use:

- Next.js
- TypeScript
- Tailwind CSS
- Prisma
- PostgreSQL
- ESLint
- Prettier

Create:

- root `package.json`
- `turbo.json`
- tsconfig base
- `.env.example`
- `README.md`
- basic app layouts
- shared UI `Button`, `Card`, `Badge` components

## Task 002 - Prisma schema

Create initial Prisma schema for Code Platform.

Include models:

- User
- Profile
- PartnerProfile
- ReferralLink
- Product
- Price
- Order
- OrderItem
- Payment
- AccessGrant
- Program
- Module
- Lesson
- LessonProgress
- TokenWallet
- TokenTransaction
- AIProvider
- AIModel
- AIConversation
- AIMessage
- PVLedgerEntry
- BonusRule
- BonusPeriod
- BonusRun
- BonusAccrual
- WithdrawalRequest
- Notification
- AuditLog
- WebhookEvent

Use PostgreSQL. Add enums for statuses and product types. Add indexes for `userId`, `sponsorId`, `orderId`, `productId`, `periodId`.

## Task 003 - Main user UI

Build the main user dashboard UI.

Routes:

- `/app/dashboard`
- `/app/ai/chat`
- `/app/academy`
- `/app/store`
- `/app/partner`
- `/app/materials`
- `/app/profile`

Create responsive layout:

- desktop sidebar
- mobile bottom navigation
- top header with token balance and profile menu

Use placeholder data and a polished modern UI.

## Task 004 - Store MVP

Implement Store MVP.

Features:

- product list
- product details
- price display
- create order
- mock payment success
- grant access after successful order
- show orders in profile

Do not integrate a real payment provider yet. Use service layer in `packages/commerce`.

## Task 005 - AI Chat MVP

Implement AI Chat MVP.

Features:

- create conversation
- send message
- receive mocked AI response first
- save messages
- show conversation history
- deduct tokens using `TokenTransaction`
- block request if token balance is insufficient

Use `packages/ai` for provider abstraction.

## Task 006 - Partner MVP

Implement Partner Cabinet MVP.

Features:

- generate referral code for user
- create referral link
- register user with referral code
- connect sponsor relation
- show invited users
- calculate direct referral bonus from paid orders
- show bonus history

Do not implement binary bonus yet. Use `packages/partner-engine`.
