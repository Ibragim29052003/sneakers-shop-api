
DROP SCHEMA IF EXISTS lab_store CASCADE;
CREATE SCHEMA lab_store;

SET search_path TO lab_store, public;


CREATE TABLE lab_suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    rating NUMERIC(3, 2) NOT NULL DEFAULT 5.00,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deactivated_at TIMESTAMP
);

CREATE TABLE lab_supplier_accounts (
    supplier_id INTEGER PRIMARY KEY REFERENCES lab_suppliers(supplier_id) ON DELETE CASCADE,
    reserved_budget NUMERIC(12, 2) NOT NULL DEFAULT 0,
    spent_budget NUMERIC(12, 2) NOT NULL DEFAULT 0
);

CREATE TABLE lab_categories (
    category_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE lab_products (
    product_id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES lab_suppliers(supplier_id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES lab_categories(category_id),
    name TEXT NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE lab_product_stock (
    stock_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES lab_products(product_id) ON DELETE CASCADE,
    warehouse_code TEXT NOT NULL,
    total_qty INTEGER NOT NULL CHECK (total_qty >= 0),
    reserved_qty INTEGER NOT NULL DEFAULT 0 CHECK (reserved_qty >= 0),
    UNIQUE (product_id, warehouse_code)
);

CREATE TABLE lab_supplier_contracts (
    contract_id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES lab_suppliers(supplier_id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'expired', 'terminated')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    budget_limit NUMERIC(12, 2) NOT NULL CHECK (budget_limit >= 0)
);

CREATE TABLE lab_supplier_requests (
    request_id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES lab_suppliers(supplier_id) ON DELETE CASCADE,
    product_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'under_review', 'approved', 'rejected', 'cancelled')
    ),
    priority TEXT NOT NULL DEFAULT 'normal' CHECK (priority IN ('normal', 'high', 'urgent')),
    estimated_cost NUMERIC(10, 2) NOT NULL CHECK (estimated_cost >= 0),
    quoted_cost NUMERIC(10, 2),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    resolved_at TIMESTAMP,
    cancelled_at TIMESTAMP
);

CREATE TABLE lab_customer_orders (
    order_id SERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('new', 'processing', 'shipped', 'cancelled', 'delayed')),
    shipping_tier TEXT NOT NULL DEFAULT 'standard' CHECK (shipping_tier IN ('standard', 'priority', 'express')),
    warehouse_code TEXT NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    shipped_at TIMESTAMP
);

CREATE TABLE lab_order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES lab_customer_orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES lab_products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0)
);

CREATE TABLE lab_shipping_rate_upgrades (
    from_tier TEXT NOT NULL,
    to_tier TEXT NOT NULL,
    surcharge NUMERIC(10, 2) NOT NULL CHECK (surcharge >= 0),
    PRIMARY KEY (from_tier, to_tier)
);

CREATE TABLE lab_restock_windows (
    window_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES lab_products(product_id) ON DELETE CASCADE,
    warehouse_code TEXT NOT NULL,
    slot_start TIMESTAMP NOT NULL,
    slot_end TIMESTAMP NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN ('planned', 'finished', 'cancelled')),
    CHECK (slot_end > slot_start)
);

