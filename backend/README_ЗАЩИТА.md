# README_ЗАЩИТА.md

## 1) Краткое описание проекта
**Sneaker Store API** — backend интернет-магазина кроссовок на Django REST Framework.
Проект демонстрирует полный цикл e-commerce: каталог, фильтрация, корзина, заказы, отзывы, избранное, аналитика, роли и ограничения доступа.

## 2) Стек технологий
- Python 3.11+
- Django, Django REST Framework
- PostgreSQL (в Docker), SQLite (локально при необходимости)
- JWT (SimpleJWT)
- django-filter
- Celery + Celery Beat + Redis
- Mailhog
- Sentry SDK
- Django Silk
- OAuth2 (Google через dj-rest-auth + allauth)
- Docker / Docker Compose

## 2.1) Что обязательно, а что опционально
- Для базовой защиты (`удовлетворительно`) не требуются реальные ключи Google/Sentry.
- Для демонстрации дополнительных требований (`хорошо` и `отлично`) нужны:
`SENTRY_DSN`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.
- Если ключи не заданы, можно показывать только базовый функционал API без живой интеграции Sentry/OAuth.

## 3) Локальный запуск на Mac
```bash terminal
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Проверка:
- API: `http://127.0.0.1:8000/api/v1/products/`
- Админка: `http://127.0.0.1:8000/admin/`

## 4) Запуск через Docker
```bash terminal
docker compose up --build
```

Если нужно выполнить команды внутри backend-контейнера:
```bash terminal
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

## 5) Запуск тестов
Локально:
```bash terminal
cd backend
source .venv/bin/activate
python manage.py test tests.test_course_requirements -v 2
```

Docker:
```bash terminal
docker compose exec backend python manage.py test tests.test_course_requirements -v 2
```

## 6) Импорт Postman collection
1. Открыть Postman → **Import**.
2. Выбрать файл: `backend/docs/postman_collection.json`.
3. Запустить папку **Auth** (login buyer/admin).
4. Затем запускать остальные папки по порядку.

## 7) Что показать преподавателю
- Каталог и фильтры (`min_price/max_price`, `category`, `supplier`, `colors/sizes/fabrics`).
- Корзина (добавление, ограничение по stock).
- Заказ (успешный сценарий + ошибки).
- Отзыв только после покупки.
- Права доступа (buyer vs admin/manager).
- Аннотации (`avg_rating`, `sold_quantity`, `favorites_count`).
- Silk-профилирование (`/silk/`).
- Sentry (`/api/v1/debug/sentry/`).
- Celery + Beat (фоновые задачи).
- Mailhog (письма по заказам).
- OAuth2 endpoints (`/api/v1/auth/google/`).

## 8) Таблица соответствия требованиям

| Требование | Где реализовано | Как проверить |
|---|---|---|
| Роли и доступы | `core/permissions.py`, `orders/views.py`, `products/views.py` | buyer получает 403 на admin endpoints |
| Каталог и фильтрация | `products/views.py`, `products/filters.py` | `GET /api/v1/products/?min_price=500&max_price=5000` |
| Корзина | `carts/views.py`, `carts/serializers.py` | `POST /api/v1/cart-items/` и негатив по stock |
| Заказы и валидации | `orders/serializers.py`, `orders/views.py` | плохой адрес/маленькая сумма -> 400 |
| Отзывы после покупки | `reviews/serializers.py` | без покупки 400, после completed 201 |
| Избранное | `products/views.py` (`ProductFavoriteViewSet`) | add/list/delete favorites |
| Аннотации | `products/views.py` | в `GET /products/` есть `avg_rating/sold_quantity/favorites_count` |
| Postman коллекция | `docs/postman_collection.json` | импорт и последовательный прогон |
| Тесты курсовой | `tests/test_course_requirements.py` | `manage.py test ...` |
| Sentry | `core/views.py`, `settings` | вызвать `/api/v1/debug/sentry/` |
| Silk | `core/urls.py` + settings флаг | открыть `/silk/` |
| Celery/Beat | `orders/tasks.py`, `products/tasks.py`, celery config | запуск worker+beat |
| Mailhog | docker/env конфиг | письмо после создания заказа |
| OAuth2 | `users/social_urls.py`, auth urls | endpoint `/api/v1/auth/google/` |

## 9) Список endpoint'ов для демонстрации
- `POST /api/v1/auth/login/`
- `GET /api/v1/auth/profile/`
- `GET /api/v1/products/`
- `POST /api/v1/products/` (admin only)
- `GET /api/v1/cart/`
- `POST /api/v1/cart-items/`
- `POST /api/v1/orders/`
- `PATCH /api/v1/orders/{id}/` (admin/manager)
- `POST /api/v1/reviews/`
- `GET /api/v1/favorites/`
- `GET /api/v1/analytics/products/` (admin only)

## 10) Тестовые пользователи
- **buyer@test.com** / `testpass123`
- **admin@test.com** / `testpass123`
- **manager@test.com** / `testpass123` (если создан в БД)

---

## Финальный чек перед защитой
```bash terminal
cd backend
source .venv/bin/activate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test tests.test_course_requirements -v 2
python manage.py runserver
```

Для Docker:
```bash terminal
docker compose up --build
docker compose exec backend python manage.py check
docker compose exec backend python manage.py test tests.test_course_requirements -v 2
```
