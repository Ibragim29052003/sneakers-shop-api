/**
 * Dynamic filter loading for product admin
 * Loads filters based on selected category
 */

(function($) {
    'use strict';
    
    // Wait for Django admin to be ready
    $(document).ready(function() {
        
        // Get the category select element
        var categorySelect = $('#id_categories');
        
        // Get the filter inline container
        var filterInline = $('.inline-related[data-inline-model="productfilter"]');
        
        // If category is already selected (editing existing product)
        var initialCategories = categorySelect.val();
        if (initialCategories && initialCategories.length > 0) {
            updateFiltersForCategories(initialCategories);
        }
        
        // Listen for category changes
        categorySelect.on('change', function() {
            var selectedCategories = $(this).val() || [];
            updateFiltersForCategories(selectedCategories);
        });
        
        /**
         * Update filter options based on selected categories
         */
        function updateFiltersForCategories(categoryIds) {
            if (!categoryIds || categoryIds.length === 0) {
                // Clear filter options if no category selected
                clearFilterOptions();
                return;
            }
            
            // Show loading indicator
            showLoading();
            
            // Fetch filters for selected categories via AJAX
            $.ajax({
                url: '/api/v1/filter-groups/by_category/',
                data: {
                    category_id: categoryIds[0] // Use first selected category
                },
                success: function(data) {
                    updateFilterOptions(data);
                },
                error: function() {
                    console.error('Failed to load filters');
                    hideLoading();
                }
            });
        }
        
        /**
         * Update the filter option dropdowns in the inline
         */
        function updateFilterOptions(filterGroups) {
            // Find all filter_option select elements in the inline
            var filterSelects = filterInline.find('select[name$="-filter_option"]');
            
            filterSelects.each(function() {
                var select = $(this);
                var currentValue = select.val();
                
                // Clear existing options
                select.empty();
                
                // Add new options based on filter groups
                if (filterGroups && filterGroups.length > 0) {
                    filterGroups.forEach(function(group) {
                        if (group.options && group.options.length > 0) {
                            // Create optgroup for each filter group
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
                
                // Restore selected value if it still exists
                if (currentValue) {
                    select.val(currentValue);
                }
            });
            
            hideLoading();
            
            // Show/hide the entire filter inline based on category selection
            if (filterGroups && filterGroups.length > 0) {
                filterInline.show();
            } else {
                filterInline.hide();
            }
        }
        
        /**
         * Clear all filter options
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
         * Show loading indicator
         */
        function showLoading() {
            var addButton = filterInline.find('.add-row a');
            if (addButton.length) {
                addButton.after('<span class="loading-indicator"> Загрузка фильтров...</span>');
            }
        }
        
        /**
         * Hide loading indicator
         */
        function hideLoading() {
            filterInline.find('.loading-indicator').remove();
        }
        
    });
    
})(django.jQuery);
