import { type FC } from "react";
import { Link } from "react-router-dom";

import Price from "@/components/Price/Price";
import type {
  HomeShowcaseBlock,
  ShowcaseProduct,
} from "@/services/api/productsApi";

import styles from "./HomeShowcases.module.scss";

interface HomeShowcasesProps {
  premium?: HomeShowcaseBlock;
  bestsellers?: HomeShowcaseBlock;
}

const getProductImage = (product: ShowcaseProduct) =>
  product.main_image_url || product.images[0]?.image || "";

const getProductOldPrice = (product: ShowcaseProduct) =>
  product.old_price ? parseFloat(product.old_price) : undefined;

const getProductPrice = (product: ShowcaseProduct) => parseFloat(product.price);

const getDiscountPercent = (product: ShowcaseProduct) => {
  if (!product.old_price) return null;

  const oldPrice = parseFloat(product.old_price);
  const currentPrice = parseFloat(product.price);

  if (!oldPrice || oldPrice <= currentPrice) return null;

  return Math.round(((oldPrice - currentPrice) / oldPrice) * 100);
};

const formatSoldLabel = (soldQuantity: number) => {
  if (soldQuantity % 10 === 1 && soldQuantity % 100 !== 11) {
    return `${soldQuantity} заказ`;
  }

  if (
    soldQuantity % 10 >= 2 &&
    soldQuantity % 10 <= 4 &&
    (soldQuantity % 100 < 12 || soldQuantity % 100 > 14)
  ) {
    return `${soldQuantity} заказа`;
  }

  return `${soldQuantity} заказов`;
};

const HomeShowcases: FC<HomeShowcasesProps> = ({ premium, bestsellers }) => {
  const premiumItems = premium?.items ?? [];
  const bestsellerItems = bestsellers?.items ?? [];

  if (premiumItems.length === 0 && bestsellerItems.length === 0) {
    return null;
  }

  const premiumLead = premiumItems[0];
  const premiumSecondary = premiumItems.slice(1, 4);

  return (
    <section className={styles.showcases} aria-label="Промо-подборки">
      {premiumLead && premium && (
        <article className={`${styles.showcases__block} ${styles.showcases__block_premium}`}>
          <div className={styles.showcases__header}>
            <span className={styles.showcases__eyebrow}>Selected</span>
            <div className={styles.showcases__headerText}>
              <h2 className={styles.showcases__title}>{premium.title}</h2>
              <p className={styles.showcases__description}>{premium.description}</p>
            </div>
          </div>

          <div className={styles.showcases__premiumLayout}>
            <Link
              to={`/product/${premiumLead.id}`}
              className={styles.showcases__leadCard}
              aria-label={`Открыть товар ${premiumLead.name}`}
            >
              <div className={styles.showcases__leadImageWrap}>
                <img
                  className={styles.showcases__leadImage}
                  src={getProductImage(premiumLead)}
                  alt={premiumLead.name}
                  loading="lazy"
                />
                <span className={styles.showcases__leadBadge}>Premium pick</span>
              </div>

              <div className={styles.showcases__leadContent}>
                <h3 className={styles.showcases__leadTitle}>{premiumLead.name}</h3>
                <p className={styles.showcases__leadText}>
                  Сильный акцент для главной витрины с более высокой ценовой категорией.
                </p>
                <div className={styles.showcases__leadFooter}>
                  <Price
                    newPrice={getProductPrice(premiumLead)}
                    oldPrice={getProductOldPrice(premiumLead)}
                  />
                  <span className={styles.showcases__cta}>Смотреть товар</span>
                </div>
              </div>
            </Link>

            <div className={styles.showcases__miniList}>
              {premiumSecondary.map((product) => {
                const discount = getDiscountPercent(product);

                return (
                  <Link
                    key={product.id}
                    to={`/product/${product.id}`}
                    className={styles.showcases__miniCard}
                    aria-label={`Открыть товар ${product.name}`}
                  >
                    <img
                      className={styles.showcases__miniImage}
                      src={getProductImage(product)}
                      alt={product.name}
                      loading="lazy"
                    />
                    <div className={styles.showcases__miniContent}>
                      <div className={styles.showcases__miniMeta}>
                        <span className={styles.showcases__miniLabel}>Premium</span>
                        {discount && (
                          <span className={styles.showcases__miniDiscount}>
                            -{discount}%
                          </span>
                        )}
                      </div>
                      <h3 className={styles.showcases__miniTitle}>{product.name}</h3>
                      <Price
                        newPrice={getProductPrice(product)}
                        oldPrice={getProductOldPrice(product)}
                      />
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        </article>
      )}

      {bestsellerItems.length > 0 && bestsellers && (
        <article className={`${styles.showcases__block} ${styles.showcases__block_bestsellers}`}>
          <div className={styles.showcases__header}>
            <span className={styles.showcases__eyebrow}>Trending</span>
            <div className={styles.showcases__headerText}>
              <h2 className={styles.showcases__title}>{bestsellers.title}</h2>
              <p className={styles.showcases__description}>{bestsellers.description}</p>
            </div>
          </div>

          <div className={styles.showcases__rankGrid}>
            {bestsellerItems.map((product, index) => (
              <Link
                key={product.id}
                to={`/product/${product.id}`}
                className={styles.showcases__rankCard}
                aria-label={`Открыть товар ${product.name}`}
              >
                <span className={styles.showcases__rankIndex}>0{index + 1}</span>
                <div className={styles.showcases__rankImageWrap}>
                  <img
                    className={styles.showcases__rankImage}
                    src={getProductImage(product)}
                    alt={product.name}
                    loading="lazy"
                  />
                </div>
                <div className={styles.showcases__rankContent}>
                  <div className={styles.showcases__rankMeta}>
                    <span className={styles.showcases__rankLabel}>
                      {bestsellers.based_on_sales ? "Продажи" : "Новинка"}
                    </span>
                    {product.sold_quantity > 0 && (
                      <span className={styles.showcases__rankSold}>
                        {formatSoldLabel(product.sold_quantity)}
                      </span>
                    )}
                  </div>
                  <h3 className={styles.showcases__rankTitle}>{product.name}</h3>
                  <Price
                    newPrice={getProductPrice(product)}
                    oldPrice={getProductOldPrice(product)}
                  />
                </div>
              </Link>
            ))}
          </div>
        </article>
      )}
    </section>
  );
};

export default HomeShowcases;
