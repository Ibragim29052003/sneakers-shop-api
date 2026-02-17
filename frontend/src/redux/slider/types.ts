export type Slide = {
  id: string;
  imageUrl: string;
  title: string;
  description: string;
  newPrice: number;
  oldPrice?: number;
  link: string;
};

export interface SliderState {
  slides: Slide[];
  currentIndex: number;
  loading?: boolean; // НА ПОДУМАТЬ еще подумаю, приходят ли с сервера или нет
  autoPlay: boolean; // включена ли автопрокрутка слайдов
  showArrows: boolean;
}
