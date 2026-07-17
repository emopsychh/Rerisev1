# Code - API v0.1

## Auth API

```txt
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/forgot-password
POST /api/auth/reset-password
GET  /api/auth/me
```

## Store API

```txt
GET  /api/products
GET  /api/products/:slug
POST /api/orders
GET  /api/orders
GET  /api/orders/:id
POST /api/payments/create
POST /api/payments/webhook
```

## Academy API

```txt
GET  /api/programs
GET  /api/programs/:slug
GET  /api/lessons/:id
POST /api/lessons/:id/complete
POST /api/homework/:id/submit
```

## AI API

```txt
POST /api/ai/chat
GET  /api/ai/conversations
GET  /api/ai/conversations/:id
POST /api/ai/images
GET  /api/ai/generations
GET  /api/ai/prompts
```

## Partner API

```txt
GET  /api/partner/overview
GET  /api/partner/links
POST /api/partner/links
GET  /api/partner/team
GET  /api/partner/tree
GET  /api/partner/bonuses
POST /api/partner/calculator
POST /api/partner/withdrawals
```

## Admin API

```txt
GET    /api/admin/users
PATCH  /api/admin/users/:id
GET    /api/admin/orders
GET    /api/admin/products
POST   /api/admin/products
PATCH  /api/admin/products/:id
GET    /api/admin/bonus-runs
POST   /api/admin/bonus-runs
POST   /api/admin/withdrawals/:id/approve
POST   /api/admin/withdrawals/:id/reject
```
