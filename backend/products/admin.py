"""
настройка админки для приложения товаров

Демонстрация:
- models.ImageField (в модели ProductImage)
- models.FileField (в других приложениях)
- Генерация PDF документа в админке
- Действия на сайте администрирования (admin actions)
"""
from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.urls import reverse
from .models import Category, Product, ProductCategory, ProductImage, SliderImage, FilterGroup, FilterOption, ProductFilter
from simple_history.admin import SimpleHistoryAdmin
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


class ProductCategoryInline(admin.TabularInline):
    """
    Inline для отображения связей товар-категория.
    Позволяет выбрать категорию (women/men/children) при создании товара.
    """
    model = ProductCategory
    extra = 1
    # Используем обычный select для удобства выбора


class ProductFilterInline(admin.TabularInline):
    """
    Inline для отображения связей товар-фильтры.
    Позволяет выбирать фильтры при создании товара.
    
    При редактировании существующего товара фильтры автоматически
    фильтруются по выбранным категориям товара.
    """
    model = ProductFilter
    extra = 1
    # Используем обычный select вместо raw_id_fields для удобства выбора
    
    def get_formset(self, request, obj=None, **kwargs):
        """
        Динамически фильтруем options на основе выбранной категории.
        """
        from django import forms
        
        class ProductFilterFormSet(forms.ModelForm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                
                # Для существующего объекта фильтруем по категориям
                if obj and obj.pk:
                    category_ids = list(obj.categories.values_list('id', flat=True))
                    if category_ids:
                        # Фильтруем опции по категориям товара
                        self.fields['filter_option'].queryset = FilterOption.objects.filter(
                            group__is_active=True,
                            group__category__in=category_ids,
                            is_active=True
                        ).select_related('group').order_by('group__name', 'name')
                        return
                
                # Для нового объекта показываем все активные фильтры
                # (пользователь сначала выберет категорию, затем пересохранит)
                self.fields['filter_option'].queryset = FilterOption.objects.filter(
                    group__is_active=True,
                    is_active=True
                ).select_related('group').order_by('group__name', 'name')
            
            class Meta:
                model = ProductFilter
                fields = ['filter_option']
        
        return super().get_formset(request, obj, **kwargs)


class ProductImageInline(admin.TabularInline):
    """
    Inline для отображения изображений товара.
    Позволяет добавить фото при создании товара.
    """
    model = ProductImage
    extra = 0
    readonly_fields = ('created_at', 'image_preview')
    
    @display(description='превью')
    def image_preview(self, obj):
        # отображение превью изображения
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 80px; height: auto;" />',
                obj.image.url
            )
        return ''



@admin.register(Category)
class CategoryAdmin(SimpleHistoryAdmin):
    # настройка админки для модели категории
    list_display = ('name', 'parent', 'is_active', 'created_at')
    list_filter = ('parent', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ('parent',)
    list_display_links = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'parent', 'is_active')
        }),
        (_('даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin):
    # настройка админки для модели товара
    list_display = ('name', 'sku', 'get_price_display', 'get_old_price_display', 'get_is_active_status', 'created_at', 'get_category_list')
    list_filter = ('is_active', 'product_categories__category', 'created_at', 'price')
    search_fields = ('name', 'description', 'sku')
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ()
    list_display_links = ('name', 'sku')
    
    inlines = (ProductImageInline, ProductCategoryInline, ProductFilterInline)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'sku', 'price', 'old_price', 'is_active')
        }),
        (_('Категории'), {
            'fields': (),
            'description': 'Выберите категорию в разделе "Связи товаров и категорий" ниже. После выбора категории появятся фильтры.'
        }),
        (_('даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    class Media:
        js = ('admin/js/product_filters.js',)
    
    # =========================================================================
    # ПРИМЕРЫ АДМИНСКИХ ДЕЙСТВИЙ (ADMIN ACTIONS)
    # =========================================================================
    
    def archive_products(self, request, queryset):
        """
        Действие: архивирование выбранных товаров.
        
        ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ADMIN ACTIONS:
        1. Массовое удаление объектов
        2. Массовое изменение статуса
        3. Экспорт данных
        4. Отправка email уведомлений
        5. Генерация отчётов
        """
        updated = queryset.update(status='archived', is_active=False)
        self.message_user(request, f'{updated} товаров архивировано.')
    archive_products.short_description = 'Архивировать выбранные товары'
    
    def activate_products(self, request, queryset):
        """Действие: активация выбранных товаров."""
        updated = queryset.update(status='active', is_active=True)
        self.message_user(request, f'{updated} товаров активировано.')
    activate_products.short_description = 'Активировать выбранные товары'
    
    def mark_as_draft(self, request, queryset):
        """Действие: перевод в черновик."""
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} товаров переведено в черновик.')
    mark_as_draft.short_description = 'Перевести в черновик'
    
    # Регистрация действий
    actions = [archive_products, activate_products, mark_as_draft, 'generate_pdf_report']
    
    # =========================================================================
    # ПРИМЕР ГЕНЕРАЦИИ PDF В АДМИНКЕ
    # =========================================================================
    
    def generate_pdf_report(self, request, queryset):
        """
        Действие: генерация PDF отчёта о выбранных товарах.
        
        ПРИМЕР ГЕНЕРАЦИИ PDF (стр. 488 учебника):
        
        Использование reportlab для создания PDF документов:
        1. Создание документа с помощью SimpleDocTemplate
        2. Добавление таблиц, параграфов, изображений
        3. Стилизация элементов
        4. Возврат HTTP ответа с PDF
        """
        # Создание PDF документа
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="products_report.pdf"'
        
        # Создание документа A4
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        
        # Стили
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
        )
        
        # Заголовок
        elements.append(Paragraph('Отчёт по товарам', title_style))
        elements.append(Spacer(1, 20))
        
        # Данные для таблицы
        data = [['Название', 'Артикул', 'Цена', 'Статус']]
        for product in queryset:
            data.append([
                product.name,
                product.sku,
                f'{product.price} ₽',
                product.get_status_display()
            ])
        
        # Создание таблицы
        table = Table(data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1.2*inch])
        
        # Стилизация таблицы
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Итоговая информация
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f'Всего товаров: {len(queryset)}', styles['Normal']))
        
        # Сборка документа
        doc.build(elements)
        
        return response
    
    generate_pdf_report.short_description = 'Сгенерировать PDF отчёт'
    
    @display(description=_('цена'))
    def get_price_display(self, obj):
        # отображение цены с валютой
        return f'{obj.price} ₽'
    
    @display(description=_('старая цена'))
    def get_old_price_display(self, obj):
        # отображение старой цены с валютой
        if obj.old_price:
            return f'{obj.old_price} ₽'
        return '-'
    
    @display(description=_('активен'))
    def get_is_active_status(self, obj):
        # отображение статуса активности
        if obj.is_active:
            return format_html('<span style="color: green;">{} {}</span>', '✓', 'да')
        return format_html('<span style="color: red;">{} {}</span>', '✗', 'нет')
    
    @display(description=_('категории'))
    def get_category_list(self, obj):
        # отображение списка категорий
        categories = [pc.category.name for pc in obj.product_categories.select_related('category').all()]
        return ', '.join(categories) if categories else '-'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('categories', 'images')


