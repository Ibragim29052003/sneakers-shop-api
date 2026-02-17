import { Navigate, Route, Routes } from "react-router-dom";
import WomenPage from "@/pages/women-page/WomenPage";
import MenPage from "@/pages/men-page/MenPage";
import ChildrenPage from "@/pages/children-page/ChildrenPage";
import AboutPage from "@/pages/about-page/AboutPage";
import ProductDetailPage from "@/pages/product-detail-page";

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
    </Routes>
  );
};

export default AppRouter;
