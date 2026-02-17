import { useCallback, useEffect, useState, type FC } from "react";
import { useAppDispatch, useAppSelector } from "@/redux/store";

import styles from "./Slider.module.scss";
import ArrowButton from "@/components/ArrowButton/ArrowButton";
import Price from "@/components/Price/Price";

import {
  selectAutoPlay,
  selectCurrentIndex,
  selectShowArrows,
  selectSlides,
} from "@/redux/slider/selectors";
import { setCurrentIndex, toggleAutoPlay } from "@/redux/slider/slice";
import { useSwipeable } from "react-swipeable";

const Slider: FC = () => {
  const dispatch = useAppDispatch();
  const [isHovered, setIsHovered] = useState(false);

  // получаем данные из редакса
  const slides = useAppSelector(selectSlides);
  const currentIndex = useAppSelector(selectCurrentIndex);
  const autoPlay = useAppSelector(selectAutoPlay);
  const showArrows = useAppSelector(selectShowArrows);

  // функция перехода к следующему слайду
  // useCallback для мемоизации, чтобы не создавать новую функцию при каждом рендере
  const goToNextSlide = useCallback(() => {
    // считаем новый индекс, если дошли до конца, то возвращаемся к первому слайду
    const nextIndex = (currentIndex + 1) % slides.length;
    dispatch(setCurrentIndex(nextIndex)); // меняем currentIndex в редаксе
  }, [currentIndex, slides.length, dispatch]);

  // функция перехода к предыдущему слайду
  const goToPrevSlide = useCallback(() => {
    const prevIndex = (currentIndex - 1 + slides.length) % slides.length;
    dispatch(setCurrentIndex(prevIndex));
  }, [currentIndex, slides.length, dispatch]);

  // автопрокрутка слайдов
  useEffect(() => {
    if (!autoPlay || slides.length === 0) return; // если автоплей выключен или нет слайдов, не запускаем

    const interval = setInterval(goToNextSlide, 5000);

    return () => clearInterval(interval); // отработает при размонтировании или изменении зависимостей
  }, [autoPlay, goToNextSlide, slides.length]);

  // пауза автопрокрутки при наведении мыши
  const handleMouseEnter = () => {
    dispatch(toggleAutoPlay());
    setIsHovered(true);
  };
  const handleMouseLeave = () => {
    dispatch(toggleAutoPlay());
    setIsHovered(false);
  };

  const handlers = useSwipeable({
    onSwipedLeft: () => goToNextSlide(),
    onSwipedRight: () => goToPrevSlide(),
    preventScrollOnSwipe: true, //  предотвращает скролл страницы при свайпе
    trackMouse: true, // для drag мышью
  })

  // если слайды не загружены, показываем заглушку (можно заменить на спиннер или скелетон)
  if (slides.length === 0) return <div>Загрузка слайдов</div>;

  return (
    <div
      className={styles.slider}
      onMouseEnter={handleMouseEnter} {...handlers}
      onMouseLeave={handleMouseLeave}
      role="region"
      aria-label="Слайдер"
    >
      <div
        className={styles.slider__slidesContainer}
        ////// смещаем по X в зависимости от currentIndex ALOOOOOOOO
        style={{ transform: `translateX(-${currentIndex * 100}%)` }}
      >
        {slides.map((slide) => (
          <div key={slide.id} className={styles.slider__slide}>
             <img
              className={styles.slider__img}
              src={slide.imageUrl}
              alt={slide.title}
            />
            <div className={styles.slider__info}>
              <div className={styles.slider__info_text}>
                <h1 className={styles.slider__title}>{slide.title}</h1>
                <p className={styles.slider__description}>
                  {slide.description}
                </p>
                <Price newPrice={slide.newPrice} oldPrice={slide.oldPrice} />
              </div>

              <a className={styles.slider__link} href={slide.link} target="blank">
                Купить на WB
              </a>
            </div>
          </div>
        ))}
      </div>
      {showArrows && (
        <>
          <ArrowButton direction="left" onClick={goToPrevSlide} ariaLabel="Предыдущий слайд" isVisible={isHovered} />
          <ArrowButton direction="right" onClick={goToNextSlide} ariaLabel="Следующий слайд" isVisible={isHovered} />
        </>
      )}

      <div className={styles.slider__dots}>
        {slides.map((_, index) => (
          <button 
          key={index}
          className={`${styles.slider__dot} ${index === currentIndex ? styles.slider__dot_active : ''}`}
          onClick={() => dispatch(setCurrentIndex(index))}
          aria-label={`Слайд ${index + 1}`}
          aria-current={index === currentIndex ? 'true' : undefined}
         />
        ))}
      </div>

    </div>
  );
};

export default Slider;
