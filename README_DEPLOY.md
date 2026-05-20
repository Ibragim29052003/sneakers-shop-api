# Run Guide: Docker и без Docker

Ниже две полные инструкции запуска проекта: `с Docker` и `без Docker`.

## 1. Запуск с Docker (backend + инфраструктура)

### 1.1 Подготовка
```bash
cd /Users/ibragimkuszeterov/Desktop/veb_main_univer/Django_cource_sem_4/onlineStore
cp backend/.env.example backend/.env
```


### 1.2 Поднять контейнеры
```bash
docker compose up -d --build
docker compose ps
```

Ожидаемые сервисы: `postgres`, `redis`, `mailhog`, `backend`, `celery`, `celery-beat`.

### 1.3 Инициализация и проверка backend
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py check
```

Проверка API:
```bash
curl http://127.0.0.1:8000/api/v1/products/
```

### 1.4 Поднять frontend (локально)
```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5173/`  
Прокси-запрос для каталога:
```bash
curl "http://127.0.0.1:5173/api/v1/products/?is_active=true&category=women"
```

## 2. Запуск без Docker (полностью локально)

### 2.1 Что должно быть установлено


### 2.2 Настройка backend/.env для локального режима


### 2.3 Поднять backend локально
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Проверка API:
```bash
curl http://127.0.0.1:8000/api/v1/products/
```

### 2.4 Поднять frontend локально
```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Проверка проблемного запроса:
```bash
curl "http://127.0.0.1:5173/api/v1/products/?is_active=true&category=women"
```

## 3. Остановка

Docker-режим:
```bash
docker compose down
```

Локальный режим:
1. В терминалах с `runserver` и `vite` нажмите `Ctrl+C`.

## 4. Частые причины ошибок
1. `400` на `category=women`: старая версия backend без фикса фильтра category.
2. `404 /api/v1/my-supplier-profile/`: пользователь не поставщик (ожидаемо).
3. `403 /api/v1/my-contracts/`: пользователь не имеет роли поставщика (ожидаемо).
4. `connection refused` к БД: проверьте `POSTGRES_HOST/POSTGRES_PORT` и что PostgreSQL запущен.
