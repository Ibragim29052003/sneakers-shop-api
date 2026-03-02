import { Navigate, Route, Routes } from "react-router-dom";
import WomenPage from "@/pages/women-page/WomenPage";
import MenPage from "@/pages/men-page/MenPage";
import ChildrenPage from "@/pages/children-page/ChildrenPage";
import AboutPage from "@/pages/about-page/AboutPage";
import ProductDetailPage from "@/pages/product-detail-page";
import CartPage from "@/pages/cart-page";
import SupplierRequestsPage from "@/pages/supplier-requests-page";
import { SupplierRegisterPage } from "@/pages/supplier-register-page";
import ManagerPage from "@/pages/manager-page";

// Компонент защиты маршрутов по ролям
interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
}

const ProtectedRoute = ({ children, allowedRoles = [] }: ProtectedRouteProps) => {
  // Получаем данные пользователя из localStorage
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;
  
  // Извлекаем роль пользователя
  let userRole: string | null = null;
  if (user) {
    // Проверяем поле role (может быть прямым полем или в массиве roles)
    if (user.role) {
      userRole = user.role;
    } else if (user.roles && Array.isArray(user.roles) && user.roles.length > 0) {
      // Берём первую роль из массива
      userRole = user.roles[0]?.role?.name || null;
    }
  }
  
  // Если пользователь не авторизован, перенаправляем на главную
  if (!user) {
    return <Navigate to="/women" replace />;
  }
  
  // Если есть список разрешённых ролей и роль пользователя не в этом списке
  if (allowedRoles.length > 0 && userRole && !allowedRoles.includes(userRole)) {
    // Поставщик -> на страницу заявок
    if (userRole === 'supplier') {
      return <Navigate to="/supplier-requests" replace />;
    }
    // Для остальных -> на главную
    return <Navigate to="/women" replace />;
  }
  
  return <>{children}</>;
};

const AppRouter = () => {
  return (
    // Routes - это контейнер для всех маршрутов. Он следит за URL и отображает нужный компонент
    <Routes>
      {/* Если пользователь открывает корневой путь "/", перенаправляем его на "/women" */}
      <Route path="/" element={<Navigate to="/women" replace />} />
      <Route path="/women" element={<WomenPage />} />
      <Route path="/men" element={<MenPage />} />
      <Route path="/children" element={<ChildrenPage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/product/:id" element={<ProductDetailPage />}/>
      <Route path="/cart" element={<CartPage />}/>
      <Route path="/supplier-requests" element={<SupplierRequestsPage />}/>
      <Route path="/register-supplier" element={<SupplierRegisterPage />}/>
      <Route path="/manager" element={
        <ProtectedRoute allowedRoles={['admin', 'manager']}>
          <ManagerPage />
        </ProtectedRoute>
      }/>
    </Routes>
  );
};

export default AppRouter;
