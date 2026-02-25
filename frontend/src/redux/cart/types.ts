// Тип элемента корзины
export interface CartItem {
  id: number;           // ID товара
  title: string;        // Название товара
  imageUrl: string;     // URL изображения товара
  price: number;        // Текущая цена товара
  oldPrice?: number;    // Старая цена (если есть скидка)
  quantity: number;     // Количество данного товара в корзине
}

// Тип состояния корзины
export interface CartState {
  items: CartItem[];    // Массив товаров в корзине
  totalCount: number;   // Общее количество всех товаров в корзине
}
