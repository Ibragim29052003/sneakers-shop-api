import type { Slide } from "@/redux/slider/types";
import styles from "./ProductGrid.module.scss";
import ProductCard from "@/components/ProductCard/ProductCard";
import { forwardRef, memo, type FC, type Ref } from "react";
import ProductCardSkeleton from "@/components/ProductCardSkeleton/ProductCardSkeleton";

interface ProductGridProps {
  extraClassName?: string;
  visibleProducts: Omit<Slide, "description" | "link">[];
  isFilterVisible: boolean;
  loading: boolean;
}

const ProductGrid: FC<ProductGridProps & { ref?: Ref<HTMLUListElement> }> =
  forwardRef(
    ({ extraClassName, visibleProducts, isFilterVisible, loading }, ref) => {
      const SKELETONARRAY = [...Array(12)];

      return (
        <ul
          className={`${styles.productGrid__grid} ${extraClassName || ""} ${
            !isFilterVisible ? styles.productGrid__grid_filterInvisible : ""
          }`}
          ref={ref}
          aria-busy={loading}
          aria-label="Список товаров"
        >
          {loading
            ? SKELETONARRAY.map((_, i) => (
                <li
                  key={i}
                  className={styles.productGrid__item}
                  aria-hidden="true"
                >
                  <ProductCardSkeleton />
                </li>
              ))
            : visibleProducts.map((product) => (
                <li key={product.id} className={styles.productGrid__item}>
                  <ProductCard product={product} />
                </li>
              ))}
        </ul>
      );
    }
  );

export default memo(ProductGrid);
