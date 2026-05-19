"""Представления для приложения товаров."""

from django.db.models import Avg, Count, DecimalField, F, IntegerField, Q, Sum, Value
from django.db.models.functions import Cast, Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdminOrReadOnly, IsAdminRole
from .filters import ProductFilterSet
from .models import (
    Category,
    FilterGroup,
    FilterOption,
    Product,
    ProductFavorite,
    ProductFilter,
    ProductImage,
    SliderImage,
)
from .serializers import (
    CategorySerializer,
    FilterGroupByCategorySerializer,
    FilterGroupSerializer,
    FilterOptionSerializer,
    ProductFavoriteSerializer,
    ProductFilterSerializer,
    ProductImageSerializer,
    ProductSerializer,
    ProductShowcaseSerializer,
    SliderImageSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return super().get_queryset().prefetch_related('subcategories')


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilterSet
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', '-price', 'created_at', '-created_at', 'name', 'avg_rating', 'sold_quantity']
    ordering = ['-created_at']

    category_mapping = {
        'women': ['женщин', 'women', 'woman', 'женская', 'для женщин', 'для девочек', 'жен'],
        'men': ['мужчин', 'men', 'man', 'мужская', 'для мужчин', 'для мальчиков', 'муж'],
        'children': ['детей', 'children', 'child', 'детская', 'для детей', 'ребенок', 'kids'],
    }

    def _get_base_queryset(self):
        return (
            super()
            .get_queryset()
            .exclude(status='draft')
            .select_related('supplier')
            .prefetch_related('categories', 'images')
            .annotate(
                avg_rating=Coalesce(
                    Cast(Avg('reviews__rating'), output_field=DecimalField(max_digits=3, decimal_places=2)),
                    Value(0, output_field=DecimalField(max_digits=3, decimal_places=2)),
                ),
                sold_quantity=Coalesce(
                    Sum(
                        'order_items__quantity',
                        filter=Q(order_items__order__status__name__in=['paid', 'delivered', 'completed']),
                    ),
                    Value(0),
                ),
                favorites_count=Coalesce(Count('favorites', distinct=True), Value(0)),
            )
        )

    def _apply_category_filter(self, queryset, category_param):
        if not category_param:
            return queryset

        search_names = self.category_mapping.get(category_param, [])
        if not search_names:
            return queryset

        category_query = Q()
        for name in search_names:
            category_query |= Q(name__icontains=name)

        category_ids = list(Category.objects.filter(category_query).values_list('id', flat=True))
        product_filter = Q(published_pages__contains=[category_param])
        if category_ids:
            product_filter |= Q(categories__id__in=category_ids)

        matching_product_ids = (
            Product.objects.exclude(status='draft').filter(product_filter).values_list('id', flat=True).distinct()
        )
        return queryset.filter(id__in=matching_product_ids)
    
    def get_queryset(self):
        queryset = self._get_base_queryset()

        category_param = self.request.query_params.get('category')
        if category_param:
            queryset = self._apply_category_filter(queryset, category_param)

        for filter_name in ['colors', 'sizes', 'fabrics']:
            raw_values = self.request.query_params.get(filter_name)
            if not raw_values:
                continue
            values = [v.strip() for v in raw_values.split(',') if v.strip()]
            if values:
                query = Q()
                for value in values:
                    query |= Q(product_filters__filter_option__name__iexact=value)
                queryset = queryset.filter(query)

        return queryset.distinct()

    @action(detail=False, methods=['get'], url_path='home-showcases')
    def home_showcases(self, request):
        category = request.query_params.get('category')
        limit = request.query_params.get('limit', '4')
        limit = int(limit) if str(limit).isdigit() else 4
        limit = max(1, min(limit, 8))

        base_queryset = self._apply_category_filter(self._get_base_queryset().filter(is_active=True), category)

        premium_queryset = base_queryset.order_by('-price', '-created_at')[:limit]

        bestseller_queryset = (
            base_queryset.annotate(
                sold_quantity=Coalesce(
                    Sum(
                        'order_items__quantity',
                        filter=Q(order_items__order__status__name__in=['paid', 'delivered', 'completed']),
                    ),
                    Value(0),
                )
            )
            .filter(sold_quantity__gt=0)
            .order_by('-sold_quantity', '-created_at')[:limit]
        )

        bestsellers_from_sales = bestseller_queryset.exists()
        if not bestsellers_from_sales:
            bestseller_queryset = base_queryset.annotate(sold_quantity=Value(0, output_field=IntegerField())).order_by(
                '-created_at'
            )[:limit]

        return Response(
            {
                'category': category,
                'premium': {
                    'title': 'Премиальная подборка',
                    'description': 'Самые выразительные и дорогие позиции категории.',
                    'items': ProductShowcaseSerializer(premium_queryset, many=True, context={'request': request}).data,
                },
                'bestsellers': {
                    'title': 'Хиты продаж',
                    'description': (
                        'Товары, которые чаще всего покупают.'
                        if bestsellers_from_sales
                        else 'Пока заказов мало, поэтому показываем свежие предложения.'
                    ),
                    'based_on_sales': bestsellers_from_sales,
                    'items': ProductShowcaseSerializer(
                        bestseller_queryset,
                        many=True,
                        context={'request': request},
                    ).data,
                },
            }
        )


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return super().get_queryset().select_related('product')


class SliderImageViewSet(viewsets.ModelViewSet):
    queryset = SliderImage.objects.all()
    serializer_class = SliderImageSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'product']
    search_fields = ['title', 'description']
    ordering_fields = ['order', 'created_at']
    ordering = ['order', '-created_at']
    
    def get_queryset(self):
        """
        Получение слайдов с предзагрузкой связанного товара.
        """
        return super().get_queryset().select_related('product')
    
    @action(detail=False, methods=['get'], url_path='active-slides')
    def active_slides(self, request):
        """
        Получение только активных слайдов для публичного API.
        
        Используется на главной странице для отображения слайдера.
        """
        slides = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(slides, many=True)
        return Response(serializer.data)


