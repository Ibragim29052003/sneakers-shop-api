# Чек-лист соответствия курсовой работе (интернет-магазин кроссовок)

## 1) Основные задания (оценка "удовлетворительно")

1. Бизнес-логика, роли, ТЗ: `СДЕЛАНО`
- ТЗ: `backend/docs/technical_spec.md`
- Роли и права: `backend/core/permissions.py`, `backend/users/views.py`, `backend/orders/views.py`

2. Валидации БЛ (минимум 3): `СДЕЛАНО`
- Остатки при корзине/заказе: `backend/carts/serializers.py`, `backend/orders/serializers.py`
- Адрес доставки: `backend/orders/serializers.py`
- Мин/макс сумма заказа: `backend/orders/serializers.py`
- Доступ к заказу owner/admin: `backend/core/permissions.py`, `backend/orders/views.py`
- Отзыв только после покупки: `backend/reviews/serializers.py`
- Скидка и категория: `backend/products/serializers.py`

3. Оптимизация запросов (`select_related`): `СДЕЛАНО`
- Заказы с пользователем/статусом: `backend/orders/views.py`
- Отзывы с пользователем/товаром: `backend/reviews/views.py`
- Позиции корзины: `backend/carts/views.py`
- Товары с поставщиком: `backend/products/views.py`

4. Сериализаторы: `СДЕЛАНО`
- `SerializerMethodField`: `products/serializers.py`, `orders/serializers.py`, `reviews/serializers.py`, `carts/serializers.py`
- Передача через `context`: `backend/reviews/views.py`, `backend/products/serializers.py`

5. Аннотации: `СДЕЛАНО`
- `avg_rating`, `sold_quantity`, `favorites_count`: `backend/products/views.py`

6. FilterSet: `СДЕЛАНО`
- Цена/категория/поставщик/атрибуты: `backend/products/filters.py`

7. Postman: `СДЕЛАНО`
- Коллекция: `backend/docs/postman_collection.json`

## 2) Дополнительные задания (оценка "хорошо")

1. Sentry: `СДЕЛАНО (инфраструктура)`
- Настройки + debug endpoint: `backend/core/settings.py`, `backend/core/urls.py`

2. Тестирование (минимум 10): `СДЕЛАНО`
- API/валидации/роли/фильтры/аннотации: `backend/tests/test_course_requirements.py`
- Celery-задачи: `backend/tests/test_tasks.py`

3. Докстринги и типизация: `ЧАСТИЧНО`
- Докстринги есть широко.
- Типизация есть, но во многих местах используется `Any` (можно улучшить при желании).

4. Django Silk: `СДЕЛАНО (инфраструктура)`
- Подключение по флагу `DJANGO_ENABLE_SILK=True`: `backend/core/settings.py`, `backend/core/urls.py`

## 3) Дополнительные задания (оценка "отлично")

1. Celery периодические задачи: `СДЕЛАНО`
- Конфиг и задачи: `backend/core/celery.py`, `backend/orders/tasks.py`, `backend/products/tasks.py`

2. Mailhog: `СДЕЛАНО`
- SMTP настройки и сервис в docker-compose: `backend/core/settings.py`, `docker-compose.yml`

3. Деплой: `СДЕЛАНО`
- Docker + инструкция: `docker-compose.yml`, `README_DEPLOY.md`

4. OAuth2: `СДЕЛАНО (Google)`
- `allauth` + `dj-rest-auth`: `backend/core/settings.py`, `backend/users/social_views.py`, `backend/users/social_urls.py`

## 4) Что проверить перед защитой

1. Запустить тесты:
- `manage.py test tests.test_course_requirements -v 2`
- `manage.py test tests.test_tasks -v 2`

2. Для полной демонстрации "отлично" заполнить env:
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `SENTRY_DSN`

3. Поднять сервисы:
- `docker compose up --build`

