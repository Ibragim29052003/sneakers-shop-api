import { useState, useMemo } from 'react';
import {
  useCreateSupplierRequestMutation,
  useGetSuppliersQuery,
} from '@/services/api/suppliersApi';
import type { CreateSupplierRequest } from '@/services/api/suppliersApi';
import styles from './CreateSupplierRequestForm.module.scss';

interface FormErrors {
  supplier?: string;
  product_name?: string;
  quantity?: string;
  suggested_price?: string;
  product_sku?: string;
}

interface CreateSupplierRequestFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

const CreateSupplierRequestForm: React.FC<CreateSupplierRequestFormProps> = ({
  onSuccess,
  onCancel,
}) => {
  const [createRequest, { isLoading: isSubmitting }] = useCreateSupplierRequestMutation();
  const { data: suppliers, isLoading: isSuppliersLoading } = useGetSuppliersQuery();

  const [formData, setFormData] = useState<CreateSupplierRequest>({
    supplier: 0,
    product_name: '',
    product_sku: '',
    product_description: '',
    quantity: 1,
    suggested_price: undefined,
    notes: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);

  // Валидация полей
  const validateField = useMemo(() => {
    return (name: string, value: string | number | null | undefined): string | undefined => {
      switch (name) {
        case 'supplier':
          if (!value || (typeof value === 'number' && value === 0)) {
            return 'Пожалуйста, выберите поставщика';
          }
          break;
        case 'product_name':
          if (!value || (typeof value === 'string' && value.trim() === '')) {
            return 'Пожалуйста, введите название товара';
          }
          if (typeof value === 'string' && value.length < 3) {
            return 'Название товара должно содержать минимум 3 символа';
          }
          if (typeof value === 'string' && value.length > 200) {
            return 'Название товара не должно превышать 200 символов';
          }
          break;
        case 'quantity':
          if (typeof value === 'number') {
            if (value < 1) {
              return 'Количество должно быть не менее 1';
            }
            if (!Number.isInteger(value)) {
              return 'Количество должно быть целым числом';
            }
            if (value > 1000000) {
              return 'Количество не должно превышать 1 000 000';
            }
          }
          break;
        case 'suggested_price':
          if (value !== undefined && value !== null && value !== '') {
            const numValue = typeof value === 'string' ? parseFloat(value) : value;
            if (isNaN(numValue)) {
              return 'Введите корректную цену';
            }
            if (numValue <= 0) {
              return 'Цена должна быть больше 0';
            }
            if (numValue > 100000000) {
              return 'Цена не должна превышать 100 000 000';
            }
          }
          break;
        case 'product_sku':
          if (value && typeof value === 'string' && value.length > 50) {
            return 'Артикул не должен превышать 50 символов';
          }
          break;
        default:
          break;
      }
      return undefined;
    };
  }, []);

  // Обработчик изменения полей
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    
    let processedValue: string | number | null | undefined = value;
    
    if (type === 'number') {
      processedValue = value === '' ? null : parseFloat(value);
    }

    setFormData((prev) => ({
      ...prev,
      [name]: processedValue,
    }));

    // Валидация при изменении
    if (touched[name]) {
      const error = validateField(name, processedValue);
      setErrors((prev) => ({
        ...prev,
        [name]: error,
      }));
    }
  };

  // Обработчик потери фокуса
  const handleBlur = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    setTouched((prev) => ({
      ...prev,
      [name]: true,
    }));

    const processedValue = value;
    const error = validateField(name, formData[name as keyof CreateSupplierRequest]);
    setErrors((prev) => ({
      ...prev,
      [name]: error,
    }));
  };

  // Проверка всей формы перед отправкой
  const validateForm = useMemo(() => {
    const newErrors: FormErrors = {};
    let isValid = true;

    const supplierError = validateField('supplier', formData.supplier);
    if (supplierError) {
      newErrors.supplier = supplierError;
      isValid = false;
    }

    const productNameError = validateField('product_name', formData.product_name);
    if (productNameError) {
      newErrors.product_name = productNameError;
      isValid = false;
    }

    const quantityError = validateField('quantity', formData.quantity);
    if (quantityError) {
      newErrors.quantity = quantityError;
      isValid = false;
    }

    const priceError = validateField('suggested_price', formData.suggested_price);
    if (priceError) {
      newErrors.suggested_price = priceError;
      isValid = false;
    }

    const skuError = validateField('product_sku', formData.product_sku);
    if (skuError) {
      newErrors.product_sku = skuError;
      isValid = false;
    }

    setErrors(newErrors);
    setTouched({
      supplier: true,
      product_name: true,
      quantity: true,
      suggested_price: true,
      product_sku: true,
    });

    return isValid;
  }, [formData, validateField]);

  // Отправка формы
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitSuccess(false);

    if (!validateForm) {
      return;
    }

    // Подготовка данных для отправки
    const dataToSend = { ...formData };
    
    // Удаляем пустые строки и undefined значения, чтобы не отправлять их на сервер
    Object.keys(dataToSend).forEach((key) => {
      const value = dataToSend[key as keyof CreateSupplierRequest];
      if (value === '' || value === undefined) {
        delete (dataToSend as Record<string, unknown>)[key];
      }
    });

    console.log('Отправка данных:', dataToSend);

    try {
      await createRequest(dataToSend).unwrap();
      setSubmitSuccess(true);
      
      // Сброс формы
      setFormData({
        supplier: 0,
        product_name: '',
        product_sku: '',
        product_description: '',
        quantity: 1,
        suggested_price: undefined,
        notes: '',
      });
      setTouched({});
      setErrors({});

      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      console.error('Ошибка при создании заявки:', err);
      setSubmitError('Не удалось создать заявку. Пожалуйста, попробуйте ещё раз.');
    }
  };

  // Функция для получения класса ошибки
  const getInputClassName = (fieldName: keyof FormErrors): string => {
    const baseClass = styles.formField__input;
    const errorClass = styles['formField__input--error'];
    const validClass = styles['formField__input--valid'];
    
    if (touched[fieldName] && errors[fieldName]) {
      return `${baseClass} ${errorClass}`;
    }
    if (touched[fieldName] && !errors[fieldName]) {
      const formValue = formData[fieldName as keyof CreateSupplierRequest];
      if (formValue !== undefined && formValue !== null && formValue !== '') {
        return `${baseClass} ${validClass}`;
      }
    }
    return baseClass;
  };

  if (isSuppliersLoading) {
    return (
      <div className={styles.loading} role="status" aria-live="polite">
        Загрузка поставщиков...
      </div>
    );
  }

  if (submitSuccess) {
    return (
      <div className={styles.successMessage} role="alert">
        <div className={styles.successMessage__icon} aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
        </div>
        <h2 className={styles.successMessage__title}>Заявка успешно создана!</h2>
        <p className={styles.successMessage__text}>
          Ваша заявка на поставку товара была отправлена на рассмотрение.
        </p>
        <button
          type="button"
          className={`${styles.button} ${styles['button--primary']}`}
          onClick={() => setSubmitSuccess(false)}
        >
          Создать ещё одну заявку
        </button>
      </div>
    );
  }

  return (
    <form 
      className={styles.form} 
      onSubmit={handleSubmit}
      noValidate
      aria-labelledby="form-title"
    >
      <h2 id="form-title" className={styles.form__title}>Создание заявки на поставку</h2>

      {submitError && (
        <div className={styles.formError} role="alert">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {submitError}
        </div>
      )}

      {/* Выбор поставщика */}
      <div className={styles.formField}>
        <label 
          htmlFor="supplier" 
          className={styles.formField__label}
        >
          Поставщик <span className={styles.required}>*</span>
        </label>
        <select
          id="supplier"
          name="supplier"
          className={`${styles.formField__select} ${touched.supplier && errors.supplier ? styles['formField__select--error'] : ''}`}
          value={formData.supplier || ''}
          onChange={handleChange}
          onBlur={handleBlur}
          aria-required="true"
          aria-invalid={touched.supplier && !!errors.supplier}
          aria-describedby={errors.supplier ? 'supplier-error' : undefined}
        >
          <option value="" disabled>Выберите поставщика</option>
          {suppliers?.map((supplier) => (
            <option key={supplier.id} value={supplier.id}>
              {supplier.name}
            </option>
          ))}
        </select>
        {touched.supplier && errors.supplier && (
          <p id="supplier-error" className={styles.formField__error} role="alert">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {errors.supplier}
          </p>
        )}
      </div>

      {/* Название товара */}
      <div className={styles.formField}>
        <label 
          htmlFor="product_name" 
          className={styles.formField__label}
        >
          Название товара <span className={styles.required}>*</span>
        </label>
        <input
          type="text"
          id="product_name"
          name="product_name"
          className={getInputClassName('product_name')}
          value={formData.product_name}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder="Введите название товара"
          aria-required="true"
          aria-invalid={touched.product_name && !!errors.product_name}
          aria-describedby={errors.product_name ? 'product_name-error' : undefined}
          maxLength={200}
        />
        {touched.product_name && errors.product_name && (
          <p id="product_name-error" className={styles.formField__error} role="alert">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {errors.product_name}
          </p>
        )}
      </div>

      {/* Артикул товара */}
      <div className={styles.formField}>
        <label 
          htmlFor="product_sku" 
          className={styles.formField__label}
        >
          Артикул товара
        </label>
        <input
          type="text"
          id="product_sku"
          name="product_sku"
          className={getInputClassName('product_sku')}
          value={formData.product_sku || ''}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder="Введите артикул (если есть)"
          aria-invalid={touched.product_sku && !!errors.product_sku}
          aria-describedby={errors.product_sku ? 'product_sku-error' : 'product_sku-hint'}
          maxLength={50}
        />
        {touched.product_sku && errors.product_sku && (
          <p id="product_sku-error" className={styles.formField__error} role="alert">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {errors.product_sku}
          </p>
        )}
        <p id="product_sku-hint" className={styles.formField__hint}>
          Необязательное поле
        </p>
      </div>

      {/* Описание товара */}
      <div className={styles.formField}>
        <label 
          htmlFor="product_description" 
          className={styles.formField__label}
        >
          Описание товара
        </label>
        <textarea
          id="product_description"
          name="product_description"
          className={styles.formField__textarea}
          value={formData.product_description || ''}
          onChange={handleChange}
          placeholder="Введите описание товара (характеристики, особенности)"
          rows={4}
          aria-describedby="product_description-hint"
        />
        <p id="product_description-hint" className={styles.formField__hint}>
          Необязательное поле
        </p>
      </div>

      {/* Количество и цена в одной строке */}
      <div className={styles.formRow}>
        {/* Количество */}
        <div className={styles.formField}>
          <label 
            htmlFor="quantity" 
            className={styles.formField__label}
          >
            Количество <span className={styles.required}>*</span>
          </label>
          <div className={styles.inputWithSuffix}>
            <input
              type="number"
              id="quantity"
              name="quantity"
              className={`${styles.formField__input} ${styles['formField__input--withSuffix']}`}
              value={formData.quantity}
              onChange={handleChange}
              onBlur={handleBlur}
              min="1"
              max="1000000"
              step="1"
              aria-required="true"
              aria-invalid={touched.quantity && !!errors.quantity}
              aria-describedby={errors.quantity ? 'quantity-error' : 'quantity-hint'}
            />
            <span className={styles.inputSuffix} aria-hidden="true">шт.</span>
          </div>
          {touched.quantity && errors.quantity && (
            <p id="quantity-error" className={styles.formField__error} role="alert">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              {errors.quantity}
            </p>
          )}
          <p id="quantity-hint" className={styles.formField__hint}>
            Минимум 1 шт.
          </p>
        </div>

        {/* Предложенная цена */}
        <div className={styles.formField}>
          <label 
            htmlFor="suggested_price" 
            className={styles.formField__label}
          >
            Предложенная цена
          </label>
          <div className={styles.inputWithSuffix}>
            <input
              type="number"
              id="suggested_price"
              name="suggested_price"
              className={`${styles.formField__input} ${styles['formField__input--withSuffix']}`}
              value={formData.suggested_price || ''}
              onChange={handleChange}
              onBlur={handleBlur}
              min="0.01"
              max="100000000"
              step="0.01"
              placeholder="0.00"
              aria-invalid={touched.suggested_price && !!errors.suggested_price}
              aria-describedby={errors.suggested_price ? 'suggested_price-error' : 'suggested_price-hint'}
            />
            <span className={styles.inputSuffix} aria-hidden="true">₽</span>
          </div>
          {touched.suggested_price && errors.suggested_price && (
            <p id="suggested_price-error" className={styles.formField__error} role="alert">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              {errors.suggested_price}
            </p>
          )}
          <p id="suggested_price-hint" className={styles.formField__hint}>
            Цена за единицу в рублях
          </p>
        </div>
      </div>

      {/* Примечания */}
      <div className={styles.formField}>
        <label 
          htmlFor="notes" 
          className={styles.formField__label}
        >
          Примечания
        </label>
        <textarea
          id="notes"
          name="notes"
          className={styles.formField__textarea}
          value={formData.notes || ''}
          onChange={handleChange}
          placeholder="Дополнительная информация к заявке"
          rows={3}
          aria-describedby="notes-hint"
        />
        <p id="notes-hint" className={styles.formField__hint}>
          Необязательное поле
        </p>
      </div>

      {/* Кнопки формы */}
      <div className={styles.form__actions}>
        {onCancel && (
          <button
            type="button"
            className={`${styles.button} ${styles['button--secondary']}`}
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Отмена
          </button>
        )}
        <button
          type="submit"
          className={`${styles.button} ${styles['button--primary']}`}
          disabled={isSubmitting}
          aria-busy={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <span className={styles.spinner} aria-hidden="true"></span>
              Создание...
            </>
          ) : (
            'Создать заявку'
          )}
        </button>
      </div>

      <p className={styles.form__requiredNote}>
        <span className={styles.required}>*</span> — обязательные поля
      </p>
    </form>
  );
};

export default CreateSupplierRequestForm;
