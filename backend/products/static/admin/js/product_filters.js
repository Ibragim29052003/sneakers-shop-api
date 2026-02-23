/**
 * Динамическая загрузка фильтров для админки товаров
 * Загружает фильтры на основе выбранной категории
 */

(function($) {
    'use strict';
    
    // Ждем готовности Django админки
    $(document).ready(function() {
        
        // Получаем элемент выбора категории
        var categorySelect = $('#id_categories');
        
        // Получаем контейнер для инлайн фильтров
        var filterInline = $('.inline-related[data-inline-model="productfilter"]');
        
        // Если категория уже выбрана (редактирование существующего товара)
        var initialCategories = categorySelect.val();
        if (initialCategories && initialCategories.length > 0) {
            updateFiltersForCategories(initialCategories);
        }
        
        // Слушаем изменения категории
        categorySelect.on('change', function() {
            var selectedCategories = $(this).val() || [];
            updateFiltersForCategories(selectedCategories);
        });
        
        /**
         * Обновить опции фильтров на основе выбранных категорий
         */
        function updateFiltersForCategories(categoryIds) {
            if (!categoryIds || categoryIds.length === 0) {
                // Очистить опции фильтров если категория не выбрана
                clearFilterOptions();
                return;
            }
            
            // Показать индикатор загрузки
            showLoading();
            
            // Загрузить фильтры для выбранных категорий через AJAX
            $.ajax({
                url: '/api/v1/filter-groups/by_category/',
                data: {
                    category_id: categoryIds[0] // Используем первую выбранную категорию
                },
                success: function(data) {
                    updateFilterOptions(data);
                },
                error: function() {
                    hideLoading();
                }
            });
        }
        
        /**
         * Обновить выпадающие списки опций фильтров в инлайне
         */
        function updateFilterOptions(filterGroups) {
            // Находим все элементы select для filter_option в инлайне
            var filterSelects = filterInline.find('select[name$="-filter_option"]');
            
            filterSelects.each(function() {
                var select = $(this);
                var currentValue = select.val();
                
                // Очищаем существующие опции
                select.empty();
                
                // Добавляем новые опции на основе групп фильтров
                if (filterGroups && filterGroups.length > 0) {
                    filterGroups.forEach(function(group) {
                        if (group.options && group.options.length > 0) {
                            // Создаем optgroup для каждой группы фильтров
                            var optgroup = $('<optgroup>');
                            optgroup.attr('label', group.name);
                            
                            group.options.forEach(function(option) {
                                var optionEl = $('<option>');
                                optionEl.val(option.id);
                                optionEl.text(option.name);
                                optgroup.append(optionEl);
                            });
                            
                            select.append(optgroup);
                        }
                    });
                }
                
                // Восстанавливаем выбранное значение если оно все еще существует
                if (currentValue) {
                    select.val(currentValue);
                }
            });
            
            hideLoading();
            
            // Показать/скрыть весь инлайн фильтров на основе выбора категории
            if (filterGroups && filterGroups.length > 0) {
                filterInline.show();
            } else {
                filterInline.hide();
            }
        }
        
        /**
         * Очистить все опции фильтров
         */
        function clearFilterOptions() {
            var filterSelects = filterInline.find('select[name$="-filter_option"]');
            filterSelects.each(function() {
                var select = $(this);
                select.empty();
                select.append($('<option>', {
                    value: '',
                    text: '---------'
                }));
            });
            filterInline.hide();
        }
        
        /**
         * Показать индикатор загрузки
         */
        function showLoading() {
            var addButton = filterInline.find('.add-row a');
            if (addButton.length) {
                addButton.after('<span class="loading-indicator"> Загрузка фильтров...</span>');
            }
        }
        
        /**
         * Скрыть индикатор загрузки
         */
        function hideLoading() {
            filterInline.find('.loading-indicator').remove();
        }
        
    });
    
})(django.jQuery);
