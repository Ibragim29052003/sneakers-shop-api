import type { FC } from "react";
import styles from "./Skeleton.module.scss";

interface SkeletonProps {
  width?: string;
  height?: string;
  borderRadius?: string;
  className?: string;
}

const Skeleton: FC<SkeletonProps> = ({
  width,
  height,
  borderRadius,
  className,
}) => {
  return (
    <div
      className={`${styles.skeleton} ${className || ""}`}
      style={{ width, height, borderRadius }}
    >
    </div>
  );
};

export default Skeleton;
