import { useState, useMemo } from 'react';
import { useGetSupplierRequestsQuery, useUpdateSupplierRequestMutation, useGetSupplierProductsQuery, useAssignManagerMutation, useGetManagersQuery } from '@/services/api/suppliersApi';
import { useCreateProductMutation, useGetCategoriesQuery } from '@/services/api/productsApi';
import type { SupplierProductRequest } from '@/services/api/suppliersApi';
import styles from './ManagerPage.module.scss';

type TabType = 'my-requests' | 'all-requests';

// Доступные страницы для публикации товара
const PUBLISH_PAGES = [
  { value: 'women', label: 'Женщинам', categoryNames: ['женщин', 'women', 'woman', 'женская', 'для женщин'] },
  { value: 'men', label: 'Мужчинам', categoryNames: ['мужчин', 'men', 'man', 'мужская', 'для мужчин'] },
  { value: 'children', label: 'Детям', categoryNames: ['детей', 'children', 'child', 'детская', 'для детей'] },
];

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

const ManagerPage = () => {
  const [activeTab, setActiveTab] = useState<TabType>('my-requests');
  const [selectedRequest, setSelectedRequest] = useState<SupplierProductRequest | null>(null);
  const [showProductForm, setShowProductForm] = useState(false);
  const [showAssignManager, setShowAssignManager] = useState<number | null>(null);
  const [selectedManagerId, setSelectedManagerId] = useState<number | null>(null);
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
  
  // Mutations
  const [updateRequest] = useUpdateSupplierRequestMutation();
  const [createProduct] = useCreateProductMutation();
  const [assignManager] = useAssignManagerMutation();
  
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
    </div>
  );
};

export default ManagerPage;
