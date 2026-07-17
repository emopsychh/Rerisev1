# Backend (Django)

См. корневой [README](../README.md).

```bash
copy .env.example .env
docker compose up -d
.\.venv\Scripts\activate
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```
