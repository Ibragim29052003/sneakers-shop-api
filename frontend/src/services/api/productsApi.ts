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
  search?: string;       // поиск по названию
  ordering?: string;     // сортировка (например: "price" или "-price")
  page?: number;         // номер страницы (пагинация)
  page_size?: number;    // количество элементов на странице
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
      query: (params) => ({
        url: '/products/',
        params: {
          ...params,
          is_active: true,
        },
      }),
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

    /**
     * АВТОРИЗАЦИЯ (LOGIN)
     * 
     * builder.mutation - создаёт эндпоинт для изменения данных (POST, PUT, DELETE)
     * 
     * Использование:
     * const [login] = useLoginMutation()
     * login({ username: 'user', password: 'pass' })
     */
    login: builder.mutation<
      { access: string; refresh: string },  // тип успешного ответа
      { username: string; password: string } // тип аргументов
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
      { id: number; email: string; username: string },
      { email: string; username: string; password: string }
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
  }),
});

// Автоматически сгенерированные хуки
// Имена формируются: use + {НазваниеЭндпоинта} + Query/Mutation
export const {
  useGetProductsQuery,           // для getProducts
  useGetFilteredProductsQuery,    // для getFilteredProducts
  useGetProductByIdQuery,        // для getProductById
  useGetCategoriesQuery,         // для getCategories
  useGetCategoryByIdQuery,       // для getCategoryById
  useGetFiltersByCategoryQuery,  // для getFiltersByCategory
  useGetSliderSlidesQuery,       // для getSliderSlides (все слайды)
  useGetActiveSliderSlidesQuery, // для getActiveSliderSlides
  useCreateSliderSlideMutation,  // для createSliderSlide
  useUpdateSliderSlideMutation,  // для updateSliderSlide
  useDeleteSliderSlideMutation,  // для deleteSliderSlide
  useLoginMutation,              // для login
  useRegisterMutation,           // для register
  useRefreshTokenMutation,       // для refreshToken
} = productsApi;
