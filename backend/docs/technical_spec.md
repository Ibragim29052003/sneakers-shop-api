# Техническое задание (ТЗ)

## 1. Название проекта
**Sneaker Store API** — серверная часть интернет-магазина кроссовок.

## 2. Цель проекта
Разработать REST API для e-commerce системы с ролевым доступом, бизнес-валидациями, аналитикой и инфраструктурой, достаточной для защиты курсовой работы на «отлично».

## 3. Описание предметной области
Система предназначена для продажи кроссовок:
- каталог товаров с фильтрацией,
- корзина и оформление заказа,
- отзывы покупателей,
- избранные товары,
- аналитика для административной роли,
- поддержка расширенных интеграций (Sentry, Silk, Celery, Mailhog, OAuth2).

## 4. Роли пользователей
- **Покупатель (user)**
- **Администратор (admin / staff)**
- **Менеджер (manager)** — используется для управления заказами и заявками поставщиков.

## 5. Таблица прав доступа по ролям

| Функция | Покупатель | Менеджер | Администратор |
|---|---:|---:|---:|
| Просмотр каталога | ✅ | ✅ | ✅ |
| Фильтрация/поиск/сортировка товаров | ✅ | ✅ | ✅ |
| Создание/редактирование товара | ❌ | ❌ | ✅ |
| Работа с корзиной | ✅ | ✅ | ✅ |
| Создание заказа | ✅ | ✅ | ✅ |
| Просмотр только своих заказов | ✅ | ✅ (через manager-orders) | ✅ |
| Изменение статуса заказа | ❌ | ✅ | ✅ |
| Создание отзыва после покупки | ✅ | ✅ | ✅ |
| Модерация отзывов | ❌ | ❌ | ✅ |
| Работа с избранным | ✅ | ✅ | ✅ |
| Просмотр аналитики | ❌ | ❌ | ✅ |

## 6. Основная бизнес-логика

### Каталог
- Публичный просмотр активных товаров.
- Товары в статусе `draft` исключаются из публичной выдачи.
- Для товаров рассчитываются аннотации `avg_rating`, `sold_quantity`, `favorites_count`.

### Фильтрация
- Фильтрация по диапазону цены, категории, поставщику.
- Фильтрация по атрибутам (`colors`, `sizes`, `fabrics`) с поддержкой списков.
- Поиск по `name`, `description`, `sku`; сортировка по цене, рейтингу, дате.

### Корзина
- У каждого пользователя своя корзина.
- При повторном добавлении того же товара позиции объединяются.
- Нельзя добавить недоступный товар или количество выше остатка.

### Заказ
- Заказ создается из текущей корзины.
- Проверяется непустая корзина, остатки, валидность адреса, диапазон суммы.
- После создания заказа корзина очищается, остатки уменьшаются, формируются OrderItem.

### Статусы заказа
- Справочник статусов отдельной моделью.
- Изменение статуса доступно только admin/manager.
- При смене статуса запускается фоновая email-задача.

### Отзывы
- Отзыв может оставить только пользователь, который купил товар.
- Разрешены статусы покупки: `paid`, `delivered`, `completed`.
- Один пользователь может оставить только один отзыв на товар.

### Избранное
- Покупатель может добавить товар в избранное, получить список, удалить запись.
- Избранное строго ограничено текущим пользователем.

### Аналитика
- Endpoint аналитики доступен только администратору.
- Возвращаются: топ по продажам, рейтингу, избранному и сводка заказов.

## 7. Валидации
- **Остатки:** запрет добавления/заказа сверх stock.
- **Адрес:** формат `"Улица, д 10, Город, 123456"`.
- **Сумма заказа:** от `500` до `100000`.
- **Доступ к заказу:** покупатель видит/получает только свои заказы.
- **Отзыв после покупки:** только при наличии завершенной покупки.
- **Рейтинг:** от 1 до 5.
- **Цена товара:** цена > 0; `old_price >= price`.

## 8. Модели данных
- `User`
- `Role`
- `Product`
- `Category`
- `ProductImage`
- `Cart`
- `CartItem`
- `Order`
- `OrderItem`
- `Review`
- `ProductFavorite`
- `Supplier`

## 9. API endpoints (основные)