CREATE TABLE lab_cart_reservations (
    reservation_id SERIAL PRIMARY KEY,
    reservation_code TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'converted')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE lab_order_events (
    event_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES lab_customer_orders(order_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE lab_order_events_archive (
    event_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    occurred_at TIMESTAMP NOT NULL,
    archived_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE lab_shipments (
    shipment_id SERIAL PRIMARY KEY,
    warehouse_code TEXT NOT NULL,
    route_code TEXT NOT NULL,
    scheduled_at TIMESTAMP NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'cancelled', 'departed')),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    used_capacity INTEGER NOT NULL DEFAULT 0 CHECK (used_capacity >= 0)
);

CREATE TABLE lab_shipment_orders (
    shipment_order_id SERIAL PRIMARY KEY,
    shipment_id INTEGER NOT NULL REFERENCES lab_shipments(shipment_id) ON DELETE CASCADE,
    order_id INTEGER NOT NULL REFERENCES lab_customer_orders(order_id) ON DELETE CASCADE,
    seats_reserved INTEGER NOT NULL DEFAULT 1 CHECK (seats_reserved > 0),
    UNIQUE (shipment_id, order_id)
);

-- Здесь я добавляю тестовые данные для проверки функций и процедур.

INSERT INTO lab_suppliers (name, rating, created_at) VALUES
('Северный ветер', 4.80, NOW() - INTERVAL '180 days'),
('Городская вершина', 4.30, NOW() - INTERVAL '120 days'),
('Зеленая линия текстиля', 4.95, NOW() - INTERVAL '90 days');

INSERT INTO lab_supplier_accounts (supplier_id, reserved_budget, spent_budget) VALUES
(1, 120000.00, 300000.00),
(2, 45000.00, 180000.00),
(3, 90000.00, 240000.00);

INSERT INTO lab_categories (name) VALUES
('Верхняя одежда'),
('Обувь'),
('Аксессуары');

INSERT INTO lab_products (supplier_id, category_id, name, sku, price, created_at) VALUES
(1, 1, 'Штормовая куртка', 'SJ-001', 12990.00, NOW() - INTERVAL '70 days'),
(1, 2, 'Треккинговые ботинки', 'TB-002', 18990.00, NOW() - INTERVAL '60 days'),
(2, 3, 'Дорожный ремень', 'TR-003', 2990.00, NOW() - INTERVAL '45 days'),
(3, 1, 'Шерстяное пальто', 'WC-004', 15990.00, NOW() - INTERVAL '30 days'),
(3, 3, 'Кожаные перчатки', 'LG-005', 4990.00, NOW() - INTERVAL '20 days');

INSERT INTO lab_product_stock (product_id, warehouse_code, total_qty, reserved_qty) VALUES
(1, 'MSK', 40, 5),
(2, 'MSK', 12, 4),
(3, 'MSK', 100, 15),
(4, 'SPB', 18, 3),
(5, 'SPB', 50, 10);

INSERT INTO lab_supplier_contracts (supplier_id, status, start_date, end_date, budget_limit) VALUES
(1, 'active', CURRENT_DATE - 180, CURRENT_DATE + 45, 500000.00),
(2, 'active', CURRENT_DATE - 160, CURRENT_DATE - 2, 250000.00),
(3, 'draft', CURRENT_DATE - 20, CURRENT_DATE + 180, 400000.00);

INSERT INTO lab_supplier_requests (
    supplier_id, product_name, status, priority, estimated_cost, quoted_cost,
    created_at, reviewed_at, resolved_at
) VALUES
(1, 'Партия зимних курток', 'under_review', 'urgent', 70000.00, 73000.00, NOW() - INTERVAL '72 hours', NOW() - INTERVAL '48 hours', NULL),
(1, 'Дозаказ ботинок', 'approved', 'high', 45000.00, 47000.00, NOW() - INTERVAL '10 days', NOW() - INTERVAL '8 days', NOW() - INTERVAL '7 days'),
(2, 'Промо-набор ремней', 'pending', 'normal', 15000.00, NULL, NOW() - INTERVAL '36 hours', NULL, NULL),
(3, 'Линейка премиальных пальто', 'approved', 'high', 80000.00, 85000.00, NOW() - INTERVAL '12 days', NOW() - INTERVAL '11 days', NOW() - INTERVAL '9 days'),
(3, 'Обновление аксессуаров', 'rejected', 'normal', 12000.00, 14000.00, NOW() - INTERVAL '18 days', NOW() - INTERVAL '17 days', NOW() - INTERVAL '16 days');

INSERT INTO lab_customer_orders (
    customer_name, status, shipping_tier, warehouse_code, total_amount, created_at, shipped_at
) VALUES
('Иван Петров', 'new', 'standard', 'MSK', 25980.00, NOW() - INTERVAL '2 days', NULL),
('Анна Сидорова', 'processing', 'priority', 'MSK', 2990.00, NOW() - INTERVAL '1 day', NULL),
('Дмитрий Козлов', 'processing', 'standard', 'SPB', 20980.00, NOW() - INTERVAL '12 hours', NULL),
('Мария Волкова', 'shipped', 'express', 'SPB', 4990.00, NOW() - INTERVAL '15 days', NOW() - INTERVAL '13 days');

INSERT INTO lab_order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 2, 12990.00),
(2, 3, 1, 2990.00),
(3, 4, 1, 15990.00),
(3, 5, 1, 4990.00),
(4, 5, 1, 4990.00);

