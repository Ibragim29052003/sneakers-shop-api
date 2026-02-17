import styles from "./FilterCheckboxGroup.module.scss";

interface FilterCheckboxGroupProps<T extends string> {
  legend: string; // заголовок группы
  options: readonly T[]; // все возможные варианты
  selected: T[]; // выбранные значения
  onChange: (values: T[]) => void; // колбэк при изменении
  counts?: Record<string, number>; // добавляем опциональное поле для подсчетов
}

const FilterCheckboxGroup = <T extends string>({
  legend,
  options,
  selected,
  onChange,
  counts = {}, // по умолчанию пустой объект
}: FilterCheckboxGroupProps<T>) => {
  // если значение есть — удаляем, если значения нет — добавляем (такая логика типична для чекбоксов)
  const toggleValue = (value: T) => {
    return selected.includes(value)
      ? // filter для иммутабельного изменения, то есть наша функция всегда возвращает новый массив не изменяя исходный
        selected.filter((item) => item !== value)
      : [...selected, value];
  };

  return (
    <fieldset className={styles.filterCheckbox__group}>
      <legend className={styles.filterCheckbox__legend}>{legend}</legend>
      <ul className={styles.filterCheckbox__list}>
        {options.map((option) => {
          return (
            <li className={styles.filterCheckbox__item} key={option}>
              <label className={styles.filterCheckbox__label}>
                <input
                  type="checkbox"
                  className={styles.filterCheckbox__checkbox}
                  checked={selected.includes(option)}
                  onChange={() => onChange(toggleValue(option))}
                />
                <div className={styles.filterCheckbox__info}>
                  <span className={styles.filterCheckbox__text}>{option}</span>
                  <span className={styles.filterCheckbox__count}>
                    {counts[option.toLowerCase()] ?? 0}
                  </span>
                </div>
              </label>
            </li>
          );
        })}
      </ul>
    </fieldset>
  );
};

export default FilterCheckboxGroup;