| Method | URL | Роль | Описание |
|---|---|---|---|
| POST | `/api/v1/auth/register/` | all | Регистрация |
| POST | `/api/v1/auth/login/` | all | JWT login |
| POST | `/api/v1/auth/refresh/` | all | JWT refresh |
| GET | `/api/v1/auth/profile/` | auth | Профиль текущего пользователя |
| GET | `/api/v1/products/` | all | Список товаров |
| GET | `/api/v1/products/{id}/` | all | Детали товара |
| POST | `/api/v1/products/` | admin | Создание товара |
| PATCH | `/api/v1/products/{id}/` | admin | Обновление товара |
| GET | `/api/v1/cart/` | auth | Корзина пользователя |
| POST | `/api/v1/cart-items/` | auth | Добавить товар в корзину |
| PATCH | `/api/v1/cart-items/{id}/` | auth | Изменить количество |
| DELETE | `/api/v1/cart-items/{id}/` | auth | Удалить товар из корзины |
| POST | `/api/v1/orders/` | auth | Создать заказ из корзины |
| GET | `/api/v1/orders/` | auth | Мои заказы / все для admin |
| GET | `/api/v1/orders/{id}/` | owner/admin | Детали заказа |
| PATCH | `/api/v1/orders/{id}/` | admin/manager | Обновить статус заказа |
| POST | `/api/v1/reviews/` | auth | Создать отзыв |
| PATCH | `/api/v1/reviews/{id}/` | owner | Обновить отзыв |
| DELETE | `/api/v1/reviews/{id}/` | owner | Удалить отзыв |
| GET | `/api/v1/favorites/` | auth | Список избранного |
| POST | `/api/v1/favorites/` | auth | Добавить в избранное |
| DELETE | `/api/v1/favorites/{id}/` | auth | Удалить из избранного |
| GET | `/api/v1/analytics/products/` | admin | Аналитика |

## 10. Оптимизация запросов

### `select_related`
- `Order -> user, status`
- `OrderItem -> order, product`
- `Review -> user, product`
- `CartItem -> product, cart`
- `Product -> supplier`

### `prefetch_related`
- `Order -> items__product`
- `Product -> categories, images`
- `Cart -> items__product`
- `FilterGroup -> options`

## 11. SerializerMethodField
Используются вычисляемые поля:
- `ProductSerializer.main_image_url`
- `ProductSerializer.absolute_url`
- `ProductSerializer.supplier_name`
- `ReviewSerializer.rating_stars`
- `OrderSerializer.total_display`
- `CartSerializer.total_items`
- `CartSerializer.total_price`
- `CartItemSerializer.total_price`

## 12. Context в сериализаторах
- Передача `request` для построения абсолютных ссылок в Product/ProductImage/Slider serializers.
- Передача `product` в `ReviewCreateSerializer` через `perform_create`.

## 13. Аннотации
- `avg_rating` — средний рейтинг товара.
- `sold_quantity` — количество проданных единиц.
- `favorites_count` — число добавлений в избранное.

## 14. FilterSet
`ProductFilterSet` поддерживает:
- цена: `min_price`, `max_price`
- категория: `category`
- поставщик: `supplier`, `supplier_name`
- цвет: `color`, `colors`
- размер: `size`, `sizes`
- материал: `fabric`, `fabrics`

## 15. Postman
- Путь: `backend/docs/postman_collection.json`
- Проверяются сценарии: auth, products, filters, cart, orders, reviews, favorites, analytics, negative cases.

## 16. Тестирование
Основные тесты находятся в `backend/tests/test_course_requirements.py`:
- валидации товара,
- ограничения корзины,
- оформление заказа и доступы,
- отзывы после покупки,
- фильтрация,
- права на аналитику,
- избранное,
- аннотации.

## 17. Дополнительные задания
- **Sentry**: интегрирован endpoint проверки `/api/v1/debug/sentry/`.
- **Silk**: профилирование запросов при `DJANGO_ENABLE_SILK=True`.
- **Celery + Celery Beat**: фоновые задачи и периодика.
- **Mailhog**: локальный SMTP и просмотр писем.
- **Deploy/Docker**: docker-compose и инструкции деплоя.
- **OAuth2**: интеграция `dj-rest-auth` + `allauth` (Google).

## 18. Инструкция запуска
1. `cd backend`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python manage.py migrate`
5. `python manage.py createsuperuser`
6. `python manage.py runserver`

## 19. Инструкция демонстрации на защите
1. Авторизация buyer/admin в Postman.
2. Каталог + фильтры + сортировка.
3. Добавление товара в корзину, оформление заказа.
4. Негативы: плохой адрес, недостаточная сумма, запрет buyer на admin-действия.
5. Отзыв только после покупки + запрет повторного отзыва.
6. Избранное (add/list/delete).
7. Аналитика: buyer=403, admin=200.
8. Демонстрация Silk, Sentry, Celery, Mailhog, OAuth2 endpoints.
