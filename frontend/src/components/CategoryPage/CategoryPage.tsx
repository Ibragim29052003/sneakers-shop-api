import { useEffect, type FC } from "react";
import styles from "./CategoryPage.module.scss";
import { useAppDispatch, useAppSelector } from "@/redux/store";
import { selectFilters } from "@/redux/filter/selectors";

// Импортируем хуки из RTK Query
// useGetFilteredProductsQuery - получает отфильтрованные товары для каталога
// useGetProductsQuery - получает товары для слайдера
import { useGetFilteredProductsQuery, useGetProductsQuery } from "@/services/api/productsApi";

// Импортируем экшн для обновления слайдов в Redux
import { setSlides } from "@/redux/slider/slice";

// Импортируем тип Slide
import type { Slide } from "@/redux/slider/types";

// Импортируем компоненты
import Slider from "@/features/slider/Slider";
import CatalogLayout from "../CatalogLayout";
import Spiner from "@/components/Spiner/Spiner";

// Хук для debounce (задержка запроса при изменении фильтров)
import useDebounce from "@/hooks/useDebounce";

interface CategoryPageProps {
  // Категория страницы: women, men или children
  category: "women" | "men" | "children";
}

/**
 * Тип для товаров в каталоге
 * Отличается от Slide отсутствием link и description
 */
type CatalogProduct = Omit<Slide, "link" | "description">;

/**
 * Функция преобразования Product (с бэкенда) в Slide (для слайдера)
 * 
 * @param product - товар с бэкенда
 * @returns - товар в формате для слайдера
 */
const transformProductToSlide = (product: any): Slide => ({
  id: String(product.id),
  // Используем main_image_url или первое изображение из массива
  imageUrl: product.main_image_url || product.images?.[0]?.image || "",
  title: product.name,
  description: product.description || "",
  // Цена приходит строкой "5000.00" - преобразуем в число
  newPrice: parseFloat(product.price),
  oldPrice: undefined,
  // Ссылка на страницу товара
  link: `/product/${product.id}`,
});

/**
 * Функция преобразования Product в формат для каталога
 */
const transformProductToCatalogProduct = (product: any): CatalogProduct => ({
  id: String(product.id),
  imageUrl: product.main_image_url || product.images?.[0]?.image || "",
  title: product.name,
  newPrice: parseFloat(product.price),
  oldPrice: undefined,
});

const CategoryPage: FC<CategoryPageProps> = ({ category }) => {
  // Подключаем Redux
  const dispatch = useAppDispatch();
  
  // Получаем фильтры из Redux
  const filters = useAppSelector(selectFilters);
  
  // Debounce - задержка 300мс перед отправкой запроса при изменении фильтров
  // Это нужно чтобы не отправлять запрос на каждый чих
  const debouncedFilters = useDebounce(filters, 300);

  /**
   * ЗАПРОС 1: Получение товаров для каталога
   * 
   * useGetFilteredProductsQuery автоматически:
   * - Делает GET запрос к /api/v1/products/
   * - Передаёт параметры filters (категория, цена, фильтры)
   * - Возвращает данные + состояние загрузки + ошибки
   */
  const {
    data: products,           // массив товаров
    isLoading: productsLoading, // true пока грузится
    error: productsError,      // объект ошибки если есть
  } = useGetFilteredProductsQuery({ 
    ...debouncedFilters,  // распыляем фильтры (category, min_price, max_price...)
    category              // добавляем категорию
  });

  /**
   * ЗАПРОС 2: Получение товаров для слайдера
   * 
   * Загружаем только 10 товаров (page_size: 10) для показа в слайдере
   */
  const {
    data: productsResponse,   // полный ответ с пагинацией
    isLoading: slidesLoading,  // индикатор загрузки
    error: slidesError,       // ошибка
  } = useGetProductsQuery({ 
    category, 
    page_size: 10 
  });

  /**
   * ПРИ ПОЛУЧЕНИИ ДАННЫХ - сохраняем в Redux для слайдера
   * 
   * useEffect запускается когда:
   * 1. productsResponse изменится (пришёл ответ от сервера)
   * 2. slidesLoading изменится (загрузка завершилась)
   */
  useEffect(() => {
    // Проверяем что загрузка завершена и данные есть
    if (!slidesLoading && productsResponse?.results) {
      // Преобразуем товары в формат слайдера
      const slides = productsResponse.results.map(transformProductToSlide);
      // Сохраняем в Redux store
      dispatch(setSlides(slides));
    }
  }, [dispatch, productsResponse, slidesLoading]);

  // Преобразуем товары для каталога
  const catalogProducts: CatalogProduct[] = products?.map(transformProductToCatalogProduct) || [];

  // Показываем загрузку
  if (slidesLoading) return <Spiner />;
  
  // Показываем ошибку если есть
  if (slidesError || productsError) return <div>Ошибка загрузки товаров</div>;

  return (
    <div className={styles.categoryPage}>
      {/* Слайдер - получает данные через Redux (useAppSelector) */}
      <Slider />
      
      {/* Каталог с товарами */}
      <CatalogLayout
        category={category}
        products={catalogProducts}
        loading={productsLoading}
      />
    </div>
  );
};

export default CategoryPage;
