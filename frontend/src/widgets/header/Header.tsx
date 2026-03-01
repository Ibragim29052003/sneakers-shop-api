import { Link, useLocation } from "react-router-dom";
import { useEffect, useRef, useState, type FC } from "react";
import styles from "./Header.module.scss";
import Arrow from "@/shared/assets/icons/header/arrow-down.svg?react";
import Search from "@/shared/assets/icons/header/search.svg?react";
import TransitionWB from "@/shared/assets/icons/header/transition-wb.svg?react";
import Logo from "@/shared/assets/icons/Logo.svg?react";
import Basket from "@/shared/assets/icons/header/basket.svg?react";
import DropdownMenu from "./DropdownMenu";
import { LoginModal } from "@/components/LoginModal/LoginModal";
import { useAppSelector, useAppDispatch } from "@/redux/store";
import { clearCart, setCart } from "@/redux/cart/slice";

const Header: FC = () => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [isCategoriesOpen, setIsCategoriesOpen] = useState(false);
  const [isHidden, setIsHidden] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isSupplier, setIsSupplier] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isManager, setIsManager] = useState(false);

  const location = useLocation();
  const currentPath = location.pathname;
  const isMainActive = ["/women", "/men", "/children"].includes(currentPath);

  // Получаем общее количество товаров в корзине из Redux
  const cartTotalCount = useAppSelector((state) => state.cart.totalCount);
  const dispatch = useAppDispatch();

  const burgerRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Проверка авторизации и статуса поставщика при загрузке
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const isAuth = !!token;
    setIsAuthenticated(isAuth);
    
    console.log('Header mount, token exists:', !!token);
    
    // Если пользователь авторизован - загружаем его корзину и проверяем статус поставщика
    if (isAuth) {
      const loadUserCart = async () => {
        try {
          console.log('Fetching user cart from server...');
          const response = await fetch('/api/v1/cart/', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          
          console.log('Cart response status:', response.status);
          
          if (response.ok) {
            const cartData = await response.json();
            console.log('Server cart data:', cartData);
            dispatch(setCart({ items: cartData.items || [] }));
          } else if (response.status === 401) {
            console.log('Unauthorized - token might be invalid');
          } else {
            console.log('Failed to load cart, status:', response.status);
          }
        } catch (error) {
          console.error('Failed to load user cart:', error);
        }
      };
      
      // Проверка статуса поставщика и прав админа
      const checkSupplierStatus = async () => {
        try {
          const currentToken = localStorage.getItem("access_token");
          if (!currentToken) return;
          
          let isUserAdmin = false;
          
          // Сначала проверяем права админа из JWT токена
          try {
            const tokenParts = currentToken.split('.');
            if (tokenParts.length === 3) {
              const payload = JSON.parse(atob(tokenParts[1]));
              isUserAdmin = payload.is_staff || false;
              setIsAdmin(isUserAdmin);
              if (isUserAdmin) {
                setIsSupplier(true);
              }
            }
          } catch (e) {
            console.error('Failed to parse token:', e);
          }
          
          // Проверяем статус поставщика
          const supplierResponse = await fetch('/api/v1/my-supplier-profile/', {
            headers: {
              'Authorization': `Bearer ${currentToken}`,
              'Content-Type': 'application/json',
            },
          });
          
          // 200 - пользователь поставщик, 404 - не поставщик
          if (supplierResponse.ok) {
            setIsSupplier(true);
          } else if (!isUserAdmin) {
            // Если не админ и не поставщик - сбрасываем флаг
            setIsSupplier(false);
          }
          
          // Проверяем, является ли пользователь менеджером (есть ли заявки с его manager_id)
          if (!isUserAdmin) {
            try {
              const requestsResponse = await fetch('/api/v1/supplier-requests/?page_size=1', {
                headers: {
                  'Authorization': `Bearer ${currentToken}`,
                  'Content-Type': 'application/json',
                },
              });
              
              if (requestsResponse.ok) {
                const requestsData = await requestsResponse.json();
                // Если есть заявки, где user является менеджером
                const hasManagedRequests = requestsData.results?.some(
                  (r: { manager: number | null }) => r.manager !== null
                );
                setIsManager(hasManagedRequests);
              }
            } catch (e) {
              console.error('Failed to check manager status:', e);
            }
          }
        } catch (error) {
          console.error('Failed to check supplier status:', error);
          setIsSupplier(false);
        }
      };
      
      loadUserCart();
      checkSupplierStatus();
    } else {
      setIsSupplier(false);
    }
  }, [dispatch]);

  // Открыть модальное окно логина если передан state
  useEffect(() => {
    const locationState = location.state as { openLoginModal?: boolean } | null;
    if (locationState?.openLoginModal) {
      setIsAuthModalOpen(true);
      // Очищаем state чтобы не открывать модалку при обновлении страницы
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  // Обработчик выхода
  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    dispatch(clearCart());
    setIsAuthenticated(false);
    window.location.reload();
  };

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
    // Админ видит "Управление заявками", менеджер - "Панель менеджера", поставщик - "Предложить товар", обычный пользователь - "Стать поставщиком"
    isAdmin 
      ? { link: "/supplier-requests", text: "Управление заявками" }
      : isManager
        ? { link: "/manager", text: "Панель менеджера" }
        : isSupplier 
          ? { link: "/supplier-requests", text: "Предложить товар" }
          : { link: "/register-supplier", text: "Стать поставщиком" },
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
        !listRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node) &&
        burgerRef.current &&
        !burgerRef.current.contains(event.target as Node)
      ) {
        setIsCategoriesOpen(false);
        setMenuOpen(false);
      }
    };
    document.addEventListener("click", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("click", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isCategoriesOpen, menuOpen]);

  useEffect(() => {
    if (isCategoriesOpen) {
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

  useEffect(() => {
    let lastScrollY = window.scrollY;
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        setIsHidden(true);
      } else {
        setIsHidden(false);
      }
      lastScrollY = currentScrollY;
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
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
                        aria-haspopup="menu"
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
                    {isAuthenticated ? (
                      <button
                        className={`${styles.header__wb} ${styles.header__wb_menu}`}
                        onClick={handleLogout}
                      >
                        <TransitionWB
                          className={styles.header__wb_icon}
                          aria-label="Иконка выхода"
                        />
                        <p className={styles.header__wb_text}>Выйти</p>
                      </button>
                    ) : (
                      <button
                        className={`${styles.header__wb} ${styles.header__wb_menu}`}
                        onClick={() => setIsAuthModalOpen(true)}
                      >
                        <TransitionWB
                          className={styles.header__wb_icon}
                          aria-label="Иконка входа"
                        />
                        <p className={styles.header__wb_text}>Войти</p>
                      </button>
                    )}
                  </li>
                )}
              </ul>
              <div className={styles.header__wb_search_wrapper}>
                <Search
                  className={styles.header__search}
                  aria-label="Иконка поиска"
                />
                {!menuOpen && (
                  <>
                    <Link to="/cart" className={styles.header__cart} aria-label={`Корзина, ${cartTotalCount} товаров`}>
                      <Basket
                        className={styles.header__wb_cart}
                        aria-hidden="true"
                      />
                      {cartTotalCount > 0 && (
                        <span className={styles.header__cart_count} aria-live="polite">
                          {cartTotalCount}
                        </span>
                      )}
                    </Link>
                    {isAuthenticated ? (
                      <button
                        className={styles.header__wb}
                        onClick={handleLogout}
                      >
                        <TransitionWB
                          className={styles.header__wb_icon}
                          aria-label="Иконка выхода"
                        />
                        <p className={styles.header__wb_text}>Выйти</p>
                      </button>
                    ) : (
                      <button
                        className={styles.header__wb}
                        onClick={() => setIsAuthModalOpen(true)}
                      >
                        <TransitionWB
                          className={styles.header__wb_icon}
                          aria-label="Иконка входа"
                        />
                        <p className={styles.header__wb_text}>Войти</p>
                      </button>
                    )}
                  </>
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
      <LoginModal
        openModal={isAuthModalOpen}
        onOpenChange={setIsAuthModalOpen}
        onLoginSuccess={() => setIsAuthenticated(true)}
      />
    </>
  );
};

export default Header;
