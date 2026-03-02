import { useState, useMemo, useEffect } from 'react';
import {
  useGetSupplierRequestsQuery,
  useGetRequestStatusesQuery,
  useUpdateSupplierRequestMutation,
  useAssignManagerMutation,
  useCreateProductFromRequestMutation,
  useGetCommunicationsByRequestQuery,
  useCreateCommunicationMutation,
  useGetMyContractsQuery,
} from '@/services/api/suppliersApi';
import { useGetProductsQuery } from '@/services/api/productsApi';
import type { SupplierProductRequest } from '@/services/api/suppliersApi';
import { CreateSupplierRequestForm } from './index';
import styles from './SupplierRequestsPage.module.scss';

type TabType = 'all' | 'pending' | 'under_review' | 'approved' | 'rejected' | 'contracts';

const SupplierRequestsPage = () => {
  const [activeTab, setActiveTab] = useState<TabType>('all');
  const [showAssignModal, setShowAssignModal] = useState<boolean>(false);
  const [selectedRequestId, setSelectedRequestId] = useState<number | null>(null);
  const [managerId, setManagerId] = useState<string>('');
  const [showCreateForm, setShowCreateForm] = useState<boolean>(false);
  const [showProductModal, setShowProductModal] = useState<boolean>(false);
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [showChatModal, setShowChatModal] = useState<boolean>(false);
  const [chatMessage, setChatMessage] = useState<string>('');
  
  // Проверка роли пользователя
  const [isSupplier, setIsSupplier] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isLoadingRole, setIsLoadingRole] = useState(true);
  const [supplierId, setSupplierId] = useState<number | null>(null);
  
  // Проверка авторизации и роли при загрузке
  useEffect(() => {
    const checkUserRole = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setIsLoadingRole(false);
        return;
      }
      
      try {
        // Сначала проверяем права админа из JWT токена
        try {
          const tokenParts = token.split('.');
          if (tokenParts.length === 3) {
            const payload = JSON.parse(atob(tokenParts[1]));
            const isUserAdmin = payload.is_staff || false;
            setIsAdmin(isUserAdmin);
          }
        } catch (e) {
          console.error('Failed to parse token:', e);
        }
        
        // Проверяем статус поставщика и получаем ID
        const supplierResponse = await fetch('/api/v1/my-supplier-profile/', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (supplierResponse.ok) {
          const supplierData = await supplierResponse.json();
          setIsSupplier(true);
          setSupplierId(supplierData.id);
        }
      } catch (error) {
        console.error('Error checking user role:', error);
      } finally {
        setIsLoadingRole(false);
      }
    };
    
    checkUserRole();
  }, []);

  // Получаем статусы заявок для маппинга ID в name
  const { data: statuses } = useGetRequestStatusesQuery();
  
  const { data: requests, isLoading, error } = useGetSupplierRequestsQuery({
    page_size: 100,
  });

  // Получаем договоры поставщика
  const { data: contracts = [] } = useGetMyContractsQuery();

  // Фильтрация на фронтенде по статусу и поставщику
  const filteredRequests = useMemo(() => {
    if (!requests) return [];
    
    let filtered = requests;
    
    // Поставщики видят только свои заявки
    if (isSupplier && supplierId) {
      filtered = filtered.filter(request => request.supplier === supplierId);
    }
    
    if (activeTab === 'all') return filtered;
    
    // Логи для отладки
    console.log('Filtering by:', activeTab);
    console.log('Available statuses:', requests.map(r => r.status_name));
    
    return filtered.filter(request => request.status_name === activeTab);
  }, [requests, activeTab, isSupplier, supplierId]);

  const [updateRequest] = useUpdateSupplierRequestMutation();
  const [assignManager] = useAssignManagerMutation();
  const [createProductFromRequest] = useCreateProductFromRequestMutation();
  const [sendMessage] = useCreateCommunicationMutation();
  const { data: products } = useGetProductsQuery({ page_size: 100 });
  
  // Получаем коммуникации для чата
  const { data: communications = [] } = useGetCommunicationsByRequestQuery(
    selectedRequestId ?? 0,
    { skip: !selectedRequestId || !showChatModal }
  );

  // Получить статус заявки для отображения
  const getStatusClass = (statusName: string): string => {
    const statusMap: Record<string, string> = {
      'pending': 'statusBadge--pending',
      'under_review': 'statusBadge--underReview',
      'approved': 'statusBadge--approved',
      'revision_required': 'statusBadge--revisionRequired',
      'rejected': 'statusBadge--rejected',
    };
    return statusMap[statusName] || 'statusBadge--pending';
  };

  // Обработчик одобрения заявки
  const handleApprove = async (request: SupplierProductRequest) => {
    const approvedStatus = statuses?.find(s => s.name === 'approved');
    if (approvedStatus) {
      await updateRequest({
        id: request.id,
        data: { status: approvedStatus.id, review_comment: 'Заявка одобрена' },
      }).unwrap();
    }
  };

  // Обработчик отклонения заявки
  const handleReject = async (request: SupplierProductRequest) => {
    const rejectedStatus = statuses?.find(s => s.name === 'rejected');
    if (rejectedStatus) {
      await updateRequest({
        id: request.id,
        data: { status: rejectedStatus.id, review_comment: 'Заявка отклонена' },
      }).unwrap();
    }
  };

  // Открыть модальное окно назначения менеджера
  const openAssignModal = (requestId: number) => {
    setSelectedRequestId(requestId);
    setShowAssignModal(true);
  };

  // Назначить менеджера
  const handleAssignManager = async () => {
    if (selectedRequestId && managerId) {
      try {
        await assignManager({
          requestId: selectedRequestId,
          managerId: parseInt(managerId),
        }).unwrap();
        setShowAssignModal(false);
        setManagerId('');
        setSelectedRequestId(null);
      } catch (err) {
        console.error('Ошибка при назначении менеджера:', err);
      }
    }
  };

  // Открыть модальное окно создания товара
  const openProductModal = (requestId: number) => {
    setSelectedRequestId(requestId);
    setSelectedProductId(null);
    setShowProductModal(true);
  };

  // Создать товар из заявки
  const handleCreateProduct = async () => {
    if (selectedRequestId && selectedProductId) {
      try {
        await createProductFromRequest({
          requestId: selectedRequestId,
          product: selectedProductId,
        }).unwrap();
        setShowProductModal(false);
        setSelectedRequestId(null);
        setSelectedProductId(null);
      } catch (err) {
        console.error('Ошибка при создании товара:', err);
      }
    }
  };
  
  // Открыть чат с менеджером
  const openChat = (requestId: number) => {
    setSelectedRequestId(requestId);
    setShowChatModal(true);
  };
  
  // Отправить сообщение менеджеру
  const handleSendChatMessage = async () => {
    if (selectedRequestId && chatMessage.trim()) {
      try {
        await sendMessage({
          request: selectedRequestId,
          message: chatMessage.trim(),
        }).unwrap();
        setChatMessage('');
      } catch (err) {
        console.error('Ошибка при отправке сообщения:', err);
      }
    }
  };

  // Форматтер даты
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  // Форматтер цены
  const formatPrice = (price: string | null): string => {
    if (!price) return '-';
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
    }).format(parseFloat(price));
  };

  // Получить инициалы менеджера
  const getManagerInitials = (managerName: string | null): string => {
    if (!managerName) return '?';
    const parts = managerName.split('@');
    return parts[0].charAt(0).toUpperCase();
  };

  const tabs: { key: TabType; label: string }[] = [
    { key: 'all', label: 'Все' },
    { key: 'pending', label: 'Ожидают' },
    { key: 'under_review', label: 'На рассмотрении' },
    { key: 'approved', label: 'Одобренные' },
    { key: 'rejected', label: 'Отклоненные' },
    { key: 'contracts', label: 'Договоры' },
  ];

  if (isLoading || isLoadingRole) {
    return (
      <main className={styles.supplierRequestsPage}>
        <div className={styles.loading} role="status" aria-live="polite">
          Загрузка...
        </div>
      </main>
    );
  }

  // Проверка доступа - только поставщики и админы могут видеть эту страницу
  if (!isSupplier && !isAdmin) {
    return (
      <main className={styles.supplierRequestsPage}>
        <div className={styles.error} role="alert">
          <h2>Доступ запрещён</h2>
          <p>Эта страница доступна только для поставщиков и администраторов.</p>
          <p>Если вы хотите стать поставщиком, нажмите "Стать поставщиком" в меню.</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className={styles.supplierRequestsPage}>
        <div className={styles.error} role="alert">
          Ошибка при загрузке заявок
        </div>
      </main>
    );
  }

  return (
    <main className={styles.supplierRequestsPage}>
      {/* Заголовок страницы - разный для админа и поставщика */}
      <div className={styles.pageHeader}>
        {isAdmin ? (
          <>
            <h1 className={styles.pageHeader__title}>Заявки поставщиков</h1>
            <p className={styles.pageHeader__subtitle}>Управление заявками на поставку товаров</p>
          </>
        ) : (
          <>
            <h1 className={styles.pageHeader__title}>Предложить товар</h1>
            <p className={styles.pageHeader__subtitle}>Предложите свой товар для продажи на маркетплейсе</p>
          </>
        )}
        <button
          type="button"
          className={`${styles.createButton}`}
          onClick={() => setShowCreateForm(true)}
          aria-label={isAdmin ? "Создать новую заявку" : "Предложить товар"}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          {isAdmin ? 'Создать заявку' : 'Предложить товар'}
        </button>
      </div>

      {/* Вкладки - только для админов */}
      {(isAdmin || isSupplier) && (
        <nav className={styles.tabs} aria-label="Фильтр заявок по статусу">
          {tabs.map(tab => (
            <button
              key={tab.key}
              type="button"
              className={`${styles.tabs__tab} ${activeTab === tab.key ? styles['tabs__tab--active'] : ''}`}
              onClick={(e) => {
                e.preventDefault();
                setActiveTab(tab.key);
              }}
              aria-pressed={activeTab === tab.key}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      )}

      {activeTab === 'contracts' ? (
        <section className={styles.emptyState} aria-label="Договоры">
          {contracts.length === 0 ? (
            <>
              <div className={styles.emptyState__icon}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
              </div>
              <h2 className={styles.emptyState__title}>Нет договоров</h2>
              <p className={styles.emptyState__text}>У вас пока нет договоров с магазином</p>
            </>
          ) : (
            <div className={styles.requestsList}>
              {contracts.map(contract => (
                <article key={contract.id} className={styles.requestCard}>
                  <div className={styles.requestCard__header}>
                    <div className={styles.requestCard__info}>
                      <h3 className={styles.requestCard__title}>{contract.title}</h3>
                      <span className={styles.requestCard__supplier}>Договор № {contract.contract_number}</span>
                    </div>
                    <span 
                      className={`${styles.statusBadge} ${contract.status_name === 'active' ? styles['statusBadge--approved'] : contract.status_name === 'expired' ? styles['statusBadge--rejected'] : styles['statusBadge--pending']}`}
                    >
                      {contract.status_name === 'active' ? 'Активен' : contract.status_name === 'expired' ? 'Истёк' : contract.status_name}
                    </span>
                  </div>
                  <dl className={styles.requestCard__details}>
                    <div className={styles.requestCard__detail}>
                      <dt className={styles['requestCard__detail-label']}>Дата начала</dt>
                      <dd className={styles['requestCard__detail-value']}>{formatDate(contract.start_date)}</dd>
                    </div>
                    <div className={styles.requestCard__detail}>
                      <dt className={styles['requestCard__detail-label']}>Дата окончания</dt>
                      <dd className={styles['requestCard__detail-value']}>{formatDate(contract.end_date)}</dd>
                    </div>
                    <div className={styles.requestCard__detail}>
                      <dt className={styles['requestCard__detail-label']}>Сумма</dt>
                      <dd className={styles['requestCard__detail-value']}>{contract.total_amount ? formatPrice(contract.total_amount) : '-'}</dd>
                    </div>
                    <div className={styles.requestCard__detail}>
                      <dt className={styles['requestCard__detail-label']}>Товаров</dt>
                      <dd className={styles['requestCard__detail-value']}>{contract.products_count}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          )}
        </section>
      ) : (
      !filteredRequests || filteredRequests.length === 0 ? (
        <section className={styles.emptyState} aria-label="Нет заявок">
          <div className={styles.emptyState__icon}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h2 className={styles.emptyState__title}>Нет заявок</h2>
          <p className={styles.emptyState__text}>Заявок с выбранным статусом не найдено</p>
        </section>
      ) : (
        <section className={styles.requestsList} aria-label="Список заявок">
          {filteredRequests.map(request => (
            <article key={request.id} className={styles.requestCard}>
              <div className={styles.requestCard__header}>
                <div className={styles.requestCard__info}>
                  <h3 className={styles.requestCard__title}>{request.product_name}</h3>
                  <span className={styles.requestCard__supplier}>{request.supplier_name}</span>
                </div>
                <span 
                  className={`${styles.statusBadge} ${styles[getStatusClass(request.status_name)]}`}
                  aria-label={`Статус: ${request.status_name}`}
                >
                  {request.status_name}
                </span>
              </div>

              <dl className={styles.requestCard__details}>
                <div className={styles.requestCard__detail}>
                  <dt className={styles['requestCard__detail-label']}>Артикул</dt>
                  <dd className={styles['requestCard__detail-value']}>{request.product_sku || '-'}</dd>
                </div>
                <div className={styles.requestCard__detail}>
                  <dt className={styles['requestCard__detail-label']}>Количество</dt>
                  <dd className={styles['requestCard__detail-value']}>{request.quantity} шт.</dd>
                </div>
                <div className={styles.requestCard__detail}>
                  <dt className={styles['requestCard__detail-label']}>Предложенная цена</dt>
                  <dd className={styles['requestCard__detail-value']}>{formatPrice(request.suggested_price)}</dd>
                </div>
                <div className={styles.requestCard__detail}>
                  <dt className={styles['requestCard__detail-label']}>Дата создания</dt>
                  <dd className={styles['requestCard__detail-value']}>{formatDate(request.created_at)}</dd>
                </div>
              </dl>

              <div className={styles.requestCard__manager}>
                <div className={styles.manager__avatar} aria-hidden="true">
                  {getManagerInitials(request.manager_name)}
                </div>
                <div className={styles.manager__info}>
                  <span className={styles.manager__label}>Менеджер</span>
                  <span className={styles.manager__name}>
                    {request.manager_name || <span className={styles.manager__noManager}>Не назначен</span>}
                  </span>
                </div>
                {isAdmin && (
                  <button
                    type="button"
                    className={`${styles.actionBtn} ${styles['actionBtn--assign']}`}
                    onClick={() => openAssignModal(request.id)}
                    aria-label={`Назначить менеджера для заявки ${request.product_name}`}
                  >
                    Назначить
                  </button>
                )}
                {/* Кнопка чата для поставщиков, когда менеджер назначен */}
                {isSupplier && request.manager_name && (
                  <button
                    type="button"
                    className={`${styles.actionBtn} ${styles['actionBtn--createProduct']}`}
                    onClick={() => openChat(request.id)}
                    aria-label={`Отправить сообщение менеджеру по заявке ${request.product_name}`}
                  >
                    Написать менеджеру
                  </button>
                )}
              </div>

              {/* Кнопки одобрения/отклонения - только для админов */}
              {isAdmin && (request.status_name === 'pending' || request.status_name === 'under_review') && (
                <div className={styles.requestCard__actions}>
                  <button
                    type="button"
                    className={`${styles.actionBtn} ${styles['actionBtn--approve']}`}
                    onClick={() => handleApprove(request)}
                    aria-label={`Одобрить заявку ${request.product_name}`}
                  >
                    Одобрить
                  </button>
                  <button
                    type="button"
                    className={`${styles.actionBtn} ${styles['actionBtn--reject']}`}
                    onClick={() => handleReject(request)}
                    aria-label={`Отклонить заявку ${request.product_name}`}
                  >
                    Отклонить
                  </button>
                </div>
              )}

              {/* Кнопка создания товара для одобренных заявок - только для админов */}
              {isAdmin && request.status_name === 'approved' && (
                <div className={styles.requestCard__actions}>
                  <button
                    type="button"
                    className={`${styles.actionBtn} ${styles['actionBtn--createProduct']}`}
                    onClick={() => openProductModal(request.id)}
                    aria-label={`Создать товар из заявки ${request.product_name}`}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <line x1="12" y1="5" x2="12" y2="19" />
                      <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    Создать товар
                  </button>
                </div>
              )}
            </article>
          ))}
        </section>
      ))}
      

      {/* Модальное окно назначения менеджера */}
      {showAssignModal && (
        <div 
          className={styles.modalOverlay} 
          onClick={() => setShowAssignModal(false)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <h2 id="modal-title" className={styles.modal__title}>Назначить менеджера</h2>
            
            <div className={styles.formGroup}>
              <label htmlFor="managerId" className={styles.formGroup__label}>
                ID пользователя
              </label>
              <input
                type="number"
                id="managerId"
                className={styles.formGroup__input}
                value={managerId}
                onChange={e => setManagerId(e.target.value)}
                placeholder="Введите ID пользователя"
              />
            </div>
            
            <p className={styles.modal__hint}>
              Введите ID пользователя, которого нужно назначить менеджером заявки
            </p>

            <div className={styles.modal__actions}>
              <button
                type="button"
                className={`${styles.actionBtn} ${styles['actionBtn--assign']}`}
                onClick={() => setShowAssignModal(false)}
              >
                Отмена
              </button>
              <button
                type="button"
                className={`${styles.actionBtn} ${styles['actionBtn--approve']}`}
                onClick={handleAssignManager}
                disabled={!managerId}
              >
                Назначить
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно создания заявки */}
      {showCreateForm && (
        <div
          className={styles.modalOverlay}
          onClick={() => setShowCreateForm(false)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="create-form-title"
        >
          <div className={styles.createFormModal} onClick={e => e.stopPropagation()}>
            <button
              type="button"
              className={styles.closeButton}
              onClick={() => setShowCreateForm(false)}
              aria-label="Закрыть форму"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
            <CreateSupplierRequestForm
              onSuccess={() => {
                setShowCreateForm(false);
              }}
              onCancel={() => setShowCreateForm(false)}
              isSupplierMode={isSupplier}
              supplierId={supplierId || undefined}
            />
          </div>
        </div>
      )}

      {/* Модальное окно создания товара из заявки */}
      {showProductModal && (
        <div
          className={styles.modalOverlay}
          onClick={() => setShowProductModal(false)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="product-modal-title"
        >
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <h2 id="product-modal-title" className={styles.modal__title}>Создать товар из заявки</h2>
            
            <p className={styles.modal__hint}>
              Выберите товар из каталога, к которому будет привязан поставщик
            </p>
            
            <div className={styles.formGroup}>
              <label htmlFor="productSelect" className={styles.formGroup__label}>
                Товар из каталога
              </label>
              <select
                id="productSelect"
                className={styles.formGroup__select}
                value={selectedProductId || ''}
                onChange={(e) => setSelectedProductId(e.target.value ? parseInt(e.target.value) : null)}
                aria-required="true"
              >
                <option value="" disabled>Выберите товар</option>
                {products?.results?.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.name} (арт. {product.sku || '-'})
                  </option>
                ))}
              </select>
            </div>

            <div className={styles.modal__actions}>
              <button
                type="button"
                className={`${styles.actionBtn} ${styles['actionBtn--assign']}`}
                onClick={() => setShowProductModal(false)}
              >
                Отмена
              </button>
              <button
                type="button"
                className={`${styles.actionBtn} ${styles['actionBtn--createProduct']}`}
                onClick={handleCreateProduct}
                disabled={!selectedProductId}
              >
                Создать товар поставщика
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Модальное окно чата с менеджером */}
      {showChatModal && (
        <div
          className={styles.modalOverlay}
          onClick={() => setShowChatModal(false)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="chat-modal-title"
        >
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <h2 id="chat-modal-title" className={styles.modal__title}>Переписка с менеджером</h2>
            
            <div className={styles.communicationList}>
              {communications.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#666' }}>Сообщений пока нет</p>
              ) : (
                communications.map((msg) => (
                  <div 
                    key={msg.id} 
                    className={`${styles.message} ${msg.direction === 'supplier' ? styles.fromSupplier : styles.fromManager}`}
                  >
                    <div className={styles.messageHeader}>
                      <span>{msg.sender_email}</span>
                      <span>{new Date(msg.created_at).toLocaleString('ru-RU')}</span>
                    </div>
                    <div className={styles.messageText}>{msg.message}</div>
                  </div>
                ))
              )}
            </div>
            
            <div className={styles.messageForm}>
              <textarea
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="Введите сообщение..."
                rows={3}
                className={styles.formGroup__textarea}
              />
              <button
                type="button"
                className={`${styles.actionBtn} ${styles['actionBtn--createProduct']}`}
                onClick={handleSendChatMessage}
                disabled={!chatMessage.trim()}
              >
                Отправить
              </button>
            </div>

            <div className={styles.modal__actions}>
              <button
                type="button"
                className={`${styles.actionBtn} ${styles['actionBtn--assign']}`}
                onClick={() => setShowChatModal(false)}
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};

export default SupplierRequestsPage;