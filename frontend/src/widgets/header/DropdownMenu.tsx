import { forwardRef } from "react";
import styles from "./Header.module.scss";
import { Link } from "react-router-dom";

type NavItem = {
  link?: string;
  text: string;
};

interface DropdownMenuProps {
  isOpen: boolean;
  categories: NavItem[];
  currentPath: string;
  onClose: () => void
}

// forwardRef - позволяет родительскому компоненту передать ref этому компоненту
// первый параметр - тип рефа (HTMLUListElement (тип элемента, на который ссылается ref) ),
// второй - тип пропсов (DropdownMenuProps)
const DropdownMenu = forwardRef<HTMLUListElement, DropdownMenuProps>(
  // деструктурируем пропсы, listRef - второй параметр forwardRef, который приходит от родителя
  ({ isOpen, categories, currentPath, onClose }, listRef) => {
    return (
      <ul
        className={`${styles.header__categories_list} ${isOpen ? styles.header__categories_list_open : ''}`}
        ref={listRef}
        id="categories-list"
        role="menu"
        aria-hidden={!isOpen}
      >
        {categories.map((category, categoryIndex) => (
          <li key={categoryIndex} className={styles.header__categories_item} >
            <Link
              to={category.link || '#'}
              className={`${styles.header__categories_link} ${category.link === currentPath ? styles.header__categories_link_active : ''}`}
              aria-label={`Перейти к странице ${category.text}`}
              onClick={onClose}
            >
              {category.text}
            </Link>
          </li>
        ))}
      </ul>
    );
  }
);

export default DropdownMenu;
