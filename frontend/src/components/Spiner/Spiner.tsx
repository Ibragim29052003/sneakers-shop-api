import { type FC } from 'react'
import styles from './Spiner.module.scss'

const Spiner: FC = () => {
  return (
    <div className={styles.spinner}>
        <div className={styles.spinner__spinnerCircle}></div>
      </div>  )
}

export default Spiner