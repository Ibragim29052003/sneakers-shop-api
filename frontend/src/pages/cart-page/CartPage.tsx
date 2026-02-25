import { type FC, useState } from "react";
import styles from "./CartPage.module.scss";
import { useAppSelector, useAppDispatch } from "@/redux/store";
import { removeFromCart, removeItemCompletely, clearCart, addToCart } from "@/redux/cart/slice";
import { Link } from "react-router-dom";
import Price from "@/components/Price/Price";
import { LoginModal } from "@/components/LoginModal/LoginModal";

type CheckoutStep = "cart" | "processing" | "success";

const CartPage: FC = () => {
  const dispatch = useAppDispatch();
  const cartItems = useAppSelector((state) => state.cart.items);
  
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return !!localStorage.getItem("access_token");
  });
  const [checkoutStep, setCheckoutStep] = useState<CheckoutStep>("cart");
  const [orderNumber, setOrderNumber] = useState<string>("");

  const handleIncrement = (id: number) => {
    const item = cartItems.find((item) => item.id === id);
    if (item) {
      dispatch(addToCart({
        id: item.id,
        title: item.title,
        imageUrl: item.imageUrl,
        price: item.price,
        oldPrice: item.oldPrice,
      }));
    }
  };

  const handleDecrement = (id: number) => {
    dispatch(removeFromCart(id));
  };

  const handleRemove = (id: number) => {
    dispatch(removeItemCompletely(id));
  };

  const handleClearCart = () => {
    dispatch(clearCart());
  };

  const handleCheckout = () => {
    if (!isAuthenticated) {
      setIsAuthModalOpen(true);
      return;
    }
    
    // Начинаем симуляцию оформления заказа
    setCheckoutStep("processing");
    
    // Симуляция процесса оформления (2 секунды)
    setTimeout(() => {
      // Генерируем номер заказа
      const orderNum = `TSH-${Date.now().toString().slice(-8)}`;
      setOrderNumber(orderNum);
      setCheckoutStep("success");
      
      // Очищаем корзину после успешного заказа
      dispatch(clearCart());
    }, 2000);
  };

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setIsAuthModalOpen(false);
  };

  const handleContinueShopping = () => {
    setCheckoutStep("cart");
    setOrderNumber("");
  };

  const totalPrice = cartItems.reduce(
    (total, item) => total + item.price * item.quantity,
    0
  );

  const totalOldPrice = cartItems.reduce(
    (total, item) => total + (item.oldPrice || item.price) * item.quantity,
    0
  );

  const hasDiscount = totalOldPrice > totalPrice;
  const discount = totalOldPrice - totalPrice;

  if (checkoutStep === "success") {
    return (
      <section className={styles.cart}>
        <div className="container">
          <div className={styles.cart__success}>
            <div className={styles.cartSuccess}>
              <div className={styles.cartSuccess__icon}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h1 className={styles.cartSuccess__title}>Заказ оформлен!</h1>
              <p className={styles.cartSuccess__text}>
                Спасибо за ваш заказ. Номер вашего заказа:
              </p>
              <span className={styles.cartSuccess__orderNumber}>{orderNumber}</span>
              <p className={styles.cartSuccess__subtext}>
                Мы отправим вам email с подтверждением заказа.
              </p>
              <Link 
                to="/women" 
                className={styles.cartSuccess__button}
                onClick={handleContinueShopping}
              >
                Продолжить покупки
              </Link>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (checkoutStep === "processing") {
    return (
      <section className={styles.cart}>
        <div className="container">
          <div className={styles.cart__processing}>
            <div className={styles.cartProcessing}>
              <div className={styles.cartProcessing__spinner}></div>
              <h1 className={styles.cartProcessing__title}>Оформление заказа</h1>
              <p className={styles.cartProcessing__text}>
                Пожалуйста, подождите...
              </p>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (cartItems.length === 0) {
    return (
      <section className={styles.cart}>
        <div className="container">
          <div className={styles.cart__empty}>
            <div className={styles.cart__empty_content}>
              <p className={styles.cart__empty_text}>Ваша корзина пуста</p>
              <p className={styles.cart__empty_subtext}>
                Добавьте товары, чтобы оформить заказ
              </p>
              <Link to="/women" className={styles.cart__empty_link}>
                Перейти к покупкам
              </Link>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.cart}>
      <div className="container">
        
        <div className={styles.cart__content}>
          <div className={styles.cart__items}>
            <ul className={styles.cart__list} role="list" aria-label="Товары в корзине">
              {cartItems.map((item) => (
                <li key={item.id} className={styles.cart__item}>
                  <article className={styles.cartProduct}>
                    <Link 
                      to={`/product/${item.id}`} 
                      className={styles.cartProduct__imageLink}
                      aria-label={`Перейти к товару: ${item.title}`}
                    >
                      <div className={styles.cartProduct__imageWrapper}>
                        {item.imageUrl ? (
                          <img 
                            src={item.imageUrl} 
                            alt={item.title} 
                            className={styles.cartProduct__image}
                            loading="lazy"
                          />
                        ) : (
                          <div className={styles.cartProduct__noImage}>
                            <span>Нет фото</span>
                          </div>
                        )}
                      </div>
                    </Link>

                    <div className={styles.cartProduct__info}>
                      <Link 
                        to={`/product/${item.id}`}
                        className={styles.cartProduct__title}
                      >
                        <h2 className={styles.cartProduct__title_text}>{item.title}</h2>
                      </Link>

                      <div className={styles.cartProduct__price}>
                        <Price 
                          oldPrice={item.oldPrice} 
                          newPrice={item.price} 
                        />
                      </div>

                      <div className={styles.cartProduct__actions}>
                        <div 
                          className={styles.cartProduct__quantity}
                          role="group"
                          aria-label={`Количество товара: ${item.title}`}
                        >
                          <button
                            className={styles.cartProduct__quantityBtn}
                            onClick={() => handleDecrement(item.id)}
                            aria-label={`Уменьшить количество ${item.title}`}
                            type="button"
                          >
                            -
                          </button>
                          <span 
                            className={styles.cartProduct__quantityValue}
                            aria-live="polite"
                          >
                            {item.quantity}
                          </span>
                          <button
                            className={styles.cartProduct__quantityBtn}
                            onClick={() => handleIncrement(item.id)}
                            aria-label={`Увеличить количество ${item.title}`}
                            type="button"
                          >
                            +
                          </button>
                        </div>

                        <button
                          className={styles.cartProduct__remove}
                          onClick={() => handleRemove(item.id)}
                          aria-label={`Удалить ${item.title} из корзины`}
                          type="button"
                        >
                          Удалить
                        </button>
                      </div>
                    </div>

                    <div className={styles.cartProduct__total}>
                      <span className={styles.cartProduct__totalLabel}>Сумма:</span>
                      <span className={styles.cartProduct__totalValue}>
                        {item.price * item.quantity} ₽
                      </span>
                    </div>
                  </article>
                </li>
              ))}
            </ul>

            <button
              className={styles.cart__clear}
              onClick={handleClearCart}
              aria-label="Очистить корзину"
              type="button"
            >
              Очистить корзину
            </button>
          </div>

          <aside className={styles.cart__summary}>
            <div className={styles.cartSummary}>
              <h2 className={styles.cartSummary__title}>Итого</h2>
              
              <div className={styles.cartSummary__details}>
                <div className={styles.cartSummary__row}>
                  <span className={styles.cartSummary__label}>Товаров:</span>
                  <span className={styles.cartSummary__value}>
                    {cartItems.reduce((sum, item) => sum + item.quantity, 0)} шт.
                  </span>
                </div>

                {hasDiscount && (
                  <div className={styles.cartSummary__row}>
                    <span className={styles.cartSummary__label}>Скидка:</span>
                    <span className={styles.cartSummary__discount}>
                      -{discount} ₽
                    </span>
                  </div>
                )}

                <div className={styles.cartSummary__row}>
                  <span className={styles.cartSummary__label}>Сумма:</span>
                  <span className={styles.cartSummary__value}>
                    {totalPrice} ₽
                  </span>
                </div>
              </div>

              {!isAuthenticated && (
                <div className={styles.cartSummary__authWarning}>
                  <p>Для оформления заказа необходимо войти в аккаунт или зарегистрироваться</p>
                </div>
              )}

              <button 
                className={styles.cartSummary__checkout}
                onClick={handleCheckout}
                type="button"
              >
                {isAuthenticated ? "Оформить заказ" : "Войти для оформления"}
              </button>

              <Link 
                to="/women" 
                className={styles.cartSummary__continue}
              >
                Продолжить покупки
              </Link>
            </div>
          </aside>
        </div>
      </div>

      <LoginModal
        openModal={isAuthModalOpen}
        onOpenChange={setIsAuthModalOpen}
        onLoginSuccess={handleLoginSuccess}
      />
    </section>
  );
};

export default CartPage;
