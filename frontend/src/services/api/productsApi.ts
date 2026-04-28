import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// ТИПЫ ДАННЫХ (соответствуют Django моделям)

// Категория товара
export interface Category {
  id: number;
  name: string;
  description: string;
  parent: number | null;
  parent_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  subcategories_count: number;
}

// Изображение товара
export interface ProductImage {
  id: number;
  image: string;        // URL изображения
  product?: number;
  is_main: boolean;     // является ли главным
  alt_text: string;
  created_at: string;
}

// Основная модель товара
export interface Product {
  id: number;
  name: string;
  description: string;
  price: string;        // Цена в виде строки (decimal в Python)
  old_price: string | null;  // Старая цена для отображения скидки
  sku: string;          // Артикул
  is_active: boolean;
  created_at: string;
  updated_at: string;
  categories: Category[];
  images: ProductImage[];
  main_image_url: string | null;  // URL главного изображения
  external_url: string | null;
  supplier: number | null;  // ID поставщика
  supplier_name: string | null;  // Имя поставщика
  published_pages: string[];  // Страницы для публикации (women, men, children)
}

export interface ShowcaseProduct extends Product {
  sold_quantity: number;
}

export interface HomeShowcaseBlock {
  title: string;
  description: string;
  items: ShowcaseProduct[];
  based_on_sales?: boolean;
}

export interface HomeShowcasesResponse {
  category: string | null;
  premium: HomeShowcaseBlock;
  bestsellers: HomeShowcaseBlock;
}

// Модель слайда для слайдера
export interface SliderSlide {
  id: number;
  title: string;
  description: string;
  image_url: string | null;
  product: number | null;
  product_name: string | null;
  product_price: string | null;
  price: string | null;
  old_price: string | null;
  link: string | null;
  is_active: boolean;
  order: number;
  created_at: string;
  updated_at: string;
}

// Опция фильтра
export interface FilterOption {
  id: number;
  name: string;
  is_active: boolean;
  order: number;
}

// Группа фильтров
export interface FilterGroup {
  id: number;
  name: string;
  options: FilterOption[];
  order: number;
}

// Группа фильтров с счетчиками (для динамических счетчиков)
export interface FilterOptionWithCount {
  id: number;
  name: string;
  order: number;
  count: number;  // Количество товаров с этим фильтром
}

export interface FilterGroupWithCounts {
  id: number;
  name: string;
  order: number;
  options: FilterOptionWithCount[];
}

// Параметры для запроса фильтров с счетчиками
export interface FilterGroupCountsParams {
  category: string;
  filters?: {
    colors?: string[];
    sizes?: string[];
    fabrics?: string[];
  };
  minPrice?: number;
  maxPrice?: number;
}

// Ответ с пагинацией от Django REST Framework
export interface ProductsResponse {
  count: number;         // общее количество товаров
  next: string | null;  // URL следующей страницы
  previous: string | null; // URL предыдущей страницы
  results: Product[];    // массив товаров
}

// Параметры для фильтрации товаров
export interface FilterParams {
  category?: string;     // фильтр по категории
  min_price?: number;    // минимальная цена
  max_price?: number;    // максимальная цена
  price__gte?: number;   // минимальная цена (django-filter)
  price__lte?: number;   // максимальная цена (django-filter)
  search?: string;       // поиск по названию
  ordering?: string;     // сортировка (например: "price" или "-price")
  page?: number;         // номер страницы (пагинация)
  page_size?: number;    // количество элементов на странице
  // Фильтры
  colors?: string[];     // массив цветов
  sizes?: string[];      // массив размеров
  fabrics?: string[];    // массив материалов
}

/**
 * СОЗДАНИЕ API СЕРВИСА
 * 
 * createApi - создаёт API сервис RTK Query
 * fetchBaseQuery - базовый запрос (использует fetch под капотом)
 */
