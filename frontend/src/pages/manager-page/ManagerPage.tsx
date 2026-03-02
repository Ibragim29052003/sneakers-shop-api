import { useState, useMemo } from 'react';
import { useGetSupplierRequestsQuery, useUpdateSupplierRequestMutation, useGetSupplierProductsQuery, useAssignManagerMutation, useGetManagersQuery, useGetSupplierContractsQuery, useGetSuppliersQuery, useCreateContractMutation } from '@/services/api/suppliersApi';
import { useCreateProductMutation, useGetCategoriesQuery } from '@/services/api/productsApi';
import { useGetManagerOrdersQuery } from '@/services/api/ordersApi';
import type { SupplierProductRequest, SupplierContract, Supplier, SupplierProduct } from '@/services/api/suppliersApi';
import type { Order } from '@/services/api/ordersApi';
import styles from './ManagerPage.module.scss';

type TabType = 'dashboard' | 'my-requests' | 'all-requests';

// Доступные страницы для публикации товара
const PUBLISH_PAGES = [
  { value: 'women', label: 'Женщинам', categoryNames: ['женщин', 'women', 'woman', 'женская', 'для женщин'] },
  { value: 'men', label: 'Мужчинам', categoryNames: ['мужчин', 'men', 'man', 'мужская', 'для мужчин'] },
  { value: 'children', label: 'Детям', categoryNames: ['детей', 'children', 'child', 'детская', 'для детей'] },
];

interface ContractFormData {
  supplier: number | '';
  contract_number: string;
  title: string;
  description: string;
  start_date: string;
  end_date: string;
  total_amount: string;
  notes: string;
  is_auto_renew: boolean;
}

interface ProductFormData {
  name: string;
  description: string;
  price: string;
  oldPrice: string;
  SKU: string;
  isPublished: boolean;
  category: string;
  publishedPages: string[];
}

// Компонент Дашборд
interface DashboardTabProps {
  contracts: SupplierContract[];
  expiringContracts: SupplierContract[];
  supplierProducts: SupplierProduct[];
  requests: SupplierProductRequest[];
  suppliers: Supplier[];
  orders: Order[];
  onCreateContract: () => void;
}

