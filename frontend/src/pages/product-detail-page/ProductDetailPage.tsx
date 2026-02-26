import { useState, useCallback, useEffect, type FC } from "react";
import { useParams, Link } from "react-router-dom";
import { useGetProductByIdQuery } from "@/services/api/productsApi";
import { useSwipeable } from "react-swipeable";
import { useAppDispatch } from "@/redux/store";
import { addToCart } from "@/redux/cart/slice";

import styles from "./ProductDetailPage.module.scss";

// SVG иконки
const CartIcon = () => (
  <svg
    className={styles.productDetail__addToCartIcon}
    viewBox="0 0 24 24"
    aria-hidden="true"
  >
    <path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z" />
  </svg>
);

const HeartIcon = ({ filled = false }: { filled?: boolean }) => (
  <svg
    className={styles.productDetail__favoriteIcon}
    viewBox="0 0 24 24"
    aria-hidden="true"
  >
    <path
      d={
        filled
          ? "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
          : "M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z"
      }
    />
  </svg>
);

const ChevronLeftIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path
      d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"
      fill="currentColor"
    />
  </svg>
);

const ChevronRightIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path
      d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"
      fill="currentColor"
    />
  </svg>
);

const CheckIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path
      d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"
      fill="currentColor"
    />
  </svg>
);

const CloseIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path
      d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
      fill="currentColor"
    />
  </svg>
);

// Тип уведомления
interface Notification {
  id: number;
  type: "success" | "error";
  title: string;
  message: string;
}

