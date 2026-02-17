import { useEffect, useRef, useState, type FC } from "react";
import styles from "./Header.module.scss";
import Arrow from "@/shared/assets/icons/header/arrow-down.svg?react";
import Search from "@/shared/assets/icons/header/search.svg?react";
import TransitionWB from "@/shared/assets/icons/header/transition-wb.svg?react";
import Logo from "@/shared/assets/icons/Logo.svg?react";
import { Link, useLocation } from "react-router-dom";
import DropdownMenu from "./DropdownMenu";

const Header: FC = () => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [isCategoriesOpen, setIsCategoriesOpen] = useState(false);
  const [isHidden, setIsHidden] = useState(false);

  const location = useLocation();
  const currentPath = location.pathname;
  const isMainActive = ["/women", "/men", "/children"].includes(currentPath);

  const burgerRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  type NavItem = {
    link?: string;
    text: string;
  };

  const categories: NavItem[] = [
    { link: "/women", text: "Женщинам" },
    { link: "/men", text: "Мужчинам" },
    { link: "/children", text: "Детям" },
  ];

  const navItems: NavItem[] = [
    { text: "Главная" },
    { link: "/about", text: "О нас" },
  ];

  useEffect(() => {
    if (!isCategoriesOpen && !menuOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsCategoriesOpen(false);
        setMenuOpen(false);
      }
    };
    const handleClickOutside = (event: MouseEvent) => {
      if (
        listRef.current &&
        !listRef.current.contains(event.target as Node) && // если был клик вне списка
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node) && // если был клик вне кнопки
        burgerRef.current &&
        !burgerRef.current.contains(event.target as Node) // если был клик вне бургера
      ) {
        setIsCategoriesOpen(false);
        setMenuOpen(false);
      }
    };
    document.addEventListener("click", handleClickOutside); // слушаем клики по всему документу
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("click", handleClickOutside); // функция очистки, выполнится при размонтировании или изменении isCategoriesOpen
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isCategoriesOpen, menuOpen]);

  useEffect(() => {
    if (isCategoriesOpen) {
      // когда dropdown открывается, фокусируемся на активной категории или первой
      const activeLink = listRef.current?.querySelector(
        `a[href="${currentPath}"]`
      ) as HTMLAnchorElement;
      const firstLink = listRef.current?.querySelector(
        "a"
      ) as HTMLAnchorElement;
      if (activeLink) {
        activeLink.focus();
      } else if (firstLink) {
        firstLink.focus();
      }
    }
  }, [isCategoriesOpen, currentPath]);

  // для умного скрывания шапки
  useEffect(() => {
    let lastScrollY = window.scrollY;
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        // скроллим вниз
        setIsHidden(true);
      } else {
        // скроллим вверх
        setIsHidden(false);
      }
      lastScrollY = currentScrollY;
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header className={styles.header}>
      <div
        className={`${styles.header__fixed} ${
          isHidden ? styles.header__fixed_hidden : ""
        }`}
      >
        <div className="container">
          <nav className={styles.header__nav} role="navigation">
            <Link
              to="/"
              aria-label="Вернуться на главную страницу"
              className={styles.header__logo}
            >
              <Logo className={styles.header__logo_logo} />
              <p className={styles.header__logo_text}>TaSaHa</p>
            </Link>

            <ul
              className={`${styles.header__list} ${
                menuOpen ? styles.header__list_open : ""
              }`}
              role={menuOpen ? "menu" : undefined}
              aria-hidden={!menuOpen}
            >
              {navItems.map((item, itemId) => (
                <li key={itemId} className={styles.header__list_item}>
                  {item.text === "Главная" ? (
                    <button
                      className={`${styles.header__expandable} ${
                        isMainActive ? styles.header__expandable_active : ""
                      }`}
                      onClick={() => setIsCategoriesOpen(!isCategoriesOpen)}
                      aria-expanded={isCategoriesOpen}
                      aria-controls="categories-list"
                      aria-haspopup="menu" // указывает, что кнопка открывает меню
                      ref={buttonRef}
                    >
                      {item.text}
                      <Arrow
                        className={`${styles.header__expandable_icon} ${
                          isCategoriesOpen
                            ? styles.header__expandable_icon_open
                            : ""
                        } `}
                      />
                    </button>
                  ) : (
                    <Link
                      to={item.link || "#"}
                      className={`${styles.header__list_link} ${
                        currentPath === item.link
                          ? styles.header__list_link_active
                          : ""
                      }`}
                      aria-label={`Перейти к странице ${item.text}`}
                      onClick={() => setMenuOpen(false)}
                    >
                      {item.text}
                    </Link>
                  )}
                  {item.text === "Главная" && (
                    <DropdownMenu
                      ref={listRef}
                      isOpen={isCategoriesOpen}
                      categories={categories}
                      currentPath={currentPath}
                      onClose={() => {
                        setIsCategoriesOpen(false);
                        setMenuOpen(false);
                      }}
                    />
                  )}
                </li>
              ))}
              {menuOpen && (
                <li className={styles.header__list_item}>
                  <a
                    href="https://www.wildberries.ru/brands/310895408-tasaha"
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`${styles.header__wb} ${styles.header__wb_menu}`}
                  >
                    <TransitionWB
                      className={styles.header__wb_icon}
                      aria-label="Иконка перехода на Wildberries"
                    />
                    <p className={styles.header__wb_text}>Перейти на WB</p>
                  </a>
                </li>
              )}
            </ul>
            <div className={styles.header__wb_search_wrapper}>
              <Search
                className={styles.header__search}
                aria-label="Иконка поиска"
              />
              {!menuOpen && (
                <a
                  href="https://www.wildberries.ru/brands/310895408-tasaha"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.header__wb}
                >
                  <TransitionWB
                    className={styles.header__wb_icon}
                    aria-label="Иконка перехода на Wildberries"
                  />
                  <p className={styles.header__wb_text}>Перейти на WB</p>
                </a>
              )}
            </div>

            <button
              className={`${styles.header__burger} ${
                menuOpen ? styles.header__burger_open : ""
              }`}
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label={menuOpen ? "Закрыть меню" : "Открыть меню"}
              aria-expanded={menuOpen}
              ref={burgerRef}
            >
              <span className={styles.header__burger_line}></span>
              <span className={styles.header__burger_line}></span>
              <span className={styles.header__burger_line}></span>
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
