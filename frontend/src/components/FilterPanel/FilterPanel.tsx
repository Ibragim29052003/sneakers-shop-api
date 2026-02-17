import { useAppDispatch, useAppSelector } from "@/redux/store";
import styles from "./FilterPanel.module.scss";
import { selectFilters } from "@/redux/filter/selectors";
import { updateFilters, clearFilters } from "@/redux/filter/slice";
import FilterCheckboxGroup from "./FilterCheckboxGroup/FilterCheckboxGroup";
import PriceRange from "../PriceRange/PriceRange";
import useDebounce from "@/hooks/useDebounce";

// category определяет, какие именно фильтры будут показаны
interface FilterPanelProps {
  category: "women" | "men" | "children";
  onApply?: () => void;
}

// Базовая конфигурация фильтров для Django
const defaultConfig = {
  fabrics: ["Хлопок", "Шерсть", "Шёлк", "Лён", "Синтетика"],
  colors: ["Чёрный", "Белый", "Синий", "Красный", "Зелёный"],
  sizes: ["XS", "S", "M", "L", "XL", "XXL"],
};

const FilterPanel = ({ category, onApply }: FilterPanelProps) => {
  const dispatch = useAppDispatch();

  // получаем данные из редакса
  const filters = useAppSelector(selectFilters);
  const debouncedFilters = useDebounce(filters, 300);

  // Для Django используем статическую конфигурацию
  const config = defaultConfig;

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

        <FilterCheckboxGroup
          legend="Категории товаров"
          options={config.fabrics}
          selected={filters.fabrics}
          onChange={(values) => updateFilter("fabrics", values)}
        />

        <FilterCheckboxGroup
          legend="Цвета"
          options={config.colors}
          selected={filters.colors}
          onChange={(values) => updateFilter("colors", values)}
        />

        <FilterCheckboxGroup
          legend="Размеры"
          options={config.sizes}
          selected={filters.sizes}
          onChange={(values) => updateFilter("sizes", values)}
        />

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
