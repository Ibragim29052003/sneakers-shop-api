import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@/shared/scss/index.scss";
import App from "./app/App.tsx";
import { BrowserRouter } from "react-router-dom";
import { Provider } from "react-redux";
import { store } from "./redux/store.ts";

const root = createRoot(document.getElementById("root") as HTMLElement);

root.render(
  <StrictMode>
    {/* 
  BrowserRouter нужен для управления переходами между страницами без перезагрузки браузера
  Он позволяет сделать SPA (Single Page Application), где:
       1. URL в адресной строке меняется
       2. контент на странице меняется
       3. страница не перезагружается
        */}
    <Provider store={store}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Provider>
  </StrictMode>
);
