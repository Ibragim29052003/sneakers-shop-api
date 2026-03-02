import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// ==================== ТИПЫ ДАННЫХ ====================

// Поставщик
export interface Supplier {
  id: number;
  name: string;
  inn: string;
  kpp: string;
  ogrn: string;
  legal_address: string;
  actual_address: string;
  phone: string;
  email: string;
  website: string;
  contact_person: string;
  contact_phone: string;
  notes: string;
  is_active: boolean;
  user: number | null;
  user_email: string | null;
  created_at: string;
  updated_at: string;
  contracts_count?: number;
  products_count?: number;
}

// Регистрация поставщика (создание нового пользователя и поставщика)
export interface RegisterSupplierData {
  name: string;
  inn?: string;
  kpp?: string;
  ogrn?: string;
  legal_address?: string;
  actual_address?: string;
  phone?: string;
  email: string;
  website?: string;
  contact_person?: string;
  contact_phone?: string;
  password: string;
  notes?: string;
}

// Упрощённая регистрация: компания + товар в одной форме
export interface RegisterSupplierWithRequestData {
  // Данные компании
  name: string;
  email: string;
  password: string;
  contact_person?: string;
  phone?: string;
  inn?: string;
  kpp?: string;
  ogrn?: string;
  legal_address?: string;
  actual_address?: string;
  website?: string;
  notes?: string;
  // Данные товара
  product_name: string;
  product_sku?: string;
  product_description?: string;
  quantity?: number;
  suggested_price?: number;
  product_notes?: string;
}

// Ответ после регистрации с заявкой
export interface RegisterSupplierWithRequestResponse {
  supplier: Supplier;
  product_request: SupplierProductRequest;
  message: string;
}

// Заявка на регистрацию поставщика (от существующего пользователя)
export interface ApplySupplierData {
  name: string;
  inn?: string;
  kpp?: string;
  ogrn?: string;
  legal_address?: string;
  actual_address?: string;
  phone?: string;
  email?: string;
  website?: string;
  contact_person?: string;
  contact_phone?: string;
  notes?: string;
}

// Статус заявки
export interface RequestStatus {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
}

// Статус договора
export interface ContractStatus {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
}

