# README_DEPLOY

## 1) Подготовка переменных окружения

Создайте файл `.env` (или используйте существующий `.env.example`) и задайте минимум:

- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY=<your-secret-key>`
- `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`
- `POSTGRES_DB=onlinestore`
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=postgres`
- `POSTGRES_HOST=postgres`
- `POSTGRES_PORT=5432`
- `CELERY_BROKER_URL=redis://redis:6379/0`
- `CELERY_RESULT_BACKEND=redis://redis:6379/0`
- `EMAIL_HOST=mailhog`
- `EMAIL_PORT=1025`
- `DEFAULT_FROM_EMAIL=noreply@onlinestore.local`

Для Google OAuth дополнительно:
- `GOOGLE_CLIENT_ID=<google-client-id>`
- `GOOGLE_CLIENT_SECRET=<google-client-secret>`

Опционально для Silk:
- `DJANGO_ENABLE_SILK=True`

## 2) Запуск в Docker

```bash terminal
docker compose up --build
```

## 3) Применение миграций

```bash terminal
docker compose exec backend python manage.py migrate
```

## 4) Создание суперпользователя

```bash terminal
docker compose exec backend python manage.py createsuperuser
```

## Что учтено
- backend запускается через gunicorn
- DEBUG=False для деплоя
- ALLOWED_HOSTS задаются через env
- collectstatic выполняется при старте backend
- media и static вынесены в volumes
- подключены сервисы: postgres, redis, celery, celery-beat, mailhog
