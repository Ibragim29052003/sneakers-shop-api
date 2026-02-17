import { useState, useRef, useEffect } from "react";
import { useAppDispatch, useAppSelector } from "@/redux/store";
import styles from "./SortPanel.module.scss";
import { selectFilters } from "@/redux/filter/selectors";
import { setSortBy, setIsNew } from "@/redux/filter/slice";
import Arrow from "@/shared/assets/icons/header/arrow-down.svg?react";

const SORT_OPTIONS = [
  { value: "new", label: "Новинки" },
  { value: "price_asc", label: "Цена по возрастанию" },
  { value: "price_desc", label: "Цена по убыванию" },
];

const SortPanel = () => {
  const dispatch = useAppDispatch();
  const filters = useAppSelector(selectFilters);
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const handleSelect = (value: string) => {
    dispatch(setSortBy(value as "new" | "price_asc" | "price_desc"));
    if (value === "new") dispatch(setIsNew(true));
    else if (filters.isNew) dispatch(setIsNew(undefined));
    setOpen(false);
  };

  // закрытие при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // управление клавишами
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") setOpen(false);
  };

  const currentLabel =
    SORT_OPTIONS.find((opt) => opt.value === filters.sortBy)?.label ||
    "Сортировать";

  return (
    <div className={styles.sortPanel} onKeyDown={handleKeyDown}>
      <label className={styles.sortPanel__label}>Сортировать по:</label>
      <div
        className={`${styles.sortPanel__customSelect} ${
          open ? styles.sortPanel__customSelect_open : ""
        }`}
        onClick={() => setOpen(!open)}
        tabIndex={0}
        role="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        ref={wrapperRef}
      >
        <span className={styles.sortPanel__selected}>{currentLabel}</span>
        <Arrow
          className={`${styles.sortPanel__icon} ${
            open ? styles.sortPanel__icon_open : ""
          }`}
        />

        {open && (
          <ul className={styles.sortPanel__options} role="listbox">
            {SORT_OPTIONS.map((opt) => (
              <li
                key={opt.value}
                className={`${styles.sortPanel__option} ${
                  filters.sortBy === opt.value
                    ? styles.sortPanel__option_active
                    : ""
                }`}
                role="option"
                aria-selected={filters.sortBy === opt.value}
                onClick={() => handleSelect(opt.value)}
                tabIndex={0}
              >
                {opt.label}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default SortPanel;