const DashboardTab = ({ contracts, expiringContracts, supplierProducts, requests, suppliers, orders, onCreateContract }: DashboardTabProps) => {
  // Подсчёт статистики
  const activeContracts = contracts.filter(c => c.status_name === 'active');
  const pendingRequests = requests.filter(r => r.status_name === 'pending' || r.status_name === 'under_review');
  const approvedRequests = requests.filter(r => r.status_name === 'approved');
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };
  
  const formatCurrency = (value: string | null) => {
    if (!value) return '—';
    return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(Number(value));
  };
  
  return (
    <div className={styles.dashboard}>
      {/* Карточки статистики */}
      <div className={styles.dashboardStats}>
        <div className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>{activeContracts.length}</span>
            <span className={styles.statLabel}>Активных договоров</span>
          </div>
        </div>
        
        <div className={`${styles.statCard} ${styles.statCardWarning}`}>
          <div className={styles.statIcon}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>{expiringContracts.length}</span>
            <span className={styles.statLabel}>Истекают скоро</span>
          </div>
        </div>
        
        <div className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <path d="M16 10a4 4 0 0 1-8 0"></path>
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>{supplierProducts.length}</span>
            <span className={styles.statLabel}>Товаров от поставщиков</span>
          </div>
        </div>
        
        <div className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>{pendingRequests.length}</span>
            <span className={styles.statLabel}>Новых заявок</span>
          </div>
        </div>
        
        <div className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>{suppliers.length}</span>
            <span className={styles.statLabel}>Поставщиков</span>
          </div>
        </div>
        
        <div className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="9" cy="21" r="1"></circle>
              <circle cx="20" cy="21" r="1"></circle>
              <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>{orders.length}</span>
            <span className={styles.statLabel}>Заказов</span>
          </div>
        </div>
      </div>
      
      {/* Секция истекающих договоров */}
      {expiringContracts.length > 0 && (
        <div className={styles.dashboardSection}>
          <h2 className={styles.dashboardSectionTitle}>Истекающие договоры (30 дней)</h2>
          <div className={styles.dashboardTable}>
            <table>
              <thead>
                <tr>
                  <th>Номер договора</th>
                  <th>Поставщик</th>
                  <th>Название</th>
                  <th>Дата окончания</th>
                  <th>Сумма</th>
                  <th>Статус</th>
                </tr>
              </thead>
              <tbody>
                {expiringContracts.map(contract => (
                  <tr key={contract.id}>
                    <td>{contract.contract_number}</td>
                    <td>{contract.supplier_name}</td>
                    <td>{contract.title}</td>
                    <td>{formatDate(contract.end_date)}</td>
                    <td>{formatCurrency(contract.total_amount)}</td>
                    <td>
                      <span className={styles.statusBadge} data-status={contract.status_name}>
                        {contract.status_name === 'active' && 'Активен'}
                        {contract.status_name === 'draft' && 'Черновик'}
                        {contract.status_name === 'suspended' && 'Приостановлен'}
                        {contract.status_name === 'expired' && 'Истёк'}
                        {contract.status_name === 'terminated' && 'Расторгнут'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Секция всех договоров */}
      <div className={styles.dashboardSection}>
        <div className={styles.dashboardSectionHeader}>
          <h2 className={styles.dashboardSectionTitle}>Все договоры с поставщиками</h2>
          <button 
            className={`${styles.button} ${styles.buttonPrimary}`}
            onClick={onCreateContract}
          >
            Создать договор
          </button>
        </div>
        {contracts.length === 0 ? (
          <div className={styles.emptyState}>
            <p>Договоров не найдено</p>
          </div>
        ) : (
          <div className={styles.dashboardTable}>
            <table>
              <thead>
                <tr>
                  <th>Номер договора</th>
                  <th>Поставщик</th>
                  <th>Название</th>
                  <th>Дата начала</th>
                  <th>Дата окончания</th>
                  <th>Сумма</th>
                  <th>Товаров</th>
                  <th>Статус</th>
                </tr>
              </thead>
              <tbody>
                {contracts.slice(0, 10).map(contract => (
                  <tr key={contract.id}>
                    <td>{contract.contract_number}</td>
                    <td>{contract.supplier_name}</td>
                    <td>{contract.title}</td>
                    <td>{formatDate(contract.start_date)}</td>
                    <td>{formatDate(contract.end_date)}</td>
                    <td>{formatCurrency(contract.total_amount)}</td>
                    <td>{contract.products_count}</td>
                    <td>
                      <span className={styles.statusBadge} data-status={contract.status_name}>
                        {contract.status_name === 'active' && 'Активен'}
                        {contract.status_name === 'draft' && 'Черновик'}
                        {contract.status_name === 'suspended' && 'Приостановлен'}
                        {contract.status_name === 'expired' && 'Истёк'}
                        {contract.status_name === 'terminated' && 'Расторгнут'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {contracts.length > 10 && (
              <p className={styles.dashboardNote}>Показано 10 из {contracts.length} договоров</p>
            )}
          </div>
        )}
      </div>
      
      {/* Секция товаров от поставщиков */}
      <div className={styles.dashboardSection}>
        <h2 className={styles.dashboardSectionTitle}>Товары от поставщиков</h2>
        {supplierProducts.length === 0 ? (
          <div className={styles.emptyState}>
            <p>Товаров не найдено</p>
          </div>
        ) : (
          <div className={styles.dashboardTable}>
            <table>
              <thead>
                <tr>
                  <th>Товар</th>
                  <th>Поставщик</th>
                  <th>Артикул поставщика</th>
                  <th>Цена поставщика</th>
                  <th>Договор</th>
                  <th>Предпочитаемый</th>
                </tr>
              </thead>
              <tbody>
                {supplierProducts.slice(0, 10).map(sp => (
                  <tr key={sp.id}>
                    <td>{sp.product_name}</td>
                    <td>{sp.supplier_name}</td>
                    <td>{sp.supplier_sku || '—'}</td>
                    <td>{formatCurrency(sp.supplier_price)}</td>
                    <td>{sp.contract_number || '—'}</td>
                    <td>
                      {sp.is_preferred ? (
                        <span className={styles.preferredBadge}>Да</span>
                      ) : (
                        <span>—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {supplierProducts.length > 10 && (
              <p className={styles.dashboardNote}>Показано 10 из {supplierProducts.length} товаров</p>
            )}
          </div>
        )}
      </div>
      
      {/* Секция заявок */}
      <div className={styles.dashboardSection}>
        <h2 className={styles.dashboardSectionTitle}>Заявки на поставку</h2>
        {requests.length === 0 ? (
          <div className={styles.emptyState}>
            <p>Заявок не найдено</p>
          </div>
        ) : (
          <div className={styles.dashboardTable}>
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Товар</th>
                  <th>Поставщик</th>
                  <th>Количество</th>
                  <th>Цена</th>
                  <th>Статус</th>
                  <th>Дата</th>
                </tr>
              </thead>
              <tbody>
                {requests.slice(0, 10).map(request => (
                  <tr key={request.id}>
                    <td>#{request.id}</td>
                    <td>{request.product_name}</td>
                    <td>{request.supplier_name}</td>
                    <td>{request.quantity}</td>
                    <td>{formatCurrency(request.suggested_price)}</td>
                    <td>
                      <span className={styles.statusBadge} data-status={request.status_name}>
                        {request.status_name === 'pending' && 'Ожидает'}
                        {request.status_name === 'under_review' && 'На рассмотрении'}
                        {request.status_name === 'approved' && 'Одобрена'}
                        {request.status_name === 'rejected' && 'Отклонена'}
                        {request.status_name === 'revision_required' && 'На доработке'}
                      </span>
                    </td>
                    <td>{formatDate(request.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {requests.length > 10 && (
              <p className={styles.dashboardNote}>Показано 10 из {requests.length} заявок</p>
            )}
          </div>
        )}
      </div>
      
      {/* Секция заказов */}
      <div className={styles.dashboardSection}>
        <h2 className={styles.dashboardSectionTitle}>Заказы</h2>
        {orders.length === 0 ? (
          <div className={styles.emptyState}>
            <p>Заказов не найдено</p>
          </div>
        ) : (
          <div className={styles.dashboardTable}>
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Покупатель</th>
                  <th>Статус</th>
                  <th>Сумма</th>
                  <th>Товаров</th>
                  <th>Дата</th>
                </tr>
              </thead>
              <tbody>
                {orders.slice(0, 10).map(order => (
                  <tr key={order.id}>
                    <td>#{order.id}</td>
                    <td>{order.user.first_name || order.user.last_name 
                      ? `${order.user.first_name} ${order.user.last_name}`.trim() 
                      : order.user.email}</td>
                    <td>
                      <span className={styles.statusBadge} data-status={order.status_info.name}>
                        {order.status_info.name}
                      </span>
                    </td>
                    <td>{formatCurrency(order.total)}</td>
                    <td>{order.items.length}</td>
                    <td>{formatDate(order.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {orders.length > 10 && (
              <p className={styles.dashboardNote}>Показано 10 из {orders.length} заказов</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const ManagerPage = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [selectedRequest, setSelectedRequest] = useState<SupplierProductRequest | null>(null);
  const [showProductForm, setShowProductForm] = useState(false);
  const [showAssignManager, setShowAssignManager] = useState<number | null>(null);
  const [selectedManagerId, setSelectedManagerId] = useState<number | null>(null);
  const [showContractForm, setShowContractForm] = useState(false);
  const [contractFormData, setContractFormData] = useState<ContractFormData>({
    supplier: '',
    contract_number: '',
    title: '',
    description: '',
    start_date: '',
    end_date: '',
    total_amount: '',
    notes: '',
    is_auto_renew: false,
  });
  const [productFormData, setProductFormData] = useState<ProductFormData>({
    name: '',
    description: '',
    price: '',
    oldPrice: '',
    SKU: '',
    isPublished: false,
    category: '',
    publishedPages: [],
  });
  
  // Получаем заявки
  const { data: requests = [], isLoading, error } = useGetSupplierRequestsQuery({});
  const { data: supplierProducts = [] } = useGetSupplierProductsQuery({});
  const { data: categories = [] } = useGetCategoriesQuery();
  
  // Получаем договоры
  const { data: allContracts = [] } = useGetSupplierContractsQuery({});
  const { data: expiringContracts = [] } = useGetSupplierContractsQuery({ expiring_soon: true });
  
  // Получаем поставщиков
  const { data: suppliers = [] } = useGetSuppliersQuery();
  
  // Получаем заказы
  const { data: orders = [] } = useGetManagerOrdersQuery();
  
  // Mutations
  const [updateRequest] = useUpdateSupplierRequestMutation();
  const [createProduct] = useCreateProductMutation();
  const [assignManager] = useAssignManagerMutation();
  const [createContract] = useCreateContractMutation();
  
  // Получаем список менеджеров
  const { data: managers = [] } = useGetManagersQuery();
  
  // Фильтруем заявки по менеджеру
  const myRequests = requests.filter((r) => r.manager !== null);
  const displayRequests = activeTab === 'my-requests' ? myRequests : requests;
  
  // Находим товар поставщика для выбранной заявки
  const linkedProduct = useMemo(() => {
    if (!selectedRequest) return null;
    return supplierProducts.find(
      (sp) => sp.supplier === selectedRequest.supplier && 
              sp.supplier_sku === (selectedRequest.product_sku || '')
    );
  }, [selectedRequest, supplierProducts]);
  
  // Статусы заявок
  const getStatusClass = (status: string) => {
    switch (status) {
      case 'pending': return styles.pending;
      case 'under_review': return styles.underReview;
      case 'approved': return styles.approved;
      case 'rejected': return styles.rejected;
      case 'revision_required': return styles.revisionRequired;
      default: return '';
    }
  };
  
  // Обработчики
  const handleApprove = async (request: SupplierProductRequest) => {
    await updateRequest({
      id: request.id,
      data: { status: 3, review_comment: 'Заявка одобрена' }
    });
  };
  
  const handleReject = async (request: SupplierProductRequest) => {
    await updateRequest({
      id: request.id,
      data: { status: 5, review_comment: 'Заявка отклонена' }
    });
  };
  
  const handleRequestRevision = async (request: SupplierProductRequest) => {
    await updateRequest({
      id: request.id,
      data: { status: 4, review_comment: 'Требует доработки' }
    });
  };
  
  // Назначить менеджера заявке
  const handleAssignManager = async (requestId: number) => {
    if (!selectedManagerId) return;
    
    try {
      await assignManager({ requestId, managerId: selectedManagerId }).unwrap();
      setShowAssignManager(null);
      setSelectedManagerId(null);
      alert('Менеджер успешно назначен!');
    } catch (error) {
      console.error('Ошибка при назначении менеджера:', error);
      alert('Не удалось назначить менеджера');
    }
  };
  
  // Открыть форму создания товара
  const openProductForm = (request: SupplierProductRequest) => {
    setSelectedRequest(request);
    setProductFormData({
      name: request.product_name,
      description: request.product_description || '',
      price: request.suggested_price || '',
      oldPrice: request.suggested_old_price || '',
      SKU: request.product_sku || '',
      isPublished: false,
      category: request.category || '',
      publishedPages: [],
    });
    setShowProductForm(true);
  };
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  if (isLoading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }
  
  if (error) {
    return <div className={styles.error}>Ошибка при загрузке данных</div>;
  }
  
  return (
    <div className={styles.managerPage}>
      <h1 className={styles.pageTitle}>Панель менеджера</h1>
      
      <div className={styles.tabs}>
        <button
          className={`${styles.tabs__tab} ${activeTab === 'dashboard' ? styles['tabs__tab--active'] : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Дашборд
        </button>
        <button
          className={`${styles.tabs__tab} ${activeTab === 'my-requests' ? styles['tabs__tab--active'] : ''}`}
          onClick={() => setActiveTab('my-requests')}
        >
          Мои заявки ({myRequests.length})
        </button>
        <button
          className={`${styles.tabs__tab} ${activeTab === 'all-requests' ? styles['tabs__tab--active'] : ''}`}
          onClick={() => setActiveTab('all-requests')}
        >
          Все заявки ({requests.length})
        </button>
      </div>
      
      {activeTab === 'dashboard' && (
        <DashboardTab 
          contracts={allContracts}
          expiringContracts={expiringContracts}
          supplierProducts={supplierProducts}
          requests={requests}
          suppliers={suppliers}
          orders={orders}
          onCreateContract={() => setShowContractForm(true)}
        />
      )}
      
      {displayRequests.length === 0 ? (
        <div className={styles.emptyState}>
          <p>Заявок не найдено</p>
        </div>
      ) : (
        displayRequests.map((request) => (
          <div key={request.id} className={styles.card}>
            <div className={styles.requestHeader}>
              <div className={styles.requestInfo}>
                <h3>{request.product_name}</h3>
                <p>Поставщик: {request.supplier_name}</p>
                <p>Артикул: {request.product_sku || '—'}</p>
                <p>Количество: {request.quantity}</p>
                {request.suggested_price && (
                  <p>Предложенная цена: {request.suggested_price} ₽</p>
                )}
                <p>Создано: {formatDate(request.created_at)}</p>
              </div>
              <span className={`${styles.status} ${getStatusClass(request.status_name)}`}>
                {request.status_name === 'pending' && 'Ожидает'}
                {request.status_name === 'under_review' && 'На рассмотрении'}
                {request.status_name === 'approved' && 'Одобрена'}
                {request.status_name === 'rejected' && 'Отклонена'}
                {request.status_name === 'revision_required' && 'Требует доработки'}
              </span>
            </div>
            
            <div className={styles.requestActions}>
              {request.status_name === 'pending' || request.status_name === 'under_review' ? (
                <>
                  <button 
                    className={`${styles.button} ${styles.buttonSuccess}`}
                    onClick={() => handleApprove(request)}
                  >
                    Одобрить
                  </button>
                  <button 
                    className={`${styles.button} ${styles.buttonDanger}`}
                    onClick={() => handleReject(request)}
                  >
                    Отклонить
                  </button>
                  <button 
                    className={`${styles.button} ${styles.buttonSecondary}`}
                    onClick={() => handleRequestRevision(request)}
                  >
                    На доработку
                  </button>
                </>
              ) : null}
              
              {/* Кнопка назначения менеджера - только для заявок без менеджера */}
              {!request.manager && (
                <button 
                  className={`${styles.button} ${styles.buttonPrimary}`}
                  onClick={() => setShowAssignManager(request.id)}
                >
                  Назначить менеджера
                </button>
              )}
              
              {request.status_name === 'approved' && (
                <button 
                  className={`${styles.button} ${styles.buttonPrimary}`}
                  onClick={() => openProductForm(request)}
                >
                  Создать товар
                </button>
              )}
            </div>
          </div>
        ))
      )}
      
      {/* Модальное окно создания товара */}
      {showProductForm && selectedRequest && (
        <div className={styles.modalOverlay} onClick={() => setShowProductForm(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>Создание товара из заявки</h2>
            <p className={styles.modalSubtitle}>
              Заявка от: {selectedRequest.supplier_name}
            </p>
            
            <div className={styles.formSection}>
              <h4>Информация о товаре</h4>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Название товара *</label>
                <input
                  type="text"
                  className={styles.formInput}
                  value={productFormData.name}
                  onChange={(e) => setProductFormData({ ...productFormData, name: e.target.value })}
                />
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Описание</label>
                <textarea
                  className={styles.formTextarea}
                  value={productFormData.description}
                  onChange={(e) => setProductFormData({ ...productFormData, description: e.target.value })}
                  rows={4}
                />
              </div>
              
              {/* Изображения товара от поставщика */}
              {selectedRequest?.product_images && selectedRequest.product_images.length > 0 && (
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Изображения товара от поставщика</label>
                  <div className={styles.imagePreviewGrid}>
                    {selectedRequest.product_images.map((image, index) => (
                      <div key={index} className={styles.imagePreviewItem}>
                        <img
                          src={image}
                          alt={`Изображение товара ${index + 1}`}
                          className={styles.imagePreview}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Цена (₽) *</label>
                  <input
                    type="number"
                    className={styles.formInput}
                    value={productFormData.price}
                    onChange={(e) => setProductFormData({ ...productFormData, price: e.target.value })}
                  />
                </div>
                
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Старая цена (₽)</label>
                  <input
                    type="number"
                    className={styles.formInput}
                    value={productFormData.oldPrice}
                    onChange={(e) => setProductFormData({ ...productFormData, oldPrice: e.target.value })}
                  />
                </div>
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Артикул</label>
                <input
                  type="text"
                  className={styles.formInput}
                  value={productFormData.SKU}
                  onChange={(e) => setProductFormData({ ...productFormData, SKU: e.target.value })}
                />
              </div>
              
              {/* Выбор страниц для публикации */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Опубликовать на страницах:</label>
                <div className={styles.checkboxGroup}>
                  {PUBLISH_PAGES.map((page) => (
                    <label key={page.value} className={styles.checkboxLabel}>
                      <input
                        type="checkbox"
                        checked={productFormData.publishedPages.includes(page.value)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setProductFormData({ 
                              ...productFormData, 
                              publishedPages: [...productFormData.publishedPages, page.value] 
                            });
                          } else {
                            setProductFormData({ 
                              ...productFormData, 
                              publishedPages: productFormData.publishedPages.filter(p => p !== page.value) 
                            });
                          }
                        }}
                      />
                      {page.label}
                    </label>
                  ))}
                </div>
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={productFormData.isPublished}
                    onChange={(e) => setProductFormData({ ...productFormData, isPublished: e.target.checked })}
                  />
                  Опубликовать товар сразу
                </label>
              </div>
            </div>
            
            <div className={styles.modalActions}>
              <button 
                className={`${styles.button} ${styles.buttonSecondary}`}
                onClick={() => setShowProductForm(false)}
              >
                Отмена
              </button>
              <button 
                className={`${styles.button} ${styles.buttonSuccess}`}
                onClick={async () => {
                  try {
                    // Находим категории для выбранных страниц
                    const categoryIds: number[] = [];
                    
                    for (const page of PUBLISH_PAGES) {
                      if (productFormData.publishedPages.includes(page.value)) {
                        // Ищем категории, соответствующие этой странице
                        const matchingCategories = categories.filter(cat => 
                          page.categoryNames.some(name => 
                            cat.name.toLowerCase().includes(name.toLowerCase())
                          )
                        );
                        categoryIds.push(...matchingCategories.map(c => c.id));
                      }
                    }
                    
                    // Создаём товар
                    const productData = {
                      name: productFormData.name,
                      description: productFormData.description,
                      price: productFormData.price,
                      old_price: productFormData.oldPrice || null,
                      sku: productFormData.SKU,
                      is_active: productFormData.isPublished || productFormData.publishedPages.length > 0,
                      published_pages: productFormData.publishedPages,
                      categories_ids: categoryIds,
                      // Добавляем изображения из заявки поставщика
                      image_urls: selectedRequest?.product_images || [],
                    };
                    
                    await createProduct(productData).unwrap();
                    
                    alert('Товар успешно создан!');
                    setShowProductForm(false);
                  } catch (error) {
                    console.error('Ошибка при создании товара:', error);
                    alert('Ошибка при создании товара');
                  }
                }}
              >
                Создать товар
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Модальное окно назначения менеджера */}
      {showAssignManager && (
        <div className={styles.modalOverlay} onClick={() => { setShowAssignManager(null); setSelectedManagerId(null); }}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>Назначить менеджера</h2>
            <p className={styles.modalSubtitle}>
              Выберите менеджера для этой заявки
            </p>
            
            <div className={styles.formSection}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Менеджер *</label>
                <select
                  className={styles.formInput}
                  value={selectedManagerId || ''}
                  onChange={(e) => setSelectedManagerId(Number(e.target.value))}
                >
                  <option value="" disabled>Выберите менеджера</option>
                  {managers.map((manager) => (
                    <option key={manager.id} value={manager.id}>
                      {manager.first_name || manager.last_name 
                        ? `${manager.first_name} ${manager.last_name}`.trim() 
                        : manager.email}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className={styles.modalActions}>
              <button 
                className={`${styles.button} ${styles.buttonSecondary}`}
                onClick={() => { setShowAssignManager(null); setSelectedManagerId(null); }}
              >
                Отмена
              </button>
              <button 
                className={`${styles.button} ${styles.buttonSuccess}`}
                onClick={() => handleAssignManager(showAssignManager)}
                disabled={!selectedManagerId}
              >
                Назначить
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Модальное окно создания договора */}
      {showContractForm && (
        <div className={styles.modalOverlay} onClick={() => setShowContractForm(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>Создание договора с поставщиком</h2>
            
            <div className={styles.formSection}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Поставщик *</label>
                <select
                  className={styles.formInput}
                  value={contractFormData.supplier}
                  onChange={(e) => setContractFormData({ ...contractFormData, supplier: Number(e.target.value) })}
                >
                  <option value="">Выберите поставщика</option>
                  {suppliers.map((supplier) => (
                    <option key={supplier.id} value={supplier.id}>
                      {supplier.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Номер договора *</label>
                <input
                  type="text"
                  className={styles.formInput}
                  value={contractFormData.contract_number}
                  onChange={(e) => setContractFormData({ ...contractFormData, contract_number: e.target.value })}
                  placeholder="ДГ-2026-001"
                />
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Название договора *</label>
                <input
                  type="text"
                  className={styles.formInput}
                  value={contractFormData.title}
                  onChange={(e) => setContractFormData({ ...contractFormData, title: e.target.value })}
                  placeholder="Договор поставки №..."
                />
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Описание</label>
                <textarea
                  className={styles.formTextarea}
                  value={contractFormData.description}
                  onChange={(e) => setContractFormData({ ...contractFormData, description: e.target.value })}
                  rows={3}
                  placeholder="Условия договора..."
                />
              </div>
              
              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Дата начала *</label>
                  <input
                    type="date"
                    className={styles.formInput}
                    value={contractFormData.start_date}
                    onChange={(e) => setContractFormData({ ...contractFormData, start_date: e.target.value })}
                  />
                </div>
                
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Дата окончания *</label>
                  <input
                    type="date"
                    className={styles.formInput}
                    value={contractFormData.end_date}
                    onChange={(e) => setContractFormData({ ...contractFormData, end_date: e.target.value })}
                  />
                </div>
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Сумма договора (₽)</label>
                <input
                  type="number"
                  className={styles.formInput}
                  value={contractFormData.total_amount}
                  onChange={(e) => setContractFormData({ ...contractFormData, total_amount: e.target.value })}
                  placeholder="0.00"
                />
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Notes</label>
                <textarea
                  className={styles.formTextarea}
                  value={contractFormData.notes}
                  onChange={(e) => setContractFormData({ ...contractFormData, notes: e.target.value })}
                  rows={2}
                  placeholder="Дополнительные условия..."
                />
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={contractFormData.is_auto_renew}
                    onChange={(e) => setContractFormData({ ...contractFormData, is_auto_renew: e.target.checked })}
                  />
                  Автоматически продлевать договор
                </label>
              </div>
            </div>
            
            <div className={styles.modalActions}>
              <button 
                className={`${styles.button} ${styles.buttonSecondary}`}
                onClick={() => {
                  setShowContractForm(false);
                  setContractFormData({
                    supplier: '',
                    contract_number: '',
                    title: '',
                    description: '',
                    start_date: '',
                    end_date: '',
                    total_amount: '',
                    notes: '',
                    is_auto_renew: false,
                  });
                }}
              >
                Отмена
              </button>
              <button 
                className={`${styles.button} ${styles.buttonSuccess}`}
                onClick={async () => {
                  if (!contractFormData.supplier || !contractFormData.contract_number || !contractFormData.title || !contractFormData.start_date || !contractFormData.end_date) {
                    alert('Пожалуйста, заполните все обязательные поля');
                    return;
                  }
                  
                  try {
                    await createContract({
                      supplier: contractFormData.supplier,
                      contract_number: contractFormData.contract_number,
                      title: contractFormData.title,
                      description: contractFormData.description,
                      start_date: contractFormData.start_date,
                      end_date: contractFormData.end_date,
                      total_amount: contractFormData.total_amount ? Number(contractFormData.total_amount) : undefined,
                      notes: contractFormData.notes,
                      is_auto_renew: contractFormData.is_auto_renew,
                    }).unwrap();
                    
                    // Закрываем форму и сбрасываем данные
                    setShowContractForm(false);
                    setContractFormData({
                      supplier: '',
                      contract_number: '',
                      title: '',
                      description: '',
                      start_date: '',
                      end_date: '',
                      total_amount: '',
                      notes: '',
                      is_auto_renew: false,
                    });
                  } catch (error) {
                    console.error('Ошибка при создании договора:', error);
                    alert('Ошибка при создании договора');
                  }
                }}
              >
                Создать договор
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManagerPage;
