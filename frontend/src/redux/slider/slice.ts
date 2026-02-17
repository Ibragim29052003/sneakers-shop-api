import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { Slide, SliderState } from "./types";

const initialState: SliderState = {
  slides: [], // массив слайдов
  currentIndex: 0,
//   loading: false, // НА ПОДУМАТЬ
  autoPlay: true, // включена ли автопрокрутка слайдов
  showArrows: true,
};

const sliderSlice = createSlice({
  name: "slider",
  initialState,
  reducers: {
    // устанавливаем/загружаем массив слайдов
    setSlides: (state, action: PayloadAction<Slide[]>) => {
      state.slides = action.payload; // кладем массив слайдов
      state.currentIndex = 0; // начинаем с первого слайда
    },
    // переходим к следующему слайду
    setCurrentIndex: (state, action: PayloadAction<number>) => {
      state.currentIndex = action.payload;
    },
    toggleAutoPlay: (state) => {
    // можно использовать, когда пользователь навел мышь на слайдер, или ушел со страницы
        state.autoPlay = !state.autoPlay;
    },
    setShowArrows: (state, action: PayloadAction<boolean>) => {
        state.showArrows = action.payload
    },
  },
});

export const {
    setSlides,
    setCurrentIndex,
    toggleAutoPlay,
    setShowArrows
} = sliderSlice.actions

export default sliderSlice.reducer