const ProductDetailPage: FC = () => {
  const { id } = useParams<{ id: string }>();
  const dispatch = useAppDispatch();
  const productId = id ? parseInt(id, 10) : 0;

  // Получение данных о товаре
  const { data: product, isLoading, error } = useGetProductByIdQuery(productId);

  // Локальное состояние
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [isFavorite, setIsFavorite] = useState(false);
  const [isAddingToCart, setIsAddingToCart] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Вычисление скидки
  const calculateDiscount = () => {
    if (!product?.old_price || !product.price) return 0;
    const oldPrice = parseFloat(product.old_price);
    const newPrice = parseFloat(product.price);
    if (oldPrice <= newPrice) return 0;
    return Math.round(((oldPrice - newPrice) / oldPrice) * 100);
  };

  const discount = product ? calculateDiscount() : 0;

  // Получение всех изображений товара
  const getAllImages = () => {
    if (!product) return [];
    if (product.images && product.images.length > 0) {
      return product.images.map((img) => img.image);
    }
    if (product.main_image_url) {
      return [product.main_image_url];
    }
    return ["/placeholder-product.jpg"];
  };

  const images = product ? getAllImages() : [];

  // Навигация по слайдам
  const goToNextSlide = useCallback(() => {
    setSelectedImageIndex((prev) => (prev + 1) % images.length);
  }, [images.length]);

  const goToPrevSlide = useCallback(() => {
    setSelectedImageIndex((prev) => (prev - 1 + images.length) % images.length);
  }, [images.length]);

  // Поддержка свайпов
  const handlers = useSwipeable({
    onSwipedLeft: goToNextSlide,
    onSwipedRight: goToPrevSlide,
    preventScrollOnSwipe: true,
    trackMouse: true,
  });

  // Обработчики
  const handleThumbnailClick = useCallback((index: number) => {
    setSelectedImageIndex(index);
  }, []);

  // Функция показа уведомления
  const showNotification = useCallback(
    (type: "success" | "error", title: string, message: string) => {
      const newNotification: Notification = {
        id: Date.now(),
        type,
        title,
        message,
      };
      setNotifications((prev) => [...prev, newNotification]);

      // Удаляем уведомление через 4 секунды
      setTimeout(() => {
        setNotifications((prev) =>
          prev.map((n) =>
            n.id === newNotification.id ? { ...n, hiding: true } : n
          )
        );
        setTimeout(() => {
          setNotifications((prev) =>
            prev.filter((n) => n.id !== newNotification.id)
          );
        }, 300);
      }, 4000);
    },
    []
  );

  // Закрыть уведомление
  const closeNotification = useCallback((id: number) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, hiding: true } : n))
    );
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, 300);
  }, []);

  // Обработчик добавления в корзину
  const handleAddToCart = useCallback(() => {
    if (!product) return;

    setIsAddingToCart(true);

    // Добавляем в Redux корзину
    dispatch(
      addToCart({
        id: product.id,
        title: product.name,
        imageUrl: product.main_image_url || "",
        price: parseFloat(product.price) || 0,
        oldPrice: product.old_price ? parseFloat(product.old_price) : undefined,
      })
    );

    setIsAddingToCart(false);

    // Показываем красивое уведомление
    showNotification("success", "Товар добавлен в корзину", product.name);
  }, [product, dispatch, showNotification]);

  const handleFavoriteToggle = useCallback(() => {
    setIsFavorite((prev) => !prev);
  }, []);

  // Категория товара для хлебных крошек
  const categoryName = product?.categories?.[0]?.name || "Товар";

  // Состояние загрузки
  if (isLoading) {
    return (
      <div className={styles.productDetail}>
        <div
          className={styles.productDetail__loading}
          role="status"
          aria-label="Загрузка товара"
        >
          <div className={styles.productDetail__loadingSpinner} />
          <span className={styles.visuallyHidden}>Загрузка товара...</span>
        </div>
      </div>
    );
  }

  // Ошибка при загрузке
  if (error || !product) {
    return (
      <div className={styles.productDetail}>
        <div className={styles.productDetail__error} role="alert">
          <h2 className={styles.productDetail__errorTitle}>
            Ошибка загрузки товара
          </h2>
          <p className={styles.productDetail__errorMessage}>
            Не удалось загрузить информацию о товаре. Пожалуйста, попробуйте
            позже.
          </p>
          <button
            className={styles.productDetail__errorButton}
            onClick={() => window.location.reload()}
          >
            Повторить
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.productDetail__container}>
      <nav className={styles.productDetail__breadcrumb} aria-label="Навигация">
        <Link to="/" className={styles.productDetail__breadcrumbLink}>
          Главная
        </Link>
        <span className={styles.productDetail__breadcrumbSeparator}>/</span>
        <Link to="/women" className={styles.productDetail__breadcrumbLink}>
          Каталог
        </Link>
        <span className={styles.productDetail__breadcrumbSeparator}>/</span>
        <span className={styles.productDetail__breadcrumbCurrent}>
          {categoryName}
        </span>
      </nav>

      <div className={styles.productDetail}>
        {/* Хлебные крошки */}

        {/* Галерея изображений - Слайдер */}
        <div className={styles.productDetail__gallery}>
          {images.length > 0 && (
            <div
              className={styles.productDetail__slider}
              role="region"
              aria-label="Галерея товара"
              {...handlers}
            >
              <div className={styles.productDetail__sliderContainer}>
                <div
                  className={styles.productDetail__slides}
                  style={{
                    transform: `translateX(-${selectedImageIndex * 100}%)`,
                  }}
                >
                  {images.map((image, index) => (
                    <div key={index} className={styles.productDetail__slide}>
                      <img
                        src={image}
                        alt={`${product.name} - изображение ${index + 1}`}
                        className={styles.productDetail__slideImage}
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === "ArrowLeft") goToPrevSlide();
                          if (e.key === "ArrowRight") goToNextSlide();
                        }}
                      />
                    </div>
                  ))}
                </div>

                {/* Кнопки навигации */}
                {images.length > 1 && (
                  <>
                    <button
                      className={`${styles.productDetail__navButton} ${styles.productDetail__navButton_prev}`}
                      onClick={goToPrevSlide}
                      aria-label="Предыдущее изображение"
                    >
                      <ChevronLeftIcon />
                    </button>
                    <button
                      className={`${styles.productDetail__navButton} ${styles.productDetail__navButton_next}`}
                      onClick={goToNextSlide}
                      aria-label="Следующее изображение"
                    >
                      <ChevronRightIcon />
                    </button>

                    {/* Точечная навигация */}
                    <div
                      className={styles.productDetail__dots}
                      role="tablist"
                      aria-label="Навигация по слайдам"
                    >
                      {images.map((_, index) => (
                        <button
                          key={index}
                          className={`${styles.productDetail__dot} ${
                            index === selectedImageIndex
                              ? styles.productDetail__dot_active
                              : ""
                          }`}
                          onClick={() => handleThumbnailClick(index)}
                          role="tab"
                          aria-selected={index === selectedImageIndex}
                          aria-label={`Слайд ${index + 1}`}
                        />
                      ))}
                    </div>

                    {/* Счетчик */}
                    <div
                      className={styles.productDetail__counter}
                      aria-live="polite"
                    >
                      {selectedImageIndex + 1} / {images.length}
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Миниатюры */}
          {images.length > 1 && (
            <div
              className={styles.productDetail__thumbnails}
              role="tablist"
              aria-label="Миниатюры изображений"
            >
              {images.map((image, index) => (
                <button
                  key={index}
                  className={`${styles.productDetail__thumbnail} ${
                    index === selectedImageIndex
                      ? styles.productDetail__thumbnail_active
                      : ""
                  }`}
                  onClick={() => handleThumbnailClick(index)}
                  role="tab"
                  aria-selected={index === selectedImageIndex}
                  aria-label={`Изображение ${index + 1}`}
                  tabIndex={0}
                >
                  <img
                    src={image}
                    alt={`Миниатюра ${index + 1}`}
                    className={styles.productDetail__thumbnailImage}
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Информация о товаре */}
        <div className={styles.productDetail__info}>
          <h1 className={styles.productDetail__title}>{product.name}</h1>

          <p className={styles.productDetail__sku}>
            Артикул: {product.sku || "—"}
          </p>

          {/* Цена */}
          <div className={styles.productDetail__priceBlock}>
            <span className={styles.productDetail__price}>
              {parseFloat(product.price).toLocaleString("ru-RU")} ₽
            </span>

            {product.old_price &&
              parseFloat(product.old_price) > parseFloat(product.price) && (
                <>
                  <span className={styles.productDetail__oldPrice}>
                    {parseFloat(product.old_price).toLocaleString("ru-RU")} ₽
                  </span>
                  <span className={styles.productDetail__discount}>
                    -{discount}%
                  </span>
                </>
              )}
          </div>

          {/* Описание */}
          <p className={styles.productDetail__description}>
            {product.description || "Описание товара недоступно."}
          </p>

          {/* Опции товара (цвет, размер) */}
          <div className={styles.productDetail__options}>
            {/* Цвет */}
            <div className={styles.productDetail__optionGroup}>
              <span className={styles.productDetail__optionLabel}>Цвет</span>
              <div
                className={styles.productDetail__colorOptions}
                role="radiogroup"
                aria-label="Выбор цвета"
              >
                {["#000000", "#FFFFFF", "#665AB5", "#EB3F5E", "#309D5B"].map(
                  (color, index) => (
                    <button
                      key={index}
                      className={`${styles.productDetail__colorOption} ${
                        selectedColor === color
                          ? styles.productDetail__colorOption_active
                          : ""
                      }`}
                      style={{ backgroundColor: color }}
                      onClick={() => setSelectedColor(color)}
                      role="radio"
                      aria-checked={selectedColor === color}
                      aria-label={`Цвет ${color}`}
                      tabIndex={0}
                    />
                  )
                )}
              </div>
            </div>

            {/* Размер */}
            <div className={styles.productDetail__optionGroup}>
              <span className={styles.productDetail__optionLabel}>Размер</span>
              <div
                className={styles.productDetail__sizeOptions}
                role="radiogroup"
                aria-label="Выбор размера"
              >
                {["XS", "S", "M", "L", "XL", "XXL"].map((size) => (
                  <button
                    key={size}
                    className={`${styles.productDetail__sizeOption} ${
                      selectedSize === size
                        ? styles.productDetail__sizeOption_active
                        : ""
                    }`}
                    onClick={() => setSelectedSize(size)}
                    role="radio"
                    aria-checked={selectedSize === size}
                    tabIndex={0}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Кнопки действий */}
          <div className={styles.productDetail__actions}>
            <button
              className={styles.productDetail__addToCart}
              onClick={handleAddToCart}
              disabled={isAddingToCart}
              aria-label={
                isAddingToCart
                  ? "Добавление в корзину..."
                  : "Добавить в корзину"
              }
            >
              <CartIcon />
              {isAddingToCart ? "Добавляем..." : "В корзину"}
            </button>

            <button
              className={`${styles.productDetail__favorite} ${
                isFavorite ? styles.productDetail__favorite_active : ""
              }`}
              onClick={handleFavoriteToggle}
              aria-label={
                isFavorite ? "Удалить из избранного" : "Добавить в избранное"
              }
              aria-pressed={isFavorite}
            >
              <HeartIcon filled={isFavorite} />
            </button>
          </div>

          {/* Детали товара */}
          <div className={styles.productDetail__details}>
            <div className={styles.productDetail__detailItem}>
              <span className={styles.productDetail__detailLabel}>
                Категория:
              </span>
              <span className={styles.productDetail__detailValue}>
                {product.categories?.map((c) => c.name).join(", ") || "—"}
              </span>
            </div>
            <div className={styles.productDetail__detailItem}>
              <span className={styles.productDetail__detailLabel}>
                Артикул:
              </span>
              <span className={styles.productDetail__detailValue}>
                {product.sku || "—"}
              </span>
            </div>
            <div className={styles.productDetail__detailItem}>
              <span className={styles.productDetail__detailLabel}>
                Наличие:
              </span>
              <span className={styles.productDetail__detailValue}>
                {product.is_active ? "В наличии" : "Нет в наличии"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Уведомления */}
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`${styles.notification} ${
            styles[`notification_${notification.type}`]
          } ${(notification as any).hiding ? styles.hiding : ""}`}
          role="alert"
        >
          <div className={styles.notification__icon}>
            <CheckIcon />
          </div>
          <div className={styles.notification__content}>
            <p className={styles.notification__title}>{notification.title}</p>
            <p className={styles.notification__message}>
              {notification.message}
            </p>
          </div>
          <button
            className={styles.notification__close}
            onClick={() => closeNotification(notification.id)}
            aria-label="Закрыть уведомление"
          >
            <CloseIcon />
          </button>
        </div>
      ))}
    </div>
  );
};

export default ProductDetailPage;