export const productsApi = createApi({
  // Путь в Redux store где будут храниться данные
  reducerPath: 'productsApi',
  
  // Базовый URL и настройки запроса
  baseQuery: fetchBaseQuery({
    // Все запросы будут к /api/v1 (прокси перенаправит на localhost:8000)
    baseUrl: '/api/v1',
    
    // Подготовка заголовков каждого запроса
    prepareHeaders: (headers) => {
      // Получаем токен из localStorage (где мы его сохраняем после логина)
      const token = localStorage.getItem('access_token');
      
      // Если токен есть - добавляем в заголовки
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      
      return headers;
    },
  }),
  
  // Определение эндпоинтов API
  endpoints: (builder) => ({
    /**
     * ПОЛУЧИТЬ ВСЕ ТОВАРЫ
     * 
     * builder.query - создаёт эндпоинт для получения данных (GET запрос)
     * 
     * Использование в компоненте:
     * const { data, isLoading, error } = useGetProductsQuery({ page: 1 })
     */
    getProducts: builder.query<ProductsResponse, FilterParams>({
      // Формирование URL запроса
      query: (params) => ({
        url: '/products/',
        params: {
          ...params,
          // Django по умолчанию возвращает все товары, включая неактивные
          // Добавляем is_active=true чтобы получить только активные
          is_active: true,
        },
      }),
    }),

    /**
     * ПОЛУЧИТЬ ОТФИЛЬТРОВАННЫЕ ТОВАРЫ
     * 
     * Тоже самое что getProducts, но возвращает только массив results
     * (удобнее для компонентов которые не нуждаются в пагинации)
     */
    getFilteredProducts: builder.query<Product[], FilterParams>({
      query: (params) => {
        // Формируем URL параметры
        const queryParams: Record<string, string | number | boolean | undefined> = {
          is_active: true,
        };
        
        // Добавляем параметры если они есть
        if (params.category) queryParams.category = params.category;
        if (params.min_price) queryParams.min_price = params.min_price;
        if (params.max_price) queryParams.max_price = params.max_price;
        if (params.price__gte !== undefined) queryParams.price__gte = params.price__gte;
        if (params.price__lte !== undefined) queryParams.price__lte = params.price__lte;
        if (params.search) queryParams.search = params.search;
        if (params.ordering) queryParams.ordering = params.ordering;
        if (params.page) queryParams.page = params.page;
        if (params.page_size) queryParams.page_size = params.page_size;
        
        // Преобразуем массивы фильтров в строку через запятую
        if (params.colors && params.colors.length > 0) {
          queryParams.colors = params.colors.join(',');
        }
        if (params.sizes && params.sizes.length > 0) {
          queryParams.sizes = params.sizes.join(',');
        }
        if (params.fabrics && params.fabrics.length > 0) {
          queryParams.fabrics = params.fabrics.join(',');
        }
        
        return {
          url: '/products/',
          params: queryParams,
        };
      },
      // Трансформируем ответ - берём только results из пагинированного ответа
      transformResponse: (response: ProductsResponse) => response.results,
    }),

    /**
     * ПОЛУЧИТЬ ТОВАР ПО ID
     * 
     * Использование:
     * const { data } = useGetProductByIdQuery(123)
     */
    getProductById: builder.query<Product, number>({
      query: (id) => `/products/${id}/`,
    }),

    /**
     * СОЗДАТЬ ТОВАР
     * 
     * Использование:
     * const [createProduct] = useCreateProductMutation()
     * createProduct({ name: 'Товар', price: '1000', published_pages: ['women', 'men'], categories_ids: [1, 2] })
     */
    createProduct: builder.mutation<Product, {
      name: string;
      description?: string;
      price: string;
      old_price?: string | null;
      sku?: string;
      status?: 'draft' | 'active' | 'archived' | 'out_of_stock';
      is_active?: boolean;
      published_pages?: string[];
      categories_ids?: number[];
      image_urls?: string[];  // Добавлено поле для URL изображений
    }>({
      query: (product) => ({
        url: '/products/',
        method: 'POST',
        body: product,
      }),
    }),

    updateProduct: builder.mutation<Product, {
      id: number;
      product: {
        name?: string;
        description?: string;
        price?: string;
        old_price?: string | null;
        sku?: string;
        is_active?: boolean;
        published_pages?: string[];
        categories_ids?: number[];
        image_urls?: string[];
      };
    }>({
      query: ({ id, product }) => ({
        url: `/products/${id}/`,
        method: 'PATCH',
        body: product,
      }),
    }),

    deleteProduct: builder.mutation<void, number>({
      query: (id) => ({
        url: `/products/${id}/`,
        method: 'DELETE',
      }),
    }),

    uploadProductImage: builder.mutation<ProductImage, {
      product: number;
      imageFile: File;
      is_main?: boolean;
      alt_text?: string;
    }>({
      query: ({ product, imageFile, is_main = false, alt_text = '' }) => {
        const formData = new FormData();
        formData.append('product', String(product));
        formData.append('image_file', imageFile);
        formData.append('is_main', String(is_main));
        formData.append('alt_text', alt_text);

        return {
          url: '/product-images/',
          method: 'POST',
          body: formData,
        };
      },
    }),

    deleteProductImage: builder.mutation<void, number>({
      query: (id) => ({
        url: `/product-images/${id}/`,
        method: 'DELETE',
      }),
    }),

    /**
     * ПОЛУЧИТЬ КАТЕГОРИИ
     * 
     * Использование:
     * const { data } = useGetCategoriesQuery()
     */
    getCategories: builder.query<Category[], void>({
      query: () => '/categories/',
      transformResponse: (response: { results: Category[] }) => response.results,
    }),

    /**
     * ПОЛУЧИТЬ КАТЕГОРИЮ ПО ID
     */
    getCategoryById: builder.query<Category, number>({
      query: (id) => `/categories/${id}/`,
    }),

    /**
     * ПОЛУЧИТЬ ФИЛЬТРЫ ПО КАТЕГОРИИ
     * 
     * Использование:
     * const { data } = useGetFiltersByCategoryQuery('children')
     */
    getFiltersByCategory: builder.query<FilterGroup[], string>({
      query: (category) => `/filter-groups/by_category/?category=${category}`,
    }),

    /**
     * ПОЛУЧИТЬ ФИЛЬТРЫ С СЧЕТЧИКАМИ
     * 
     * Возвращает фильтры с подсчетом количества товаров для каждой опции.
     * Счетчики учитывают уже выбранные фильтры.
     * 
     * Использование:
     * const { data } = useGetFiltersWithCountsQuery({ category: 'women', filters: { colors: ['Красный'], sizes: ['XL'] } })
     */
    getFiltersWithCounts: builder.query<FilterGroupWithCounts[], FilterGroupCountsParams>({
      query: (params) => {
        const urlParams = new URLSearchParams();
        urlParams.append('category', params.category);
        
        // Добавляем выбранные фильтры
        if (params.filters) {
          if (params.filters.colors && params.filters.colors.length > 0) {
            urlParams.append('colors', params.filters.colors.join(','));
          }
          if (params.filters.sizes && params.filters.sizes.length > 0) {
            urlParams.append('sizes', params.filters.sizes.join(','));
          }
          if (params.filters.fabrics && params.filters.fabrics.length > 0) {
            urlParams.append('fabrics', params.filters.fabrics.join(','));
          }
        }
        
        // Ценовой диапазон
        if (params.minPrice !== undefined) {
          urlParams.append('min_price', params.minPrice.toString());
        }
        if (params.maxPrice !== undefined) {
          urlParams.append('max_price', params.maxPrice.toString());
        }
        
        return `/filter-groups/with_counts/?${urlParams.toString()}`;
      },
    }),

    // Получить все слайды (для админки)
    getSliderSlides: builder.query<SliderSlide[], void>({
      query: () => '/slider/',
    }),

    // Создать слайд
    createSliderSlide: builder.mutation<SliderSlide, Partial<SliderSlide>>({
      query: (slide) => ({
        url: '/slider/',
        method: 'POST',
        body: slide,
      }),
    }),

    // Обновить слайд
    updateSliderSlide: builder.mutation<SliderSlide, { id: number; slide: Partial<SliderSlide> }>({
      query: ({ id, slide }) => ({
        url: `/slider/${id}/`,
        method: 'PATCH',
        body: slide,
      }),
    }),

    // Удалить слайд
    deleteSliderSlide: builder.mutation<void, number>({
      query: (id) => ({
        url: `/slider/${id}/`,
        method: 'DELETE',
      }),
    }),

    /**
     * ПОЛУЧИТЬ АКТИВНЫЕ СЛАЙДЫ ДЛЯ СЛАЙДЕРА
     * 
     * Использование:
     * const { data } = useGetActiveSliderSlidesQuery()
     */
    getActiveSliderSlides: builder.query<SliderSlide[], void>({
      query: () => '/slider/active-slides/',
    }),

    getHomeShowcases: builder.query<HomeShowcasesResponse, string>({
      query: (category) => ({
        url: '/products/home-showcases/',
        params: {
          category,
          limit: 4,
        },
      }),
    }),

    /**
     * АВТОРИЗАЦИЯ (LOGIN)
     * 
     * builder.mutation - создаёт эндпоинт для изменения данных (POST, PUT, DELETE)
     * 
     * Использование:
     * const [login] = useLoginMutation()
     * login({ email: 'user@test.com', password: 'pass' })
     */
    login: builder.mutation<
      { access: string; refresh: string; user: any },
      { email: string; password: string }
    >({
      query: (credentials) => ({
        url: '/auth/login/',
        method: 'POST',
        body: credentials,
      }),
    }),

    /**
     * РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ
     */
    register: builder.mutation<
      { id: number; email: string; first_name: string },
      { email: string; password: string; password_confirm: string; first_name?: string }
    >({
      query: (userData) => ({
        url: '/auth/register/',
        method: 'POST',
        body: userData,
      }),
    }),

    /**
     * ОБНОВЛЕНИЕ ТОКЕНА
     * 
     * Используется когда access токен истёк
     */
    refreshToken: builder.mutation<
      { access: string },
      { refresh: string }
    >({
      query: (refreshData) => ({
        url: '/auth/refresh/',
        method: 'POST',
        body: refreshData,
      }),
    }),

    /**
     * ПОЛУЧИТЬ КОРЗИНУ ПОЛЬЗОВАТЕЛЯ
     * 
     * Возвращает корзину авторизованного пользователя с сервера
     * 
     * Использование:
     * const { data } = useGetUserCartQuery()
     */
    getUserCart: builder.query<{
      id: number;
      items: Array<{
        id: number;
        product: {
          id: number;
          name: string;
          price: string;
          old_price: string | null;
          main_image_url: string | null;
        };
        quantity: number;
        total_price: string;
      }>;
      total_items: number;
      total_price: string;
    }, void>({
      query: () => '/cart/',
    }),
  }),
});

