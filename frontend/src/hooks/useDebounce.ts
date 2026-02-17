// хук для отложенного обновления значения

import { useEffect, useState } from "react";

const useDebounce = <T,>(value: T, delay = 300): T => {

    const [debouncedValue, setDebouncedValue] = useState(value) 

    useEffect(() => {
        const timeoutId = setTimeout(() => {
            // это выполнится, если в течении delay не было нового вызова этого эффекта 
            setDebouncedValue(value)
        }, delay)

        return () => {
            clearTimeout(timeoutId)
        }
    }, [value, delay])

    return debouncedValue // текущее отложенное значение
} 

export default useDebounce