// Тип документа
export interface DocumentType {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

// Тип уведомления
export interface AlertType {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

// Источник товара
export interface ProductSupplierSource {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

// Договор с поставщиком
export interface SupplierContract {
  id: number;
  supplier: number;
  supplier_name: string;
  status: number;
  status_name: string;
  contract_number: string;
  title: string;
  description: string;
  start_date: string;
  end_date: string;
  total_amount: string | null;
  notes: string;
  is_auto_renew: boolean;
  created_at: string;
  updated_at: string;
  documents_count: number;
  products_count: number;
  is_expiring_soon: boolean;
  is_expired: boolean;
}

// Заявка на поставку товара
export interface SupplierProductRequest {
  id: number;
  supplier: number;
  supplier_name: string;
  status: number;
  status_name: string;
  category: string;
  product_name: string;
  product_sku: string;
  product_description: string;
  product_images: string[];
  quantity: number;
  suggested_price: string | null;
  suggested_old_price: string | null;
  notes: string;
  reviewed_by: number | null;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  review_comment: string;
  manager: number | null;
  manager_name: string | null;
  created_at: string;
  updated_at: string;
  documents_count: number;
}

// Создание заявки
export interface CreateSupplierRequest {
  supplier: number;
  category?: string;
  product_name: string;
  product_sku?: string;
  product_description?: string;
  product_images?: string[];
  quantity: number;
  suggested_price?: number;
  suggested_old_price?: number;
  notes?: string;
}

// Управление заявкой (одобрение/отклонение)
export interface ManageSupplierRequest {
  status: number;
  review_comment?: string;
}

// Документ заявки
export interface RequestDocument {
  id: number;
  request: number;
  document_type: number;
  document_type_name: string;
  file: string;
  file_name: string;
  description: string;
  uploaded_at: string;
  uploaded_by: number;
  uploaded_by_name: string;
}

// Товар поставщика
export interface SupplierProduct {
  id: number;
  supplier: number;
  supplier_name: string;
  product: number;
  product_name: string;
  contract: number | null;
  contract_number: string | null;
  supplier_sku: string;
  supplier_price: string | null;
  is_preferred: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}

// Системное уведомление
export interface SystemAlert {
  id: number;
  alert_type: number;
  alert_type_name: string;
  user: number;
  user_email: string;
  title: string;
  message: string;
  is_read: boolean;
  read_by: number | null;
  read_by_email: string | null;
  read_at: string | null;
  contract: number | null;
  contract_number: string | null;
  request: number | null;
  request_info: {
    id: number;
    product_name: string;
    supplier_name: string;
  } | null;
  created_at: string;
}

// Параметры фильтрации заявок
export interface RequestFilterParams {
  supplier?: number;
  status?: number;
  search?: string;
  page?: number;
  page_size?: number;
}

// Коммуникация по заявке
export interface RequestCommunication {
  id: number;
  request: number;
  request_info: {
    id: number;
    product_name: string;
    supplier_name: string;
    status: string;
  };
  sender: number | null;
  sender_email: string | null;
  direction: 'manager' | 'supplier';
  message: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

// Создание сообщения
export interface CreateCommunication {
  request: number;
  message: string;
}

// Создание договора
export interface CreateContract {
  supplier: number;
  contract_number: string;
  title: string;
  description?: string;
  start_date: string;
  end_date: string;
  total_amount?: number;
  notes?: string;
  status?: number;
  is_auto_renew?: boolean;
}

// ==================== API СЕРВИС ====================

export const suppliersApi = createApi({
  reducerPath: 'suppliersApi',
  
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
    // ==================== ПОСТАВЩИКИ ====================
    
    // Получить всех поставщиков
    getSuppliers: builder.query<Supplier[], void>({
      query: () => '/suppliers/',
      transformResponse: (response: { results: Supplier[] }) => response.results,
    }),
    
    // Получить поставщика по ID
    getSupplierById: builder.query<Supplier, number>({
      query: (id) => `/suppliers/${id}/`,
    }),
    
    // Получить профиль поставщика текущего пользователя
    getMySupplierProfile: builder.query<Supplier, void>({
      query: () => '/my-supplier-profile/',
    }),
    
    // Зарегистрировать нового поставщика (публичный эндпоинт)
    registerSupplier: builder.mutation<Supplier, RegisterSupplierData>({
      query: (data) => ({
        url: '/register-supplier/',
        method: 'POST',
        body: data,
      }),
    }),
    
    // Упрощённая регистрация: компания + заявка на товар
    registerSupplierWithRequest: builder.mutation<RegisterSupplierWithRequestResponse, RegisterSupplierWithRequestData>({
      query: (data) => ({
        url: '/register-supplier-with-request/',
        method: 'POST',
        body: data,
      }),
    }),
    
    // Подать заявку на регистрацию поставщика (от существующего пользователя)
    applySupplier: builder.mutation<Supplier, ApplySupplierData>({
      query: (data) => ({
        url: '/apply-supplier/',
        method: 'POST',
        body: data,
      }),
    }),
    
    // ==================== ЗАЯВКИ НА ПОСТАВКУ ====================
    
    // Получить все заявки на поставку
    getSupplierRequests: builder.query<SupplierProductRequest[], RequestFilterParams>({
      query: (params) => {
        const queryParams: Record<string, string | number | undefined> = {};
        
        if (params.supplier) queryParams.supplier = params.supplier;
        if (params.status) queryParams.status = params.status;
        if (params.search) queryParams.search = params.search;
        if (params.page) queryParams.page = params.page;
        if (params.page_size) queryParams.page_size = params.page_size;
        
        return {
          url: '/supplier-requests/',
          params: queryParams,
        };
      },
      transformResponse: (response: { results: SupplierProductRequest[] }) => response.results,
    }),
    
    // Получить заявку по ID
    getSupplierRequestById: builder.query<SupplierProductRequest, number>({
      query: (id) => `/supplier-requests/${id}/`,
    }),
    
    // Создать заявку на поставку
    createSupplierRequest: builder.mutation<SupplierProductRequest, CreateSupplierRequest>({
      query: (request) => ({
        url: '/supplier-requests/',
        method: 'POST',
        body: request,
      }),
    }),
    
    // Обновить заявку (управление - одобрение/отклонение)
    updateSupplierRequest: builder.mutation<SupplierProductRequest, { id: number; data: ManageSupplierRequest }>({
      query: ({ id, data }) => ({
        url: `/supplier-requests/${id}/`,
        method: 'PATCH',
        body: data,
      }),
    }),
    
    // Назначить менеджера заявки
    assignManager: builder.mutation<{ detail: string }, { requestId: number; managerId: number }>({
      query: ({ requestId, managerId }) => ({
        url: `/supplier-requests/${requestId}/assign-manager/`,
        method: 'POST',
        body: { manager_id: managerId },
      }),
    }),
    
    // Создать товар поставщика из заявки
    createProductFromRequest: builder.mutation<SupplierProduct, { requestId: number; product: number }>({
      query: ({ requestId, product }) => ({
        url: `/supplier-requests/${requestId}/create-product/`,
        method: 'POST',
        body: { product },
      }),
    }),
    
    // ==================== СТАТУСЫ ====================
    
    // Получить все статусы заявок
    getRequestStatuses: builder.query<RequestStatus[], void>({
      query: () => '/request-statuses/',
      transformResponse: (response: { results: RequestStatus[] }) => response.results,
    }),
    
    // ==================== УВЕДОМЛЕНИЯ ====================
    
    // Получить уведомления текущего пользователя
    getUserAlerts: builder.query<{
      count: number;
      unread_count: number;
      alerts: SystemAlert[];
    }, void>({
      query: () => '/my-alerts/',
    }),
    
    // Отметить уведомление как прочитанное
    markAlertAsRead: builder.mutation<SystemAlert, number>({
      query: (id) => ({
        url: `/system-alerts/${id}/`,
        method: 'PATCH',
        body: { is_read: true },
      }),
    }),
    
    // Отметить все уведомления как прочитанные
    markAllAlertsAsRead: builder.mutation<{ detail: string }, void>({
      query: () => ({
        url: '/my-alerts/',
        method: 'POST',
      }),
    }),
    
    // ==================== ДОГОВОРЫ ====================
    
    // Получить все договоры
    getSupplierContracts: builder.query<SupplierContract[], { supplier?: number; status?: number; expiring_soon?: boolean }>({
      query: (params) => {
        const queryParams: Record<string, string | number | undefined> = {};
        if (params.supplier) queryParams.supplier = params.supplier;
        if (params.status) queryParams.status = params.status;
        if (params.expiring_soon) queryParams.expiring_soon = 'true';
        return {
          url: '/supplier-contracts/',
          params: queryParams,
        };
      },
      transformResponse: (response: { results: SupplierContract[] }) => response.results,
    }),
    
    // ==================== ТОВАРЫ ПОСТАВЩИКОВ ====================
    
    // Получить товары поставщиков
    getSupplierProducts: builder.query<SupplierProduct[], { supplier?: number; product?: number }>({
      query: (params) => {
        const queryParams: Record<string, string | number | undefined> = {};
        if (params.supplier) queryParams.supplier = params.supplier;
        if (params.product) queryParams.product = params.product;
        return {
          url: '/supplier-products/',
          params: queryParams,
        };
      },
      transformResponse: (response: { results: SupplierProduct[] }) => response.results,
    }),
    
    // ==================== КОММУНИКАЦИИ ====================
    
    // Получить все коммуникации
    getCommunications: builder.query<RequestCommunication[], { request?: number; direction?: string }>({
      query: (params) => {
        const queryParams: Record<string, string | number | undefined> = {};
        if (params.request) queryParams.request = params.request;
        if (params.direction) queryParams.direction = params.direction;
        return {
          url: '/request-communications/',
          params: queryParams,
        };
      },
      transformResponse: (response: { results: RequestCommunication[] }) => response.results,
    }),
    
    // Получить коммуникации по заявке
    getCommunicationsByRequest: builder.query<RequestCommunication[], number>({
      query: (requestId) => `/supplier-requests/${requestId}/communications/`,
    }),
    
    // Отправить сообщение
    createCommunication: builder.mutation<RequestCommunication, CreateCommunication>({
      query: (data) => ({
        url: '/request-communications/',
        method: 'POST',
        body: data,
      }),
    }),
    
    // Отметить сообщение как прочитанное
    markCommunicationAsRead: builder.mutation<{ detail: string }, number>({
      query: (id) => ({
        url: `/communications/${id}/mark-read/`,
        method: 'POST',
      }),
    }),
    
    // Загрузить изображение товара
    uploadProductImage: builder.mutation<{ url: string; file_name: string }, FormData>({
      query: (formData) => ({
        url: '/upload-product-image/',
        method: 'POST',
        body: formData,
      }),
    }),
    
    // Получить список менеджеров
    getManagers: builder.query<{
      id: number;
      email: string;
      first_name: string;
      last_name: string;
      is_active: boolean;
    }[], void>({
      query: () => '/managers/',
    }),
    
    // ==================== ДОГОВОРЫ ПОСТАВЩИКА ====================
    
    // Получить свои договоры (для поставщика)
    getMyContracts: builder.query<SupplierContract[], void>({
      query: () => '/my-contracts/',
      transformResponse: (response: SupplierContract[]) => response,
    }),
    
    // Получить истекающие договоры
    getExpiringContracts: builder.query<{
      count: number;
      contracts: SupplierContract[];
      days_until_expiration: number;
    }, void>({
      query: () => '/expiring-contracts/',
    }),
    
    // Обработать истекшие договоры (только админ)
    handleExpiredContracts: builder.mutation<{
      processed_contracts: number;
      results: Array<{
        contract_id: number;
        contract_number: string;
        supplier_name: string;
        affected_products_count: number;
        affected_products: string[];
      }>;
    }, void>({
      query: () => ({
        url: '/handle-expired-contracts/',
        method: 'POST',
      }),
    }),
    
    // Создать договор с поставщиком
    createContract: builder.mutation<SupplierContract, CreateContract>({
      query: (data) => ({
        url: '/create-contract/',
        method: 'POST',
        body: data,
      }),
    }),
  }),
});

// Автоматически сгенерированные хуки
export const {
  // Поставщики
  useGetSuppliersQuery,
  useGetSupplierByIdQuery,
  useGetMySupplierProfileQuery,
  useRegisterSupplierMutation,
  useRegisterSupplierWithRequestMutation,
  useApplySupplierMutation,
  
  // Заявки
  useGetSupplierRequestsQuery,
  useGetSupplierRequestByIdQuery,
  useCreateSupplierRequestMutation,
  useUpdateSupplierRequestMutation,
  useAssignManagerMutation,
  useCreateProductFromRequestMutation,
  
  // Статусы
  useGetRequestStatusesQuery,
  
  // Уведомления
  useGetUserAlertsQuery,
  useMarkAlertAsReadMutation,
  useMarkAllAlertsAsReadMutation,
  
  // Договоры
  useGetSupplierContractsQuery,
  
  // Товары поставщиков
  useGetSupplierProductsQuery,
  
  // Коммуникации
  useGetCommunicationsQuery,
  useGetCommunicationsByRequestQuery,
  useCreateCommunicationMutation,
  useMarkCommunicationAsReadMutation,
  
  // Загрузка изображений
  useUploadProductImageMutation,
  
  // Менеджеры
  useGetManagersQuery,
  
  // Договоры поставщика
  useGetMyContractsQuery,
  useGetExpiringContractsQuery,
  useHandleExpiredContractsMutation,
  useCreateContractMutation,
} = suppliersApi;
