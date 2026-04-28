import { useDeferredValue, useEffect, useMemo, useState, type FC } from "react";
import styles from "./CatalogLayout.module.scss";
import ProductGridStyles from "@/components/ProductList/ProductGrid/ProductGrid.module.scss";
import FilterPanel from "@/components/FilterPanel/FilterPanel";
import ProductList from "@/components/ProductList/ProductList";
import SortPanel from "@/components/SortPanel/SortPanel";
import type { Slide } from "@/redux/slider/types";
import useMediaQuery from "@/hooks/useMediaQuery";
import useLockBodyScroll from "@/hooks/useLockBodyScroll";
import Arrow from "@/shared/assets/icons/header/arrow-down.svg?react";
import { useAppDispatch, useAppSelector } from "@/redux/store";
import { clearSearchQuery } from "@/redux/catalogSearch/slice";
import { selectCatalogSearchQuery } from "@/redux/catalogSearch/selectors";
import { setCurrentPage } from "@/redux/pagination/slice";
import { selectFilters } from "@/redux/filter/selectors";

type Category = "children" | "women" | "men";

type CatalogLayoutProps = {
  category: Category;
  products: Omit<Slide, "link" | "description">[];
  loading: boolean;
};

const CatalogLayout: FC<CatalogLayoutProps> = ({
  products,
  loading,
  category,
}) => {
  const dispatch = useAppDispatch();
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [isFilterVisible, setIsFilterVisible] = useState(true);
  const isMobile = useMediaQuery("(max-width: 767.98px)");
  const searchQuery = useAppSelector(selectCatalogSearchQuery);
  const filters = useAppSelector(selectFilters);
  const normalizedSearchQuery = searchQuery.trim();
  const deferredSearchQuery = useDeferredValue(
    normalizedSearchQuery.toLowerCase()
  );
  const hasActiveSearch = normalizedSearchQuery.length > 0;

  useLockBodyScroll(mobileFiltersOpen);

  useEffect(() => {
    dispatch(setCurrentPage(1));
  }, [deferredSearchQuery, dispatch]);

  const filteredProducts = products.filter((product) => {
    if (!deferredSearchQuery) return true;

    const searchableText = [product.title, product.supplierName]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    return searchableText.includes(deferredSearchQuery);
  });

  // Фронтовая сортировка для наглядного примера order_by (аналог через sort)
  const sortedProducts = useMemo(() => {
    const productsToSort = [...filteredProducts];

    if (filters.sortBy === "price_asc") {
      productsToSort.sort((a, b) => a.newPrice - b.newPrice);
    } else if (filters.sortBy === "price_desc") {
      productsToSort.sort((a, b) => b.newPrice - a.newPrice);
    }

    return productsToSort;
  }, [filteredProducts, filters.sortBy]);

  const productsCountLabel = hasActiveSearch
    ? `Найдено: ${filteredProducts.length} из ${products.length}`
    : `Всего товаров: ${products.length}`;

  return (
    <div
      className={styles.catalog}
      role="region"
      aria-label={`${category} catalog`}
    >
      {isMobile && (
        <div className={styles.catalog__mobileBar}>
          <div className={styles.catalog__productsCount}>
            {productsCountLabel}
          </div>
          <SortPanel />

          <button
            className={styles.catalog__filterButton}
            onClick={() => setMobileFiltersOpen(true)}
            aria-expanded={mobileFiltersOpen}
            aria-controls="filter-drawer"
          >
            Фильтры
          </button>
        </div>
      )}

      <div
        className={`${styles.catalog__body} ${
          !isFilterVisible ? styles.catalog__body_full : ""
        }`}
      >
        <div className={styles.catalog__sidebar}>
          {isFilterVisible && (
            <button
            className={styles.catalog__toggleButton}
            aria-expanded={isFilterVisible}
            onClick={() => setIsFilterVisible(!isFilterVisible)}
          >
            <Arrow
              className={`${styles.catalog__toggleArrow} ${
                !isFilterVisible ? styles.catalog__toggleArrow_open : ""
              }`}
            />
            Скрыть фильтры
          </button>
          )}

          {!isMobile && isFilterVisible && <FilterPanel category={category} onApply={() => {}} />}
        </div>

        <div className={styles.catalog__content}>
          {!isMobile && (
            <div
              className={`${styles.catalog__top} ${
                !isFilterVisible
                  ? styles.catalog__top_withToggle
                  : styles.catalog__top_visible
              }`}
            >
              <div className={styles.catalog__topInfo}>
                <div className={styles.catalog__productsCount}>
                  {productsCountLabel}
                </div>
              </div>
              {!isFilterVisible && (
                <button
                className={styles.catalog__toggleButton}
                aria-expanded={isFilterVisible}
                onClick={() => setIsFilterVisible(!isFilterVisible)}
              >
                <Arrow
                  className={`${styles.catalog__toggleArrow} ${
                    !isFilterVisible ? styles.catalog__toggleArrow_open : ""
                  }`}
                />
                Показать фильтры
              </button>
              )}
              <SortPanel />
            </div>
          )}
          {hasActiveSearch && (
            <div
              className={styles.catalog__searchSummary}
              role="status"
              aria-live="polite"
            >
              <p className={styles.catalog__searchSummary_text}>
                Найдено {filteredProducts.length} товаров по запросу «
                {normalizedSearchQuery}»
              </p>
              <button
                type="button"
                className={styles.catalog__searchSummary_button}
                onClick={() => dispatch(clearSearchQuery())}
              >
                Очистить поиск
              </button>
            </div>
          )}
          <ProductList
            products={sortedProducts}
            loading={loading}
            extraClassName={!isFilterVisible ? ProductGridStyles.productGrid__wide : ""}
            totalProducts={sortedProducts.length}
            isFilterVisible={isFilterVisible}
            searchQuery={normalizedSearchQuery}
          />
        </div>
      </div>

      <div
        id="filter-drawer"
        className={`${styles.catalog__drawer} ${
          mobileFiltersOpen ? styles.catalog__drawer_open : ""
        }`}
        role="dialog"
        aria-modal="true"
        aria-label="Фильтры"
      >
        <div className={styles.catalog__drawerHeader}>
          <button
            className={styles.catalog__drawerHeader_button}
            onClick={() => setMobileFiltersOpen(false)}
          >
            К каталогу
          </button>
          <button
            onClick={() => setMobileFiltersOpen(false)}
            aria-label="Закрыть фильтры"
            className={styles.catalog__drawerHeader_close}
          >
            <span className={styles.catalog__drawerHeader_line}></span>
            <span className={styles.catalog__drawerHeader_line}></span>
          </button>
        </div>

        {isMobile && (
          <FilterPanel
            category={category}
            onApply={() => setMobileFiltersOpen(false)}
          />
        )}
      </div>
    </div>
  );
};

export default CatalogLayout;
