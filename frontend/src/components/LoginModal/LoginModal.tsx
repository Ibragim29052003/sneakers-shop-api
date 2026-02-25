import * as Dialog from "@radix-ui/react-dialog";
import { useState, type FC } from "react";
import { useLoginMutation, useRegisterMutation } from "@/services/api/productsApi";
import styles from "./LoginModal.module.scss";

type FormData = {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
};

type FormErrors = Partial<Record<keyof FormData, string>>;
type TouchedFields = Partial<Record<keyof FormData, boolean>>;

type LoginModalProps = {
  openModal: boolean;
  onOpenChange: (open: boolean) => void;
  onLoginSuccess?: () => void;
};

export const LoginModal: FC<LoginModalProps> = ({ openModal, onOpenChange, onLoginSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<TouchedFields>({});
  const [apiError, setApiError] = useState("");

  const [login, { isLoading: isLoginLoading }] = useLoginMutation();
  const [register, { isLoading: isRegisterLoading }] = useRegisterMutation();

  const isLoading = isLoginLoading || isRegisterLoading;

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password: string): boolean => {
    return password.length >= 6;
  };

  const validateField = (field: keyof FormData): string => {
    const value = formData[field];
    let error = "";

    switch (field) {
      case "name":
        if (!value.trim()) {
          error = "Введите имя";
        } else if (value.trim().length < 2) {
          error = "Имя должно содержать минимум 2 символа";
        }
        break;
      case "email":
        if (!value.trim()) {
          error = "Введите email";
        } else if (!validateEmail(value)) {
          error = "Введите корректный email";
        }
        break;
      case "password":
        if (!value) {
          error = "Введите пароль";
        } else if (!validatePassword(value)) {
          error = "Пароль должен содержать минимум 6 символов";
        }
        break;
      case "confirmPassword":
        if (!value) {
          error = "Подтвердите пароль";
        } else if (formData.password !== value) {
          error = "Пароли не совпадают";
        }
        break;
    }

    return error;
  };

  const handleBlur = (field: keyof FormData) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    const error = validateField(field);
    setErrors((prev) => ({ ...prev, [field]: error }));
  };

  const validateForm = (): boolean => {
    const fieldsToValidate: (keyof FormData)[] = ["email", "password"];
    if (isRegister) {
      fieldsToValidate.push("name", "confirmPassword");
    }

    const newErrors: FormErrors = {};

    fieldsToValidate.forEach((field) => {
      const error = validateField(field);
      if (error) {
        newErrors[field] = error;
      }
    });

    setErrors(newErrors);
    setTouched({ name: true, email: true, password: true, confirmPassword: true });
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError("");

    if (!validateForm()) {
      return;
    }

    try {
      if (isRegister) {
        const result = await register({
          email: formData.email,
          password: formData.password,
          password_confirm: formData.confirmPassword,
          first_name: formData.name,
        }).unwrap();

        console.log("Registration successful:", result);
        handleClose();
        alert("Регистрация успешна! Теперь вы можете войти.");
        setIsRegister(false);
      } else {
        const result = await login({
          email: formData.email,
          password: formData.password,
        }).unwrap();

        console.log("Login successful:", result);
        localStorage.setItem("access_token", result.access);
        localStorage.setItem("refresh_token", result.refresh);
        handleClose();
        onLoginSuccess?.();
        window.location.reload();
      }
    } catch (error: any) {
      console.error("Auth error:", error);
      if (error.data) {
        const errorMessages = Object.values(error.data).flat().join(", ");
        setApiError(errorMessages);
      } else {
        setApiError("Произошла ошибка. Попробуйте позже.");
      }
    }
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (touched[field]) {
      const error = validateField(field);
      setErrors((prev) => ({ ...prev, [field]: error }));
    }
  };

  const handleSwitch = () => {
    setIsRegister(!isRegister);
    setFormData({ name: "", email: "", password: "", confirmPassword: "" });
    setErrors({});
    setTouched({});
    setApiError("");
  };

  const handleClose = () => {
    setFormData({ name: "", email: "", password: "", confirmPassword: "" });
    setErrors({});
    setTouched({});
    setApiError("");
    onOpenChange(false);
  };

  return (
    <Dialog.Root open={openModal} onOpenChange={handleClose}>
      <Dialog.Portal>
        <Dialog.Overlay className={styles.loginModal__overlay} />

        <Dialog.Content className={styles.loginModal__content}>
          <div className={styles.loginModal__header}>
            <Dialog.Title className={styles.loginModal__title}>
              {isRegister ? "Регистрация" : "Вход"}
            </Dialog.Title>

            <Dialog.Close asChild>
              <button
                className={styles.loginModal__close}
                aria-label="Закрыть"
                type="button"
              >
                <div className={styles.loginModal__closeIcon}>
                  <span></span>
                  <span></span>
                </div>
              </button>
            </Dialog.Close>
          </div>

          <div className={styles.loginModal__tabs}>
            <button
              className={`${styles.loginModal__tab} ${!isRegister ? styles.loginModal__tab_active : ""}`}
              onClick={() => setIsRegister(false)}
              type="button"
            >
              Вход
            </button>
            <button
              className={`${styles.loginModal__tab} ${isRegister ? styles.loginModal__tab_active : ""}`}
              onClick={() => setIsRegister(true)}
              type="button"
            >
              Регистрация
            </button>
          </div>

          {apiError && (
            <div className={styles.loginModal__errorText} style={{ marginBottom: 16, textAlign: "center" }}>
              {apiError}
            </div>
          )}

          <form className={styles.loginModal__form} onSubmit={handleSubmit}>
            {isRegister && (
              <label className={styles.loginModal__label}>
                Имя
                <input
                  className={`${styles.loginModal__input} ${touched.name && errors.name ? styles.loginModal__input_error : ""}`}
                  type="text"
                  placeholder="Введите имя"
                  value={formData.name}
                  onChange={(e) => handleInputChange("name", e.target.value)}
                  onBlur={() => handleBlur("name")}
                  disabled={isLoading}
                />
                {touched.name && errors.name && (
                  <span className={styles.loginModal__errorText}>{errors.name}</span>
                )}
              </label>
            )}

            <label className={styles.loginModal__label}>
              Email
              <input
                className={`${styles.loginModal__input} ${touched.email && errors.email ? styles.loginModal__input_error : ""}`}
                type="email"
                placeholder="Введите email"
                value={formData.email}
                onChange={(e) => handleInputChange("email", e.target.value)}
                onBlur={() => handleBlur("email")}
                disabled={isLoading}
              />
              {touched.email && errors.email && (
                <span className={styles.loginModal__errorText}>{errors.email}</span>
              )}
            </label>

            <label className={styles.loginModal__label}>
              Пароль
              <input
                className={`${styles.loginModal__input} ${touched.password && errors.password ? styles.loginModal__input_error : ""}`}
                type="password"
                placeholder="Введите пароль"
                value={formData.password}
                onChange={(e) => handleInputChange("password", e.target.value)}
                onBlur={() => handleBlur("password")}
                disabled={isLoading}
              />
              {touched.password && errors.password && (
                <span className={styles.loginModal__errorText}>{errors.password}</span>
              )}
            </label>

            {isRegister && (
              <label className={styles.loginModal__label}>
                Подтвердите пароль
                <input
                  className={`${styles.loginModal__input} ${touched.confirmPassword && errors.confirmPassword ? styles.loginModal__input_error : ""}`}
                  type="password"
                  placeholder="Повторите пароль"
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
                  onBlur={() => handleBlur("confirmPassword")}
                  disabled={isLoading}
                />
                {touched.confirmPassword && errors.confirmPassword && (
                  <span className={styles.loginModal__errorText}>{errors.confirmPassword}</span>
                )}
              </label>
            )}

            <button type="submit" className={styles.loginModal__submit} disabled={isLoading}>
              {isLoading ? "Загрузка..." : isRegister ? "Зарегистрироваться" : "Войти"}
            </button>
          </form>

          <div className={styles.loginModal__switch}>
            {isRegister ? (
              <>
                Уже есть аккаунт?
                <button onClick={handleSwitch} type="button">Войти</button>
              </>
            ) : (
              <>
                Нет аккаунта?
                <button onClick={handleSwitch} type="button">Регистрация</button>
              </>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
