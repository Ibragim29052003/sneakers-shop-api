import django_filters

from .models import Product


class ProductFilterSet(django_filters.FilterSet):
    """FilterSet для фильтрации кроссовок по цене, категории и производителю."""

    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.NumberFilter(field_name='categories__id')
    manufacturer = django_filters.NumberFilter(field_name='supplier_id')

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'category', 'manufacturer', 'is_active']
