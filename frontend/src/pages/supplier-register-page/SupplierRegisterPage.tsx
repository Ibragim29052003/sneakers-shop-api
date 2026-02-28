import { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useRegisterSupplierWithRequestMutation } from '../../services/api/suppliersApi';
import styles from './SupplierRegisterPage.module.scss';

interface FormData {
  // Company info
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  contact_person: string;
  phone: string;
  inn: string;
  kpp: string;
  ogrn: string;
  legal_address: string;
  actual_address: string;
  website: string;
  notes: string;
  // Product info
  product_name: string;
  product_sku: string;
  product_description: string;
  quantity: string;
  suggested_price: string;
  product_notes: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  phone?: string;
  inn?: string;
  product_name?: string;
  suggested_price?: string;
}

export const SupplierRegisterPage = () => {
  const navigate = useNavigate();
  const [registerSupplierWithRequest, { isLoading }] = useRegisterSupplierWithRequestMutation();
  
  const [formData, setFormData] = useState<FormData>({
    // Company
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    contact_person: '',
    phone: '',
    inn: '',
    kpp: '',
    ogrn: '',
    legal_address: '',
    actual_address: '',
    website: '',
    notes: '',
    // Product
    product_name: '',
    product_sku: '',
    product_description: '',
    quantity: '1',
    suggested_price: '',
    product_notes: '',
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [apiError, setApiError] = useState('');
  const [success, setSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // Validators
  const validateEmail = useCallback((email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }, []);

  const validatePhone = useCallback((phone: string): boolean => {
    if (!phone) return true;
    const phoneRegex = /^[\d\s\+\-\(\)]{10,20}$/;
    return phoneRegex.test(phone);
  }, []);

  const validateInn = useCallback((inn: string): boolean => {
    if (!inn) return true;
    return /^\d{10}$|^\d{12}$/.test(inn);
  }, []);

  const validatePassword = useCallback((password: string): string | undefined => {
    if (!password) return 'Пароль обязателен';
    if (password.length < 8) return 'Пароль должен быть не менее 8 символов';
    if (!/[A-Z]/.test(password)) return 'Пароль должен содержать хотя бы одну заглавную букву';
    if (!/[0-9]/.test(password)) return 'Пароль должен содержать хотя бы одну цифру';
    return undefined;
  }, []);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  }, []);

  const validate = useCallback((): boolean => {
    const newErrors: FormErrors = {};
    
    // Company validation
    if (!formData.name.trim()) {
      newErrors.name = 'Название компании обязательно';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email обязателен';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Введите корректный email';
    }
    
    const passwordError = validatePassword(formData.password);
    if (passwordError) {
      newErrors.password = passwordError;
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Пароли не совпадают';
    }
    
    if (formData.phone && !validatePhone(formData.phone)) {
      newErrors.phone = 'Введите корректный номер телефона';
    }
    
    if (formData.inn && !validateInn(formData.inn)) {
      newErrors.inn = 'ИНН должен содержать 10 или 12 цифр';
    }
    
    // Product validation
    if (!formData.product_name.trim()) {
      newErrors.product_name = 'Название товара обязательно';
    }
    
    if (formData.suggested_price && isNaN(Number(formData.suggested_price))) {
      newErrors.suggested_price = 'Введите корректную цену';
    }
    
    setErrors(newErrors);
    setTouched({
      name: true, email: true, password: true, confirmPassword: true,
      phone: true, inn: true, product_name: true, suggested_price: true,
    });
    
    return Object.keys(newErrors).length === 0;
  }, [formData, validateEmail, validatePhone, validateInn, validatePassword]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError('');
    
    if (!validate()) return;

    try {
      const result = await registerSupplierWithRequest({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        contact_person: formData.contact_person,
        phone: formData.phone,
        inn: formData.inn,
        kpp: formData.kpp,
        ogrn: formData.ogrn,
        legal_address: formData.legal_address,
        actual_address: formData.actual_address,
        website: formData.website,
        notes: formData.notes,
        product_name: formData.product_name,
        product_sku: formData.product_sku,
        product_description: formData.product_description,
        quantity: parseInt(formData.quantity) || 1,
        suggested_price: formData.suggested_price ? parseFloat(formData.suggested_price) : undefined,
        product_notes: formData.product_notes,
      }).unwrap();

      setSuccess(true);
      setSuccessMessage(result.message);
      
      // Redirect to home after 3 seconds - user can login via modal in header
      setTimeout(() => {
        navigate('/', { state: { openLoginModal: true, message: result.message } });
      }, 3000);
    } catch (error: unknown) {
      if (error && typeof error === 'object' && 'data' in error) {
        const errorData = error.data as Record<string, string[] | string>;
        const errorMessages = Object.entries(errorData)
          .map(([key, value]) => {
            if (Array.isArray(value)) {
              return `${key}: ${value.join(', ')}`;
            }
            return `${key}: ${value}`;
          })
          .join('; ');
        setApiError(errorMessages);
      } else {
        setApiError('Ошибка при отправке заявки. Попробуйте позже.');
      }
    }
  };

  if (success) {
    return (
      <div className={styles.registerPage}>
        <div className={styles.registerPage__success}>
          <h2>Заявка отправлена!</h2>
          <p>{successMessage}</p>
          <p>Вы будете перенаправлены на страницу входа...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.registerPage}>
      <div className={styles.registerPage__container}>
        <h1 className={styles.registerPage__title}>Стать поставщиком</h1>
        <p className={styles.registerPage__subtitle}>
          Заполните форму — данные компании и предложение товара. Администратор рассмотрит вашу заявку.
        </p>

        {apiError && (
          <div className={styles.formError} role="alert">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {apiError}
          </div>
        )}

        <form className={styles.registerPage__form} onSubmit={handleSubmit} noValidate>
          {/* Company Info */}
          <fieldset className={styles.registerPage__section}>
            <legend className={styles.registerPage__sectionTitle}>Информация о компании</legend>
            
            <div className={styles.formField}>
              <label htmlFor="name" className={styles.formField__label}>
                Название компании <span className={styles.required}>*</span>
              </label>
              <input
                id="name"
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className={`${styles.formField__input} ${errors.name ? styles.hasError : ''}`}
                placeholder="ООО Ромашка"
                aria-required="true"
                aria-invalid={!!errors.name}
              />
              {errors.name && <span className={styles.formField__error}>{errors.name}</span>}
            </div>

            <div className={styles.formField}>
              <label htmlFor="email" className={styles.formField__label}>
                Email <span className={styles.required}>*</span>
              </label>
              <input
                id="email"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`${styles.formField__input} ${errors.email ? styles.hasError : ''}`}
                placeholder="supplier@example.com"
                autoComplete="email"
                aria-required="true"
                aria-invalid={!!errors.email}
              />
              {errors.email && <span className={styles.formField__error}>{errors.email}</span>}
            </div>

            <div className={styles.formField}>
              <label htmlFor="password" className={styles.formField__label}>
                Пароль <span className={styles.required}>*</span>
              </label>
              <input
                id="password"
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={`${styles.formField__input} ${errors.password ? styles.hasError : ''}`}
                placeholder="Минимум 8 символов"
                autoComplete="new-password"
                aria-required="true"
                aria-invalid={!!errors.password}
              />
              {errors.password && <span className={styles.formField__error}>{errors.password}</span>}
            </div>

            <div className={styles.formField}>
              <label htmlFor="confirmPassword" className={styles.formField__label}>
                Подтвердите пароль <span className={styles.required}>*</span>
              </label>
              <input
                id="confirmPassword"
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className={`${styles.formField__input} ${errors.confirmPassword ? styles.hasError : ''}`}
                placeholder="Повторите пароль"
                autoComplete="new-password"
                aria-required="true"
                aria-invalid={!!errors.confirmPassword}
              />
              {errors.confirmPassword && <span className={styles.formField__error}>{errors.confirmPassword}</span>}
            </div>

            <div className={styles.formField}>
              <label htmlFor="contact_person" className={styles.formField__label}>
                Контактное лицо
              </label>
              <input
                id="contact_person"
                type="text"
                name="contact_person"
                value={formData.contact_person}
                onChange={handleChange}
                className={styles.formField__input}
                placeholder="Иван Иванов"
              />
            </div>

            <div className={styles.formField}>
              <label htmlFor="phone" className={styles.formField__label}>
                Телефон
              </label>
              <input
                id="phone"
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className={`${styles.formField__input} ${errors.phone ? styles.hasError : ''}`}
                placeholder="+7 (900) 123-45-67"
                autoComplete="tel"
              />
              {errors.phone && <span className={styles.formField__error}>{errors.phone}</span>}
            </div>

            <div className={styles.registerPage__row}>
              <div className={styles.formField}>
                <label htmlFor="inn" className={styles.formField__label}>
                  ИНН
                </label>
                <input
                  id="inn"
                  type="text"
                  name="inn"
                  value={formData.inn}
                  onChange={handleChange}
                  className={`${styles.formField__input} ${errors.inn ? styles.hasError : ''}`}
                  placeholder="1234567890"
                  maxLength={12}
                />
                {errors.inn && <span className={styles.formField__error}>{errors.inn}</span>}
              </div>

              <div className={styles.formField}>
                <label htmlFor="kpp" className={styles.formField__label}>
                  КПП
                </label>
                <input
                  id="kpp"
                  type="text"
                  name="kpp"
                  value={formData.kpp}
                  onChange={handleChange}
                  className={styles.formField__input}
                  placeholder="123456789"
                  maxLength={9}
                />
              </div>
            </div>

            <div className={styles.formField}>
              <label htmlFor="legal_address" className={styles.formField__label}>
                Юридический адрес
              </label>
              <input
                id="legal_address"
                type="text"
                name="legal_address"
                value={formData.legal_address}
                onChange={handleChange}
                className={styles.formField__input}
                placeholder="г. Москва, ул. Примерная д.1"
              />
            </div>

            <div className={styles.formField}>
              <label htmlFor="website" className={styles.formField__label}>
                Веб-сайт
              </label>
              <input
                id="website"
                type="url"
                name="website"
                value={formData.website}
                onChange={handleChange}
                className={styles.formField__input}
                placeholder="https://example.com"
              />
            </div>
          </fieldset>

          {/* Product Proposal */}
          <fieldset className={styles.registerPage__section}>
            <legend className={styles.registerPage__sectionTitle}>Предложение товара</legend>
            
            <div className={styles.formField}>
              <label htmlFor="product_name" className={styles.formField__label}>
                Название товара <span className={styles.required}>*</span>
              </label>
              <input
                id="product_name"
                type="text"
                name="product_name"
                value={formData.product_name}
                onChange={handleChange}
                className={`${styles.formField__input} ${errors.product_name ? styles.hasError : ''}`}
                placeholder="Ноутбук ASUS VivoBook 15"
                aria-required="true"
                aria-invalid={!!errors.product_name}
              />
              {errors.product_name && <span className={styles.formField__error}>{errors.product_name}</span>}
            </div>

            <div className={styles.formField}>
              <label htmlFor="product_sku" className={styles.formField__label}>
                Артикул товара
              </label>
              <input
                id="product_sku"
                type="text"
                name="product_sku"
                value={formData.product_sku}
                onChange={handleChange}
                className={styles.formField__input}
                placeholder="ASUS-VB-15-i5"
              />
            </div>

            <div className={styles.formField}>
              <label htmlFor="product_description" className={styles.formField__label}>
                Описание товара
              </label>
              <textarea
                id="product_description"
                name="product_description"
                value={formData.product_description}
                onChange={handleChange}
                className={styles.formField__textarea}
                placeholder="15.6 дюймов, Intel Core i5, 8GB RAM, 512GB SSD"
                rows={3}
              />
            </div>

            <div className={styles.registerPage__row}>
              <div className={styles.formField}>
                <label htmlFor="quantity" className={styles.formField__label}>
                  Количество
                </label>
                <input
                  id="quantity"
                  type="number"
                  name="quantity"
                  value={formData.quantity}
                  onChange={handleChange}
                  className={styles.formField__input}
                  min="1"
                  placeholder="1"
                />
              </div>

              <div className={styles.formField}>
                <label htmlFor="suggested_price" className={styles.formField__label}>
                  Предложенная цена (₽)
                </label>
                <input
                  id="suggested_price"
                  type="number"
                  name="suggested_price"
                  value={formData.suggested_price}
                  onChange={handleChange}
                  className={`${styles.formField__input} ${errors.suggested_price ? styles.hasError : ''}`}
                  placeholder="45000"
                  min="0"
                  step="0.01"
                />
                {errors.suggested_price && <span className={styles.formField__error}>{errors.suggested_price}</span>}
              </div>
            </div>

            <div className={styles.formField}>
              <label htmlFor="product_notes" className={styles.formField__label}>
                Notes к товару
              </label>
              <textarea
                id="product_notes"
                name="product_notes"
                value={formData.product_notes}
                onChange={handleChange}
                className={styles.formField__textarea}
                placeholder="Гарантия 2 года, есть в наличии"
                rows={2}
              />
            </div>
          </fieldset>

          <button 
            type="submit" 
            className={`${styles.submitButton} ${styles.isPrimary}`}
            disabled={isLoading}
          >
            {isLoading ? 'Отправка заявки...' : 'Отправить заявку'}
          </button>
        </form>

        <div className={styles.registerPage__footer}>
          <p>Уже есть аккаунт? <Link to="/" onClick={(e) => { e.preventDefault(); navigate('/', { state: { openLoginModal: true } }); }}>Войти</Link></p>
        </div>
      </div>
    </div>
  );
};