INSERT INTO lab_shipping_rate_upgrades (from_tier, to_tier, surcharge) VALUES
('standard', 'priority', 1500.00),
('standard', 'express', 4500.00),
('priority', 'express', 2500.00);

INSERT INTO lab_restock_windows (product_id, warehouse_code, slot_start, slot_end, status) VALUES
(1, 'MSK', NOW() + INTERVAL '3 hours', NOW() + INTERVAL '5 hours', 'planned'),
(1, 'MSK', NOW() + INTERVAL '10 hours', NOW() + INTERVAL '11 hours', 'planned'),
(1, 'MSK', NOW() + INTERVAL '20 hours', NOW() + INTERVAL '22 hours', 'planned'),
(2, 'MSK', NOW() + INTERVAL '1 hour', NOW() + INTERVAL '2 hours', 'planned'),
(2, 'MSK', NOW() + INTERVAL '8 hours', NOW() + INTERVAL '9 hours', 'planned');

INSERT INTO lab_cart_reservations (reservation_code, customer_name, status, created_at, expires_at) VALUES
('RSV-000001', 'Елена Романова', 'expired', NOW() - INTERVAL '3 years', NOW() - INTERVAL '2 years 11 months'),
('RSV-000002', 'Павел Миронов', 'expired', NOW() - INTERVAL '2 years 3 months', NOW() - INTERVAL '2 years 2 months'),
('RSV-000003', 'Ольга Смирнова', 'active', NOW() - INTERVAL '4 days', NOW() + INTERVAL '2 days');

INSERT INTO lab_order_events (order_id, event_type, payload, occurred_at) VALUES
(1, 'created', '{"source":"сайт"}', NOW() - INTERVAL '18 days'),
(1, 'paid', '{"method":"карта"}', NOW() - INTERVAL '17 days'),
(2, 'created', '{"source":"мобильное приложение"}', NOW() - INTERVAL '12 days'),
(3, 'created', '{"source":"сайт"}', NOW() - INTERVAL '5 days'),
(4, 'shipped', '{"carrier":"курьер"}', NOW() - INTERVAL '11 days');

INSERT INTO lab_shipments (warehouse_code, route_code, scheduled_at, status, capacity, used_capacity) VALUES
('MSK', 'MSK-NORTH', NOW() + INTERVAL '2 hours', 'scheduled', 3, 2),
('MSK', 'MSK-NORTH', NOW() + INTERVAL '4 hours', 'scheduled', 4, 1),
('MSK', 'MSK-SOUTH', NOW() + INTERVAL '3 hours', 'scheduled', 2, 1),
('SPB', 'SPB-CENTER', NOW() + INTERVAL '5 hours', 'scheduled', 3, 1);

INSERT INTO lab_shipment_orders (shipment_id, order_id, seats_reserved) VALUES
(1, 1, 1),
(1, 2, 1),
(3, 3, 1);

-- ЛР №3. Функции и процедуры
-- Ниже идут 8 упражнений по функциям, процедурам, переменным и IF.

