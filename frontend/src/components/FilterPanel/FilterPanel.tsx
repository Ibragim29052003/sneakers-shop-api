import { useAppDispatch, useAppSelector } from "@/redux/store";
import styles from "./FilterPanel.module.scss";
import { selectFilters } from "@/redux/filter/selectors";
import { updateFilters, clearFilters } from "@/redux/filter/slice";
import FilterCheckboxGroup from "./FilterCheckboxGroup/FilterCheckboxGroup";
import PriceRange from "../PriceRange/PriceRange";
import useDebounce from "@/hooks/useDebounce";
import { useGetFiltersByCategoryQuery, type FilterGroup } from "@/services/api/productsApi";

// category определяет, какие именно фильтры будут показаны
interface FilterPanelProps {
  category: "women" | "men" | "children";
  onApply?: () => void;
}

const FilterPanel = ({ category, onApply }: FilterPanelProps) => {
  const dispatch = useAppDispatch();

  // получаем данные из редакса
  const filters = useAppSelector(selectFilters);
  const debouncedFilters = useDebounce(filters, 300);

  // Получаем фильтры с бэкенда для данной категории
  const { data: filterGroups, isLoading, error } = useGetFiltersByCategoryQuery(category);

  // Диапазон цен - можно получить с бэкенда позже
  const priceRange = { min: 0, max: 30000 };

  // универсальная функция обновления фильтра
  const updateFilter = (
    key: keyof typeof filters,
    value: string[] | number | boolean | undefined
  ) => {
    dispatch(updateFilters({ [key]: value }));
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

        {/* Отображаем фильтры с бэкенда, только если они есть */}
        {filterGroups && filterGroups.length > 0 ? (
          filterGroups.map((group: FilterGroup) => (
            group.options && group.options.length > 0 && (
              <FilterCheckboxGroup
                key={group.id}
                legend={group.name}
                options={group.options.map(opt => opt.name)}
                selected={filters[group.name as keyof typeof filters] as string[] | undefined}
                onChange={(values) => updateFilter(group.name as keyof typeof filters, values)}
              />
            )
          ))
        ) : (
          /* Если фильтры не настроены в админке - показываем пустую панель */
          !isLoading && <p style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            Фильтры пока не настроены. Добавьте их в админке.
          </p>
        )}

        <div className={styles.filterPanel__buttons}>
          <button
            className={styles.filterPanel__clear}
            onClick={() => dispatch(clearFilters())}
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
