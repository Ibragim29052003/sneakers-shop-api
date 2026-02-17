import type { Slide } from "@/redux/slider/types";
import styles from "./ProductCard.module.scss";
import type { FC } from "react";
import { Link } from "react-router-dom";
import Price from "../Price/Price";

interface ProductCardProps {
  product: Omit<Slide, "description" | "link">; // берем все поля кроме описания и ссылки (она будет на детальной странице)
}

const ProductCard: FC<ProductCardProps> = ({ product }) => {
  return (
    <article className={styles.card} role="article">
      <Link
        to={`/product/${product.id}`}
        className={styles.card__link}
        aria-label={`Перейти к товару: ${product.title}`}
      >
        <div className={styles.card__imageContainer}>
          <img
            src={product.imageUrl}
            alt={product.title}
            className={styles.card__image}
            loading="lazy"
          />
        </div>
        <div className={styles.card__content}>
          <h3 className={styles.card__title}>{product.title}</h3>
          <Price oldPrice={product.oldPrice} newPrice={product.newPrice}/>
        </div>
      </Link>
    </article>
  );
};

export default ProductCard;
