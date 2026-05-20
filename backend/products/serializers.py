"""
Сериализаторы для приложения товаров
"""
import urllib.parse
from collections import defaultdict
from decimal import Decimal
from typing import Any

from rest_framework import serializers
from django.conf import settings
from .models import Category, Product, ProductCategory, ProductImage, SliderImage, FilterGroup, FilterOption, ProductFilter, ProductFavorite


def clean_media_path(raw_url: str) -> str:
    """Нормализует путь к медиафайлу перед сохранением в ImageField."""
    clean_path = urllib.parse.unquote(raw_url)

    while '/media/media/' in clean_path:
        clean_path = clean_path.replace('/media/media/', '/media/', 1)

    if clean_path.startswith('/media/'):
        clean_path = clean_path[7:]
    elif clean_path.startswith('media/'):
        clean_path = clean_path[6:]

    if clean_path.startswith('/'):
        clean_path = clean_path[1:]

    return clean_path


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для модели категории."""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    subcategories_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name',
            'is_active', 'created_at', 'updated_at', 'subcategories_count'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_subcategories_count(self, obj: Category) -> int:
        """Возвращает данные через `get_subcategories_count`."""
        return obj.subcategories.count()

class ProductImageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для изображений товара.
    """
    image = serializers.SerializerMethodField()
    image_file = serializers.ImageField(write_only=True, required=False, source='image')
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_file', 'product', 'is_main', 'alt_text', 'created_at']
        read_only_fields = ['created_at']
    
    def get_image(self, obj: ProductImage) -> str | None:
        """Получение полного URL изображения."""
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        base_url = getattr(settings, 'BASE_URL', '')
        if not base_url and hasattr(settings, 'DEBUG') and settings.DEBUG:
            base_url = 'http://localhost:8000'
        return f"{base_url}{obj.image.url}"


