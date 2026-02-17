import { useState, useRef, useCallback, useMemo, useEffect, type FC, type ChangeEvent } from 'react';
import { useAppDispatch, useAppSelector } from '@/redux/store';
import { updateFilters } from '@/redux/filter/slice';
import { selectFilters } from '@/redux/filter/selectors';
import useDebounce from '@/hooks/useDebounce';
import styles from './PriceRange.module.scss';

interface PriceRangeProps {
  min: number;
  max: number;
}

const PriceRange: FC<PriceRangeProps> = ({ min, max }) => {
  const dispatch = useAppDispatch();
  const filters = useAppSelector(selectFilters);

  // вычисляем текущие значения на основе Redux и props
  const computedMinPrice = useMemo(() => {
    if (filters.minPrice !== undefined && filters.minPrice >= min && filters.minPrice <= max) {
      return filters.minPrice;
    }
    return min;
  }, [min, max, filters.minPrice]);

  const computedMaxPrice = useMemo(() => {
    if (filters.maxPrice !== undefined && filters.maxPrice >= min && filters.maxPrice <= max) {
      return filters.maxPrice;
    }
    return max;
  }, [min, max, filters.maxPrice]);

  // рефы для отслеживания предыдущих значений (чтобы избежать лишних обновлений)
  const prevMinRef = useRef<number | null>(null);
  const prevMaxRef = useRef<number | null>(null);

  // текущие значения в инпутах (могут быть пустыми во время ввода)
  const [localMinPrice, setLocalMinPrice] = useState<string>(() => String(computedMinPrice));
  const [localMaxPrice, setLocalMaxPrice] = useState<string>(() => String(computedMaxPrice));

  // обновляем локальные состояния при изменении вычисляемых значений
  // необходимая синхронизация с пропсами после загрузки данных
  useEffect(() => {
    if (prevMinRef.current === null || prevMinRef.current !== computedMinPrice) {
      prevMinRef.current = computedMinPrice;
      setTimeout(() => setLocalMinPrice(String(computedMinPrice)), 0);
    }
    if (prevMaxRef.current === null || prevMaxRef.current !== computedMaxPrice) {
      prevMaxRef.current = computedMaxPrice;
      setTimeout(() => setLocalMaxPrice(String(computedMaxPrice)), 0);
    }
  }, [computedMinPrice, computedMaxPrice]);

  // рефы для отслеживания фокуса
  const minInputRef = useRef<HTMLInputElement>(null);
  const maxInputRef = useRef<HTMLInputElement>(null);

  // Debounced значения для Redux
  const debouncedMinPrice = useDebounce(
    localMinPrice === '' ? undefined : Number(localMinPrice),
    500
  );
  const debouncedMaxPrice = useDebounce(
    localMaxPrice === '' ? undefined : Number(localMaxPrice),
    500
  );

  // применение значений к Redux - сравниваем с текущим состоянием в Redux, а не с локальным состоянием
  useEffect(() => {
    const newMinPrice = debouncedMinPrice;
    const newMaxPrice = debouncedMaxPrice;
    
    // Сравниваем с текущими значениями в Redux filters
    const needsUpdate = newMinPrice !== filters.minPrice || newMaxPrice !== filters.maxPrice;
    
    if (needsUpdate) {
      dispatch(updateFilters({
        minPrice: newMinPrice,
        maxPrice: newMaxPrice
      }));
    }
  }, [debouncedMinPrice, debouncedMaxPrice, dispatch, filters.minPrice, filters.maxPrice]);

  // вычисление позиции слайдера
  const currentMin = localMinPrice === '' ? computedMinPrice : Number(localMinPrice);
  const currentMax = localMaxPrice === '' ? computedMaxPrice : Number(localMaxPrice);
  const minPercent = ((currentMin - min) / (max - min)) * 100;
  const maxPercent = ((currentMax - min) / (max - min)) * 100;

  // обработка ввода - только обновляем состояние, без валидации
  const handleMinInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const rawValue = e.target.value;
    if (rawValue === '' || /^\d*$/.test(rawValue)) {
      setLocalMinPrice(rawValue);
    }
  };

  const handleMaxInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const rawValue = e.target.value;
    if (rawValue === '' || /^\d*$/.test(rawValue)) {
      setLocalMaxPrice(rawValue);
    }
  };

  // восстановление предыдущего значения при потере фокуса (если инпут пустой)
  const handleMinBlur = useCallback(() => {
    const value = localMinPrice === '' ? computedMinPrice : Number(localMinPrice);

    if (isNaN(value) || value < min) {
      setLocalMinPrice(String(computedMinPrice));
    } else if (value > max) {
      setLocalMinPrice(String(max));
    } else {
      // проверяем, что min <= max
      const currentMaxVal = localMaxPrice === '' ? computedMaxPrice : Number(localMaxPrice);
      if (value > currentMaxVal) {
        // min не может быть больше max, восстанавливаем к предыдущему
        setLocalMinPrice(String(computedMinPrice));
      } else {
        setLocalMinPrice(String(value));
      }
    }
  }, [localMinPrice, localMaxPrice, computedMinPrice, computedMaxPrice, min, max]);

  const handleMaxBlur = useCallback(() => {
    const value = localMaxPrice === '' ? computedMaxPrice : Number(localMaxPrice);

    if (isNaN(value) || value > max) {
      setLocalMaxPrice(String(computedMaxPrice));
    } else if (value < min) {
      setLocalMaxPrice(String(min));
    } else {
      // проверяем, что max >= min
      const currentMinVal = localMinPrice === '' ? computedMinPrice : Number(localMinPrice);
      if (value < currentMinVal) {
        // max не может быть меньше min, восстанавливаем к предыдущему
        setLocalMaxPrice(String(computedMaxPrice));
      } else {
        setLocalMaxPrice(String(value));
      }
    }
  }, [localMinPrice, localMaxPrice, computedMinPrice, computedMaxPrice, min, max]);

  // обработчики для слайдера
  const handleMinChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = Math.min(Number(e.target.value), currentMax);
    setLocalMinPrice(String(value));
  };

  const handleMaxChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = Math.max(Number(e.target.value), currentMin);
    setLocalMaxPrice(String(value));
  };

  return (
    <div className={styles.priceRange}>
      <h3 className={styles.priceRange__title}>Цена</h3>

      <div className={styles.priceRange__values}>
        <div className={styles.priceRange__inputGroup}>
          <label htmlFor="min-input" className={styles.priceRange__label}>
            От
          </label>
          <div className={styles.priceRange__inputWrapper}>
            <input
              ref={minInputRef}
              id="min-input"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={localMinPrice}
              onChange={handleMinInputChange}
              onBlur={handleMinBlur}
              className={styles.priceRange__input}
              aria-label="Минимальная цена"
              placeholder={String(min)}
            />
            <span className={styles.priceRange__currency}>₽</span>
          </div>
        </div>

        <div className={styles.priceRange__inputGroup}>
          <label htmlFor="max-input" className={styles.priceRange__label}>
            До
          </label>
          <div className={styles.priceRange__inputWrapper}>
            <input
              ref={maxInputRef}
              id="max-input"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={localMaxPrice}
              onChange={handleMaxInputChange}
              onBlur={handleMaxBlur}
              className={styles.priceRange__input}
              aria-label="Максимальная цена"
              placeholder={String(max)}
            />
            <span className={styles.priceRange__currency}>₽</span>
          </div>
        </div>
      </div>

      <div className={styles.priceRange__rangeContainer}>
        <div className={styles.priceRange__sliderTrack}>
          <div
            className={styles.priceRange__sliderFill}
            style={{
              left: `${minPercent}%`,
              right: `${100 - maxPercent}%`
            }}
          />

          <input
            type="range"
            min={min}
            max={max}
            value={currentMin}
            onChange={handleMinChange}
            className={`${styles.priceRange__slider} ${styles.priceRange__sliderMin}`}
            aria-label="Минимальная цена"
          />

          <input
            type="range"
            min={min}
            max={max}
            value={currentMax}
            onChange={handleMaxChange}
            className={`${styles.priceRange__slider} ${styles.priceRange__sliderMax}`}
            aria-label="Максимальная цена"
          />
        </div>
      </div>
    </div>
  );
};

export default PriceRange;
