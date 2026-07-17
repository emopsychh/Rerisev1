# Code: product blueprint

## 1. Concept

Code is a web and mobile-first AI platform that combines:

- an aggregator of AI tools and assistants;
- practical education on GPT, image generation, content, automation, and business workflows;
- personal accounts with progress, history, subscriptions, tokens, and purchased products;
- a referral/partner model with transparent rewards, materials, and analytics.

The product should not feel like only a course marketplace. The core value should be an everyday AI workspace, while education and the partner program help users get results and grow distribution.

## 2. Competitor Reference: MetaBox

### Observed Product Areas

- **My programs**: course/program cards, progress, locked and unlocked access, community cards.
- **Store**: program bundles, individual programs, subscriptions, token packs, product PV values.
- **Materials**: marketing plan, bonus calculator, documents, share action.
- **Keys**: purchased and activated access keys.
- **Bonuses**: partner/reward area.
- **Invite/profile**: referral links, mentor info, Telegram bot connection, chats, support, access keys, name/password editing.
- **AI Hub**: a separate AI assistant/token product attached to the learning platform.

### Commercial Mechanics

- One-time program purchases.
- Program bundle purchase.
- AI subscription with monthly token allowance.
- Additional token packs.
- Product volume points, shown as PV.
- Personal referral bonus.
- Binary team bonus with left/right branches.
- Matching bonus from partner lines.
- Pre-order urgency and early-buyer bonuses.

### Presentation Structure

- Company positioning.
- Growth points and problem/solution narrative.
- Audience segments: freelancers, entrepreneurs, partners/leaders.
- Bonus model explanation.
- Product catalog with program-by-program value propositions.
- AI assistant product.
- Bundle pricing.
- Pre-order conditions.
- Bonuses for pre-order.
- Referral income explanation.
- Purchase call to action.

## 3. What Code Should Borrow

- Clear top navigation: workspace, learning, marketplace, partner center, materials, profile.
- Program cards with image, short description, progress, lock state, and CTA.
- Course detail template: duration, audience, skills, outcome, modules, assets.
- Store split into programs, subscriptions, and tokens.
- Profile with referral links, mentor, connected Telegram/account channels, subscription, and access history.
- Bonus calculator as a trust-building and planning tool.
- Marketing materials section for partners.

## 4. What Code Should Improve

- Lead with the AI workspace, not only course access.
- Make the partner model legally and ethically careful: rewards should be tied to product value and actual purchases, not vague promises of income.
- Show realistic disclaimers in calculators and bonus pages.
- Keep the UI more professional and operational: less promotional clutter inside the app, more clarity and repeat-use ergonomics.
- Separate user paths:
  - learner;
  - AI workspace user;
  - partner;
  - admin/content manager.
- Add real usage history: prompts, chats, generated assets, token spend, saved templates, course progress.
- Add onboarding by user goal instead of dropping everyone into the same catalog.

## 5. Proposed Information Architecture

### Public Area

- Landing page.
- Pricing.
- Product catalog.
- Partner program overview.
- Login and registration.

### Authenticated App

- **Dashboard**: current subscription, token balance, recent AI activity, active courses, quick actions.
- **AI Workspace**: chat, model selection, saved prompts, files/assets, history, templates.
- **Learning**: course catalog, my courses, lessons, progress, certificates or completion badges.
- **Marketplace**: bundles, courses, subscriptions, token packs, order history.
- **Partner Center**: referral link, invite tools, structure, bonuses, withdrawals, calculator.
- **Materials**: marketing plan, documents, promo assets, scripts, share links.
- **Profile**: personal data, security, connected Telegram, mentor, support, access keys.
- **Admin**: users, content, products, orders, bonuses, payouts, settings.

## 6. MVP Scope

### MVP 1: Product Foundation

- Responsive web app with desktop and mobile layouts.
- Registration/login.
- User profile.
- Dashboard.
- AI workspace shell with chat history and token balance.
- Course catalog and course detail pages.
- Marketplace with static/demo products.
- Basic purchase/order state without full payment integration.

### MVP 2: Learning and Commerce

- Lesson player.
- Course progress.
- Product bundles.
- Subscriptions and token packs.
- Real payment integration.
- Order history and access keys.

### MVP 3: Partner System

- Referral links.
- Invite tracking.
- Partner dashboard.
- Bonus ledger.
- Calculator.
- Marketing materials.
- Admin review of payouts.

### MVP 4: Mobile Mini-App

- Mobile-first UI for Telegram or PWA.
- Quick AI chat.
- Course progress.
- Token balance.
- Referral link sharing.
- Notifications.

## 7. Initial Data Model

- User
- Profile
- Role
- Subscription
- TokenBalance
- TokenTransaction
- AIConversation
- AIMessage
- PromptTemplate
- Course
- Lesson
- Enrollment
- Product
- Bundle
- Order
- Payment
- AccessKey
- ReferralCode
- ReferralRelation
- PartnerVolume
- BonusTransaction
- Payout
- MarketingMaterial
- SupportRequest

## 8. Suggested Tech Stack

- **Frontend/web**: Next.js, React, TypeScript.
- **UI**: Tailwind CSS plus shadcn/ui or a small internal component system.
- **Mobile path**: responsive PWA first, Telegram Mini App second.
- **Backend**: Next.js API routes/server actions for MVP, or NestJS if backend complexity grows quickly.
- **Database**: PostgreSQL.
- **ORM**: Prisma or Drizzle.
- **Auth**: Auth.js, Clerk, or custom email/Telegram auth depending on launch path.
- **AI integrations**: provider abstraction for OpenAI, Anthropic, Google, image/video models.
- **Payments**: provider depends on target geography and legal entity.
- **Files**: S3-compatible storage.
- **Analytics**: PostHog or similar product analytics.

## 9. UX Direction

Code should feel like a serious AI operating room for creators, entrepreneurs, and teams:

- clean, fast, and practical;
- strong information density without looking overloaded;
- calm neutral palette with a distinctive accent;
- mobile navigation designed from the start;
- partner functionality presented as business tools, not casino-like earnings hype.

## 10. Key Open Questions

- What is the first target geography and payment jurisdiction?
- Will the first launch be web-only, Telegram Mini App-first, or both?
- Which AI providers must be available at launch?
- Will Code sell courses, AI access, partner packages, or all of them from day one?
- How many reward levels are required, and what legal constraints apply?
- Do we need admin tools in MVP, or can early content be managed manually?
- Should the brand be spelled `Code`, `CODE`, or another final naming variant?
