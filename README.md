# ReRise

Monorepo: Django API + Next.js portal.

```text
Rerise/
  backend/              # Django API (+ local docker-compose: postgres/redis)
  frontend/             # Next.js portal
  docker/nginx/         # nginx config for production compose
  docker-compose.yml    # production stack (use from repo root)
  .env.example          # production env template → copy to .env
  docs/
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

From **repo root** on the VPS:

```bash
cp .env.example .env
# edit secrets / hosts in .env

docker compose up -d --build
docker compose exec api python manage.py createsuperuser
```

Usual commands (same directory):

```bash
docker compose up -d
docker compose down
docker compose ps
docker compose logs -f
docker compose exec api python manage.py createsuperuser
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
