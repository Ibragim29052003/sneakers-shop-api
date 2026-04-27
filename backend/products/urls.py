"""
Эндпоинты для ProductViewSet (доступны через router):
- GET /api/products/ - список товаров
- POST /api/products/ - создать товар
- GET /api/products/{id}/ - получить товар
- PUT /api/products/{id}/ - обновить товар
- DELETE /api/products/{id}/ - удалить товар
- GET /api/products/filter-examples/ - примеры использования filter()
- GET /api/products/manager-examples/ - примеры использования кастомного менеджера
- GET /api/products/exclude-examples/ - примеры использования exclude()
- GET /api/products/order-by-examples/ - примеры использования order_by()
- GET /api/products/double-underscore-examples/ - примеры использования __
- GET /api/products/aggregation-examples/ - примеры агрегации и аннотирования
- GET /api/products/related-name-examples/ - примеры использования related_name
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, ProductImageViewSet, SliderImageViewSet, FilterGroupViewSet, FilterOptionViewSet, ProductFilterViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='product-image')
router.register(r'slider', SliderImageViewSet, basename='slider')
router.register(r'filter-groups', FilterGroupViewSet, basename='filter-group')
router.register(r'filter-options', FilterOptionViewSet, basename='filter-option')
router.register(r'product-filters', ProductFilterViewSet, basename='product-filter')

urlpatterns = [
    path('', include(router.urls)),
]
