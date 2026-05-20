import { useState, useCallback, useEffect, useMemo, type FC } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  useGetProductByIdQuery,
  useCreateProductMutation,
  useDeleteProductMutation,
  useUpdateProductMutation,
  useUploadProductImageMutation,
  useDeleteProductImageMutation,
} from "@/services/api/productsApi";
import { useSwipeable } from "react-swipeable";
import { useAppDispatch } from "@/redux/store";
import { addToCart } from "@/redux/cart/slice";

import styles from "./ProductDetailPage.module.scss";

const CartIcon = () => (
  <svg className={styles.productDetail__addToCartIcon} viewBox="0 0 24 24" aria-hidden="true">
    <path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z" />
  </svg>
);

const CheckIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" fill="currentColor" />
  </svg>
);

const CloseIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor" />
  </svg>
);

interface Notification {
  id: number;
  type: "success" | "error";
  title: string;
  message: string;
}

interface ProductFormState {
  name: string;
  description: string;
  price: string;
  old_price: string;
  sku: string;
  is_active: boolean;
}

const CATEGORY_LABELS: Record<"women" | "men" | "children", string> = {
  women: "Женщинам",
  men: "Мужчинам",
  children: "Детям",
};

const ProductDetailPage: FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const productId = id ? parseInt(id, 10) : 0;

  const { data: product, isLoading, error, refetch } = useGetProductByIdQuery(productId);
  const [updateProduct, { isLoading: isUpdating }] = useUpdateProductMutation();
  const [deleteProduct, { isLoading: isDeleting }] = useDeleteProductMutation();
  const [createProduct, { isLoading: isCreating }] = useCreateProductMutation();
  const [uploadProductImage, { isLoading: isUploadingImage }] = useUploadProductImageMutation();
  const [deleteProductImage, { isLoading: isDeletingImage }] = useDeleteProductImageMutation();

  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [isAddingToCart, setIsAddingToCart] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);

  const [editForm, setEditForm] = useState<ProductFormState>({
    name: "",
    description: "",
    price: "",
    old_price: "",
    sku: "",
    is_active: true,
  });

  const [createForm, setCreateForm] = useState<ProductFormState>({
    name: "",
    description: "",
    price: "",
    old_price: "",
    sku: "",
    is_active: true,
  });

  const [createPublishedPage, setCreatePublishedPage] = useState<"women" | "men" | "children">("women");
  const [editImageFiles, setEditImageFiles] = useState<File[]>([]);
  const [createImageFiles, setCreateImageFiles] = useState<File[]>([]);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const hasAdminRole = Boolean(
        payload?.is_staff || payload?.roles?.includes?.("admin") || payload?.role === "admin"
      );
      setIsAdmin(hasAdminRole);
    } catch {
      setIsAdmin(false);
    }
  }, []);

  useEffect(() => {
    if (!product) return;
    setEditForm({
      name: product.name || "",
      description: product.description || "",
      price: product.price || "",
      old_price: product.old_price || "",
      sku: product.sku || "",
      is_active: product.is_active,
    });

    const primaryPage = product.published_pages?.[0];
    if (primaryPage === "women" || primaryPage === "men" || primaryPage === "children") {
      setCreatePublishedPage(primaryPage);
    }
  }, [product]);

  const showNotification = useCallback((type: "success" | "error", title: string, message: string) => {
    const notification = { id: Date.now(), type, title, message };
    setNotifications((prev) => [...prev, notification]);
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== notification.id));
    }, 3500);
  }, []);

  const closeNotification = useCallback((nid: number) => {
    setNotifications((prev) => prev.filter((n) => n.id !== nid));
  }, []);

  const images = useMemo(() => {
    if (product?.images?.length) return product.images.map((img) => img.image);
    if (product?.main_image_url) return [product.main_image_url];
    return ["/placeholder-product.jpg"];
  }, [product]);

  const primaryCatalogPage: "women" | "men" | "children" =
    product?.published_pages?.[0] === "women" || product?.published_pages?.[0] === "men" || product?.published_pages?.[0] === "children"
      ? product.published_pages[0]
      : "women";

  const categoryLabel = CATEGORY_LABELS[primaryCatalogPage];
  const categoryLink = `/${primaryCatalogPage}`;

  const currentPrice = parseFloat(product?.price || "0") || 0;
  const oldPrice = product?.old_price ? parseFloat(product.old_price) : null;
  const discountPercent = oldPrice && oldPrice > currentPrice ? Math.round(((oldPrice - currentPrice) / oldPrice) * 100) : null;

  const goToNextSlide = useCallback(() => {
    setSelectedImageIndex((prev) => (prev + 1) % images.length);
  }, [images.length]);

  const goToPrevSlide = useCallback(() => {
    setSelectedImageIndex((prev) => (prev - 1 + images.length) % images.length);
  }, [images.length]);

  const handlers = useSwipeable({
    onSwipedLeft: goToNextSlide,
    onSwipedRight: goToPrevSlide,
    preventScrollOnSwipe: true,
    trackMouse: true,
  });

  const handleAddToCart = useCallback(() => {
    if (!product) return;
    setIsAddingToCart(true);
    dispatch(
      addToCart({
        id: product.id,
        title: product.name,
        imageUrl: product.main_image_url || images[0] || "",
        price: parseFloat(product.price) || 0,
        oldPrice: product.old_price ? parseFloat(product.old_price) : undefined,
      })
    );
    setIsAddingToCart(false);
    showNotification("success", "Товар добавлен", product.name);
  }, [dispatch, images, product, showNotification]);

  const handleUpdateProduct = async () => {
    if (!product) return;
    if (!editForm.name.trim() || !editForm.price.trim()) {
      showNotification("error", "Ошибка", "Название и цена обязательны");
      return;
    }
    try {
      await updateProduct({
        id: product.id,
        product: {
          name: editForm.name.trim(),
          description: editForm.description,
          price: editForm.price.trim(),
          old_price: editForm.old_price.trim() || null,
          sku: editForm.sku.trim(),
          is_active: editForm.is_active,
        },
      }).unwrap();
      showNotification("success", "Готово", "Товар обновлен");
      await refetch();
    } catch {
      showNotification("error", "Ошибка", "Не удалось обновить товар");
    }
  };

  const handleDeleteProduct = async () => {
    if (!product) return;
    if (!window.confirm(`Удалить товар "${product.name}"?`)) return;
    try {
      await deleteProduct(product.id).unwrap();
      navigate(categoryLink);
    } catch {
      showNotification("error", "Ошибка", "Не удалось удалить товар");
    }
  };

  const handleUploadImagesToCurrentProduct = async () => {
    if (!product || editImageFiles.length === 0) return;
    try {
      for (let i = 0; i < editImageFiles.length; i += 1) {
        await uploadProductImage({
          product: product.id,
          imageFile: editImageFiles[i],
          is_main: !product.images?.length && i === 0,
          alt_text: product.name,
        }).unwrap();
      }
      setEditImageFiles([]);
      await refetch();
      showNotification("success", "Готово", "Фото добавлены");
    } catch {
      showNotification("error", "Ошибка", "Не удалось добавить фото");
    }
  };

  const handleDeleteImage = async (imageId: number) => {
    try {
      await deleteProductImage(imageId).unwrap();
      await refetch();
      showNotification("success", "Готово", "Фото удалено");
    } catch {
      showNotification("error", "Ошибка", "Не удалось удалить фото");
    }
  };

  const handleCreateNewProduct = async () => {
    if (!createForm.name.trim() || !createForm.price.trim()) {
      showNotification("error", "Ошибка", "Заполните название и цену");
      return;
    }
    try {
      const created = await createProduct({
        name: createForm.name.trim(),
        description: createForm.description,
        price: createForm.price.trim(),
        old_price: createForm.old_price.trim() || null,
        sku: createForm.sku.trim() || `SKU-${Date.now()}`,
        status: createForm.is_active ? "active" : "draft",
        is_active: createForm.is_active,
        published_pages: [createPublishedPage],
        categories_ids: [],
      }).unwrap();

      if (createImageFiles.length > 0) {
        for (let i = 0; i < createImageFiles.length; i += 1) {
          await uploadProductImage({
            product: created.id,
            imageFile: createImageFiles[i],
            is_main: i === 0,
            alt_text: created.name,
          }).unwrap();
        }
      }

      showNotification("success", "Готово", "Новый товар создан");
      navigate(`/product/${created.id}`);
    } catch {
      showNotification("error", "Ошибка", "Не удалось создать товар");
    }
  };

  if (isLoading) {
    return (
      <div className={styles.productDetail}>
        <div className={styles.productDetail__loading}>
          <div className={styles.productDetail__loadingSpinner} />
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className={styles.productDetail}>
        <div className={styles.productDetail__error}>
          <h2 className={styles.productDetail__errorTitle}>Не удалось загрузить товар</h2>
          <p className={styles.productDetail__errorMessage}>Проверьте соединение и попробуйте обновить страницу.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.productDetail__container}>
      <nav className={styles.productDetail__breadcrumb} aria-label="Навигация">
        <Link to="/" className={styles.productDetail__breadcrumbLink}>Главная</Link>
        <span className={styles.productDetail__breadcrumbSeparator}>/</span>
        <Link to={categoryLink} className={styles.productDetail__breadcrumbLink}>{categoryLabel}</Link>
        <span className={styles.productDetail__breadcrumbSeparator}>/</span>
        <span className={styles.productDetail__breadcrumbCurrent}>{product.name}</span>
      </nav>

      <div className={styles.productDetail}>
        <div className={styles.productDetail__gallery}>
          <div className={styles.productDetail__slider} {...handlers}>
            <div className={styles.productDetail__sliderContainer}>
              <div className={styles.productDetail__slides} style={{ transform: `translateX(-${selectedImageIndex * 100}%)` }}>
                {images.map((image, index) => (
                  <div key={index} className={styles.productDetail__slide}>
                    <img src={image} alt={`${product.name} ${index + 1}`} className={styles.productDetail__slideImage} />
                  </div>
                ))}
              </div>
            </div>

            {images.length > 1 && (
              <>
                <button
                  type="button"
                  className={`${styles.productDetail__navButton} ${styles.productDetail__navButton_prev}`}
                  onClick={goToPrevSlide}
                  aria-label="Предыдущее фото"
                >
                  ‹
                </button>
                <button
                  type="button"
                  className={`${styles.productDetail__navButton} ${styles.productDetail__navButton_next}`}
                  onClick={goToNextSlide}
                  aria-label="Следующее фото"
                >
                  ›
                </button>
                <div className={styles.productDetail__counter}>{selectedImageIndex + 1} / {images.length}</div>
                <div className={styles.productDetail__dots}>
                  {images.map((_, index) => (
                    <button
                      type="button"
                      key={index}
                      className={`${styles.productDetail__dot} ${index === selectedImageIndex ? styles.productDetail__dot_active : ""}`}
                      onClick={() => setSelectedImageIndex(index)}
                      aria-label={`Перейти к фото ${index + 1}`}
                    />
                  ))}
                </div>
              </>
            )}
          </div>

          {images.length > 1 && (
            <div className={styles.productDetail__thumbnails}>
              {images.map((image, index) => (
                <button
                  key={index}
                  type="button"
                  className={`${styles.productDetail__thumbnail} ${index === selectedImageIndex ? styles.productDetail__thumbnail_active : ""}`}
                  onClick={() => setSelectedImageIndex(index)}
                >
                  <img src={image} alt={`Миниатюра ${index + 1}`} className={styles.productDetail__thumbnailImage} />
                </button>
              ))}
            </div>
          )}
        </div>

        <div className={styles.productDetail__info}>
          <h1 className={styles.productDetail__title}>{product.name}</h1>
          <p className={styles.productDetail__sku}>Артикул: {product.sku || "—"}</p>

          <div className={styles.productDetail__priceBlock}>
            <span className={styles.productDetail__price}>{currentPrice.toLocaleString("ru-RU")} ₽</span>
            {oldPrice && oldPrice > currentPrice && (
              <>
                <span className={styles.productDetail__oldPrice}>{oldPrice.toLocaleString("ru-RU")} ₽</span>
                {discountPercent !== null && <span className={styles.productDetail__discount}>-{discountPercent}%</span>}
              </>
            )}
          </div>

          <p className={styles.productDetail__description}>{product.description || "Описание товара недоступно."}</p>

          <div className={styles.productDetail__actions}>
            <button className={styles.productDetail__addToCart} onClick={handleAddToCart} disabled={isAddingToCart}>
              <CartIcon />
              {isAddingToCart ? "Добавляем..." : "В корзину"}
            </button>
          </div>

          <div className={styles.productDetail__details}>
            <div className={styles.productDetail__detailItem}>
              <span className={styles.productDetail__detailLabel}>Категория</span>
              <span className={styles.productDetail__detailValue}>{categoryLabel}</span>
            </div>
            <div className={styles.productDetail__detailItem}>
              <span className={styles.productDetail__detailLabel}>Поставщик</span>
              <span className={styles.productDetail__detailValue}>{product.supplier_name || "Не указан"}</span>
            </div>
            {product.filter_attributes?.map((item) => (
              <div className={styles.productDetail__detailItem} key={item.group}>
                <span className={styles.productDetail__detailLabel}>{item.group}</span>
                <span className={styles.productDetail__detailValue}>{item.values.join(", ") || "—"}</span>
              </div>
            ))}
          </div>

          {isAdmin && (
            <div className={styles.productDetail__adminPanel}>
              <h3 className={styles.productDetail__adminTitle}>Редактирование товара</h3>
              <input className={styles.productDetail__adminInput} value={editForm.name} onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))} placeholder="Название" />
              <input className={styles.productDetail__adminInput} value={editForm.price} onChange={(e) => setEditForm((p) => ({ ...p, price: e.target.value }))} placeholder="Цена" />
              <input className={styles.productDetail__adminInput} value={editForm.old_price} onChange={(e) => setEditForm((p) => ({ ...p, old_price: e.target.value }))} placeholder="Старая цена" />
              <input className={styles.productDetail__adminInput} value={editForm.sku} onChange={(e) => setEditForm((p) => ({ ...p, sku: e.target.value }))} placeholder="SKU" />
              <textarea className={styles.productDetail__adminTextarea} value={editForm.description} onChange={(e) => setEditForm((p) => ({ ...p, description: e.target.value }))} placeholder="Описание" />

              <div className={styles.productDetail__adminImageGrid}>
                {product.images?.map((img) => (
                  <div key={img.id} className={styles.productDetail__adminImageCard}>
                    <img src={img.image} alt={img.alt_text || product.name} className={styles.productDetail__adminImagePreview} />
                    <button className={styles.productDetail__adminDangerBtn} onClick={() => handleDeleteImage(img.id)} disabled={isDeletingImage}>Удалить фото</button>
                  </div>
                ))}
              </div>

              <input type="file" multiple accept="image/*" className={styles.productDetail__adminFileInput} onChange={(e) => setEditImageFiles(Array.from(e.target.files || []))} />

              <div className={styles.productDetail__actions}>
                <button className={styles.productDetail__adminPrimaryBtn} onClick={handleUploadImagesToCurrentProduct} disabled={isUploadingImage || editImageFiles.length === 0}>{isUploadingImage ? "Загружаем..." : "Добавить фото"}</button>
                <button className={styles.productDetail__adminPrimaryBtn} onClick={handleUpdateProduct} disabled={isUpdating}>{isUpdating ? "Сохраняем..." : "Сохранить"}</button>
                <button className={styles.productDetail__adminDangerBtn} onClick={handleDeleteProduct} disabled={isDeleting}>{isDeleting ? "Удаляем..." : "Удалить товар"}</button>
              </div>
            </div>
          )}

          {isAdmin && (
            <div className={styles.productDetail__adminPanel}>
              <h3 className={styles.productDetail__adminTitle}>Создание нового товара</h3>
              <input className={styles.productDetail__adminInput} value={createForm.name} onChange={(e) => setCreateForm((p) => ({ ...p, name: e.target.value }))} placeholder="Название" />
              <input className={styles.productDetail__adminInput} value={createForm.price} onChange={(e) => setCreateForm((p) => ({ ...p, price: e.target.value }))} placeholder="Цена" />
              <input className={styles.productDetail__adminInput} value={createForm.old_price} onChange={(e) => setCreateForm((p) => ({ ...p, old_price: e.target.value }))} placeholder="Старая цена" />
              <input className={styles.productDetail__adminInput} value={createForm.sku} onChange={(e) => setCreateForm((p) => ({ ...p, sku: e.target.value }))} placeholder="SKU" />
              <textarea className={styles.productDetail__adminTextarea} value={createForm.description} onChange={(e) => setCreateForm((p) => ({ ...p, description: e.target.value }))} placeholder="Описание" />

              <label className={styles.productDetail__adminLabel}>
                Публикация:
                <select className={styles.productDetail__adminSelect} value={createPublishedPage} onChange={(e) => setCreatePublishedPage(e.target.value as "women" | "men" | "children")}>
                  <option value="women">Женщинам</option>
                  <option value="men">Мужчинам</option>
                  <option value="children">Детям</option>
                </select>
              </label>

              <input type="file" multiple accept="image/*" className={styles.productDetail__adminFileInput} onChange={(e) => setCreateImageFiles(Array.from(e.target.files || []))} />

              <div className={styles.productDetail__actions}>
                <button className={styles.productDetail__adminPrimaryBtn} onClick={handleCreateNewProduct} disabled={isCreating || isUploadingImage}>{isCreating ? "Создаем..." : "Создать товар"}</button>
              </div>
            </div>
          )}
        </div>
      </div>

      {notifications.map((notification) => (
        <div key={notification.id} className={`${styles.notification} ${styles[`notification_${notification.type}`]}`} role="alert">
          <div className={styles.notification__icon}><CheckIcon /></div>
          <div className={styles.notification__content}>
            <p className={styles.notification__title}>{notification.title}</p>
            <p className={styles.notification__message}>{notification.message}</p>
          </div>
          <button className={styles.notification__close} onClick={() => closeNotification(notification.id)} aria-label="Закрыть уведомление">
            <CloseIcon />
          </button>
        </div>
      ))}
    </div>
  );
};

export default ProductDetailPage;