class FilterGroupViewSet(viewsets.ModelViewSet):
    queryset = FilterGroup.objects.all()
    serializer_class = FilterGroupSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']
    
    def get_queryset(self):
        """Получение групп фильтров с предзагрузкой опций."""
        return super().get_queryset().prefetch_related('options')
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Получение групп фильтров для конкретной категории.
        
        GET /api/v1/filters/by_category/?category=women
        или
        GET /api/v1/filters/by_category/?category_id=1
        """
        category_param = request.query_params.get('category')
        category_id = request.query_params.get('category_id')
        
        # Если передан category (women/men/children) - ищем по названию
        if category_param:
            # Маппинг фронтенд категорий на названия в базе
            category_mapping = {
                'women': ['женщин', 'women', 'woman', 'женская'],
                'men': ['мужчин', 'men', 'man', 'мужская'],
                'children': ['детей', 'children', 'child', 'детская'],
            }
            
            search_names = category_mapping.get(category_param, [])
            if search_names:
                from django.db.models import Q
                query = Q()
                for name in search_names:
                    query |= Q(name__icontains=name)
                categories = Category.objects.filter(query)
                if categories.exists():
                    # Берём первую подходящую категорию
                    category_id = categories.first().id
        
        if not category_id:
            return Response(
                {'error': 'Требуется параметр category или category_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        filter_groups = FilterGroup.objects.filter(
            category_id=category_id,
            is_active=True
        ).prefetch_related('options').order_by('order', 'name')
        
        serializer = FilterGroupByCategorySerializer(filter_groups, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def with_counts(self, request):
        """
        Получение фильтров с подсчетом количества товаров для каждой опции.
        
        Логика подсчета:
        - Для каждой опции внутри группы считаем товары, которые:
          1. Относятся к выбранной категории
          2. Активны
          3. Соответствуют ценовому диапазону (если выбран)
          4. Имеют данную опцию
        
        Параметры:
        - category: women/men/children
        - colors: список цветов через запятую
        - sizes: список размеров через запятую
        - fabrics: список материалов через запятую
        - min_price: минимальная цена
        - max_price: максимальная цена
        """
        from django.db.models import Q, Count
        
        category_param = request.query_params.get('category')
        category_id = request.query_params.get('category_id')
        
        # Определяем category_id
        if category_param:
            category_mapping = {
                'women': ['женщин', 'women', 'woman', 'женская'],
                'men': ['мужчин', 'men', 'man', 'мужская'],
                'children': ['детей', 'children', 'child', 'детская'],
            }
            
            search_names = category_mapping.get(category_param, [])
            if search_names:
                query = Q()
                for name in search_names:
                    query |= Q(name__icontains=name)
                categories = Category.objects.filter(query)
                if categories.exists():
                    category_id = categories.first().id
        
        if not category_id:
            return Response(
                {'error': 'Требуется параметр category или category_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Маппинг названий групп фильтров на ключи параметров
        GROUP_KEY_MAP = {
            'colors': ['цвета', 'цвет', 'colors', 'color'],
            'sizes': ['размеры', 'размер', 'sizes', 'size'],
            'fabrics': ['материалы', 'материал', 'fabrics', 'fabric'],
        }
        
        # Функция для определения типа фильтра по названию группы
        def get_filter_key(group_name):
            normalized = group_name.lower().strip()
            for key, names in GROUP_KEY_MAP.items():
                if normalized in names:
                    return key
            return None
        
        # Получаем все выбранные фильтры из разных групп
        selected_filters = {}
        for param_name in ['colors', 'sizes', 'fabrics']:
            value = request.query_params.get(param_name)
            if value:
                selected_filters[param_name] = [v.strip() for v in value.split(',') if v.strip()]
        
        # Цена
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        
        # Базовый queryset товаров для категории
        base_products = Product.objects.filter(
            categories__id=category_id,
            is_active=True
        ).distinct()
        
        # Применяем ценовой фильтр к базовому набору
        if min_price:
            try:
                base_products = base_products.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                base_products = base_products.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        # Получаем все группы фильтров для категории
        filter_groups = FilterGroup.objects.filter(
            category_id=category_id,
            is_active=True
        ).prefetch_related('options').order_by('order', 'name')
        
        result = []
        for group in filter_groups:
            group_data = {
                'id': group.id,
                'name': group.name,
                'order': group.order,
                'options': []
            }
            
            # Определяем ключ текущей группы
            current_group_key = get_filter_key(group.name)
            
            # Для каждой опции считаем количество товаров
            for option in group.options.filter(is_active=True):
                # Начинаем с базового набора товаров
                products_with_option = base_products.filter(
                    product_filters__filter_option=option
                )
                
                # Добавляем фильтры из ДРУГИХ групп (не текущей)
                for filter_key, filter_values in selected_filters.items():
                    # Пропускаем текущую группу
                    if filter_key == current_group_key:
                        continue
                    
                    if filter_values:
                        # Создаем OR условие для значений внутри группы
                        filter_query = Q()
                        for val in filter_values:
                            filter_query |= Q(product_filters__filter_option__name__iexact=val)
                        
                        products_with_option = products_with_option.filter(filter_query)
                
                count = products_with_option.distinct().count()
                
                group_data['options'].append({
                    'id': option.id,
                    'name': option.name,
                    'order': option.order,
                    'count': count
                })
            
            result.append(group_data)
        
        return Response(result)


class FilterOptionViewSet(viewsets.ModelViewSet):
    queryset = FilterOption.objects.all()
    serializer_class = FilterOptionSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group', 'is_active']
    search_fields = ['name']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']
    
    def get_queryset(self):
        """Получение значений фильтров с предзагрузкой группы."""
        return super().get_queryset().select_related('group')


class ProductFilterViewSet(viewsets.ModelViewSet):
    queryset = ProductFilter.objects.all()
    serializer_class = ProductFilterSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'filter_option']
    
    def get_queryset(self):
        """Получение связей с предзагрузкой данных."""
        return super().get_queryset().select_related('product', 'filter_option__group')


class ProductFavoriteViewSet(viewsets.ModelViewSet):
    """ViewSet для избранных товаров текущего пользователя."""

    serializer_class = ProductFavoriteSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        """Возвращает избранное только текущего пользователя."""
        return ProductFavorite.objects.filter(user=self.request.user).select_related('product')


class AdminProductAnalyticsView(APIView):
    """Сводная аналитика по товарам и заказам для администраторов."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        paid_statuses = ['paid', 'delivered', 'completed']

        top_sold_products_qs = (
            Product.objects.annotate(
                sold_quantity=Coalesce(
                    Sum('order_items__quantity', filter=Q(order_items__order__status__name__in=paid_statuses)),
                    Value(0),
                ),
                revenue=Coalesce(
                    Sum(
                        F('order_items__quantity') * F('order_items__price'),
                        filter=Q(order_items__order__status__name__in=paid_statuses),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    ),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
                ),
            )
            .filter(sold_quantity__gt=0)
            .order_by('-sold_quantity', '-revenue', 'id')[:10]
        )

        top_rated_products_qs = (
            Product.objects.annotate(
                avg_rating=Coalesce(
                    Cast(Avg('reviews__rating'), output_field=DecimalField(max_digits=3, decimal_places=2)),
                    Value(0, output_field=DecimalField(max_digits=3, decimal_places=2)),
                ),
                reviews_count=Coalesce(Count('reviews', distinct=True), Value(0)),
            )
            .filter(reviews_count__gt=0)
            .order_by('-avg_rating', '-reviews_count', 'id')[:10]
        )

        most_favorited_products_qs = (
            Product.objects.annotate(favorites_count=Coalesce(Count('favorites', distinct=True), Value(0)))
            .filter(favorites_count__gt=0)
            .order_by('-favorites_count', 'id')[:10]
        )

        from orders.models import Order

        orders_summary = Order.objects.aggregate(
            total_orders=Count('id'),
            paid_orders=Count('id', filter=Q(status__name='paid')),
            completed_orders=Count('id', filter=Q(status__name__in=['delivered', 'completed'])),
            cancelled_orders=Count('id', filter=Q(status__name='cancelled')),
            total_revenue=Coalesce(
                Sum('total', filter=Q(status__name__in=paid_statuses)),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
            ),
        )

        data = {
            'top_sold_products': [
                {
                    'id': product.id,
                    'name': product.name,
                    'sold_quantity': product.sold_quantity,
                    'revenue': product.revenue,
                }
                for product in top_sold_products_qs
            ],
            'top_rated_products': [
                {
                    'id': product.id,
                    'name': product.name,
                    'avg_rating': product.avg_rating,
                    'reviews_count': product.reviews_count,
                }
                for product in top_rated_products_qs
            ],
            'most_favorited_products': [
                {
                    'id': product.id,
                    'name': product.name,
                    'favorites_count': product.favorites_count,
                }
                for product in most_favorited_products_qs
            ],
            'orders_summary': orders_summary,
        }

        return Response(data)
