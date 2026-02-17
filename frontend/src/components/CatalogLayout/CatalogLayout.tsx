import { useState, type FC } from "react";
import styles from "./CatalogLayout.module.scss";
import ProductGridStyles from "@/components/ProductList/ProductGrid/ProductGrid.module.scss";
import FilterPanel from "@/components/FilterPanel/FilterPanel";
import ProductList from "@/components/ProductList/ProductList";
import SortPanel from "@/components/SortPanel/SortPanel";
import type { Slide } from "@/redux/slider/types";
import useMediaQuery from "@/hooks/useMediaQuery";
import useLockBodyScroll from "@/hooks/useLockBodyScroll";
import Arrow from "@/shared/assets/icons/header/arrow-down.svg?react";

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
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [isFilterVisible, setIsFilterVisible] = useState(true);
  const isMobile = useMediaQuery("(max-width: 767.98px)");

  useLockBodyScroll(mobileFiltersOpen);

  return (
    <div
      className={styles.catalog}
      role="region"
      aria-label={`${category} catalog`}
    >
      {isMobile && (
        <div className={styles.catalog__mobileBar}>
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

          {!isMobile && isFilterVisible && <FilterPanel category={category} />}
        </div>

        <div className={styles.catalog__content}>
          {!isMobile && (
            <div className={`${!isFilterVisible ? styles.catalog__top : styles.catalog__top_visible}`}>
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
          <ProductList
            products={products}
            loading={loading}
            extraClassName={!isFilterVisible ? ProductGridStyles.productGrid__wide : ""}
            totalProducts={products.length}
            isFilterVisible={isFilterVisible}
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
