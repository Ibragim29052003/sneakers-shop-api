import type { FC } from "react";
import Arrow from "@/shared/assets/icons/slider/arrow-for-slider.svg?react";
import styles from "./ArrowButton.module.scss";

interface ArrowButtonProps {
  direction: "left" | "right";
  onClick: () => void;
  ariaLabel: string;
  isVisible: boolean;
}

const ArrowButton: FC<ArrowButtonProps> = ({
  direction,
  onClick,
  ariaLabel,
  isVisible,
}) => {
  return (
    <button
      className={`${styles.arrow} ${styles[`arrow__${direction}`]} ${
        isVisible ? styles.arrow__visible : styles.arrow__invisible
      }`}
      onClick={onClick}
      aria-label={ariaLabel}
    >
      <Arrow
        className={`${styles.arrow__svg} ${styles[`arrow__svg_${direction}`]}`}
      />
    </button>
  );
};

export default ArrowButton;
