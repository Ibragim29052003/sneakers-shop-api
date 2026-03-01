import { useEffect, type FC } from "react";
import styles from "./CategoryPage.module.scss";
import { useAppDispatch, useAppSelector } from "@/redux/store";
import { selectFilters } from "@/redux/filter/selectors";

// Импортируем хуки из RTK Query
// useGetFilteredProductsQuery - получает отфильтрованные товары для каталога
// useGetActiveSliderSlidesQuery - получает слайды из отдельной таблицы
import { useGetFilteredProductsQuery, useGetActiveSliderSlidesQuery } from "@/services/api/productsApi";

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
 * Функция преобразования SliderSlide в Slide (для слайдера)
 * 
 * @param slide - слайд из API /slider/active-slides/
 * @returns - слайд в формате для компонента Slider
 */
const transformSliderSlideToSlide = (slide: any): Slide => ({
  id: String(slide.id),
  imageUrl: slide.image_url || "",
  title: slide.title,
  description: slide.description || "",
  // Цена: если есть своя цена слайда - используем её, иначе цену товара
  newPrice: slide.price ? parseFloat(slide.price) : (slide.product_price ? parseFloat(slide.product_price) : 0),
  oldPrice: slide.old_price ? parseFloat(slide.old_price) : undefined,
  // Ссылка: если есть link - используем его, иначе ссылка на товар
  link: slide.link || (slide.product ? `/product/${slide.product}` : "#"),
});

/**
 * Функция преобразования Product в формат для каталога
 */
const transformProductToCatalogProduct = (product: any): CatalogProduct => ({
  id: String(product.id),
  imageUrl: product.main_image_url || product.images?.[0]?.image || "",
  title: product.name,
  newPrice: parseFloat(product.price),
  oldPrice: product.old_price ? parseFloat(product.old_price) : undefined,
  supplierId: product.supplier || null,
  supplierName: product.supplier_name || null,
});

const CategoryPage: FC<CategoryPageProps> = ({ category }) => {
  // Подключаем Redux
  const dispatch = useAppDispatch();
  
  // Получаем фильтры из Redux
  const filters = useAppSelector(selectFilters);
  
  // Debounce - задержка 300мс перед отправкой запроса при изменении фильтров
  // Это нужно чтобы не отправлять запрос на каждый чих
  const debouncedFilters = useDebounce(filters, 300);

  // Функция преобразования sortBy в ordering для API
  const getOrderingParam = (sortBy: string | undefined, isNew: boolean | undefined): string | undefined => {
    if (isNew) {
      return '-created_at'; // Новинки - по убыванию даты создания
    }
    switch (sortBy) {
      case 'price_asc':
        return 'price'; // По возрастанию цены
      case 'price_desc':
        return '-price'; // По убыванию цены
      default:
        return undefined;
    }
  };

  // Преобразуем sortBy в ordering для API
  const ordering = getOrderingParam(filters.sortBy, filters.isNew);

  // Преобразуем camelCase в snake_case для API параметров
  const apiParams = {
    ...debouncedFilters,
    category,
    ordering,
    min_price: debouncedFilters.minPrice,
    max_price: debouncedFilters.maxPrice,
  };

  // Удаляем дублирующие поля (minPrice/maxPrice теперь в min_price/max_price)
  delete (apiParams as any).minPrice;
  delete (apiParams as any).maxPrice;

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
  } = useGetFilteredProductsQuery(apiParams);

  /**
   * ЗАПРОС 2: Получение слайдов для слайдера
   * 
   * Использует отдельный эндпоинт /api/v1/slider/active-slides/
   * Слайды берутся из отдельной таблицы SliderImage
   */
  const {
    data: sliderSlides,   // массив слайдов
    isLoading: slidesLoading,  // индикатор загрузки
    error: slidesError,       // ошибка
  } = useGetActiveSliderSlidesQuery();

  /**
   * ПРИ ПОЛУЧЕНИИ ДАННЫХ - сохраняем в Redux для слайдера
   * 
   * useEffect запускается когда:
   * 1. sliderSlides изменится (пришёл ответ от сервера)
   * 2. slidesLoading изменится (загрузка завершилась)
   */
  useEffect(() => {
    // Проверяем что загрузка завершена и данные есть
    if (!slidesLoading && sliderSlides) {
      // Преобразуем слайды в формат для компонента Slider
      const slides = sliderSlides.map(transformSliderSlideToSlide);
      // Сохраняем в Redux store
      dispatch(setSlides(slides));
    }
  }, [dispatch, sliderSlides, slidesLoading]);

  // Преобразуем товары для каталога
  const catalogProducts: CatalogProduct[] = products?.map(transformProductToCatalogProduct) || [];

  // Показываем загрузку (пока грузятся или товары или слайдеры)
  if (slidesLoading || productsLoading) return <Spiner />;
  
  // Показываем ошибку если есть
  if (slidesError || productsError) return <div>Ошибка загрузки товаров</div>;

  // Определяем, нужно ли показывать слайдер (есть ли слайды)
  const shouldShowSlider = sliderSlides && sliderSlides.length > 0;

  return (
    <div className={styles.categoryPage}>
      {/* Слайдер - получает данные через Redux (useAppSelector) */}
      {shouldShowSlider && <Slider />}
      
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
