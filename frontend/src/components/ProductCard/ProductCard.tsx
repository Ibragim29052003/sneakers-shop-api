import type { Slide } from "@/redux/slider/types";
import styles from "./ProductCard.module.scss";
import type { FC, MouseEvent } from "react";
import { Link } from "react-router-dom";
import Price from "../Price/Price";
import Basket from "@/shared/assets/icons/header/basket.svg?react";
import { useAppDispatch } from "@/redux/store";
import { addToCart } from "@/redux/cart/slice";

interface ProductCardProps {
  product: Omit<Slide, "description" | "link">; // берем все поля кроме описания и ссылки (она будет на детальной странице)
}

const ProductCard: FC<ProductCardProps> = ({ product }) => {
  const dispatch = useAppDispatch();

  const handleAddToCart = (e: MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    e.stopPropagation();

    dispatch(
      addToCart({
        id: Number(product.id),
        title: product.title,
        imageUrl: product.imageUrl,
        price: product.newPrice,
        oldPrice: product.oldPrice,
      })
    );
  };

  return (
    <article className={styles.card} role="article">
      <button
        className={styles.card__cart}
        onClick={handleAddToCart}
        aria-label={`Добавить ${product.title} в корзину`}
        type="button"
      >
        <Basket className={styles.card__cart_icon} />
      </button>
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
          {/* Бейдж "От поставщика" - показывается если есть supplierName */}
          {(product.supplierId || product.supplierName) && (
            <span className={`${styles.card__badge} ${styles.card__badge_supplier}`}>
              От поставщика
            </span>
          )}
        </div>
        <div className={styles.card__content}>
          <h3 className={styles.card__title}>{product.title}</h3>
          <Price oldPrice={product.oldPrice} newPrice={product.newPrice} />
        </div>
      </Link>
    </article>
  );
};

export default ProductCard;
