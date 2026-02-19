import { useAppDispatch, useAppSelector } from "@/redux/store";
import styles from "./FilterPanel.module.scss";
import { selectFilters } from "@/redux/filter/selectors";
import { updateFilters, clearFilters } from "@/redux/filter/slice";
import FilterCheckboxGroup from "./FilterCheckboxGroup/FilterCheckboxGroup";
import PriceRange from "../PriceRange/PriceRange";
import useDebounce from "@/hooks/useDebounce";
import { 
  useGetFiltersWithCountsQuery, 
  type FilterGroupWithCounts,
  type FilterGroupCountsParams 
} from "@/services/api/productsApi";

// category определяет, какие именно фильтры будут показаны
interface FilterPanelProps {
  category: "women" | "men" | "children";
  onApply?: () => void;
}

// Маппинг названий групп фильтров на ключи Redux
const FILTER_KEY_MAP: Record<string, 'colors' | 'sizes' | 'fabrics'> = {
  'цвета': 'colors',
  'colors': 'colors',
  'размеры': 'sizes',
  'sizes': 'sizes',
  'материалы': 'fabrics',
  'fabrics': 'fabrics',
  'материал': 'fabrics',
};

// Получение ключа Redux по названию группы
const getFilterKey = (groupName: string): 'colors' | 'sizes' | 'fabrics' | null => {
  const normalizedName = groupName.toLowerCase().trim();
  return FILTER_KEY_MAP[normalizedName] || null;
};

const FilterPanel = ({ category, onApply }: FilterPanelProps) => {
  const dispatch = useAppDispatch();

  // получаем данные из редакса
  const filters = useAppSelector(selectFilters);
  const debouncedFilters = useDebounce(filters, 300);

  // Подготавливаем параметры для запроса счетчиков
  const filterParams: FilterGroupCountsParams = {
    category,
    filters: {
      colors: filters.colors?.length ? filters.colors : undefined,
      sizes: filters.sizes?.length ? filters.sizes : undefined,
      fabrics: filters.fabrics?.length ? filters.fabrics : undefined,
    },
    minPrice: filters.minPrice,
    maxPrice: filters.maxPrice,
  };

  // Получаем фильтры с счетчиками с бэкенда для данной категории
  // Запрос автоматически обновляется при изменении filters
  const { 
    data: filterGroups, 
    isLoading, 
    error 
  } = useGetFiltersWithCountsQuery(filterParams);

  // Диапазон цен - можно получить с бэкенда позже
  const priceRange = { min: 0, max: 30000 };

  // универсальная функция обновления фильтра
  const updateFilter = (
    key: keyof typeof filters,
    value: string[] | number | boolean | undefined
  ) => {
    dispatch(updateFilters({ [key]: value }));
    // Вызываем onApply если передан (для обновления товаров)
    onApply?.();
  };

  return (
    <div className={styles.filterPanel} aria-labelledby="filters-title">
      <h2 className={styles.filterPanel__title} id="filters-title">
        Фильтры
      </h2>

      <div className={styles.filterPanel__info}>
        <PriceRange
          min={priceRange?.min ?? 0}
          max={priceRange?.max ?? 30000}
        />

        {/* Загрузка фильтров */}
        {isLoading && <p>Загрузка фильтров...</p>}

        {/* Ошибка при загрузке фильтров */}
        {error && <p>Не удалось загрузить фильтры</p>}

        {/* Отображаем фильтры с счетчиками с бэкенда */}
        {filterGroups && filterGroups.length > 0 ? (
          filterGroups.map((group: FilterGroupWithCounts) => {
            // Получаем ключ Redux для этой группы фильтров
            const filterKey = getFilterKey(group.name);
            if (!filterKey) return null;
            
            return (
              group.options && group.options.length > 0 && (
                <FilterCheckboxGroup
                  key={group.id}
                  legend={group.name}
                  options={group.options.map(opt => opt.name)}
                  selected={filters[filterKey]}
                  onChange={(values) => updateFilter(filterKey, values)}
                  counts={group.options.reduce((acc, opt) => {
                    acc[opt.name.toLowerCase()] = opt.count;
                    return acc;
                  }, {} as Record<string, number>)}
                />
              )
            );
          })
        ) : (
          /* Если фильтры не настроены в админке - показываем пустую панель */
          !isLoading && <p style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            Фильтры пока не настроены. Добавьте их в админке.
          </p>
        )}

        <div className={styles.filterPanel__buttons}>
          <button
            className={styles.filterPanel__clear}
            onClick={() => {
              dispatch(clearFilters());
              onApply?.();
            }}
            type="button"
          >
            Очистить фильтры
          </button>
          <button
            className={styles.filterPanel__apply}
            onClick={() => onApply?.()}
            type="button"
          >
            Применить фильтры
          </button>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;