// Автоматически сгенерированные хуки
// Имена формируются: use + {НазваниеЭндпоинта} + Query/Mutation
export const {
  useGetProductsQuery,           // для getProducts
  useGetFilteredProductsQuery,    // для getFilteredProducts
  useGetProductByIdQuery,        // для getProductById
  useCreateProductMutation,      // для createProduct
  useUpdateProductMutation,      // для updateProduct
  useDeleteProductMutation,      // для deleteProduct
  useUploadProductImageMutation, // для uploadProductImage
  useDeleteProductImageMutation, // для deleteProductImage
  useGetCategoriesQuery,         // для getCategories
  useGetCategoryByIdQuery,       // для getCategoryById
  useGetFiltersByCategoryQuery,  // для getFiltersByCategory
  useGetFiltersWithCountsQuery,   // для getFiltersWithCounts
  useGetSliderSlidesQuery,       // для getSliderSlides (все слайды)
  useGetActiveSliderSlidesQuery, // для getActiveSliderSlides
  useGetHomeShowcasesQuery,      // для getHomeShowcases
  useCreateSliderSlideMutation,  // для createSliderSlide
  useUpdateSliderSlideMutation,  // для updateSliderSlide
  useDeleteSliderSlideMutation,  // для deleteSliderSlide
  useLoginMutation,              // для login
  useRegisterMutation,           // для register
  useRefreshTokenMutation,       // для refreshToken
  useGetUserCartQuery,           // для getUserCart
} = productsApi;
