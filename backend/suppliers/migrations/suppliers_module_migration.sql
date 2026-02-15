
-- Включаем расширение для автоматических временных меток (если не включено)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. СОЗДАНИЕ СПРАВОЧНИКОВ (STATUS, TYPE TABLES)

-- Справочник статусов договоров
CREATE TABLE IF NOT EXISTS suppliers_contractstatus (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска по имени
CREATE INDEX IF NOT EXISTS idx_contractstatus_name ON suppliers_contractstatus(name);

-- Справочник статусов заявок
CREATE TABLE IF NOT EXISTS suppliers_requeststatus (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска по имени
CREATE INDEX IF NOT EXISTS idx_requeststatus_name ON suppliers_requeststatus(name);

-- Справочник типов уведомлений
CREATE TABLE IF NOT EXISTS suppliers_alerttype (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска по имени
CREATE INDEX IF NOT EXISTS idx_alerttype_name ON suppliers_alerttype(name);

-- Справочник источников создания товаров
CREATE TABLE IF NOT EXISTS suppliers_productsuppliersource (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска по имени
CREATE INDEX IF NOT EXISTS idx_productsuppliersource_name ON suppliers_productsuppliersource(name);

-- Справочник типов документов
CREATE TABLE IF NOT EXISTS suppliers_documenttype (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска по имени
CREATE INDEX IF NOT EXISTS idx_documenttype_name ON suppliers_documenttype(name);

-- 
-- 2. ОСНОВНЫЕ ТАБЛИЦЫ
-- 

-- Таблица поставщиков
CREATE TABLE IF NOT EXISTS suppliers_supplier (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    inn VARCHAR(12) DEFAULT '',
    kpp VARCHAR(9) DEFAULT '',
    ogrn VARCHAR(15) DEFAULT '',
    legal_address TEXT DEFAULT '',
    actual_address TEXT DEFAULT '',
    phone VARCHAR(20) DEFAULT '',
    email VARCHAR(254) DEFAULT '',
    website VARCHAR(200) DEFAULT '',
    contact_person VARCHAR(100) DEFAULT '',
    contact_phone VARCHAR(20) DEFAULT '',
    notes TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для поставщиков
CREATE INDEX IF NOT EXISTS idx_supplier_name ON suppliers_supplier(name);
CREATE INDEX IF NOT EXISTS idx_supplier_inn ON suppliers_supplier(inn);
CREATE INDEX IF NOT EXISTS idx_supplier_is_active ON suppliers_supplier(is_active);

-- Таблица договоров с поставщиками
CREATE TABLE IF NOT EXISTS suppliers_suppliercontract (
    id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT NOT NULL REFERENCES suppliers_supplier(id) ON DELETE CASCADE,
    status_id BIGINT NOT NULL REFERENCES suppliers_contractstatus(id) ON DELETE PROTECT,
    contract_number VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_amount NUMERIC(15, 2) DEFAULT NULL,
    notes TEXT DEFAULT '',
    is_auto_renew BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_supplier_contract UNIQUE (supplier_id, contract_number)
);

-- Индексы для договоров
CREATE INDEX IF NOT EXISTS idx_suppliercontract_number ON suppliers_suppliercontract(contract_number);
CREATE INDEX IF NOT EXISTS idx_suppliercontract_status ON suppliers_suppliercontract(status_id);
CREATE INDEX IF NOT EXISTS idx_suppliercontract_end_date ON suppliers_suppliercontract(end_date);
CREATE INDEX IF NOT EXISTS idx_suppliercontract_supplier_status ON suppliers_suppliercontract(supplier_id, status_id);

-- Таблица заявок на поставку товаров
CREATE TABLE IF NOT EXISTS suppliers_supplierproductrequest (
    id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT NOT NULL REFERENCES suppliers_supplier(id) ON DELETE CASCADE,
    status_id BIGINT NOT NULL REFERENCES suppliers_requeststatus(id) ON DELETE PROTECT,
    product_name VARCHAR(200) NOT NULL,
    product_sku VARCHAR(50) DEFAULT '',
    product_description TEXT DEFAULT '',
    quantity INTEGER NOT NULL DEFAULT 1,
    suggested_price NUMERIC(10, 2) DEFAULT NULL,
    notes TEXT DEFAULT '',
    reviewed_by_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    review_comment TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для заявок
CREATE INDEX IF NOT EXISTS idx_supplierproductrequest_status ON suppliers_supplierproductrequest(status_id);
CREATE INDEX IF NOT EXISTS idx_supplierproductrequest_supplier_status ON suppliers_supplierproductrequest(supplier_id, status_id);
CREATE INDEX IF NOT EXISTS idx_supplierproductrequest_created_at ON suppliers_supplierproductrequest(created_at);

-- 
-- 3. ТАБЛИЦЫ ДОКУМЕНТОВ
-- 

-- Документы договоров
CREATE TABLE IF NOT EXISTS suppliers_contractdocument (
    id BIGSERIAL PRIMARY KEY,
    contract_id BIGINT NOT NULL REFERENCES suppliers_suppliercontract(id) ON DELETE CASCADE,
    document_type_id BIGINT NOT NULL REFERENCES suppliers_documenttype(id) ON DELETE PROTECT,
    file VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL
);

-- Индексы для документов договоров
CREATE INDEX IF NOT EXISTS idx_contractdocument_contract_type ON suppliers_contractdocument(contract_id, document_type_id);

-- Документы заявок
CREATE TABLE IF NOT EXISTS suppliers_requestdocument (
    id BIGSERIAL PRIMARY KEY,
    request_id BIGINT NOT NULL REFERENCES suppliers_supplierproductrequest(id) ON DELETE CASCADE,
    document_type_id BIGINT NOT NULL REFERENCES suppliers_documenttype(id) ON DELETE PROTECT,
    file VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL
);

-- Индексы для документов заявок
CREATE INDEX IF NOT EXISTS idx_requestdocument_request_type ON suppliers_requestdocument(request_id, document_type_id);

-- 
-- 4. СВЯЗЬ ТОВАРОВ И ПОСТАВЩИКОВ (M2M)
-- 

-- Таблица связи товаров и поставщиков
CREATE TABLE IF NOT EXISTS suppliers_supplierproduct (
    id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT NOT NULL REFERENCES suppliers_supplier(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products_product(id) ON DELETE CASCADE,
    supplier_sku VARCHAR(50) DEFAULT '',
    supplier_price NUMERIC(10, 2) DEFAULT NULL,
    is_preferred BOOLEAN DEFAULT FALSE,
    notes TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_supplier_product UNIQUE (supplier_id, product_id)
);

-- Индексы для связи товаров и поставщиков
CREATE INDEX IF NOT EXISTS idx_supplierproduct_supplier_product ON suppliers_supplierproduct(supplier_id, product_id);
CREATE INDEX IF NOT EXISTS idx_supplierproduct_product_preferred ON suppliers_supplierproduct(product_id, is_preferred);

-- 
-- 5. СИСТЕМНЫЕ УВЕДОМЛЕНИЯ
-- 

-- Таблица системных уведомлений
CREATE TABLE IF NOT EXISTS suppliers_systemalert (
    id BIGSERIAL PRIMARY KEY,
    alert_type_id BIGINT NOT NULL REFERENCES suppliers_alerttype(id) ON DELETE PROTECT,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_by_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    read_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    contract_id BIGINT REFERENCES suppliers_suppliercontract(id) ON DELETE CASCADE,
    request_id BIGINT REFERENCES suppliers_supplierproductrequest(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для уведомлений
CREATE INDEX IF NOT EXISTS idx_systemalert_type_read ON suppliers_systemalert(alert_type_id, is_read);
CREATE INDEX IF NOT EXISTS idx_systemalert_read_created ON suppliers_systemalert(is_read, created_at);
CREATE INDEX IF NOT EXISTS idx_systemalert_contract_read ON suppliers_systemalert(contract_id, is_read);

-- 
-- 6. РАСШИРЕНИЕ ТАБЛИЦЫ PRODUCTS (ALTER TABLE)
-- 

-- Добавление полей связи с поставщиками в таблицу товаров
ALTER TABLE products_product 
ADD COLUMN IF NOT EXISTS supplier_id BIGINT REFERENCES suppliers_supplier(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS contract_id BIGINT REFERENCES suppliers_suppliercontract(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS created_from_request_id BIGINT REFERENCES suppliers_supplierproductrequest(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS created_from_source_id BIGINT REFERENCES suppliers_productsuppliersource(id) ON DELETE SET NULL;

-- Индексы для новых полей в products
CREATE INDEX IF NOT EXISTS idx_product_supplier ON products_product(supplier_id);
CREATE INDEX IF NOT EXISTS idx_product_contract ON products_product(contract_id);
CREATE INDEX IF NOT EXISTS idx_product_created_from_request ON products_product(created_from_request_id);
CREATE INDEX IF NOT EXISTS idx_product_created_from_source ON products_product(created_from_source_id);

-- 
-- 7. SEED DATA - НАЧАЛЬНЫЕ ДАННЫЕ
-- 

-- Статусы договоров
INSERT INTO suppliers_contractstatus (name, description) VALUES 
    ('draft', 'Черновик договора'),
    ('active', 'Активный договор'),
    ('suspended', 'Приостановленный договор'),
    ('expired', 'Истёкший договор'),
    ('terminated', 'Расторгнутый договор')
ON CONFLICT (name) DO NOTHING;

-- Статусы заявок
INSERT INTO suppliers_requeststatus (name, description) VALUES 
    ('pending', 'Ожидает рассмотрения'),
    ('under_review', 'На рассмотрении'),
    ('approved', 'Одобрена'),
    ('revision_required', 'Требует доработки'),
    ('rejected', 'Отклонена')
ON CONFLICT (name) DO NOTHING;

-- Типы уведомлений
INSERT INTO suppliers_alerttype (name, description) VALUES 
    ('contract_expiring', 'Договор истекает в течение 30 дней'),
    ('contract_expired', 'Срок договора истёк'),
    ('request_waiting_review', 'Заявка ожидает рассмотрения')
ON CONFLICT (name) DO NOTHING;

-- Источники создания товаров
INSERT INTO suppliers_productsuppliersource (name, description) VALUES 
    ('manual', 'Товар создан вручную'),
    ('request', 'Товар создан из заявки поставщика'),
    ('import', 'Товар загружен через импорт'),
    ('api', 'Товар создан через API')
ON CONFLICT (name) DO NOTHING;

-- Типы документов
INSERT INTO suppliers_documenttype (name, description) VALUES 
    ('contract', 'Договор с поставщиком'),
    ('act', 'Акт выполненных работ'),
    ('invoice', 'Счёт или инвойс'),
    ('waybill', 'Товарная накладная'),
    ('certificate', 'Сертификат качества'),
    ('license', 'Лицензия или разрешение'),
    ('other', 'Прочие документы')
ON CONFLICT (name) DO NOTHING;

-- 
-- 8. ПРОВЕРКА И ОТЧЁТ
-- 

-- Вывод списка созданных таблиц
SELECT 
    'suppliers_contractstatus' AS table_name, 
    COUNT(*) AS row_count 
FROM suppliers_contractstatus
UNION ALL
SELECT 
    'suppliers_requeststatus', 
    COUNT(*) 
FROM suppliers_requeststatus
UNION ALL
SELECT 
    'suppliers_alerttype', 
    COUNT(*) 
FROM suppliers_alerttype
UNION ALL
SELECT 
    'suppliers_productsuppliersource', 
    COUNT(*) 
FROM suppliers_productsuppliersource
UNION ALL
SELECT 
    'suppliers_documenttype', 
    COUNT(*) 
FROM suppliers_documenttype
UNION ALL
SELECT 
    'suppliers_supplier', 
    COUNT(*) 
FROM suppliers_supplier
UNION ALL
SELECT 
    'suppliers_suppliercontract', 
    COUNT(*) 
FROM suppliers_suppliercontract
UNION ALL
SELECT 
    'suppliers_supplierproductrequest', 
    COUNT(*) 
FROM suppliers_supplierproductrequest
UNION ALL
SELECT 
    'suppliers_contractdocument', 
    COUNT(*) 
FROM suppliers_contractdocument
UNION ALL
SELECT 
    'suppliers_requestdocument', 
    COUNT(*) 
FROM suppliers_requestdocument
UNION ALL
SELECT 
    'suppliers_supplierproduct', 
    COUNT(*) 
FROM suppliers_supplierproduct
UNION ALL
SELECT 
    'suppliers_systemalert', 
    COUNT(*) 
FROM suppliers_systemalert;

-- Вывод добавленных колонок в products
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'products_product' 
AND column_name IN ('supplier_id', 'contract_id', 'created_from_request_id', 'created_from_source_id');

-- 
-- ЗАВЕРШЕНО
-- 
-- Миграция выполнена успешно. Все таблицы созданы, индексы добавлены,
-- seed data загружена. Таблица products_product расширена новыми полями.
-- 
