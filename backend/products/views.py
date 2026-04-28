"""
Представления для приложения товаров

В этом файле демонстрируются:
1. filter() - фильтрация queryset
2. exclude() - исключение объектов из queryset
3. order_by() - сортировка объектов
4. __ (double underscore) - доступ к полям связанных таблиц и методы
5. Aggregation (Sum, Count, Avg, Max, Min) - агрегация данных
6. Annotation - аннотирование данных
7. related_name - использование в запросах
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import redirect, get_object_or_404, Http404
from django.db.models import Sum, Count, Avg, Max, Min, F, Q, Case, When, Value, IntegerField
from django.db.models.functions import Concat, Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ProductImage, SliderImage, FilterGroup, FilterOption, ProductFilter
from .serializers import CategorySerializer, ProductSerializer, ProductImageSerializer, SliderImageSerializer, FilterGroupSerializer, FilterGroupByCategorySerializer, FilterOptionSerializer, ProductFilterSerializer, ProductSupplierDemoSerializer, ProductShowcaseSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet для модели категории."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """
        Получение списка категорий с предзагрузкой подкатегорий.
        """

        return super().get_queryset().prefetch_related('subcategories')


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet для модели товара.
    
    Содержит примеры использования:
    - filter() - фильтрация товаров
    - exclude() - исключение товаров
    - order_by() - сортировка товаров
    - __ (double underscore) - доступ к связанным таблицам
    - Aggregation - агрегация данных
    - Annotation - аннотирование данных
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'price': ['gte', 'lte'],
        'categories': ['exact'],
        'is_active': ['exact'],
    }
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', 'created_at', 'name']
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
            .prefetch_related('categories', 'images')
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

        category_ids = list(
            Category.objects.filter(category_query).values_list('id', flat=True)
        )
        product_filter = Q(published_pages__contains=[category_param])
        if category_ids:
            product_filter |= Q(categories__id__in=category_ids)

        matching_product_ids = (
            Product.objects
            .exclude(status='draft')
            .filter(product_filter)
            .values_list('id', flat=True)
            .distinct()
        )
        return queryset.filter(id__in=matching_product_ids)
    
    def get_queryset(self):
        queryset = self._get_base_queryset()
        
        # Получаем параметры фильтров из query params
        category_param = self.request.query_params.get('category')
        colors = self.request.query_params.get('colors')
        sizes = self.request.query_params.get('sizes')
        fabrics = self.request.query_params.get('fabrics')
        
        # Фильтрация по категории
        if category_param:
            queryset = self._apply_category_filter(queryset, category_param)
        
        # Применяем фильтры если они есть
        from django.db.models import Q
        filter_query = Q()
        
        # Фильтр по цветам (любой из выбранных)
        if colors:
            color_list = [c.strip() for c in colors.split(',') if c.strip()]
            if color_list:
                color_query = Q()
                for color in color_list:
                    color_query |= Q(product_filters__filter_option__name__iexact=color)
                filter_query &= color_query
        
        # Фильтр по размерам (любой из выбранных)
        if sizes:
            size_list = [s.strip() for s in sizes.split(',') if s.strip()]
            if size_list:
                size_query = Q()
                for size in size_list:
                    size_query |= Q(product_filters__filter_option__name__iexact=size)
                filter_query &= size_query
        
        # Фильтр по материалам (любой из выбранных)
        if fabrics:
            fabric_list = [f.strip() for f in fabrics.split(',') if f.strip()]
            if fabric_list:
                fabric_query = Q()
                for fabric in fabric_list:
                    fabric_query |= Q(product_filters__filter_option__name__iexact=fabric)
                filter_query &= fabric_query
        
        # Применяем фильтр если есть
        if filter_query:
            queryset = queryset.filter(filter_query).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'], url_path='home-showcases')
    def home_showcases(self, request):
        """
        Возвращает две витринные подборки для главной страницы:
        - premium: дорогие товары категории
        - bestsellers: самые продаваемые товары по данным заказов
        """
        category = request.query_params.get('category')
        limit = request.query_params.get('limit', '4')
        limit = int(limit) if str(limit).isdigit() else 4
        limit = max(1, min(limit, 8))

        base_queryset = self._apply_category_filter(
            self._get_base_queryset().filter(is_active=True),
            category,
        )

        premium_queryset = (
            base_queryset
            .order_by('-price', '-created_at')[:limit]
        )

        bestseller_queryset = (
            base_queryset
            .annotate(
                sold_quantity=Coalesce(
                    Sum('order_items__quantity'),
                    Value(0),
                )
            )
            .filter(sold_quantity__gt=0)
            .order_by('-sold_quantity', '-created_at')[:limit]
        )

        bestsellers_from_sales = bestseller_queryset.exists()

        if not bestsellers_from_sales:
            bestseller_queryset = (
                base_queryset
                .annotate(sold_quantity=Value(0, output_field=IntegerField()))
                .order_by('-created_at')[:limit]
            )

        premium_data = ProductShowcaseSerializer(
            premium_queryset,
            many=True,
            context={'request': request},
        ).data
        bestsellers_data = ProductShowcaseSerializer(
            bestseller_queryset,
            many=True,
            context={'request': request},
        ).data

        return Response({
            'category': category,
            'premium': {
                'title': 'Премиальная подборка',
                'description': 'Самые выразительные и дорогие позиции категории.',
                'items': premium_data,
            },
            'bestsellers': {
                'title': 'Хиты продаж',
                'description': (
                    'Товары, которые чаще всего покупают.'
                    if bestsellers_from_sales
                    else 'Пока заказов мало, поэтому показываем свежие предложения.'
                ),
                'based_on_sales': bestsellers_from_sales,
                'items': bestsellers_data,
            },
        })

    @action(detail=False, methods=['get'], url_path='supplier-demo')
    def supplier_demo(self, request):
        """
        Демонстрация N+1 проблемы для связи Product -> supplier.
        """
        queryset = Product.objects.filter(supplier__isnull=False).order_by('id')
###444############# http://127.0.0.1:8000/api/v1/products/supplier-demo/
        queryset = queryset.select_related('supplier')

        limit = request.query_params.get('limit')
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
        else:
            queryset = queryset[:20]

        serializer = ProductSupplierDemoSerializer(
            queryset,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def manager_examples(self, request):
        all_products_via_objects = Product.objects.all()
        all_products_via_default_manager = Product.all_objects.all()
        active_products = Product.objects.active()
        recent_products = Product.objects.recently_created(days=30)
        price_range_products = Product.objects.with_price_range(min_price=100, max_price=1000)
        uncategorized_products = Product.objects.without_category()

        return Response({
            'objects_all_count': all_products_via_objects.count(),
            'all_objects_count': all_products_via_default_manager.count(),
            'all_products_print': list(
                all_products_via_objects.values('id', 'name', 'status', 'price')
            ),
            'active_products_count': active_products.count(),
            'recent_products_count': recent_products.count(),
            'price_range_products_count': price_range_products.count(),
            'without_category_count': uncategorized_products.count(),
        })
    
#333333##
    @action(detail=False, methods=['get'])
    def filter_examples(self, request):

        # Найти все активные товары
        active_products = Product.objects.filter(is_active=True)
        
        # Найти активные товары с ценой от 100 до 1000
        active_price_range = Product.objects.filter(
            is_active=True,
            price__gte=100,
            price__lte=1000
        )
        
        # Найти товары конкретного поставщика
        # products/suppliers__name - обращение к связанной таблице через __
        supplier_products = Product.objects.filter(supplier__name='Поставщик ООО')
        
     
        # Найти товары с ценой больше или равно
        expensive_products = Product.objects.filter(price__gte=500)
        
        # Найти товары в конкретной категории
        category_products = Product.objects.filter(categories__id=1)
        
        # Найти товары, созданные за последние 7 дней
        from django.utils import timezone
        from datetime import timedelta
        recent_products = Product.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        )
        
        return Response({
            'active_count': active_products.count(),
            'active_price_range_count': active_price_range.count(),
            'supplier_products_count': supplier_products.count(),
            'expensive_products_count': expensive_products.count(),
            'category_products_count': category_products.count(),
            'recent_products_count': recent_products.count(),
        })
    
   
    
    @action(detail=False, methods=['get'])
    def exclude_examples(self, request):
        """  
        exclude() - метод для исключения объектов, соответствующих условиям.
        Возвращает QuerySet с объектами, НЕ соответствующими условиям.
        """
        
        # исключить товары определённого статуса
        not_drafts = Product.objects.exclude(status='draft')
        
        # Исключить товары без поставщика И с ценой ниже 100
        excluded_products = Product.objects.exclude(
            supplier__isnull=True,
            price__lt=100
        )
        
        # Исключить товары конкретного поставщика
        exclude_supplier = Product.objects.exclude(supplier__name='Тестовый Поставщик')
        
        # Сначала фильтруем по активности, затем исключаем определённую категорию
        filtered = Product.objects.filter(is_active=True)
        result = filtered.exclude(categories__id__in=[1, 2])
        
        # exclude() с Q объектами для сложных условий
        from django.db.models import Q
        complex_exclude = Product.objects.exclude(
            Q(status='archived') | Q(price__lt=10)
        )
        
        return Response({
            'not_drafts_count': not_drafts.count(),
            'excluded_products_count': excluded_products.count(),
            'exclude_supplier_count': exclude_supplier.count(),
            'filtered_excluded_count': result.count(),
            'complex_exclude_count': complex_exclude.count(),
        })
    
    
    @action(detail=False, methods=['get'])
    def order_by_examples(self, request):
        """       
        order_by() - метод для сортировки результатов запроса.
        По умолчанию сортировка по возрастанию.
        Для сортировки по убыванию используется минус (-).
        """
        
        # по одному полю (по возрастанию)
        # Сортировка по названию товара (А-Я)
        by_name = Product.objects.order_by('name')
        
        # по убыванию
        # Сортировка по дате создания (новые первые)
        by_created_desc = Product.objects.order_by('-created_at')
        
        # по нескольким полям
        # Сначала по статусу, затем по цене
        by_status_and_price = Product.objects.order_by('status', 'price')
        
        # с связанными полями через __
        # Сортировка по имени поставщика
        by_supplier = Product.objects.order_by('supplier__name')
        
        # с annotate (аннотация)
        # Сортировка по количеству изображений
        from django.db.models import Count
        by_images_count = Product.objects.annotate(
            images_count=Count('images')
        ).order_by('images_count')
        
        # Пример 6: order_by() с Case/When для условной сортировки
        # Сортировка: сначала дорогие товары (>1000), затем остальные
        custom_order = Product.objects.annotate(
            priority=Case(
                When(price__gt=1000, then=Value(0)),
                default=Value(1)
            )
        ).order_by('priority', '-price')
        
        return Response({
            'by_name_first': by_name.first().name if by_name.exists() else None,
            'by_created_desc_first': by_created_desc.first().name if by_created_desc.exists() else None,
            'by_status_and_price_count': by_status_and_price.count(),
            'by_supplier_count': by_supplier.count(),
            'by_images_count_count': by_images_count.count(),
            'custom_order_count': custom_order.count(),
        })

    
    @action(detail=False, methods=['get'])
    def double_underscore_examples(self, request):
        """
        Django ORM использует __ для:
        1. Доступа к полям связанных таблиц (related table lookup)
        2. Вызова методов (queryset methods)
        
        ВАРИАНТ 1: Обращение к связанной таблице (related table lookup)
        """
        
        # Обращение к связанной таблице через __
        
        # Найти товары, где имя поставщика содержит "ООО"
        products_by_supplier_name = Product.objects.filter(
            supplier__name__icontains='ООО'
        )
        
        # Найти товары, которые находятся в категории с ID=1
        products_in_category = Product.objects.filter(
            categories__id=1
        )
        
        products_with_active_contract = Product.objects.filter(
            supplier__contracts__status__name='active'
        )
        
        from django.utils import timezone
        from datetime import timedelta
        products_valid_contract = Product.objects.filter(
            supplier__contracts__end_date__gte=timezone.now().date()
        )
        
        products_with_main_image = Product.objects.filter(
            images__is_main=True
        )
        
        # Методы (queryset methods) с __
        
        # Найти товары и добавить количество изображений как аннотацию
        products_with_image_count = Product.objects.annotate(
            image_count=Count('images')
        ).filter(image_count__gt=0)
        
        # Пример 2.2: aggregate() с обращением к связанным таблицам
        # Средняя цена товаров конкретного поставщика
        from django.db.models import Avg
        avg_price_by_supplier = Product.objects.filter(
            supplier__id=1
        ).aggregate(Avg('price'))
        
        # Пример 2.3: order_by() с __ для сортировки по связанному полю
        # Сортировка товаров по названию категории
        products_by_category = Product.objects.order_by('categories__name')
        
        # Пример 2.4: exclude() с __ для исключения по связанному полю
        # Исключить товары определённого статуса поставщика
        products_exclude_inactive = Product.objects.exclude(
            supplier__is_active=False
        )
        
        # Пример 2.5: Prefetch с __ для оптимизации
        # Предварительная загрузка связанных данных
        products_prefetched = Product.objects.prefetch_related(
            'categories',
            'images',
            'supplier__contracts'
        )
        
        return Response({
            'by_supplier_name_count': products_by_supplier_name.count(),
            'in_category_count': products_in_category.count(),
            'active_contract_count': products_with_active_contract.count(),
            'valid_contract_count': products_valid_contract.count(),
            'main_image_count': products_with_main_image.count(),
            'with_image_count': products_with_image_count.count(),
            'avg_price_by_supplier': avg_price_by_supplier,
            'by_category_count': products_by_category.count(),
            'exclude_inactive_count': products_exclude_inactive.count(),
            'prefetched_count': products_prefetched.count(),
        })
    

    
    @action(detail=False, methods=['get'])
    def aggregation_examples(self, request):
        """        
        АГРЕГАЦИЯ (aggregate) - вычисляет одно значение для всего набора данных.
        Примеры: Sum, Count, Avg, Max, Min
        
        АННОТАЦИЯ (annotate) - вычисляет значение для каждого объекта отдельно.
        """
        
        # ПРИМЕР 1: Агрегация - общее количество и средняя цена товаров
        
        # aggregate() - вычисляет агрегированные значения для всего QuerySet
        # Возвращает словарь с результатами
        product_stats = Product.objects.aggregate(
            total_products=Count('id'),
            avg_price=Avg('price'),
            max_price=Max('price'),
            min_price=Min('price'),
            total_value=Sum('price')
        )
        
        # ПРИМЕР 2: Аннотация - количество изображений для каждого товара
        
        products_with_image_count = Product.objects.annotate(
            image_count=Count('images')
        ).values('id', 'name', 'image_count')
        
        # ПРИМЕР 3: Аннотация с фильтрацией - товары с категориями
        
        # Аннотация с условным подсчётом
        products_with_categories = Product.objects.annotate(
            category_count=Count('categories'),
            # Аннотация для проверки наличия главного изображения
            has_main_image=Count(
                Case(When(images__is_main=True, then=1))
            )
        ).values('id', 'name', 'category_count', 'has_main_image')
        
        # ДОПОЛНИТЕЛЬНЫЕ ПРИМЕРЫ АГРЕГАЦИИ
        
        # Агрегация по группам (GROUP BY)
        # Средняя цена товаров по статусам
        price_by_status = Product.objects.values('status').annotate(
            count=Count('id'),
            avg_price=Avg('price')
        )
        
        # Агрегация с фильтрацией связанных объектов
        # Количество активных товаров
        active_count = Product.objects.filter(is_active=True).count()
        
        # Аннотация с вычисляемым полем (F() expression)
        # Цена с НДС (20%)
        products_with_vat = Product.objects.annotate(
            price_with_vat=F('price') * 1.2
        ).values('id', 'name', 'price', 'price_with_vat')[:5]
        
        # Аннотация для связанных таблиц
        # Количество товаров у каждого поставщика
        suppliers_with_product_count = Product.objects.values(
            'supplier__name'
        ).annotate(
            product_count=Count('id')
        )
        
        # Сложная агрегация с подзапросом
        # Общая стоимость всех заказов для каждого пользователя
        from orders.models import Order
        orders_by_user = Order.objects.values('user__email').annotate(
            total_spent=Sum('total'),
            order_count=Count('id')
        )
        
        return Response({
            # Пример 1: Агрегация
            'product_stats': {
                'total_products': product_stats['total_products'],
                'avg_price': str(product_stats['avg_price']) if product_stats['avg_price'] else None,
                'max_price': str(product_stats['max_price']) if product_stats['max_price'] else None,
                'min_price': str(product_stats['min_price']) if product_stats['min_price'] else None,
            },
            # Пример 2: Аннотация
            'products_with_image_count': list(products_with_image_count[:3]),
            # Пример 3: Аннотация с фильтрацией
            'products_with_categories': list(products_with_categories[:3]),
            # Дополнительные примеры
            'price_by_status': list(price_by_status),
            'active_count': active_count,
            'products_with_vat': list(products_with_vat),
            'suppliers_with_product_count': list(suppliers_with_product_count)[:3],
        })
    
    # ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ related_name
    
    @action(detail=False, methods=['get'])
    def related_name_examples(self, request):
        """
        Демонстрация использования related_name
        
        related_name - это атрибут ForeignKey, который определяет имя
        для обратной связи от связанной модели.
        
        В модели Product:
        - supplier = ForeignKey(Supplier, related_name='products')
        - images = ForeignKey(ProductImage, related_name='product')
        
        Это позволяет обращаться:
        - supplier.products.all() - все товары поставщика
        - product.images.all() - все изображения товара
        """
        
        # Пример 1: Использование related_name='products' в Supplier
        # Получить всех поставщиков с их товарами
        from suppliers.models import Supplier
        suppliers = Supplier.objects.prefetch_related('products').filter(
            is_active=True
        )[:5]
        
        suppliers_data = []
        for supplier in suppliers:
            suppliers_data.append({
                'supplier_name': supplier.name,
                'products_count': supplier.products.count(),
                'products_names': list(supplier.products.values_list('name', flat=True)[:3])
            })
        
        # Пример 2: Использование related_name='images' в ProductImage
        # Получить товар с его изображениями
        product_with_images = Product.objects.prefetch_related('images').first()
        if product_with_images:
            images_data = list(product_with_images.images.values(
                'id', 'image', 'is_main', 'alt_text'
            ))
        else:
            images_data = []
        
        # Пример 3: Использование related_name='items' в Order
        # Получить заказ с его позициями
        from orders.models import Order
        order_with_items = Order.objects.prefetch_related('items').first()
        if order_with_items:
            order_data = {
                'order_id': order_with_items.id,
                'total': str(order_with_items.total),
                'items_count': order_with_items.items.count(),
                'items': list(order_with_items.items.values(
                    'product_name', 'quantity', 'price'
                )[:3])
            }
        else:
            order_data = {}
        
        # Пример 4: Использование related_name='orders' в User
        # Получить пользователя с его заказами
        from users.models import User
        user_with_orders = User.objects.prefetch_related('orders').first()
        if user_with_orders:
            user_orders_data = {
                'user_email': user_with_orders.email,
                'orders_count': user_with_orders.orders.count(),
                'total_spent': str(user_with_orders.orders.aggregate(
                    total=Sum('total')
                )['total'] or 0)
            }
        else:
            user_orders_data = {}
        
        return Response({
            'suppliers_with_products': suppliers_data,
            'product_images': images_data,
            'order_with_items': order_data,
            'user_orders': user_orders_data,
        })
    
    # ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ __icontains (регистронезависимый) и __contains
#**6

    @action(detail=False, methods=['get'])
    def contains_examples(self, request):
           
        # Найти товары, где название содержит "телефон" (любой регистр)
        # Эквивалентно: WHERE LOWER(name) LIKE LOWER('%телефон%')
        products_icontains = Product.objects.filter(
            name__icontains='телефон'
        )
        
        # Найти товары, где описание содержит "скидка" (любой регистр)
        # Также найдёт "СКИДКА", "Скидка", "скидка"
        products_with_discount = Product.objects.filter(
            description__icontains='скидка'
        )
        
        # Поиск по полю связанной таблицы (регистронезависимо)
        # Найти товары поставщиков, название которых содержит "ООО"
        supplier_products_icontains = Product.objects.filter(
            supplier__name__icontains='ооо'
        )
        
        # ПРИМЕР 2: __contains - регистрозависимый поиск
        
        # Найти товары, где артикул (SKU) содержит "IPHONE" (точно так)
        # Эквивалентно: WHERE sku LIKE BINARY '%IPHONE%'
        # Важно: этот поиск чуствителен к регистру
        products_contains_case = Product.objects.filter(
            sku__contains='IPHONE'  # найдёт "IPHONE13", но не "iphone13"
        )
        
        # Найти товары, где название точно содержит "Pro" (с учётом регистра)
        # Найдёт "iPhone Pro", но не "iphone pro"
        products_pro_contains = Product.objects.filter(
            name__contains='Pro'
        )
        
        # Комбинирование __contains с другими фильтрами
        # Найти активные товары с артикулом, содержащим "2024"
        active_2024 = Product.objects.filter(
            is_active=True,
            sku__contains='2024'
        )
        
        # ПРИМЕР 3: Практическое применение
        
        # Поиск по нескольким полям с __icontains (OR условие)
        from django.db.models import Q
        search_query = 'phone'
        multi_field_search = Product.objects.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
        
        return Response({
            'icontains_phone_count': products_icontains.count(),
            'icontains_discount_count': products_with_discount.count(),
            'icontains_supplier_count': supplier_products_icontains.count(),
            'contains_iphone_count': products_contains_case.count(),
            'contains_pro_count': products_pro_contains.count(),
            'contains_active_2024_count': active_2024.count(),
            'multi_field_search_count': multi_field_search.count(),
        })
    
    
    @action(detail=False, methods=['get'])
    def values_examples(self, request):
        """        
        values() - возвращает QuerySet с словарями (QuerySet[dict])
        values_list() - возвращает QuerySet с кортежами (QuerySet[tuple])
        
        В отличие от .all() который возвращает полные объекты модели,
        эти методы позволяют получить только нужные поля.
        """
        
        
        products_values = Product.objects.values('id', 'name')
        
        active_products_values = Product.objects.filter(
            is_active=True
        ).values('name', 'price')
        
        #  товары с количеством изображений
        products_with_image_count = Product.objects.annotate(
            image_count=Count('images')
        ).values('name', 'image_count')
        
        products_with_supplier = Product.objects.values(
            'name', 'supplier__name'
        )
        
        #  товары отсортированные по цене
        products_ordered = Product.objects.values(
            'name', 'price'
        ).order_by('price')
        
        
        products_names_list = Product.objects.values_list('name', flat=True)
        
        # values_list() без flat - возвращает кортежи
        products_id_name = Product.objects.values_list('id', 'name')
        
        # values_list() с фильтрацией
        # Получить id и price дорогих товаров
        expensive_products = Product.objects.filter(
            price__gte=1000
        ).values_list('id', 'price')
        
        # values_list() по связанным полям
        # Получить названия категорий всех товаров
        products_categories = Product.objects.values_list(
            'categories__name', flat=True
        )
        
        # values_list() + distinct - уникальные значения
        # Получить все уникальные статусы товаров
        unique_statuses = Product.objects.values_list(
            'status', flat=True
        ).distinct()
        
        # ПРИМЕР 3: Практическое применение
        
        # Получить словарь {id: name} для создания ChoiceField
        product_choices = dict(Product.objects.values_list('id', 'name'))
        
        # Получить первые 5 значений (list slicing)
        first_5_values = list(Product.objects.values('id', 'name')[:5])
        
        return Response({
            # values() примеры
            'products_values_sample': list(products_values[:3]),
            'active_products_values_sample': list(active_products_values[:3]),
            'products_with_image_count_sample': list(products_with_image_count[:3]),
            'products_with_supplier_sample': list(products_with_supplier[:3]),
            'products_ordered_sample': list(products_ordered[:3]),
            # values_list() примеры
            'products_names_list_first5': list(products_names_list[:5]),
            'products_id_name_first5': list(products_id_name[:5]),
            'expensive_products_first5': list(expensive_products[:5]),
            'products_categories_sample': list(products_categories[:5]),
            'unique_statuses': list(unique_statuses),
            # Практическое применение
            'product_choices': product_choices,
            'first_5_values': first_5_values,
        })
    
    # ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ count() и exists()
    
    @action(detail=False, methods=['get'])
    def count_exists_examples(self, request):
        
        
        # Общее количество товаров
        total_products = Product.objects.count()
        
        # Количество товаров с фильтрацией
        active_products_count = Product.objects.filter(is_active=True).count()
        
        # Количество товаров конкретного поставщика
        supplier_products_count = Product.objects.filter(
            supplier__name__icontains='ООО'
        ).count()
        
        # Количество товаров в конкретной категории
        category_products_count = Product.objects.filter(
            categories__id=1
        ).count()
        
        # Количество товаров по условию (цена больше 1000)
        expensive_count = Product.objects.filter(price__gt=1000).count()
        
        # count() с distinct - уникальный подсчёт
        # Количество уникальных категорий у товаров
        unique_categories_count = Product.objects.values(
            'categories'
        ).distinct().count()
        
        # count() после annotate
        # Подсчёт с аннотацией (количество изображений для каждого товара > 0)
        products_with_images_count = Product.objects.annotate(
            image_count=Count('images')
        ).filter(image_count__gt=0).count()
        
        # ПРИМЕР 2: exists() - проверка наличия объектов
        
        # Проверить существует ли хотя бы один товар
        has_any_product = Product.objects.exists()
        
        # Проверить существует ли активный товар
        has_active_product = Product.objects.filter(is_active=True).exists()
        
        # Проверить существует ли товар с конкретным ID
        product_exists = Product.objects.filter(pk=1).exists()
        
        # Проверить существует ли товар конкретного поставщика
        supplier_product_exists = Product.objects.filter(
            supplier__name='Поставщик ООО'
        ).exists()
        
        # Проверить существует ли товар в конкретной категории
        category_has_products = Product.objects.filter(
            categories__id=1
        ).exists()
        
        # exists() часто используется для проверки перед созданием
        # Проверить уникальность перед созданием
        sku_exists = Product.objects.filter(sku='UNIQUE-SKU-123').exists()
        
        # ПРИМЕР 3: Практическое применение
        
        # Паттерн: если товаров много - показать сообщение
        if total_products > 100:
            has_many_products = True
        else:
            has_many_products = False
        
        # Паттерн: проверить доступность товара перед покупкой
        product_id = request.query_params.get('product_id')
        if product_id:
            product_available = Product.objects.filter(
                pk=product_id,
                is_active=True,
                status='active'
            ).exists()
        else:
            product_available = False
        
        return Response({
            # count() примеры
            'total_products': total_products,
            'active_products_count': active_products_count,
            'supplier_products_count': supplier_products_count,
            'category_products_count': category_products_count,
            'expensive_count': expensive_count,
            'unique_categories_count': unique_categories_count,
            'products_with_images_count': products_with_images_count,
            # exists() примеры
            'has_any_product': has_any_product,
            'has_active_product': has_active_product,
            'product_exists': product_exists,
            'supplier_product_exists': supplier_product_exists,
            'category_has_products': category_has_products,
            'sku_exists': sku_exists,
            # Практическое применение
            'has_many_products': has_many_products,
            'product_available': product_available,
        })
    
    # ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ update() и delete()
    
    @action(detail=False, methods=['get', 'post'])
    def update_delete_examples(self, request):
                
        # Обновить статус всех активных товаров на 'archived'
        # Возвращает количество обновлённых записей
        archived_count = Product.objects.filter(
            is_active=False
        ).update(status='archived')
        
#№№ 
        # F expressions (выражения F) позволяют ссылаться на значения полей модели непосредственно в запросах к базе данных. 

        from django.db.models import F
        increased_price_count = Product.objects.filter(
            is_active=True
        ).update(price=F('price') * 1.1)


        # # Уменьшить количество на складе
        # Product.objects.filter(inventory__quantity__gt=0).update(
        #     inventory__quantity=F('inventory__quantity') - 1
        # )

        # # Обновить цену с учётом скидки
        # Product.objects.all().update(
        #     price=F('price') * (1 - F('discount_percentage') / 100)
        # )

        # # Найти товары, где цена меньше старой цены
        # products = Product.objects.filter(price__lt=F('old_price'))

        # # Найти товары с отрицательным остатком
        # products = Product.objects.filter(
        #     inventory__quantity__lt=F('min_stock_level')
        # )
                
        # update() с несколькими полями
        # Обновить статус и активность товаров без поставщика
        no_supplier_updated = Product.objects.filter(
            supplier__isnull=True
        ).update(
            status='out_of_stock',
            is_active=False
        )
        
        # update() с now() - обновление даты
        # Обновить дату создания у всех черновиков
        from django.db.models.functions import Now
        # Примечание: для DateTimeField используем функцию
        # Для простого обновления даты можно использовать выражение
        # (здесь используется как пример логики)
        
        # update() с Case/When - условное обновление
        # Установить разные статусы в зависимости от цены
        conditional_update_count = Product.objects.update(
            status=Case(
                When(price__lt=100, then=Value('out_of_stock')),
                When(price__gt=1000, then=Value('active')),
                default=Value('draft')
            )
        )
        
        # ПРИМЕР 2: delete() - массовое удаление
        
        # Удалить все товары со статусом 'archived'
        deleted_archived = Product.objects.filter(
            status='archived'
        ).delete()  # Возвращает (количество_удаленных, {'модель': количество})
        
        # delete() - удалить товары без категории
        # deleted_no_category = Product.objects.filter(
        #     categories__isnull=True
        # ).delete()
        
        # delete() - удалить товары конкретного поставщика
        # (в реальном приложении это было бы по ID)
        # deleted_by_supplier = Product.objects.filter(
        #     supplier__name='Тестовый Поставщик'
        # ).delete()
        
        
        # POST запрос для демонстрации update/delete (только для примера)
        if request.method == 'POST':
            action_type = request.data.get('action')
            
            if action_type == 'archive_expensive':
                # Архивировать дорогие товары
                count = Product.objects.filter(
                    price__gt=5000
                ).update(status='archived')
                return Response({'updated_count': count, 'message': 'Дорогие товары архивированы'})
            
            elif action_type == 'activate_low_price':
                # Активировать дешёвые товары
                count = Product.objects.filter(
                    price__lt=100
                ).update(is_active=True, status='active')
                return Response({'updated_count': count, 'message': 'Дешёвые товары активированы'})
            
            elif action_type == 'delete_drafts':
                # Удалить все черновики
                result = Product.objects.filter(
                    status='draft'
                ).delete()
                return Response({
                    'deleted_count': result[0], 
                    'message': 'Черновики удалены'
                })
        
        return Response({
            # update() примеры
            'archived_count': archived_count,
            'increased_price_count': increased_price_count,
            'no_supplier_updated': no_supplier_updated,
            'conditional_update_count': conditional_update_count,
            # delete() примеры
            'deleted_archived': deleted_archived[0],  # Общее количество удаленных
            # Обратите внимание: delete() возвращает кортеж (удаленные, детали)
            # Второй элемент содержит {'модель': количество} для каждой удаленной модели
        })


###    
    @action(detail=False, methods=['get'])
    def cache_examples(self, request):

        from django.core.cache import cache
        
        cache_key = 'active_products_count'
        cached_count = cache.get(cache_key)
        
        if cached_count is None:
            # Если нет в кэше - получаем из БД
            cached_count = Product.objects.filter(is_active=True).count()
            cache.set(cache_key, cached_count, 300)
        

        product_stats_data = {
            'total_count': Product.objects.count(),
            'active_count': Product.objects.filter(is_active=True).count(),
            'archived_count': Product.objects.filter(status='archived').count(),
        }
        cache.set_many({
            'product_stats_total': product_stats_data['total_count'],
            'product_stats_active': product_stats_data['active_count'],
            'product_stats_archived': product_stats_data['archived_count'],
        }, 300)
        
        stats_cached = cache.get_many(['product_stats_total', 'product_stats_active'])
        

        return Response({
            'cached_count': cached_count,
            'product_stats_data': product_stats_data,
            'stats_from_cache': stats_cached,
            'cache_info': 'Данные кэшируются на 300 секунд (5 минут)'
        })
    
    @action(detail=False, methods=['get'])
    def http404_examples(self, request):
        from django.http import Http404
        
        
        product_id = request.query_params.get('product_id', 1)
        
        try:
            # Попытка получить товар
            product = get_object_or_404(Product, pk=product_id)
            product_name = product.name
            product_price = str(product.price)
            found = True
        except Http404:
            product_name = None
            product_price = None
            found = False
        

        # Ручной вызов raise Http404 с сообщением
        request_id = request.query_params.get('request_id')
        if request_id:
            # Пример: проверка существования объекта
            from suppliers.models import SupplierProductRequest
            request_obj = SupplierProductRequest.objects.filter(pk=request_id).first()
            
            if request_obj is None:
                raise Http404(f'Заявка с ID {request_id} не найдена')
            
            request_data = {
                'id': request_obj.id,
                'name': request_obj.name,
                'status': request_obj.status
            }
        else:
            request_data = None
        
        return Response({
            # get_object_or_404 пример
            'product_found': found,
            'product_name': product_name,
            'product_price': product_price,
            # Ручной raise Http404 пример
            'request_data': request_data,
            'http404_example': 'Если объект не найден - вызывается Http404',
        })


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    
    def get_queryset(self):
        """
        Получение изображений с использованием select_related для оптимизации.
        Вместо 2 запросов (изображения + товары) выполняется 1 запрос с JOIN.
        """
        return super().get_queryset().select_related('product')
    
    # ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ return redirect
    
    @action(detail=False, methods=['get'])
    def redirect_to_first_product(self, request):
        first_product = Product.objects.first()
        if first_product:
            # Редирект на страницу первого товара, reverse() строит URL по имени маршрута, чтобы не писать адрес вручную строкой
            from django.urls import reverse
            return redirect(reverse('product-detail', kwargs={'pk': first_product.pk}))
        else:
            # Редирект на список товаров, если обращение к несуществующему объекту
            from django.urls import reverse
            return redirect(reverse('product-list'))
    
    @action(detail=False, methods=['get'])
    def redirect_after_delete(self, request):
        """
        Демонстрация редиректа после удаления объекта.
        
        В реальном приложении удаление выполняется через DELETE запрос,
        после чего делается redirect на список объектов.
        """
        from django.urls import reverse
        # Пример: после "удаления" перенаправляем на список товаров
        return redirect(reverse('product-list'))
    
    @action(detail=True, methods=['get'])
    def redirect_not_found(self, request, pk=None):
        """
        Демонстрация редиректа при обращении к несуществующему объекту.
        """
        try:
            product = self.get_object()
            return Response({'name': product.name, 'price': str(product.price)})
        except Http404:
            # Редирект на список товаров при 404
            from django.urls import reverse
            return redirect(reverse('product-list'))


class SliderImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления слайдами слайдера на главной странице.
    
    Отдельный endpoint для слайдов - слайды заполняются и редактируются
    отдельно от товаров. Каждый слайд может быть привязан к товару.
    """
    queryset = SliderImage.objects.all()
    serializer_class = SliderImageSerializer
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
    """
    ViewSet для управления группами фильтров.
    
    Позволяет создавать, редактировать и удалять группы фильтров
    (например: "Цвет", "Размер") для конкретных категорий.
    """
    queryset = FilterGroup.objects.all()
    serializer_class = FilterGroupSerializer
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
    """
    ViewSet для управления значениями фильтров.
    
    Позволяет создавать, редактировать и удалять значения фильтров
    (например: "Красный", "Синий" для группы "Цвет").
    """
    queryset = FilterOption.objects.all()
    serializer_class = FilterOptionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group', 'is_active']
    search_fields = ['name']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']
    
    def get_queryset(self):
        """Получение значений фильтров с предзагрузкой группы."""
        return super().get_queryset().select_related('group')


class ProductFilterViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления связями товаров и фильтров.
    
    Позволяет назначать фильтры товарам.
    """
    queryset = ProductFilter.objects.all()
    serializer_class = ProductFilterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'filter_option']
    
    def get_queryset(self):
        """Получение связей с предзагрузкой данных."""
        return super().get_queryset().select_related('product', 'filter_option__group')