@admin.register(ProductImage)
class ProductImageAdmin(SimpleHistoryAdmin):
    # настройка админки для модели изображений товара
    list_display = ('get_product_name', 'image_preview', 'get_is_main_status', 'created_at')
    list_filter = ('is_main', 'created_at')
    search_fields = ('product__name', 'alt_text')
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ('product',)
    list_display_links = ('get_product_name',)
    
    @display(description=_('товар'))
    def get_product_name(self, obj):
        # отображение названия товара со ссылкой
        from django.urls import reverse
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    
    @display(description=_('основное'))
    def get_is_main_status(self, obj):
        # отображение статуса основного изображения
        if obj.is_main:
            return format_html('<span style="color: green;">{}</span>', '✓')
        return format_html('<span style="color: gray;">{}</span>', '-')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(ProductCategory)
class ProductCategoryAdmin(SimpleHistoryAdmin):
    # настройка админки для модели связей товар-категория
    list_display = ('get_product_name', 'get_category_name', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('product__name', 'category__name')
    list_per_page = 25
    date_hierarchy = 'created_at'
    raw_id_fields = ('product', 'category')
    list_display_links = ('get_product_name', 'get_category_name')
    
    @display(description=_('товар'))
    def get_product_name(self, obj):
        # отображение товара со ссылкой
        from django.urls import reverse
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    
    @display(description=_('категория'))
    def get_category_name(self, obj):
        # отображение категории со ссылкой
        from django.urls import reverse
        url = reverse('admin:products_category_change', args=[obj.category.id])
        return format_html('<a href="{}">{}</a>', url, obj.category.name)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'category')


@admin.register(SliderImage)
class SliderImageAdmin(SimpleHistoryAdmin):
    """
    Настройка админки для модели слайдов слайдера.
    
    Слайды заполняются и редактируются отдельно от товаров.
    Каждый слайд может быть привязан к товару.
    """
    list_display = ('title', 'image_preview', 'get_product_name', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description', 'product__name')
    list_per_page = 25
    date_hierarchy = 'created_at'
    list_display_links = ('title',)
    list_editable = ('is_active', 'order')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'image', 'is_active', 'order')
        }),
        (_('Цена'), {
            'fields': ('price', 'old_price'),
            'description': 'Укажите цену для отображения на слайде. Если привязан товар, цена будет взята из товара.'
        }),
        (_('Связь с товаром'), {
            'fields': ('product', 'link'),
            'classes': ('collapse',)
        }),
        (_('даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    @display(description=_('товар'))
    def get_product_name(self, obj):
        if obj.product:
            from django.urls import reverse
            url = reverse('admin:products_product_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return '-'
    
    @display(description='превью')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 200px; height: auto;" />',
                obj.image.url
            )
        return '-'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(FilterGroup)
class FilterGroupAdmin(SimpleHistoryAdmin):
    """Админ-панель для групп фильтров."""
    list_display = ('name', 'category', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_active', 'order')
    list_display_links = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'is_active', 'order')
        }),
    )


@admin.register(FilterOption)
class FilterOptionAdmin(SimpleHistoryAdmin):
    """Админ-панель для значений фильтров."""
    list_display = ('name', 'group', 'is_active', 'order')
    list_filter = ('group', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_active', 'order')
    list_display_links = ('name',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group')


@admin.register(ProductFilter)
class ProductFilterAdmin(SimpleHistoryAdmin):
    """Админ-панель для связей товаров и фильтров."""
    list_display = ('product', 'filter_option', 'created_at')
    list_filter = ('filter_option__group',)
    search_fields = ('product__name', 'filter_option__name')
    list_display_links = ('product',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'filter_option__group')
