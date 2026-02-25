import { configureStore } from "@reduxjs/toolkit";
import sliderReducer from "./slider/slice";
import filtersReducer from "./filter/slice";
import paginationReducer from "./pagination/slice";
import cartReducer from "./cart/slice";
import {
  useDispatch,
  type TypedUseSelectorHook,
  useSelector as useReduxSelector,
} from "react-redux";
import { productsApi } from "@/services/api/productsApi";

export const store = configureStore({
  reducer: {
    slider: sliderReducer,
    filters: filtersReducer,
    pagination: paginationReducer,
    cart: cartReducer,

    // добавляем RTK Query reducer
    [productsApi.reducerPath]: productsApi.reducer,
  },
  // мидлверка нужна для кеширования и подписок
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(productsApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
// продвинутый UseDispatch с типизацией
export type AppDispatch = typeof store.dispatch; // в AppDispatch будут все типы экшенов из всех слайсов

export const useAppDispatch = () => useDispatch<AppDispatch>();

// useSelector - типизированный хук для получения состояния из редакса
export const useAppSelector: TypedUseSelectorHook<RootState> = useReduxSelector;
