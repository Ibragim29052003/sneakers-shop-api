import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { CartItem, CartState } from "./types";

const CART_STORAGE_KEY = "shopping_cart";

// Функция для загрузки состояния корзины из localStorage
// При запуске приложения данные корзины восстанавливаются из localStorage
const loadCartFromStorage = (): CartState => {
  try {
    const stored = localStorage.getItem(CART_STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return {
        items: parsed.items || [],
        totalCount: parsed.totalCount || 0,
      };
    }
  } catch (error) {
    console.error("Failed to load cart from localStorage:", error);
  }
  return { items: [], totalCount: 0 };
};

// Функция для сохранения состояния корзины в localStorage
// Каждый раз при изменении корзины данные сохраняются в localStorage
const saveCartToStorage = (state: CartState) => {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    console.error("Failed to save cart to localStorage:", error);
  }
};

// Начальное состояние - загружаем данные из localStorage
const initialState: CartState = loadCartFromStorage();

const cartSlice = createSlice({
  name: "cart",
  initialState,
  reducers: {
    // Добавить товар в корзину
    // Если товар уже есть - увеличиваем количество на 1
    // Если товара нет - добавляем с количеством 1
    addToCart: (state, action: PayloadAction<Omit<CartItem, "quantity">>) => {
      const existingItem = state.items.find(
        (item) => item.id === action.payload.id
      );

      if (existingItem) {
        existingItem.quantity += 1;
      } else {
        state.items.push({
          ...action.payload,
          quantity: 1,
        });
      }

      // Пересчитываем общее количество товаров
      state.totalCount = state.items.reduce(
        (total, item) => total + item.quantity,
        0
      );

      // Сохраняем в localStorage
      saveCartToStorage(state);
    },

    // Уменьшить количество товара на 1
    // Если количество становится 0 - товар удаляется из корзины
    removeFromCart: (state, action: PayloadAction<number>) => {
      const itemIndex = state.items.findIndex(
        (item) => item.id === action.payload
      );

      if (itemIndex !== -1) {
        const item = state.items[itemIndex];

        if (item.quantity > 1) {
          item.quantity -= 1;
        } else {
          state.items.splice(itemIndex, 1);
        }
      }

      // Пересчитываем общее количество товаров
      state.totalCount = state.items.reduce(
        (total, item) => total + item.quantity,
        0
      );

      // Сохраняем в localStorage
      saveCartToStorage(state);
    },

    // Полностью удалить товар из корзины (независимо от количества)
    removeItemCompletely: (state, action: PayloadAction<number>) => {
      state.items = state.items.filter((item) => item.id !== action.payload);

      // Пересчитываем общее количество товаров
      state.totalCount = state.items.reduce(
        (total, item) => total + item.quantity,
        0
      );

      // Сохраняем в localStorage
      saveCartToStorage(state);
    },

    // Очистить всю корзину
    clearCart: (state) => {
      state.items = [];
      state.totalCount = 0;
      // Сохраняем в localStorage
      saveCartToStorage(state);
    },

    // Синхронизация корзины из localStorage
    // Используется для обновления состояния при необходимости
    syncCartFromStorage: (state) => {
      const stored = loadCartFromStorage();
      state.items = stored.items;
      state.totalCount = stored.totalCount;
    },

    // Установить корзину из сервера (при входе пользователя)
    // Преобразует данные с сервера в формат фронтенда
    // force: принудительно перезаписать корзину (для случая когда пользователь вошёл заново)
    setCart: (state, action: PayloadAction<{
      items: Array<{
        id: number;
        product: {
          id: number;
          name: string;
          price: string;
          old_price: string | null;
          main_image_url: string | null;
        };
        quantity: number;
      }>;
      force?: boolean;
    }>) => {
      const { items, force } = action.payload;
      
      // Если сервер вернул пустую корзину и это не принудительное обновление - не перезаписываем localStorage
      // Это нужно чтобы не потерять данные если сервер ещё не успел их сохранить
      if ((!items || items.length === 0) && !force) {
        console.log('Server returned empty cart, keeping local data');
        return;
      }
      
      // Преобразуем данные с сервера в формат фронтенда
      state.items = items.map((item) => ({
        id: item.product.id,
        title: item.product.name,
        imageUrl: item.product.main_image_url || '',
        price: parseFloat(item.product.price) || 0,
        oldPrice: item.product.old_price ? parseFloat(item.product.old_price) : undefined,
        quantity: item.quantity,
      }));

      // Пересчитываем общее количество товаров
      state.totalCount = state.items.reduce(
        (total, item) => total + item.quantity,
        0
      );

      // Сохраняем в localStorage
      saveCartToStorage(state);
    },
  },
});

export const {
  addToCart,
  removeFromCart,
  removeItemCompletely,
  clearCart,
  syncCartFromStorage,
  setCart,
} = cartSlice.actions;

export default cartSlice.reducer;
