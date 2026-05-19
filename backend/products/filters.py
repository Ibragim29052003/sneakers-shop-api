import django_filters
from django.db.models import Q

from .models import Product


class ProductFilterSet(django_filters.FilterSet):
    """FilterSet для каталога кроссовок."""

    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.NumberFilter(field_name='categories__id')
    supplier = django_filters.NumberFilter(field_name='supplier_id')
    supplier_name = django_filters.CharFilter(field_name='supplier__name', lookup_expr='icontains')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    color = django_filters.CharFilter(method='filter_color')
    colors = django_filters.CharFilter(method='filter_colors')
    size = django_filters.CharFilter(method='filter_size')
    sizes = django_filters.CharFilter(method='filter_sizes')
    fabric = django_filters.CharFilter(method='filter_fabric')
    fabrics = django_filters.CharFilter(method='filter_fabrics')

    class Meta:
        model = Product
        fields = [
            'min_price',
            'max_price',
            'category',
            'supplier',
            'supplier_name',
            'is_active',
            'status',
            'color',
            'colors',
            'size',
            'sizes',
            'fabric',
            'fabrics',
        ]

    def _filter_by_group_values(self, queryset, values, aliases):
        parsed = [value.strip() for value in values.split(',') if value.strip()]
        if not parsed:
            return queryset

        value_query = Q()
        for value in parsed:
            value_query |= Q(product_filters__filter_option__name__iexact=value)

        filtered_by_value = queryset.filter(value_query)

        group_query = Q()
        for alias in aliases:
            alias = alias.strip()
            if not alias:
                continue
            group_query |= Q(product_filters__filter_option__group__name__icontains=alias)
            group_query |= Q(product_filters__filter_option__group__name__iexact=alias)
            group_query |= Q(product_filters__filter_option__group__name__iexact=alias.capitalize())

        if group_query:
            filtered_with_group = filtered_by_value.filter(group_query).distinct()
            if filtered_with_group.exists():
                return filtered_with_group

        return filtered_by_value.distinct()


    def filter_color(self, queryset, name, value):
        return self._filter_by_group_values(queryset, value, ['цвет', 'color'])

    def filter_colors(self, queryset, name, value):
        return self.filter_color(queryset, name, value)

    def filter_size(self, queryset, name, value):
        return self._filter_by_group_values(queryset, value, ['размер', 'size'])

    def filter_sizes(self, queryset, name, value):
        return self.filter_size(queryset, name, value)

    def filter_fabric(self, queryset, name, value):
        return self._filter_by_group_values(queryset, value, ['материал', 'ткан', 'fabric', 'style'])

    def filter_fabrics(self, queryset, name, value):
        return self.filter_fabric(queryset, name, value)
