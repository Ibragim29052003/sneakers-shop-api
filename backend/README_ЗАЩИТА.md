о # README для защиты курсовой

## Тема проекта
Интернет-магазин кроссовок (Django REST Framework).

## Быстрый запуск
```bash terminal
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

## Запуск тестов
```bash terminal
cd backend
source .venv/bin/activate
python3 manage.py test tests.test_course_requirements -v 2
```

## Что реализовано по обязательным требованиям
1. **Бизнес-логика и роли**: администратор, покупатель.
2. **Валидации**:
   - остатки на складе (корзина/заказ),
   - формат адреса доставки,
   - лимит суммы заказа,
   - доступ к заказам только владельцу/админу,
   - отзыв только после покупки.
3. **Оптимизация запросов**: `select_related`, `prefetch_related`.
4. **Сериализаторы**:
   - `SerializerMethodField`,
   - использование `context`.
5. **Аннотации**:
   - `avg_rating`,
   - `sold_quantity`,
   - `favorites_count`.
6. **FilterSet**: фильтрация по цене, категории, производителю.
7. **Postman**: `docs/postman_collection.json`.

## Новые endpoint'ы (избранное)
- `GET /api/v1/favorites/` — список избранных товаров пользователя.
- `POST /api/v1/favorites/` — добавить в избранное (`product_id`).
- `DELETE /api/v1/favorites/{id}/` — удалить из избранного.

## Документы проекта
- Техническое задание: `docs/technical_spec.md`
- Postman-коллекция: `docs/postman_collection.json`

## Полезно для демонстрации
- Список товаров с аннотациями: `GET /api/v1/products/`
- Фильтрация товаров: `GET /api/v1/products/?min_price=500&max_price=5000`
- Создание заказа из корзины: `POST /api/v1/orders/`
