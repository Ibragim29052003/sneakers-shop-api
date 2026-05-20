# Sneaker Store API

Backend интернет-магазина кроссовок на Django REST Framework.

## Что реализовано
1. Каталог товаров, фильтры, сортировка, поиск.
2. Корзина и оформление заказа.
3. Роли и права доступа (`buyer`, `manager`, `admin`).
4. Отзывы только после подтвержденной покупки.
5. Избранное.
6. Аннотации (`avg_rating`, `sold_quantity`, `favorites_count`).
7. Celery-задачи, Mailhog, Sentry, Silk, OAuth2 (Google).

## Уровни требований курсовой
1. На `удовлетворительно`: достаточно базового API, бизнес-валидаций, `select_related`, сериализаторов, аннотаций, filterset и Postman.
2. На `хорошо`: плюс Sentry, тесты, типизация/докстринги, Silk.
3. На `отлично`: плюс Celery, Mailhog, deploy-ready конфиг, OAuth2.

Если целитесь только на `удовлетворительно`, реальные ключи Google/Sentry не обязательны.
Если целитесь на `хорошо` и `отлично`, для живой демонстрации они нужны.

## Структура проекта
1. `backend/core` — настройки, роутинг, permissions, интеграции.
2. `backend/products` — каталог, фильтры, аналитика.
3. `backend/carts` — корзина.
4. `backend/orders` — заказы и статусы.
5. `backend/reviews` — отзывы.
6. `backend/users` — auth, роли, профиль, social login.
7. `backend/tests` — автотесты по курсовым требованиям.
8. `backend/docs` — ТЗ, Postman, чек-лист защиты.

## Запуск проекта: с Docker и без Docker

Полная пошаговая инструкция вынесена в корневой файл:
`README_DEPLOY.md`

Коротко:

### Вариант 1. С Docker
```bash
cp backend/.env.example backend/.env
docker compose up -d --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

### Вариант 2. Без Docker
1. Нужны локальные сервисы: PostgreSQL (обязательно), Redis/Mailhog (по необходимости).
2. В `backend/.env` должны быть локальные хосты:
`POSTGRES_HOST=localhost`, `POSTGRES_PORT=5432`.
3. Команды:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

## Что и зачем в `.env`

### Обязательные для базового запуска
1. `DJANGO_SECRET_KEY`
2. `DJANGO_DEBUG`
3. `POSTGRES_*`

### Для демонстрации доп. требований
1. `SENTRY_DSN` — чтобы реальная ошибка ушла в Sentry.
2. `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — чтобы работал OAuth2 Google.
3. `DJANGO_ENABLE_SILK=True` — чтобы открыть Silk.

## Почему нужны `GOOGLE_CLIENT_ID` и `GOOGLE_CLIENT_SECRET`
Это требования блока OAuth2 на `отлично`.
Без них endpoint Google OAuth существует, но полноценный вход через Google не будет работать.

## Как получить Google OAuth ключи
1. Откройте [Google Cloud Console](https://console.cloud.google.com/).
2. Создайте проект или выберите существующий.
3. Включите `Google Identity` / OAuth.
4. Создайте OAuth consent screen.
5. Создайте `OAuth Client ID` типа `Web application`.
6. Добавьте redirect URI:
`http://127.0.0.1:8000/accounts/google/login/callback/`
7. Скопируйте `Client ID` и `Client Secret`.
8. Запишите их в `backend/.env`:
```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```
9. Перезапустите backend:
```bash
docker compose restart backend
```

## Почему нужен `SENTRY_DSN`
Это требование блока Sentry на `хорошо`.
Без DSN исключения не отправляются в ваш Sentry-проект.

## Как получить `SENTRY_DSN`
1. Зарегистрируйтесь/войдите на [Sentry](https://sentry.io/).
2. Создайте проект (платформа Python/Django).
3. Откройте проект `Settings -> Client Keys (DSN)`.
4. Скопируйте DSN и добавьте в `backend/.env`:
```env
SENTRY_DSN=https://....ingest.sentry.io/....
```
5. Перезапустите backend:
```bash
docker compose restart backend
```
6. Проверка отправки ошибки:
`GET /api/v1/debug/sentry/`

## Как пройти Postman перед защитой
1. Импортируйте `backend/docs/postman_collection.json`.
2. Поставьте `base_url` = `http://127.0.0.1:8000` если в коллекции есть переменная.
3. Сначала выполните `Auth -> login` (buyer/admin).
4. Скопируйте access token в `Authorization: Bearer ...` или в переменную коллекции.
5. Пройдите блоки по порядку:
`Products -> Cart -> Orders -> Reviews -> Favorites -> Analytics`.
6. Покажите минимум 3 негативных кейса:
плохой адрес, нехватка остатков, запрет buyer на admin endpoint.

## Автотесты
```bash
cd backend
source .venv/bin/activate
python manage.py test tests.test_course_requirements -v 2
python manage.py test tests.test_tasks -v 2
```

## Основные документы
1. ТЗ: `backend/docs/technical_spec.md`
2. Чек-лист требований: `backend/docs/course_requirements_checklist.md`
3. Сценарий защиты: `backend/README_ЗАЩИТА.md`
4. Деплой: `README_DEPLOY.md`