class SliderImageSerializer(serializers.ModelSerializer):
    """Сериализатор для модели слайдов."""
    image_url = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = SliderImage
        fields = [
            'id', 'title', 'description', 'image', 'image_url',
            'product', 'product_name', 'product_price', 'price', 'old_price',
            'link', 'is_active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_image_url(self, obj: SliderImage) -> str | None:
        """Получение полного URL изображения."""
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        base_url = getattr(settings, 'BASE_URL', '')
        if not base_url and hasattr(settings, 'DEBUG') and settings.DEBUG:
            base_url = 'http://localhost:8000'
        return f"{base_url}{obj.image.url}"


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для модели товара."""
    DISCOUNT_ALLOWED_CATEGORY_KEYWORDS = (
        'women',
        'men',
        'children',
        'жен',
        'муж',
        'дет',
    )

    images = ProductImageSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()
    supplier_name = serializers.SerializerMethodField()
    filter_attributes = serializers.SerializerMethodField()
    avg_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    sold_quantity = serializers.IntegerField(read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)
    # Поле для создания товара с категориями - поддерживает categories_ids и categories
    categories_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )
    # Поле для создания товара с изображениями - принимает список URL изображений
    # Использует CharField для поддержки относительных URL
    image_urls = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'stock_quantity', 'old_price', 'sku', 'status',
            'is_active', 'created_at', 'updated_at', 'categories', 'categories_ids',
            'images', 'main_image_url', 'absolute_url', 'external_url', 'supplier', 'supplier_name',
            'avg_rating', 'sold_quantity', 'favorites_count', 'published_pages', 'image_urls', 'filter_attributes'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_media_url(self, relative_url: str | None) -> str | None:
        """Построение полного URL для медиафайла."""
        if not relative_url:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(relative_url)
        # Fallback: использовать BASE_URL из настроек или localhost
        base_url = getattr(settings, 'BASE_URL', '')
        if not base_url and hasattr(settings, 'DEBUG') and settings.DEBUG:
            base_url = 'http://localhost:8000'
        return f"{base_url}{relative_url}"
    
    def get_main_image_url(self, obj: Product) -> str | None:
        """Получение URL главного изображения без дополнительных запросов в БД."""
        images = list(obj.images.all())
        main_image = next((image for image in images if image.is_main), None)
        if main_image is None and images:
            main_image = images[0]

        if not main_image or not main_image.image:
            return None

        return self.get_media_url(main_image.image.url)

    def get_absolute_url(self, obj: Product) -> str | None: # отдать ссылку на товар 
        """Возвращает данные через `get_absolute_url`."""
        return self.get_media_url(obj.get_absolute_url())
    
    def get_supplier_name(self, obj: Product) -> str | None:
        """Получение имени поставщика."""
        if obj.supplier:
            return obj.supplier.name
        return None

    def get_filter_attributes(self, obj: Product) -> list[dict[str, Any]]:
        """Возвращает сгруппированные атрибуты товара на основе ProductFilter."""
        grouped_values: dict[str, list[str]] = defaultdict(list)
        product_filters = obj.product_filters.select_related('filter_option__group').all()

        for product_filter in product_filters:
            group_name = product_filter.filter_option.group.name
            option_name = product_filter.filter_option.name
            grouped_values[group_name].append(option_name)

        result: list[dict[str, Any]] = []
        for group_name in sorted(grouped_values.keys()):
            values = sorted(set(grouped_values[group_name]))
            result.append({'group': group_name, 'values': values})
        return result

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Выполняет действие `validate`."""
        price = attrs.get('price', getattr(self.instance, 'price', None))
        old_price = attrs.get('old_price', getattr(self.instance, 'old_price', None))
        stock_quantity = attrs.get('stock_quantity', getattr(self.instance, 'stock_quantity', 0))
        status = attrs.get('status', getattr(self.instance, 'status', 'draft'))
        is_active = attrs.get('is_active', getattr(self.instance, 'is_active', True))

        if price is not None and price <= 0:
            raise serializers.ValidationError({'price': 'Цена должна быть больше 0.'})

        if old_price is not None and price is not None and old_price < price:
            raise serializers.ValidationError({'old_price': 'Старая цена должна быть больше или равна текущей цене.'})

        # Валидация соответствия скидки и категории:
        # скидка применяется только для категорий, где она разрешена бизнес-правилом.
        if old_price is not None and price is not None and old_price > price:
            category_ids = self._get_category_ids_for_validation(attrs)
            if not category_ids:
                raise serializers.ValidationError(
                    {'categories_ids': 'Для товара со скидкой необходимо указать хотя бы одну категорию.'}
                )

            categories = Category.objects.filter(id__in=category_ids)
            has_allowed_category = any(
                any(keyword in category.name.lower() for keyword in self.DISCOUNT_ALLOWED_CATEGORY_KEYWORDS)
                for category in categories
            )
            if not has_allowed_category:
                raise serializers.ValidationError(
                    {'old_price': 'Скидка недоступна для выбранной категории товара.'}
                )

            discount_percent = ((old_price - price) / old_price) * Decimal('100')
            if discount_percent > Decimal('80'):
                raise serializers.ValidationError({'old_price': 'Скидка не может превышать 80%.'})

        if stock_quantity is not None and stock_quantity < 0:
            raise serializers.ValidationError({'stock_quantity': 'Остаток не может быть отрицательным.'})

        if is_active and stock_quantity == 0 and status != 'out_of_stock':
            raise serializers.ValidationError(
                {'status': 'Товар с нулевым остатком может быть активным только со статусом out_of_stock.'}
            )

        return attrs

    def _get_category_ids_for_validation(self, attrs: dict[str, Any]) -> list[int]:
        """Возвращает список category ids для валидации скидок."""
        category_ids = attrs.get('categories_ids')
        if category_ids is not None:
            return list(set(category_ids))

        if self.instance is not None:
            return list(self.instance.categories.values_list('id', flat=True))

        return []

    def validate_categories_ids(self, value: list[int]) -> list[int]:
        """Проверяет, что все переданные категории существуют."""
        unique_ids = set(value)
        existing_count = Category.objects.filter(id__in=unique_ids).count()
        if existing_count != len(unique_ids):
            raise serializers.ValidationError('Одна или несколько категорий не найдены.')
        return value

    def create(self, validated_data: dict[str, Any]) -> Product:
        """Создание товара с категориями через through модель."""
        # Получаем категории из validated_data
        category_ids = validated_data.pop('categories_ids', [])
        # Получаем URL изображений
        image_urls = validated_data.pop('image_urls', [])
        
        product = Product.objects.create(**validated_data)
        
        # Создаём связи через промежуточную таблицу
        categories = Category.objects.filter(id__in=category_ids)
        for category in categories:
            ProductCategory.objects.create(product=product, category=category)
        
        # Создаём изображения товара
        for index, image_url in enumerate(image_urls):
            ProductImage.objects.create(
                product=product,
                image=clean_media_path(image_url),
                is_main=(index == 0),  # Первое изображение - главное
                alt_text=product.name
            )
        
        return product

    def update(self, instance: Product, validated_data: dict[str, Any]) -> Product:
        """Обновление товара с категориями."""
        category_ids = validated_data.pop('categories_ids', None)
        image_urls = validated_data.pop('image_urls', None)
        
        # Обновляем остальные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обновляем категории если они переданы
        if category_ids is not None:
            # Удаляем старые связи
            ProductCategory.objects.filter(product=instance).delete()
            
            # Создаём новые связи
            categories = Category.objects.filter(id__in=category_ids)
            for category in categories:
                ProductCategory.objects.create(product=instance, category=category)

        # Полная замена изображений, если передан новый список URL
        if image_urls is not None:
            ProductImage.objects.filter(product=instance).delete()

            for index, image_url in enumerate(image_urls):
                ProductImage.objects.create(
                    product=instance,
                    image=clean_media_path(image_url),
                    is_main=(index == 0),
                    alt_text=instance.name
                )

        return instance


class ProductShowcaseSerializer(ProductSerializer):
    """Сериализатор товара для витринных блоков на главной странице."""
    sold_quantity = serializers.IntegerField(read_only=True)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['sold_quantity']


class ProductSupplierDemoSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для демонстрации select_related('supplier')."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'supplier', 'supplier_name']


class ProductCategorySerializer(serializers.ModelSerializer):
    """Сериализатор для модели связи товаров и категорий."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ProductCategory
        fields = ['id', 'product', 'product_name', 'category', 'category_name', 'created_at']
        read_only_fields = ['created_at']


class FilterOptionSerializer(serializers.ModelSerializer):
    """Сериализатор для значений фильтров."""
    
    class Meta:
        model = FilterOption
        fields = ['id', 'name', 'is_active', 'order']
        read_only_fields = ['created_at']


class FilterGroupSerializer(serializers.ModelSerializer):
    """Сериализатор для групп фильтров."""
    options = FilterOptionSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = FilterGroup
        fields = ['id', 'name', 'category', 'category_name', 'options', 'is_active', 'order', 'created_at']
        read_only_fields = ['created_at']


class ProductFilterSerializer(serializers.ModelSerializer):
    """Сериализатор для связи товаров и фильтров."""
    option_name = serializers.CharField(source='filter_option.name', read_only=True)
    group_name = serializers.CharField(source='filter_option.group.name', read_only=True)
    
    class Meta:
        model = ProductFilter
        fields = ['id', 'product', 'filter_option', 'option_name', 'group_name', 'created_at']
        read_only_fields = ['created_at']


class ProductFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных товаров пользователя."""

    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True,
    )

    class Meta:
        model = ProductFavorite
        fields = ['id', 'product', 'product_id', 'created_at']
        read_only_fields = ['created_at']

    def validate_product_id(self, product: Product) -> Product:
        """Запрещает добавлять в избранное скрытые или недоступные товары."""
        if not product.is_active or product.status in ['draft', 'archived']:
            raise serializers.ValidationError('Нельзя добавить недоступный товар в избранное.')
        return product

    def create(self, validated_data: dict[str, Any]) -> ProductFavorite:
        """Добавляет товар в избранное или возвращает существующую запись."""
        user = self.context['request'].user
        favorite, _ = ProductFavorite.objects.get_or_create(user=user, **validated_data)
        return favorite


class FilterGroupByCategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения групп фильтров по категории.
    Возвращает структуру, удобную для фронтенда.
    """
    options = FilterOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = FilterGroup
        fields = ['id', 'name', 'options', 'order']
