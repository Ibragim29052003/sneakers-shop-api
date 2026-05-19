import django_filters

from .models import Product


class ProductFilterSet(django_filters.FilterSet):
    """FilterSet для фильтрации кроссовок по цене, категории и поставщику."""

    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.NumberFilter(field_name='categories__id')
    supplier = django_filters.NumberFilter(field_name='supplier_id')
    supplier_name = django_filters.CharFilter(field_name='supplier__name', lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'category', 'supplier', 'supplier_name', 'is_active']