-- Задача 1.
-- Здесь я создаю процедуру, которая показывает заявки,
-- ожидающие обработки дольше заданного количества часов.
CREATE OR REPLACE PROCEDURE notify_overdue_requests(p_hours INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    req RECORD;
BEGIN
    FOR req IN
        SELECT request_id, supplier_id, product_name, created_at
        FROM lab_supplier_requests
        WHERE status IN ('pending', 'under_review')
          AND created_at <= NOW() - MAKE_INTERVAL(hours => p_hours)
        ORDER BY created_at
    LOOP
        RAISE NOTICE 'Просроченная заявка %: supplier=% product=% created_at=%',
            req.request_id, req.supplier_id, req.product_name, req.created_at;
    END LOOP;
END;
$$;

-- Задача 2.
-- Здесь я создаю функцию, которая возвращает длительность обработки заявки.
CREATE OR REPLACE FUNCTION get_request_processing_time(p_request_id INTEGER)
RETURNS INTERVAL
LANGUAGE plpgsql
AS $$
DECLARE
    v_duration INTERVAL;
BEGIN
    SELECT resolved_at - created_at
    INTO v_duration
    FROM lab_supplier_requests
    WHERE request_id = p_request_id;

    RETURN v_duration;
END;
$$;

-- Задача 3.
-- Здесь я создаю процедуру отмены заявки.
-- Отменить можно только ту заявку, которая еще не завершена.
CREATE OR REPLACE PROCEDURE cancel_supplier_request(p_request_id INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status TEXT;
BEGIN
    SELECT status
    INTO v_status
    FROM lab_supplier_requests
    WHERE request_id = p_request_id;

    IF v_status IS NULL THEN
        RAISE EXCEPTION 'Заявка % не найдена', p_request_id;
    END IF;

    IF v_status IN ('pending', 'under_review') THEN
        UPDATE lab_supplier_requests
        SET status = 'cancelled',
            cancelled_at = NOW(),
            resolved_at = NOW()
        WHERE request_id = p_request_id;
    ELSE
        RAISE NOTICE 'Заявку % нельзя отменить, текущий статус=%', p_request_id, v_status;
    END IF;
END;
$$;

-- Задача 4.
-- Здесь я создаю функцию, которая показывает активность поставщика:
-- общее количество заявок и сколько из них было одобрено.
CREATE OR REPLACE FUNCTION get_supplier_activity(p_supplier_id INTEGER)
RETURNS TABLE (
    total_requests INTEGER,
    approved_requests INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER AS total_requests,
        COUNT(*) FILTER (WHERE status = 'approved')::INTEGER AS approved_requests
    FROM lab_supplier_requests
    WHERE supplier_id = p_supplier_id;
END;
$$;

-- Задача 5.
-- Здесь я создаю процедуру "апгрейда" способа доставки заказа.
-- Если доплата слишком большая, процедура завершается с ошибкой.
CREATE OR REPLACE PROCEDURE upgrade_order_shipping_tier(
    p_order_id INTEGER,
    p_new_tier TEXT DEFAULT 'express',
    p_limit NUMERIC DEFAULT 50000
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_current_tier TEXT;
    v_surcharge NUMERIC;
BEGIN
    SELECT shipping_tier
    INTO v_current_tier
    FROM lab_customer_orders
    WHERE order_id = p_order_id;

    IF v_current_tier IS NULL THEN
        RAISE EXCEPTION 'Заказ % не найден', p_order_id;
    END IF;

    IF v_current_tier = p_new_tier THEN
        RAISE NOTICE 'Заказ % уже имеет уровень доставки %', p_order_id, p_new_tier;
        RETURN;
    END IF;

    SELECT surcharge
    INTO v_surcharge
    FROM lab_shipping_rate_upgrades
    WHERE from_tier = v_current_tier
      AND to_tier = p_new_tier;

    IF v_surcharge IS NULL THEN
        RAISE EXCEPTION 'Нельзя повысить доставку из % в %', v_current_tier, p_new_tier;
    END IF;

    IF v_surcharge > p_limit THEN
        RAISE EXCEPTION 'Слишком дорогой апгрейд: %', v_surcharge;
    END IF;

    UPDATE lab_customer_orders
    SET shipping_tier = p_new_tier,
        total_amount = total_amount + v_surcharge
    WHERE order_id = p_order_id;
END;
$$;

-- Задача 6.
-- Здесь я создаю процедуру массового обновления статусов договоров по дате окончания.
CREATE OR REPLACE PROCEDURE close_contracts_by_date(p_cutoff_date DATE)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE lab_supplier_contracts
    SET status = 'expired'
    WHERE status = 'active'
      AND end_date < p_cutoff_date;
END;
$$;

-- Задача 7.
-- Здесь я создаю функцию, которая считает среднее время
-- первичного рассмотрения заявок конкретного поставщика.
CREATE OR REPLACE FUNCTION get_avg_request_review_time(p_supplier_id INTEGER)
RETURNS INTERVAL
LANGUAGE plpgsql
AS $$
DECLARE
    v_avg_review_time INTERVAL;
BEGIN
    SELECT AVG(reviewed_at - created_at)
    INTO v_avg_review_time
    FROM lab_supplier_requests
    WHERE supplier_id = p_supplier_id
      AND reviewed_at IS NOT NULL;

    RETURN v_avg_review_time;
END;
$$;

-- Задача 8.
-- Здесь я создаю процедуру вывода поставщика из эксплуатации.
-- Она отменяет активные заявки, обновляет договоры и деактивирует поставщика.
CREATE OR REPLACE PROCEDURE decommission_supplier(p_supplier_id INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    req RECORD;
    v_reserved_budget NUMERIC;
BEGIN
    SELECT reserved_budget
    INTO v_reserved_budget
    FROM lab_supplier_accounts
    WHERE supplier_id = p_supplier_id
    FOR UPDATE;

    IF v_reserved_budget IS NULL THEN
        RAISE EXCEPTION 'Счет поставщика % не найден', p_supplier_id;
    END IF;

    FOR req IN
        SELECT request_id, estimated_cost
        FROM lab_supplier_requests
        WHERE supplier_id = p_supplier_id
          AND status IN ('pending', 'under_review')
    LOOP
        IF v_reserved_budget < req.estimated_cost THEN
            RAISE EXCEPTION 'Не удалось вернуть резерв по заявке %, недостаточно средств', req.request_id;
        END IF;

        v_reserved_budget := v_reserved_budget - req.estimated_cost;

        UPDATE lab_supplier_requests
        SET status = 'cancelled',
            cancelled_at = NOW(),
            resolved_at = NOW()
        WHERE request_id = req.request_id;
    END LOOP;

    UPDATE lab_supplier_accounts
    SET reserved_budget = v_reserved_budget
    WHERE supplier_id = p_supplier_id;

    UPDATE lab_supplier_contracts
    SET status = 'terminated'
    WHERE supplier_id = p_supplier_id
      AND status IN ('draft', 'active');

    UPDATE lab_suppliers
    SET is_active = FALSE,
        deactivated_at = NOW()
    WHERE supplier_id = p_supplier_id;
END;
$$;

-- ЛР №4. Циклы FOR и WHILE
-- Ниже идут 8 упражнений по циклам, массивам, генерации и пакетной обработке.

-- Задача 9.
-- Здесь я создаю функцию, которая формирует новый массив
-- из элементов, стоящих на четных индексах, с помощью цикла FOR.
CREATE OR REPLACE FUNCTION pick_even_indexed_with_for(p_values INTEGER[])
RETURNS INTEGER[]
LANGUAGE plpgsql
AS $$
DECLARE
    result_values INTEGER[] := ARRAY[]::INTEGER[];
    i INTEGER;
BEGIN
    IF p_values IS NULL THEN
        RETURN result_values;
    END IF;

    FOR i IN 1..COALESCE(cardinality(p_values), 0) LOOP
        IF MOD(i, 2) = 0 THEN
            result_values := array_append(result_values, p_values[i]);
        END IF;
    END LOOP;

    RETURN result_values;
END;
$$;

-- Задача 10.
-- Здесь я решаю такую же задачу, но уже через цикл WHILE.
CREATE OR REPLACE FUNCTION pick_even_indexed_with_while(p_values INTEGER[])
RETURNS INTEGER[]
LANGUAGE plpgsql
AS $$
DECLARE
    result_values INTEGER[] := ARRAY[]::INTEGER[];
    i INTEGER := 1;
    v_len INTEGER := COALESCE(cardinality(p_values), 0);
BEGIN
    WHILE i <= v_len LOOP
        IF MOD(i, 2) = 0 THEN
            result_values := array_append(result_values, p_values[i]);
        END IF;
        i := i + 1;
    END LOOP;

    RETURN result_values;
END;
$$;

-- Задача 11.
-- Здесь я создаю функцию для формирования массива
-- из первых N простых чисел.
CREATE OR REPLACE FUNCTION first_n_primes(p_n INTEGER)
RETURNS INTEGER[]
LANGUAGE plpgsql
AS $$
DECLARE
    result_values INTEGER[] := ARRAY[]::INTEGER[];
    candidate INTEGER := 2;
    divisor INTEGER;
    is_prime BOOLEAN;
BEGIN
    IF p_n <= 0 THEN
        RETURN result_values;
    END IF;

    WHILE cardinality(result_values) < p_n LOOP
        is_prime := TRUE;
        divisor := 2;

        WHILE divisor * divisor <= candidate LOOP
            IF MOD(candidate, divisor) = 0 THEN
                is_prime := FALSE;
                EXIT;
            END IF;
            divisor := divisor + 1;
        END LOOP;

        IF is_prime THEN
            result_values := array_append(result_values, candidate);
        END IF;

        candidate := candidate + 1;
    END LOOP;

    RETURN result_values;
END;
$$;

-- Задача 12.
-- Здесь я создаю функцию генерации уникальных кодов резервирования
-- с проверкой на коллизии через цикл WHILE.
CREATE OR REPLACE FUNCTION generate_unique_reservation_codes(p_count INTEGER)
RETURNS TEXT[]
LANGUAGE plpgsql
AS $$
DECLARE
    result_codes TEXT[] := ARRAY[]::TEXT[];
    candidate_code TEXT;
BEGIN
    IF p_count <= 0 THEN
        RETURN result_codes;
    END IF;

    WHILE cardinality(result_codes) < p_count LOOP
        candidate_code := 'RSV-' || LPAD((FLOOR(RANDOM() * 1000000))::TEXT, 6, '0');

        IF NOT EXISTS (
            SELECT 1
            FROM lab_cart_reservations
            WHERE reservation_code = candidate_code
        ) AND NOT candidate_code = ANY(result_codes) THEN
            result_codes := array_append(result_codes, candidate_code);
        END IF;
    END LOOP;

    RETURN result_codes;
END;
$$;

-- Задача 13.
-- Здесь я создаю функцию поиска первого свободного окна
-- для инвентаризации между поставками товара.
CREATE OR REPLACE FUNCTION find_inventory_audit_window(
    p_product_id INTEGER,
    p_duration_hours INTEGER
)
RETURNS TABLE (
    gap_start TIMESTAMP,
    gap_end TIMESTAMP,
    gap_hours NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    rec RECORD;
    prev_end TIMESTAMP := NOW();
    current_gap INTERVAL;
BEGIN
    FOR rec IN
        SELECT slot_start, slot_end
        FROM lab_restock_windows
        WHERE product_id = p_product_id
          AND slot_end >= NOW()
          AND status <> 'cancelled'
        ORDER BY slot_start
    LOOP
        current_gap := rec.slot_start - prev_end;

        IF EXTRACT(EPOCH FROM current_gap) / 3600 >= p_duration_hours THEN
            gap_start := prev_end;
            gap_end := rec.slot_start;
            gap_hours := ROUND((EXTRACT(EPOCH FROM current_gap) / 3600)::NUMERIC, 2);
            RETURN NEXT;
            RETURN;
        END IF;

        prev_end := rec.slot_end;
    END LOOP;
END;
$$;

-- Задача 14.
-- Здесь я создаю процедуру удаления старых резервов пачками.
-- Эту процедуру лучше вызывать отдельно, не внутри явного BEGIN/COMMIT блока.
CREATE OR REPLACE PROCEDURE prune_old_cart_reservations(p_batch_size INTEGER DEFAULT 1000)
LANGUAGE plpgsql
AS $$
DECLARE
    v_deleted INTEGER := 0;
BEGIN
    LOOP
        DELETE FROM lab_cart_reservations
        WHERE reservation_id IN (
            SELECT reservation_id
            FROM lab_cart_reservations
            WHERE created_at < NOW() - INTERVAL '2 years'
            ORDER BY reservation_id
            LIMIT p_batch_size
        );

        GET DIAGNOSTICS v_deleted = ROW_COUNT;

        EXIT WHEN v_deleted = 0;

        RAISE NOTICE 'Удалено старых резервов: %', v_deleted;
        COMMIT;
    END LOOP;
END;
$$;

-- Задача 15.
-- Здесь я создаю процедуру архивирования старых событий заказов.
CREATE OR REPLACE PROCEDURE archive_old_order_events(p_batch_size INTEGER DEFAULT 500)
LANGUAGE plpgsql
AS $$
DECLARE
    v_moved INTEGER := 0;
BEGIN
    LOOP
        WITH old_rows AS (
            SELECT event_id, order_id, event_type, payload, occurred_at
            FROM lab_order_events
            WHERE occurred_at < NOW() - INTERVAL '10 days'
            ORDER BY event_id
            LIMIT p_batch_size
        ),
        inserted AS (
            INSERT INTO lab_order_events_archive (event_id, order_id, event_type, payload, occurred_at)
            SELECT event_id, order_id, event_type, payload, occurred_at
            FROM old_rows
            ON CONFLICT (event_id) DO NOTHING
            RETURNING event_id
        )
        DELETE FROM lab_order_events
        WHERE event_id IN (SELECT event_id FROM inserted);

        GET DIAGNOSTICS v_moved = ROW_COUNT;

        EXIT WHEN v_moved = 0;

        RAISE NOTICE 'Архивировано событий: %', v_moved;
    END LOOP;
END;
$$;

-- Задача 16.
-- Здесь я создаю процедуру отмены ближайших отгрузок склада
-- и попытки переноса заказов на другие доступные отгрузки.
CREATE OR REPLACE PROCEDURE cancel_shipments_for_warehouse(
    p_warehouse_code TEXT,
    p_hours INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    shp RECORD;
    booking RECORD;
    alt_shipment_id INTEGER;
BEGIN
    FOR shp IN
        SELECT shipment_id, route_code, scheduled_at
        FROM lab_shipments
        WHERE warehouse_code = p_warehouse_code
          AND status = 'scheduled'
          AND scheduled_at BETWEEN NOW() AND NOW() + MAKE_INTERVAL(hours => p_hours)
        ORDER BY scheduled_at
    LOOP
        FOR booking IN
            SELECT shipment_order_id, order_id, seats_reserved
            FROM lab_shipment_orders
            WHERE shipment_id = shp.shipment_id
        LOOP
            SELECT shipment_id
            INTO alt_shipment_id
            FROM lab_shipments
            WHERE warehouse_code = p_warehouse_code
              AND route_code = shp.route_code
              AND status = 'scheduled'
              AND shipment_id <> shp.shipment_id
              AND scheduled_at > shp.scheduled_at
              AND capacity - used_capacity >= booking.seats_reserved
            ORDER BY scheduled_at
            LIMIT 1;

            IF alt_shipment_id IS NOT NULL THEN
                UPDATE lab_shipment_orders
                SET shipment_id = alt_shipment_id
                WHERE shipment_order_id = booking.shipment_order_id;

                UPDATE lab_shipments
                SET used_capacity = used_capacity + booking.seats_reserved
                WHERE shipment_id = alt_shipment_id;
            ELSE
                UPDATE lab_customer_orders
                SET status = 'delayed'
                WHERE order_id = booking.order_id;
            END IF;
        END LOOP;

        UPDATE lab_shipments
        SET status = 'cancelled',
            used_capacity = 0
        WHERE shipment_id = shp.shipment_id;
    END LOOP;
END;
$$;

-- Здесь я добавляю вспомогательные функции для работы
-- с групповым заказом и JSON-данными.

CREATE OR REPLACE FUNCTION get_products_json(p_limit INTEGER)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    result_json JSONB := '[]'::JSONB;
    rec RECORD;
BEGIN
    FOR rec IN
        SELECT product_id, name, price
        FROM lab_products
        ORDER BY product_id
        LIMIT p_limit
    LOOP
        result_json := result_json || jsonb_build_object(
            'product_id', rec.product_id,
            'name', rec.name,
            'price', rec.price
        );
    END LOOP;

    RETURN result_json;
END;
$$;

CREATE OR REPLACE FUNCTION get_free_stock_count(p_product_id INTEGER)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_free_stock INTEGER;
BEGIN
    SELECT COALESCE(SUM(total_qty - reserved_qty), 0)
    INTO v_free_stock
    FROM lab_product_stock
    WHERE product_id = p_product_id;

    RETURN v_free_stock;
END;
$$;

CREATE OR REPLACE PROCEDURE create_group_order(
    p_customer_name TEXT,
    p_items JSONB,
    INOUT p_order_id INTEGER DEFAULT NULL,
    INOUT p_status TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    item JSONB;
    v_product_id INTEGER;
    v_quantity INTEGER;
    v_price NUMERIC;
    v_free_stock INTEGER;
    v_total NUMERIC := 0;
BEGIN
    INSERT INTO lab_customer_orders (customer_name, status, shipping_tier, warehouse_code, total_amount)
    VALUES (p_customer_name, 'new', 'standard', 'MSK', 0)
    RETURNING order_id INTO p_order_id;

    FOR item IN
        SELECT value
        FROM jsonb_array_elements(p_items)
    LOOP
        v_product_id := (item ->> 'product_id')::INTEGER;
        v_quantity := (item ->> 'quantity')::INTEGER;

        SELECT price
        INTO v_price
        FROM lab_products
        WHERE product_id = v_product_id;

        IF v_price IS NULL THEN
            p_status := format('Товар % не найден', v_product_id);
            RAISE EXCEPTION '%', p_status;
        END IF;

        v_free_stock := get_free_stock_count(v_product_id);

        IF v_free_stock < v_quantity THEN
            p_status := format('Недостаточно остатка по товару %', v_product_id);
            RAISE EXCEPTION '%', p_status;
        END IF;

        INSERT INTO lab_order_items (order_id, product_id, quantity, unit_price)
        VALUES (p_order_id, v_product_id, v_quantity, v_price);

        UPDATE lab_product_stock
        SET reserved_qty = reserved_qty + v_quantity
        WHERE product_id = v_product_id
          AND warehouse_code = 'MSK';

        v_total := v_total + (v_price * v_quantity);
    END LOOP;

    UPDATE lab_customer_orders
    SET total_amount = v_total
    WHERE order_id = p_order_id;

    p_status := 'Заказ успешно создан';
END;
$$;









































-- SET search_path TO lab_store, public;
-- -- Переключение на учебную схему.

-- SELECT * FROM lab_suppliers;
-- SELECT * FROM lab_supplier_requests;
-- SELECT * FROM lab_customer_orders;
-- -- Показываю учебные таблицы с тестовыми данными.

-- -- ЛР 3

-- CALL notify_overdue_requests(24);
-- -- Показываю заявки, которые слишком долго ждут обработки.

-- SELECT get_request_processing_time(2);
-- -- Показываю длительность обработки заявки.

-- CALL cancel_supplier_request(1);
-- SELECT * FROM lab_supplier_requests WHERE request_id = 1;
-- -- Отменяю заявку и сразу показываю новый статус.

-- SELECT * FROM get_supplier_activity(1);
-- -- Показываю статистику по заявкам поставщика.

-- CALL upgrade_order_shipping_tier(1, 'express', 10000);
-- SELECT * FROM lab_customer_orders WHERE order_id = 1;
-- -- Меняю тип доставки и показываю обновленный заказ.

-- CALL close_contracts_by_date(CURRENT_DATE);
-- SELECT * FROM lab_supplier_contracts;
-- -- Обновляю статусы просроченных договоров.

-- SELECT get_avg_request_review_time(1);
-- -- Показываю среднее время рассмотрения заявок.

-- CALL decommission_supplier(2);
-- SELECT * FROM lab_suppliers WHERE supplier_id = 2;
-- SELECT * FROM lab_supplier_requests WHERE supplier_id = 2;
-- SELECT * FROM lab_supplier_contracts WHERE supplier_id = 2;
-- -- Вывожу поставщика из работы и показываю изменения.

-- -- ЛР 4

-- SELECT pick_even_indexed_with_for(ARRAY[10, 20, 30, 40, 50, 60]);
-- -- Массив через цикл FOR.

-- SELECT pick_even_indexed_with_while(ARRAY[10, 20, 30, 40, 50, 60]);
-- -- Та же задача через WHILE.

-- SELECT first_n_primes(10);
-- -- Первые 10 простых чисел.

-- SELECT generate_unique_reservation_codes(5);
-- -- Генерация уникальных кодов.

-- SELECT * FROM find_inventory_audit_window(1, 4);
-- -- Поиск свободного окна между поставками.

-- CALL prune_old_cart_reservations(1000);
-- SELECT * FROM lab_cart_reservations;
-- -- Удаляю старые резервы пачками.

-- CALL archive_old_order_events(500);
-- SELECT * FROM lab_order_events;
-- SELECT * FROM lab_order_events_archive;
-- -- Переношу старые события в архив.

-- CALL cancel_shipments_for_warehouse('MSK', 6);
-- SELECT * FROM lab_shipments;
-- SELECT * FROM lab_shipment_orders;
-- SELECT * FROM lab_customer_orders;
-- -- Отменяю ближайшие отгрузки и показываю результат.

