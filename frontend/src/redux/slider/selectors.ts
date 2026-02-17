import type { RootState } from "../store";

export const selectSlides = (state: RootState) => state.slider.slides // получить все слайды
export const selectCurrentIndex = (state: RootState) => state.slider.currentIndex // узнаем, какой слайд сейчас активен
export const selectAutoPlay = (state: RootState) => state.slider.autoPlay
export const selectShowArrows = (state: RootState) => state.slider.showArrows