from typing import Any

import django_filters
from django.db.models import Q

from .models import Product


class ProductFilterSet(django_filters.FilterSet):
    """FilterSet для каталога кроссовок."""

    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.CharFilter(method='filter_category')
    supplier = django_filters.NumberFilter(field_name='supplier_id')
    supplier_name = django_filters.CharFilter(field_name='supplier__name', lookup_expr='icontains')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    color = django_filters.CharFilter(method='filter_color')
    colors = django_filters.CharFilter(method='filter_colors')
    size = django_filters.CharFilter(method='filter_size')
    sizes = django_filters.CharFilter(method='filter_sizes')
    fabric = django_filters.CharFilter(method='filter_fabric')
    fabrics = django_filters.CharFilter(method='filter_fabrics')
    brand = django_filters.CharFilter(method='filter_brand')
    brands = django_filters.CharFilter(method='filter_brands')
    style = django_filters.CharFilter(method='filter_style')
    styles = django_filters.CharFilter(method='filter_styles')
    season = django_filters.CharFilter(method='filter_season')
    seasons = django_filters.CharFilter(method='filter_seasons')
    purpose = django_filters.CharFilter(method='filter_purpose')
    purposes = django_filters.CharFilter(method='filter_purposes')

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
            'brand',
            'brands',
            'style',
            'styles',
            'season',
            'seasons',
            'purpose',
            'purposes',
        ]

    def _filter_by_group_values(self, queryset: Any, values: Any, aliases: Any) -> Any:
        """Выполняет действие `_filter_by_group_values`."""
        parsed = [value.strip() for value in values.split(',') if value.strip()]
        if not parsed:
            return queryset

        combined_query = Q()
        for value in parsed:
            value_query = Q(product_filters__filter_option__name__iexact=value)
            group_query = Q()
            for alias in aliases:
                alias = alias.strip()
                if not alias:
                    continue
                group_query |= Q(product_filters__filter_option__group__name__icontains=alias)
                group_query |= Q(product_filters__filter_option__group__name__iexact=alias)
                group_query |= Q(product_filters__filter_option__group__name__iexact=alias.capitalize())
            combined_query |= (value_query & group_query) if group_query else value_query

        return queryset.filter(combined_query).distinct()

    def filter_category(self, queryset: Any, name: Any, value: Any) -> Any:
        """
        Поддерживает category как numeric id и как строковый slug (women/men/children).

        Строковые slugs обрабатываются в ProductViewSet.get_queryset, поэтому тут
        не применяем дополнительный фильтр, чтобы не получать 400 от django-filter.
        """
        category_value = str(value).strip()
        if not category_value:
            return queryset

        if category_value.isdigit():
            return queryset.filter(categories__id=int(category_value))

        return queryset


    def filter_color(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_color`."""
        return self._filter_by_group_values(queryset, value, ['цвет', 'color'])

    def filter_colors(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_colors`."""
        return self.filter_color(queryset, name, value)

    def filter_size(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_size`."""
        return self._filter_by_group_values(queryset, value, ['размер', 'size'])

    def filter_sizes(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_sizes`."""
        return self.filter_size(queryset, name, value)

    def filter_fabric(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_fabric`."""
        return self._filter_by_group_values(queryset, value, ['материал', 'ткан', 'fabric'])

    def filter_fabrics(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_fabrics`."""
        return self.filter_fabric(queryset, name, value)

    def filter_brand(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_brand`."""
        return self._filter_by_group_values(queryset, value, ['бренд', 'brand'])

    def filter_brands(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_brands`."""
        return self.filter_brand(queryset, name, value)

    def filter_style(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_style`."""
        return self._filter_by_group_values(queryset, value, ['стиль', 'style'])

    def filter_styles(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_styles`."""
        return self.filter_style(queryset, name, value)

    def filter_season(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_season`."""
        return self._filter_by_group_values(queryset, value, ['сезон', 'season'])

    def filter_seasons(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_seasons`."""
        return self.filter_season(queryset, name, value)

    def filter_purpose(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_purpose`."""
        return self._filter_by_group_values(queryset, value, ['назнач', 'purpose'])

    def filter_purposes(self, queryset: Any, name: Any, value: Any) -> Any:
        """Выполняет действие `filter_purposes`."""
        return self.filter_purpose(queryset, name, value)
