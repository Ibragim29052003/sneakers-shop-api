"""
Сериализаторы для приложения товаров
"""
from rest_framework import serializers
from django.conf import settings
from .models import Category, Product, ProductCategory, ProductImage, SliderImage, FilterGroup, FilterOption, ProductFilter


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

#333333$$ Получение количества подкатегорий

    def get_subcategories_count(self, obj):
        return obj.subcategories.count()

#@@@ser 5555 (46 - Сериализаторы строят абсолютную ссылку, чтобы фронтенд мог сразу показать изображение)

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
    
    def get_image(self, obj):
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
    
    def get_image_url(self, obj):
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
    images = ProductImageSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()
    supplier_name = serializers.SerializerMethodField()
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
            'id', 'name', 'description', 'price', 'old_price', 'sku', 'status',
            'is_active', 'created_at', 'updated_at', 'categories', 'categories_ids',
            'images', 'main_image_url', 'absolute_url', 'external_url', 'supplier', 'supplier_name',
            'published_pages', 'image_urls'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_media_url(self, relative_url):
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
    
    def get_main_image_url(self, obj):
        """Получение URL главного изображения."""
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return self.get_media_url(main_image.image.url)
        first_image = obj.images.first()
        if first_image:
            return self.get_media_url(first_image.image.url)
        return None

    def get_absolute_url(self, obj): # отдать ссылку на товар 
        return self.get_media_url(obj.get_absolute_url())
    
    def get_supplier_name(self, obj):
        """Получение имени поставщика."""
        if obj.supplier:
            return obj.supplier.name
        return None

    def create(self, validated_data):
        """Создание товара с категориями через through модель."""
        # Получаем категории из validated_data
        category_ids = validated_data.pop('categories_ids', [])
        # Получаем URL изображений
        image_urls = validated_data.pop('image_urls', [])
        
        product = Product.objects.create(**validated_data)
        
        # Создаём связи через промежуточную таблицу
        for cat_id in category_ids:
            try:
                category = Category.objects.get(id=cat_id)
                ProductCategory.objects.create(product=product, category=category)
            except Category.DoesNotExist:
                pass
        
        # Создаём изображения товара
        for index, image_url in enumerate(image_urls):
            # Очищаем URL от двойного кодирования
            import urllib.parse
            
            # Декодируем URL (убираем двойное кодирование типа %2520 -> %20)
            decoded_url = urllib.parse.unquote(image_url)
            
            # Убираем префикс /media/ если есть (Django добавит его сам)
            # и убираем двойные /media/ если есть
            clean_path = decoded_url
            
            # Убираем любые повторения /media/
            while '/media/media/' in clean_path:
                clean_path = clean_path.replace('/media/media/', '/media/', 1)
            
            # Убираем /media/ в начале
            if clean_path.startswith('/media/'):
                clean_path = clean_path[7:]  # убираем /media/
            elif clean_path.startswith('media/'):
                clean_path = clean_path[6:]  # убираем media/
            
            # Убираем начальный слэш если есть
            if clean_path.startswith('/'):
                clean_path = clean_path[1:]
#@@@ser
            # Создаём объект изображения
            ProductImage.objects.create(
                product=product,
                image=clean_path,  # Сохраняем путь без /media/
                is_main=(index == 0),  # Первое изображение - главное
                alt_text=product.name
            )
        
        return product

    def update(self, instance, validated_data):
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
            for cat_id in category_ids:
                try:
                    category = Category.objects.get(id=cat_id)
                    ProductCategory.objects.create(product=instance, category=category)
                except Category.DoesNotExist:
                    pass

        # Полная замена изображений, если передан новый список URL
        if image_urls is not None:
            import urllib.parse

            ProductImage.objects.filter(product=instance).delete()

            for index, image_url in enumerate(image_urls):
                decoded_url = urllib.parse.unquote(image_url)
                clean_path = decoded_url

                while '/media/media/' in clean_path:
                    clean_path = clean_path.replace('/media/media/', '/media/', 1)

                if clean_path.startswith('/media/'):
                    clean_path = clean_path[7:]
                elif clean_path.startswith('media/'):
                    clean_path = clean_path[6:]

                if clean_path.startswith('/'):
                    clean_path = clean_path[1:]

                ProductImage.objects.create(
                    product=instance,
                    image=clean_path,
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
    option_value = serializers.CharField(source='filter_option.value', read_only=True)
    group_name = serializers.CharField(source='filter_option.group.name', read_only=True)
    
    class Meta:
        model = ProductFilter
        fields = ['id', 'product', 'filter_option', 'option_name', 'option_value', 'group_name', 'created_at']
        read_only_fields = ['created_at']


class FilterGroupByCategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения групп фильтров по категории.
    Возвращает структуру, удобную для фронтенда.
    """
    options = FilterOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = FilterGroup
        fields = ['id', 'name', 'options', 'order']
