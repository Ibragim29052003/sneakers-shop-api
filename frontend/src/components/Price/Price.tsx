import type { FC } from "react";
import styles from "./Price.module.scss";

interface PriceProps {
  oldPrice?: number;
  newPrice: number;
  currency?: string;
}

const Price: FC<PriceProps> = ({ oldPrice, newPrice, currency = "₽" }) => {
  return (
    <div className={styles.price}>
      {oldPrice && (
        <span className={styles.price__oldPrice}>
          {oldPrice}
          {currency}
        </span>
      )}
      <span className={styles.price__newPrice}>
        {newPrice}
        {currency}
      </span>
    </div>
  );
};

export default Price;