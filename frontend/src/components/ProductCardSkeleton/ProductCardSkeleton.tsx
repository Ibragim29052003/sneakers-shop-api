import Skeleton from "@/components/Skeleton/Skeleton";
import styles from "../ProductCard/ProductCard.module.scss";

const ProductCardSkeleton = () => {
  return (
    <div className={styles.card} aria-hidden="true">
      <div className={styles.card__imageContainer}>
        <Skeleton className={styles.card__imageSkeleton} />
      </div>

      <div className={styles.card__content}>
        <Skeleton className={styles.card__titleSkeleton} />
        <Skeleton className={styles.card__priceSkeleton} />
      </div>
    </div>
  );
};

export default ProductCardSkeleton;
