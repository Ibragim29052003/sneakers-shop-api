import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider, Layout } from "antd";
import ru_RU from "antd/locale/ru_RU";
import styles from "./App.module.scss";
import Header from "@/widgets/header/Header";
import Footer from "@/widgets/footer/Footer";
import AppRouter from './router/AppRouter'

const App = () => {
  // Создаём клиент для TanStack Query, который управляет API-запросами, кешированием и синхронизацией данных.
  // retry: 1 - автоматически повторяет неудачные запросы 1 раз для повышения стабильности при плохом интернете.
  // Создаю для будущего сервера

  const client = new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
      },
    },
  });

  return (
    // оборачиваем все приложение в провайдер клиента TanStack Query для доступа к функционалу запросов из любого компонента.
    // без этого провайдера TanStack Query не сможет работать.
    <QueryClientProvider client={client}>
      {/* locale={ru_RU} — делаем весь интерфейс на русском */}
      <ConfigProvider locale={ru_RU}>
        <Layout className={styles.layout}>
          {/* Основной контент приложения будет здесь */}
          <Header />
          <Layout.Content className="container"> {/* Основная часть страницы */}
            <AppRouter /> {/* Роутер — здесь будут страницы */}
          </Layout.Content>
          <Footer />
        </Layout>
      </ConfigProvider>
    </QueryClientProvider>
  );
};

export default App;
