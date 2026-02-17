import type { FC } from "react";
import styles from "./Pagination.module.scss";
import ArrowPagination from "@/shared/assets/icons/slider/arrow-for-slider.svg?react";

interface PaginationProps {
  currentPage: number;
  totalPage: number;
  onPageChange: (page: number) => void;
}

const Pagination: FC<PaginationProps> = ({
  currentPage,
  totalPage,
  onPageChange,
}) => {
  // const pages = [...Array(totalPage)] // если к примеру totalPage = 5, то будет [undefined, undefined, undefined, undefined, undefined]

  const pageNumbers = Array.from({ length: totalPage }, (_, i) => i + 1);
  return (
    <nav className={styles.pagination} aria-label="Пагинация">
      <ul className={styles.pagination__list}>
        <li className={styles.pagination__item}>
          <button
            className={`${styles.pagination__button} ${styles.pagination__button_left}`}
            type="button"
            aria-label="Предыдущая страница"
            disabled={currentPage <= 1}
            onClick={() => onPageChange(currentPage - 1)}
          >
            <ArrowPagination />
          </button>
        </li>

        {pageNumbers.map((countPage, idCountPage) => (
          <li className={styles.pagination__item} key={idCountPage}>
            <button
              className={styles.pagination__numberPage}
              type="button"
              aria-label={`Страница ${countPage}`}
              aria-current={countPage === currentPage ? "page" : undefined}
              onClick={() => onPageChange(countPage)}
            >
              {countPage}
            </button>
          </li>
        ))}
        <li className={styles.pagination__item}>
          <button
            className={`${styles.pagination__button} ${styles.pagination__button_right}`}
            type="button"
            aria-label="Следующая страница"
            disabled={currentPage >= totalPage}
            onClick={() => onPageChange(currentPage + 1)}
          >
            <ArrowPagination />
          </button>
        </li>
      </ul>
    </nav>
  );
};

export default Pagination;
