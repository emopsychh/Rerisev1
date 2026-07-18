# ReRise

Monorepo: Django API + Next.js portal.

```text
Rerise/
  backend/     # Django 5 + DRF + PostgreSQL
  frontend/    # Next.js 15 (product shell)
  docker/      # prod nginx + env template
  docs/        # canonical API / ROADMAP (not frontend/docs)
```

## Quick start

### Backend

```bash
cd backend
copy .env.example .env
docker compose up -d
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

- API: http://127.0.0.1:8000/api/v1/
- Swagger: http://127.0.0.1:8000/api/docs/
- Admin: http://127.0.0.1:8000/admin/

### Frontend

```bash
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

- UI: http://127.0.0.1:3020
- `NEXT_PUBLIC_API_URL` → `http://127.0.0.1:8000/api/v1`

## Production (Docker)

From repo root on the VPS:

```bash
cp docker/.env.example docker/.env
# edit secrets, PUBLIC_HOST / DJANGO_* / RERISE_REFERRAL_BASE_URL

docker compose -f docker-compose.prod.yml --env-file docker/.env up -d --build

# optional demo data (once):
# set RUN_SEED_DEMO=true in docker/.env, then:
docker compose -f docker-compose.prod.yml --env-file docker/.env up -d --force-recreate api

docker compose -f docker-compose.prod.yml exec api python manage.py createsuperuser
```

Stack: `nginx` → `web` (Next) + `api` (gunicorn) + `celery` + `celery-beat` + `postgres` + `redis`.

- Site: `http://<host>/`
- API health: `http://<host>/api/v1/health/`
- Admin: `http://<host>/admin/`

Local infra only (Postgres + Redis): `cd backend && docker compose up -d`

## Docs

- **[docs/ROADMAP.md](docs/ROADMAP.md)** — product roadmap
- **[docs/04-api-contracts.md](docs/04-api-contracts.md)** — API contracts
- `frontend/docs/` — product owner notes (not API source of truth)

## Payments (backend)

| `PAYMENT_PROVIDER` | Mode |
|---|---|
| `manual` | Admin → Confirm Payment |
| `mock` | Test payment_url |
| `cryptobot` | Crypto Pay + webhook |
