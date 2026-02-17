import type { Slide } from "@/redux/slider/types";
import styles from "./ProductList.module.scss";
import { useRef, useEffect, type FC } from "react";
import Spiner from "../Spiner/Spiner";
import Pagination from "../Pagination/Pagination";
import { useAppDispatch, useAppSelector } from "@/redux/store";
import ProductGrid from "./ProductGrid/ProductGrid";
import {
  selectCurrentPage,
  selectItemsPerPage,
} from "@/redux/pagination/selectors";
import { setCurrentPage } from "@/redux/pagination/slice";

interface ProductListProps {
  products: Omit<Slide, "description" | "link">[]; // берем все поля кроме описания и ссылки (она будет на детальной странице)
  loading: boolean; // флаг загрузки
  extraClassName?: string; // дополнительный класс
  totalProducts: number;
  isFilterVisible: boolean;
}

const ProductList: FC<ProductListProps> = ({
  products,
  loading,
  extraClassName,
  totalProducts,
  isFilterVisible,
}) => {
  const dispatch = useAppDispatch();
  const currentPage = useAppSelector(selectCurrentPage);
  const itemsPerPage = useAppSelector(selectItemsPerPage);

  // const ITEMS_PER_RAGE = 12; // количество товаров на странице (заглавными буквами - потому что не должно меняться)
  const totalPages = Math.ceil(totalProducts / itemsPerPage);
  const showPagination = totalPages > 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const visibleProducts = products.slice(startIndex, startIndex + itemsPerPage);

  const cardsRef = useRef<HTMLUListElement>(null);

  const handlePageChange = (page: number) => {
    if (page === currentPage) return;
    dispatch(setCurrentPage(page));
  };

  // скролл после обновления контента
  useEffect(() => {
    if (currentPage > 0 && visibleProducts.length > 0) {
      cardsRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }, [currentPage, visibleProducts.length]);

  if (loading) {
    return (
      <div
        className={styles.productList__loading}
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        <div aria-hidden="true">
          <Spiner />
        </div>
        <p className={styles.productList__loading_text}>Загрузка товаров...</p>
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div
        className={styles.productList__empty}
        role="region"
        aria-live="polite"
      >
        <p className={styles.productList__empty_title}>Товары не найдены</p>
        <p className={styles.productList__empty_text}>
          Попробуйте изменить фильтры
        </p>
      </div>
    );
  }

  return (
    <div
      className={styles.productList}
      role="region"
      aria-label="Список товаров"
      >
      <ProductGrid
        extraClassName={extraClassName}
        ref={cardsRef}
        visibleProducts={visibleProducts}
        isFilterVisible={isFilterVisible}
        loading={loading}
      />

      {showPagination && (
        <Pagination
          currentPage={currentPage}
          totalPage={totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
};

export default ProductList;
