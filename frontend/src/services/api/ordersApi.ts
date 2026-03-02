import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// ==================== ТИПЫ ДАННЫХ ====================

// Статус заказа
export interface OrderStatus {
  id: number;
  name: string;
  description: string;
  is_final: boolean;
  created_at: string;
}

// Товар в заказе
export interface OrderItem {
  id: number;
  product: number | null;
  product_name: string;
  product_sku: string;
  price: string;
  quantity: number;
  get_total_price: string;
  created_at: string;
}

// Заказ
export interface Order {
  id: number;
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
  status: number;
  status_info: OrderStatus;
  total: string;
  total_display: string;
  shipping_address: string;
  notes: string;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

// ==================== API СЕРВИС ====================

export const ordersApi = createApi({
  reducerPath: 'ordersApi',
  
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/v1',
    
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('access_token');
      
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      
      return headers;
    },
  }),
  
  endpoints: (builder) => ({
    // Получить все заказы (для менеджеров)
    getManagerOrders: builder.query<Order[], void>({
      query: () => '/manager-orders/',
    }),
    
    // Получить статусы заказов
    getOrderStatuses: builder.query<OrderStatus[], void>({
      query: () => '/order-statuses/',
      transformResponse: (response: { results: OrderStatus[] }) => response.results,
    }),
  }),
});

// Автоматически сгенерированные хуки
export const {
  useGetManagerOrdersQuery,
  useGetOrderStatusesQuery,
} = ordersApi;
