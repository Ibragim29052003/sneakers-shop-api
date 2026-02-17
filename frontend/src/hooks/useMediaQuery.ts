// хук для отслеживания медиа-запросов

import { useEffect, useState } from "react"

const useMediaQuery = (query: string) => {
    // window.matchMedia(query).matches` — true, если запрос совпадает
    const [matches, setMatches] = useState(() => window.matchMedia(query).matches)

    useEffect(() => {
        const mediaQueryList = window.matchMedia(query)
        // обновляет состояние matches при изменении медиа-запроса
        const listener = (event: MediaQueryListEvent) => setMatches(event.matches)

        mediaQueryList.addEventListener('change', listener)

        return () => mediaQueryList.removeEventListener('change', listener)
    }, [query])
 // текущее состояние совпадения медиа-запроса
    return matches
}

export default useMediaQuery