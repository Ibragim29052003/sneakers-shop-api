"""
Эндпоинты для каталога товаров интернет-магазина.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminProductAnalyticsView,
    CategoryViewSet,
    FilterGroupViewSet,
    FilterOptionViewSet,
    ProductFavoriteViewSet,
    ProductFilterViewSet,
    ProductImageViewSet,
    ProductViewSet,
    SliderImageViewSet,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='product-image')
router.register(r'slider', SliderImageViewSet, basename='slider')
router.register(r'filter-groups', FilterGroupViewSet, basename='filter-group')
router.register(r'filter-options', FilterOptionViewSet, basename='filter-option')
router.register(r'product-filters', ProductFilterViewSet, basename='product-filter')
router.register(r'favorites', ProductFavoriteViewSet, basename='product-favorite')

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/products/', AdminProductAnalyticsView.as_view(), name='admin-product-analytics'),
]
