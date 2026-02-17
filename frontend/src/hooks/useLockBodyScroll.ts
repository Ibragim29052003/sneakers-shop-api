// хук блокирует скролл страницы, когда открыта модалка или drawer

import { useLayoutEffect } from "react";

 // locked - true = блокируем скролл, false = разблокируем
 
const useLockBodyScroll = (locked: boolean) => {
  useLayoutEffect(() => {
    if (!locked) return;

    // запоминаем текущую позицию скролла
    const scrollY = window.scrollY;

    // фиксируем body, чтобы заблокировать прокрутку
    document.body.style.position = "fixed";
    document.body.style.top = `-${scrollY}px`;
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";

    // при размонтировании или закрытии модалки возвращаем скролл
    return () => {
      document.body.style.position = "";
      document.body.style.top = "";
      document.body.style.left = "";
      document.body.style.right = "";
      document.body.style.width = "";
      window.scrollTo(0, scrollY);
    };
  }, [locked]);
};

export default useLockBodyScroll