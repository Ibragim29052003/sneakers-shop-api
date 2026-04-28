SET search_path TO lab_store, public;

-- 1. Добавляет тестовые данные для анализа производительности.
-- 2. Создаёт таблицу для демонстрации поиска по массивам и `jsonb`.
-- 3. Создаёт курсоры.
-- 4. Создаёт процедуры для удаления и создания индексов.
-- 5. Создаёт обычные, временные, материализованные и рекурсивные представления.
-- 6. Выполняет `ANALYZE`, чтобы PostgreSQL видел актуальную статистику.

-- СЛУЖЕБНЫЙ БЛОК 1.
-- Подготовка тестовых данных для EXPLAIN, курсоров и индексов
-- Этот блок нужен только для того, чтобы запросы были не на 5 строках,
-- а на ощутимом объеме данных, который можно анализировать в TablePlus.
CREATE OR REPLACE PROCEDURE lab5_seed_benchmark_data()
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM lab_products
        WHERE sku LIKE 'BENCH-SKU-%'
    ) THEN
        RAISE NOTICE 'Тестовые данные для ЛР5 уже были загружены';
        RETURN;
    END IF;

    INSERT INTO lab_products (supplier_id, category_id, name, sku, price, created_at)
    SELECT
        ((gs - 1) % 3) + 1,
        ((gs - 1) % 3) + 1,
        'Тестовый товар ' || gs,
        'BENCH-SKU-' || LPAD(gs::TEXT, 5, '0'),
        (1500 + (gs % 70) * 230)::NUMERIC(10, 2),
        NOW() - MAKE_INTERVAL(days => (gs % 365))
    FROM generate_series(1, 300) AS gs;

    INSERT INTO lab_product_stock (product_id, warehouse_code, total_qty, reserved_qty)
    SELECT
        p.product_id,
        w.warehouse_code,
        20 + (p.product_id % 90),
        p.product_id % 15
    FROM lab_products p
    CROSS JOIN (VALUES ('MSK'), ('SPB')) AS w(warehouse_code)
    WHERE p.sku LIKE 'BENCH-SKU-%'
    ON CONFLICT (product_id, warehouse_code) DO NOTHING;

    INSERT INTO lab_customer_orders (
        customer_name, status, shipping_tier, warehouse_code, total_amount, created_at, shipped_at
    )
    SELECT
        'Тестовый клиент ' || gs,
        (ARRAY['new', 'processing', 'shipped', 'cancelled', 'delayed'])[1 + (gs % 5)],
        (ARRAY['standard', 'priority', 'express'])[1 + (gs % 3)],
        (ARRAY['MSK', 'SPB'])[1 + (gs % 2)],
        0,
        NOW() - MAKE_INTERVAL(days => (gs % 240), hours => (gs % 24)),
        CASE
            WHEN (ARRAY['new', 'processing', 'shipped', 'cancelled', 'delayed'])[1 + (gs % 5)] = 'shipped'
                THEN NOW() - MAKE_INTERVAL(days => (gs % 180))
            ELSE NULL
        END
    FROM generate_series(1, 4000) AS gs;

    WITH bench_orders AS (
        SELECT
            order_id,
            ROW_NUMBER() OVER (ORDER BY order_id) AS rn
        FROM lab_customer_orders
        WHERE customer_name LIKE 'Тестовый клиент %'
    ),
    bench_products AS (
        SELECT
            product_id,
            price,
            ROW_NUMBER() OVER (ORDER BY product_id) AS rn
        FROM lab_products
        WHERE sku LIKE 'BENCH-SKU-%'
    )
    INSERT INTO lab_order_items (order_id, product_id, quantity, unit_price)
    SELECT
        o.order_id,
        p.product_id,
        1 + (o.rn % 3),
        p.price
    FROM bench_orders o
    JOIN bench_products p
      ON p.rn = ((o.rn - 1) % 300) + 1
    UNION ALL
    SELECT
        o.order_id,
        p.product_id,
        1 + ((o.rn + 1) % 2),
        p.price
    FROM bench_orders o
    JOIN bench_products p
      ON p.rn = ((o.rn + 47) % 300) + 1
    WHERE o.rn % 4 <> 0;

    UPDATE lab_customer_orders o
    SET total_amount = totals.total_amount
    FROM (
        SELECT
            oi.order_id,
            SUM(oi.quantity * oi.unit_price)::NUMERIC(12, 2) AS total_amount
        FROM lab_order_items oi
        GROUP BY oi.order_id
    ) AS totals
    WHERE totals.order_id = o.order_id
      AND o.customer_name LIKE 'Тестовый клиент %';

    WITH generated AS (
        SELECT
            gs,
            ((gs - 1) % 3) + 1 AS supplier_id,
            'Тестовая поставка ' || gs AS product_name,
            (ARRAY['pending', 'under_review', 'approved', 'rejected', 'cancelled'])[1 + (gs % 5)] AS status,
            (ARRAY['normal', 'high', 'urgent'])[1 + (gs % 3)] AS priority,
            (1200 + (gs % 140) * 95)::NUMERIC(10, 2) AS estimated_cost,
            (1400 + (gs % 160) * 100)::NUMERIC(10, 2) AS quoted_cost,
            NOW() - MAKE_INTERVAL(days => (gs % 210), hours => (gs % 24)) AS created_at
        FROM generate_series(1, 6000) AS gs
    )
    INSERT INTO lab_supplier_requests (
        supplier_id, product_name, status, priority, estimated_cost, quoted_cost,
        created_at, reviewed_at, resolved_at, cancelled_at
    )
    SELECT
        supplier_id,
        product_name,
        status,
        priority,
        estimated_cost,
        CASE
            WHEN status IN ('under_review', 'approved', 'rejected') THEN quoted_cost
            ELSE NULL
        END,
        created_at,
        CASE
            WHEN status IN ('under_review', 'approved', 'rejected')
                THEN created_at + INTERVAL '6 hours'
            ELSE NULL
        END,
        CASE
            WHEN status IN ('approved', 'rejected', 'cancelled')
                THEN created_at + INTERVAL '1 day'
            ELSE NULL
        END,
        CASE
            WHEN status = 'cancelled'
                THEN created_at + INTERVAL '1 day'
            ELSE NULL
        END
    FROM generated;

    WITH bench_orders AS (
        SELECT
            order_id,
            created_at,
            status,
            ROW_NUMBER() OVER (ORDER BY order_id) AS rn
        FROM lab_customer_orders
        WHERE customer_name LIKE 'Тестовый клиент %'
    )
    INSERT INTO lab_order_events (order_id, event_type, payload, occurred_at)
    SELECT
        order_id,
        'created',
        jsonb_build_object(
            'source',
            CASE WHEN rn % 2 = 0 THEN 'сайт' ELSE 'мобильное приложение' END,
            'campaign',
            CASE WHEN rn % 5 = 0 THEN 'winter-sale' ELSE 'base' END
        ),
        created_at + INTERVAL '5 minutes'
    FROM bench_orders;

    WITH bench_orders AS (
        SELECT
            order_id,
            created_at,
            status,
            ROW_NUMBER() OVER (ORDER BY order_id) AS rn
        FROM lab_customer_orders
        WHERE customer_name LIKE 'Тестовый клиент %'
          AND status IN ('processing', 'shipped', 'delayed')
    )
    INSERT INTO lab_order_events (order_id, event_type, payload, occurred_at)
    SELECT
        order_id,
        'paid',
        jsonb_build_object(
            'method',
            CASE WHEN rn % 3 = 0 THEN 'карта' ELSE 'сбп' END,
            'priority',
            CASE WHEN rn % 4 = 0 THEN 'vip' ELSE 'regular' END
        ),
        created_at + INTERVAL '2 hours'
    FROM bench_orders;

    WITH bench_orders AS (
        SELECT
            order_id,
            created_at
        FROM lab_customer_orders
        WHERE customer_name LIKE 'Тестовый клиент %'
          AND status = 'shipped'
    )
    INSERT INTO lab_order_events (order_id, event_type, payload, occurred_at)
    SELECT
        order_id,
        'shipped',
        jsonb_build_object('carrier', 'курьер', 'status', 'departed'),
        created_at + INTERVAL '2 days'
    FROM bench_orders;

    INSERT INTO lab_shipments (warehouse_code, route_code, scheduled_at, status, capacity, used_capacity)
    SELECT
        CASE WHEN gs % 2 = 0 THEN 'MSK' ELSE 'SPB' END,
        'LAB5-ROUTE-' || (((gs - 1) % 6) + 1),
        NOW() + MAKE_INTERVAL(days => (gs % 45), hours => (gs % 10)),
        CASE
            WHEN gs % 11 = 0 THEN 'cancelled'
            WHEN gs % 4 = 0 THEN 'departed'
            ELSE 'scheduled'
        END,
        12 + (gs % 6),
        0
    FROM generate_series(1, 90) AS gs;

    WITH bench_orders AS (
        SELECT
            order_id,
            ROW_NUMBER() OVER (ORDER BY order_id) AS rn
        FROM lab_customer_orders
        WHERE customer_name LIKE 'Тестовый клиент %'
          AND status IN ('processing', 'shipped', 'delayed')
    ),
    available_shipments AS (
        SELECT
            shipment_id,
            ROW_NUMBER() OVER (ORDER BY scheduled_at, shipment_id) AS rn
        FROM lab_shipments
        WHERE route_code LIKE 'LAB5-ROUTE-%'
          AND status <> 'cancelled'
    ),
    shipment_count AS (
        SELECT COUNT(*) AS cnt
        FROM available_shipments
    )
    INSERT INTO lab_shipment_orders (shipment_id, order_id, seats_reserved)
    SELECT
        s.shipment_id,
        o.order_id,
        1
    FROM bench_orders o
    CROSS JOIN shipment_count sc
    JOIN available_shipments s
      ON s.rn = ((o.rn - 1) % sc.cnt) + 1
    WHERE o.rn <= LEAST(600, sc.cnt * 8);

    UPDATE lab_shipments s
    SET used_capacity = COALESCE(stats.total_reserved, 0)
    FROM (
        SELECT
            shipment_id,
            SUM(seats_reserved) AS total_reserved
        FROM lab_shipment_orders
        GROUP BY shipment_id
    ) AS stats
    WHERE stats.shipment_id = s.shipment_id;

    RAISE NOTICE 'Тестовые данные для ЛР5 успешно добавлены';
END;
$$;

CALL lab5_seed_benchmark_data();


-- СЛУЖЕБНЫЙ БЛОК 2.
-- Таблица и синхронизация данных для массива и JSONB
-- Этот блок нужен для части задания, где требуется показать:
-- 1. фильтрацию по массиву;
-- 2. фильтрацию по json-формату;
-- 3. полезность индексов для таких запросов.
CREATE TABLE IF NOT EXISTS lab_product_search_profiles (
    product_id INTEGER PRIMARY KEY REFERENCES lab_products(product_id) ON DELETE CASCADE,
    search_tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    attributes JSONB NOT NULL DEFAULT '{}'::JSONB,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE PROCEDURE lab5_sync_product_search_profiles()
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO lab_product_search_profiles (product_id, search_tags, attributes, updated_at)
    SELECT
        p.product_id,
        ARRAY_REMOVE(
            ARRAY[
                LOWER(REPLACE(c.name, ' ', '_')),
                'supplier_' || p.supplier_id,
                CASE
                    WHEN p.price >= 15000 THEN 'premium'
                    WHEN p.price >= 5000 THEN 'middle'
                    ELSE 'budget'
                END,
                CASE
                    WHEN COALESCE(stock.free_qty, 0) > 20 THEN 'in_stock'
                    ELSE 'limited'
                END,
                CASE
                    WHEN p.created_at >= NOW() - INTERVAL '30 days' THEN 'new'
                    ELSE NULL
                END
            ],
            NULL
        ),
        jsonb_build_object(
            'category', c.name,
            'supplier', s.name,
            'warehouse', COALESCE(stock.main_warehouse, 'MSK'),
            'price_band',
            CASE
                WHEN p.price >= 15000 THEN 'high'
                WHEN p.price >= 5000 THEN 'middle'
                ELSE 'low'
            END,
            'free_qty', COALESCE(stock.free_qty, 0),
            'is_benchmark', (p.sku LIKE 'BENCH-SKU-%')
        ),
        NOW()
    FROM lab_products p
    JOIN lab_categories c
      ON c.category_id = p.category_id
    JOIN lab_suppliers s
      ON s.supplier_id = p.supplier_id
    LEFT JOIN (
        SELECT
            product_id,
            MAX(warehouse_code) AS main_warehouse,
            SUM(total_qty - reserved_qty) AS free_qty
        FROM lab_product_stock
        GROUP BY product_id
    ) AS stock
      ON stock.product_id = p.product_id
    ON CONFLICT (product_id) DO UPDATE
    SET search_tags = EXCLUDED.search_tags,
        attributes = EXCLUDED.attributes,
        updated_at = NOW();
END;
$$;

CALL lab5_sync_product_search_profiles();


-- ЧАСТЬ I. КУРСОРЫ
-- Курсор не меняет сам алгоритм выполнения запроса, но позволяет читать
-- большой результат частями, а не загружать его целиком в память клиента.
--
-- Здесь подготовлены 4 курсора:
-- 1. по заявкам поставщиков;
-- 2. по аналитике продаж;
-- 3. по полнотекстовому поиску;
-- 4. по фильтрации массива и jsonb.

CREATE OR REPLACE FUNCTION lab5_open_supplier_requests_cursor(
    p_cursor_name TEXT DEFAULT 'lab5_supplier_requests_cursor',
    p_from_timestamp TIMESTAMP DEFAULT NOW() - INTERVAL '180 days',
    p_statuses TEXT[] DEFAULT ARRAY['pending', 'under_review', 'approved']::TEXT[]
)
RETURNS REFCURSOR
LANGUAGE plpgsql
AS $$
DECLARE
    v_cursor REFCURSOR := p_cursor_name;
BEGIN
    OPEN v_cursor FOR
    SELECT
        supplier_id,
        status,
        priority,
        product_name,
        estimated_cost,
        created_at
    FROM lab_supplier_requests
    WHERE created_at >= p_from_timestamp
      AND status = ANY(p_statuses)
    ORDER BY supplier_id, created_at DESC;

    RETURN v_cursor;
END;
$$;

CREATE OR REPLACE FUNCTION lab5_open_sales_analytics_cursor(
    p_cursor_name TEXT DEFAULT 'lab5_sales_cursor',
    p_from_timestamp TIMESTAMP DEFAULT NOW() - INTERVAL '180 days',
    p_warehouses TEXT[] DEFAULT ARRAY['MSK', 'SPB']::TEXT[]
)
RETURNS REFCURSOR
LANGUAGE plpgsql
AS $$
DECLARE
    v_cursor REFCURSOR := p_cursor_name;
BEGIN
    OPEN v_cursor FOR
    SELECT
        o.warehouse_code,
        s.name AS supplier_name,
        c.name AS category_name,
        COUNT(DISTINCT o.order_id) AS orders_count,
        SUM(oi.quantity) AS units_sold,
        ROUND(SUM(oi.quantity * oi.unit_price)::NUMERIC, 2) AS revenue
    FROM lab_customer_orders o
    JOIN lab_order_items oi
      ON oi.order_id = o.order_id
    JOIN lab_products p
      ON p.product_id = oi.product_id
    JOIN lab_suppliers s
      ON s.supplier_id = p.supplier_id
    JOIN lab_categories c
      ON c.category_id = p.category_id
    WHERE o.created_at >= p_from_timestamp
      AND o.status IN ('processing', 'shipped')
      AND o.warehouse_code = ANY(p_warehouses)
    GROUP BY o.warehouse_code, s.name, c.name
    ORDER BY revenue DESC, units_sold DESC;

    RETURN v_cursor;
END;
$$;

CREATE OR REPLACE FUNCTION lab5_open_product_search_cursor(
    p_cursor_name TEXT DEFAULT 'lab5_product_search_cursor',
    p_search_text TEXT DEFAULT 'куртка'
)
RETURNS REFCURSOR
LANGUAGE plpgsql
AS $$
DECLARE
    v_cursor REFCURSOR := p_cursor_name;
BEGIN
    OPEN v_cursor FOR
    SELECT
        p.product_id,
        p.sku,
        p.name,
        p.price,
        ts_rank(
            to_tsvector('russian', COALESCE(p.name, '') || ' ' || COALESCE(p.sku, '')),
            websearch_to_tsquery('russian', p_search_text)
        ) AS rank_value
    FROM lab_products p
    WHERE to_tsvector('russian', COALESCE(p.name, '') || ' ' || COALESCE(p.sku, ''))
          @@ websearch_to_tsquery('russian', p_search_text)
    ORDER BY rank_value DESC, p.product_id;

    RETURN v_cursor;
END;
$$;

CREATE OR REPLACE FUNCTION lab5_open_profile_filter_cursor(
    p_cursor_name TEXT DEFAULT 'lab5_profile_filter_cursor',
    p_tags TEXT[] DEFAULT ARRAY['middle', 'in_stock']::TEXT[],
    p_json_filter JSONB DEFAULT '{"warehouse":"MSK","price_band":"middle"}'::JSONB
)
RETURNS REFCURSOR
LANGUAGE plpgsql
AS $$
DECLARE
    v_cursor REFCURSOR := p_cursor_name;
BEGIN
    OPEN v_cursor FOR
    SELECT
        p.product_id,
        p.name,
        profile.search_tags,
        profile.attributes
    FROM lab_product_search_profiles profile
    JOIN lab_products p
      ON p.product_id = profile.product_id
    WHERE profile.search_tags && p_tags
      AND profile.attributes @> p_json_filter
    ORDER BY p.product_id;

    RETURN v_cursor;
END;
$$;


-- ЧАСТЬ I. ИНДЕКСЫ
-- Здесь вынесены процедуры:
-- 1. удаления индексов, чтобы сравнить план "до";
-- 2. создания индексов, чтобы сравнить план "после".
--
-- Индексы покрывают:
-- - фильтрацию и группировку по заявкам;
-- - заказы и состав заказа;
-- - связанные таблицы товаров;
-- - полнотекстовый поиск;
-- - массивы;
-- - JSONB.
--
-- Индексы не создаются автоматически, чтобы можно было честно сравнить
-- планы "до" и "после" в lab_5_test.sql.

CREATE OR REPLACE PROCEDURE lab5_drop_indexes()
LANGUAGE plpgsql
AS $$
BEGIN
    DROP INDEX IF EXISTS idx_lab5_supplier_requests_filter;
    DROP INDEX IF EXISTS idx_lab5_customer_orders_filter;
    DROP INDEX IF EXISTS idx_lab5_order_items_order_product;
    DROP INDEX IF EXISTS idx_lab5_products_category_supplier;
    DROP INDEX IF EXISTS idx_lab5_shipment_orders_order_shipment;
    DROP INDEX IF EXISTS idx_lab5_shipments_status_schedule;
    DROP INDEX IF EXISTS idx_lab5_products_fts;
    DROP INDEX IF EXISTS idx_lab5_product_profiles_tags_gin;
    DROP INDEX IF EXISTS idx_lab5_product_profiles_attributes_gin;
END;
$$;

CREATE OR REPLACE PROCEDURE lab5_create_indexes()
LANGUAGE plpgsql
AS $$
BEGIN
    CALL lab5_sync_product_search_profiles();

    CREATE INDEX IF NOT EXISTS idx_lab5_supplier_requests_filter
        ON lab_supplier_requests (status, created_at, supplier_id, priority)
        WHERE status IN ('pending', 'under_review', 'approved');

    CREATE INDEX IF NOT EXISTS idx_lab5_customer_orders_filter
        ON lab_customer_orders (status, warehouse_code, created_at);

    CREATE INDEX IF NOT EXISTS idx_lab5_order_items_order_product
        ON lab_order_items (order_id, product_id);

    CREATE INDEX IF NOT EXISTS idx_lab5_products_category_supplier
        ON lab_products (category_id, supplier_id);

    CREATE INDEX IF NOT EXISTS idx_lab5_shipment_orders_order_shipment
        ON lab_shipment_orders (order_id, shipment_id);

    CREATE INDEX IF NOT EXISTS idx_lab5_shipments_status_schedule
        ON lab_shipments (status, scheduled_at, warehouse_code, route_code);

    CREATE INDEX IF NOT EXISTS idx_lab5_products_fts
        ON lab_products
        USING GIN (to_tsvector('russian', COALESCE(name, '') || ' ' || COALESCE(sku, '')));

    CREATE INDEX IF NOT EXISTS idx_lab5_product_profiles_tags_gin
        ON lab_product_search_profiles
        USING GIN (search_tags);

    CREATE INDEX IF NOT EXISTS idx_lab5_product_profiles_attributes_gin
        ON lab_product_search_profiles
        USING GIN (attributes jsonb_path_ops);

    ANALYZE lab_supplier_requests;
    ANALYZE lab_customer_orders;
    ANALYZE lab_order_items;
    ANALYZE lab_products;
    ANALYZE lab_shipments;
    ANALYZE lab_shipment_orders;
    ANALYZE lab_product_search_profiles;
END;
$$;

SELECT
    tablename AS "Таблица",
    indexname AS "Индекс",
    indexdef AS "Определение"
FROM pg_indexes
WHERE schemaname = 'lab_store'
  AND indexname LIKE 'idx_lab5_%'
ORDER BY tablename;

-- ЧАСТЬ II. ПРЕДСТАВЛЕНИЯ
--
-- ЗАДАНИЕ 1.
-- Представление для отображения всех доступных товаров.
-- На его основе в test-файле показываются товары конкретного поставщика.
CREATE OR REPLACE VIEW v_available_products AS
SELECT
    p.product_id,
    p.sku,
    p.name AS product_name,
    c.name AS category_name,
    s.name AS supplier_name,
    p.price,
    p.created_at,
    COALESCE(stock.free_qty, 0) AS free_qty,
    COALESCE(stock.warehouses, ARRAY[]::TEXT[]) AS warehouses
FROM lab_products p
JOIN lab_categories c
  ON c.category_id = p.category_id
JOIN lab_suppliers s
  ON s.supplier_id = p.supplier_id
LEFT JOIN (
    SELECT
        product_id,
        SUM(total_qty - reserved_qty) AS free_qty,
        ARRAY_AGG(warehouse_code ORDER BY warehouse_code) AS warehouses
    FROM lab_product_stock
    GROUP BY product_id
) AS stock
  ON stock.product_id = p.product_id
WHERE s.is_active = TRUE
  AND COALESCE(stock.free_qty, 0) > 0;


-- Временные представления создаются отдельной процедурой,
-- потому что TEMP VIEW живет только в рамках текущего сеанса.
--
-- ЗАДАНИЕ 2.
-- Временное представление: все поставщики и их средние цены.
--
-- ЗАДАНИЕ 3.
-- Временное представление: товары в заданном диапазоне цен.
--
-- ЗАДАНИЕ 4.
-- Временное представление: доступные места на конкретной отгрузке.
--
-- ЗАДАНИЕ 5.
-- Временное представление: клиенты с бронированием на следующий месяц.
--
-- ЗАДАНИЕ 7.
-- Временное представление: отгрузки с заполненностью меньше 50%.
--
-- ЗАДАНИЕ 8.
-- Временное представление: поставщики с количеством отмененных заявок.
--
-- ЗАДАНИЕ 10.
-- Временное представление: клиенты с отправками в ближайшие 7 дней.
CREATE OR REPLACE PROCEDURE lab5_create_temp_views()
LANGUAGE plpgsql
AS $$
BEGIN
    EXECUTE $sql$
        CREATE OR REPLACE TEMP VIEW tv_supplier_avg_product_prices AS
        SELECT
            s.supplier_id,
            s.name AS supplier_name,
            COUNT(p.product_id) AS product_count,
            ROUND(AVG(p.price)::NUMERIC, 2) AS avg_price
        FROM lab_suppliers s
        JOIN lab_products p
          ON p.supplier_id = s.supplier_id
        GROUP BY s.supplier_id, s.name
    $sql$;

    EXECUTE $sql$
        CREATE OR REPLACE TEMP VIEW tv_products_in_price_range AS
        SELECT
            product_id,
            sku,
            name AS product_name,
            price,
            created_at
        FROM lab_products
        WHERE price BETWEEN 3000 AND 15000
    $sql$;REFRESH MATERIALIZED VIEW

    EXECUTE $sql$
        CREATE OR REPLACE TEMP VIEW tv_shipment_available_capacity AS
        SELECT
            shipment_id,
            warehouse_code,
            route_code,
            scheduled_at,
            capacity,
            used_capacity,
            capacity - used_capacity AS free_capacity
        FROM lab_shipments
        WHERE status = 'scheduled'
          AND capacity - used_capacity > 0
    $sql$;

    EXECUTE $sql$
        CREATE OR REPLACE TEMP VIEW tv_customers_booked_next_month AS
        SELECT
            o.order_id,
            o.customer_name,
            o.status,
            s.route_code,
            s.warehouse_code,
            s.scheduled_at
        FROM lab_customer_orders o
        JOIN lab_shipment_orders so
          ON so.order_id = o.order_id
        JOIN lab_shipments s
          ON s.shipment_id = so.shipment_id
        WHERE s.scheduled_at >= date_trunc('month', CURRENT_DATE + INTERVAL '1 month')
          AND s.scheduled_at < date_trunc('month', CURRENT_DATE + INTERVAL '2 months')
    $sql$;

    EXECUTE $sql$
        CREATE OR REPLACE TEMP VIEW tv_low_fill_shipments AS
        SELECT
            shipment_id,
            warehouse_code,
            route_code,
            scheduled_at,
            capacity,
            used_capacity,
            ROUND((used_capacity::NUMERIC / NULLIF(capacity, 0)) * 100, 2) AS fill_ratio
        FROM lab_shipments
        WHERE status = 'scheduled'
          AND used_capacity::NUMERIC / NULLIF(capacity, 0) < 0.50
    $sql$;

    EXECUTE $sql$
        CREATE OR REPLACE TEMP VIEW tv_suppliers_cancelled_requests AS
        SELECT
            s.supplier_id,
            s.name AS supplier_name,
            COUNT(r.request_id) FILTER (WHERE r.status = 'cancelled') AS cancelled_requests
        FROM lab_suppliers s
        LEFT JOIN lab_supplier_requests r
          ON r.supplier_id = s.supplier_id
        GROUP BY s.supplier_id, s.name
    $sql$;

    EXECUTE $sql$
        CREATE OR REPLACE TEMP VIEW tv_customers_booked_next_7_days AS
        SELECT
            o.order_id,
            o.customer_name,
            o.status,
            s.route_code,
            s.warehouse_code,
            s.scheduled_at
        FROM lab_customer_orders o
        JOIN lab_shipment_orders so
          ON so.order_id = o.order_id
        JOIN lab_shipments s
          ON s.shipment_id = so.shipment_id
        WHERE s.scheduled_at >= NOW()
          AND s.scheduled_at < NOW() + INTERVAL '7 days'
        ORDER BY s.scheduled_at
    $sql$;
END;
$$;


-- ЧАСТЬ II. МАТЕРИАЛИЗОВАННЫЕ ПРЕДСТАВЛЕНИЯ
--
-- ЗАДАНИЕ 6.
-- Материализованное представление: количество отправок по сезонам.
DROP MATERIALIZED VIEW IF EXISTS mv_shipments_by_season;
CREATE MATERIALIZED VIEW mv_shipments_by_season AS
SELECT
    CASE
        WHEN EXTRACT(MONTH FROM scheduled_at) IN (12, 1, 2) THEN 'winter'
        WHEN EXTRACT(MONTH FROM scheduled_at) IN (6, 7, 8) THEN 'summer'
        ELSE 'offseason'
    END AS season_name,
    warehouse_code,
    COUNT(*) AS shipment_count,
    COUNT(*) FILTER (WHERE status = 'departed') AS departed_count,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_count
FROM lab_shipments
GROUP BY 1, 2;

-- ЗАДАНИЕ 9.
-- Материализованное представление: количество заказов по дням недели.
DROP MATERIALIZED VIEW IF EXISTS mv_orders_by_weekday;
CREATE MATERIALIZED VIEW mv_orders_by_weekday AS
SELECT
    EXTRACT(ISODOW FROM created_at)::INTEGER AS iso_weekday,
    TRIM(TO_CHAR(created_at, 'Day')) AS weekday_name,
    warehouse_code,
    COUNT(*) AS order_count,
    ROUND(SUM(total_amount)::NUMERIC, 2) AS revenue
FROM lab_customer_orders
GROUP BY 1, 2, 3;

-- ЗАДАНИЕ 11.
-- Материализованное представление: среднее время ожидания до отправки по маршрутам.
DROP MATERIALIZED VIEW IF EXISTS mv_avg_wait_to_shipment_by_route;
CREATE MATERIALIZED VIEW mv_avg_wait_to_shipment_by_route AS
SELECT
    s.route_code,
    s.warehouse_code,
    COUNT(*) AS booked_orders,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (s.scheduled_at - o.created_at)) / 3600)::NUMERIC,
        2
    ) AS avg_wait_hours
FROM lab_shipment_orders so
JOIN lab_shipments s
  ON s.shipment_id = so.shipment_id
JOIN lab_customer_orders o
  ON o.order_id = so.order_id
GROUP BY s.route_code, s.warehouse_code;

-- ЗАДАНИЕ 12.
-- Материализованное представление: самые загруженные склады.
DROP MATERIALIZED VIEW IF EXISTS mv_busiest_warehouses;
CREATE MATERIALIZED VIEW mv_busiest_warehouses AS
SELECT
    o.warehouse_code,
    COUNT(DISTINCT o.order_id) AS order_count,
    COUNT(oi.order_item_id) AS item_rows,
    COALESCE(SUM(oi.quantity), 0) AS units_sold,
    ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0)::NUMERIC, 2) AS revenue,
    COUNT(DISTINCT so.shipment_id) AS shipment_count
FROM lab_customer_orders o
LEFT JOIN lab_order_items oi
  ON oi.order_id = o.order_id
LEFT JOIN lab_shipment_orders so
  ON so.order_id = o.order_id
GROUP BY o.warehouse_code;

CREATE OR REPLACE PROCEDURE lab5_refresh_materialized_views()
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_shipments_by_season;
    REFRESH MATERIALIZED VIEW mv_orders_by_weekday;
    REFRESH MATERIALIZED VIEW mv_avg_wait_to_shipment_by_route;
    REFRESH MATERIALIZED VIEW mv_busiest_warehouses;
END;
$$;


-- ЧАСТЬ II. РЕКУРСИВНЫЕ ПРЕДСТАВЛЕНИЯ
--
-- ЗАДАНИЕ 13.
-- Создать 5 рекурсивных представлений.
--
-- 13.1. Последовательность чисел от 1 до 10.
CREATE OR REPLACE RECURSIVE VIEW rv_numbers_1_10 (n) AS
SELECT 1
UNION ALL
SELECT n + 1
FROM rv_numbers_1_10
WHERE n < 10;

-- 13.2. Ближайшие 7 календарных дней.
CREATE OR REPLACE RECURSIVE VIEW rv_next_7_days (step_no, calendar_day) AS
SELECT 1, CURRENT_DATE
UNION ALL
SELECT step_no + 1, calendar_day + 1
FROM rv_next_7_days
WHERE step_no < 7;

-- 13.3. Развертывание quantity по позициям заказа в отдельные единицы.
CREATE OR REPLACE RECURSIVE VIEW rv_order_item_units (
    order_item_id,
    product_id,
    unit_no,
    total_units
) AS
SELECT
    order_item_id,
    product_id,
    1,
    quantity
FROM lab_order_items
WHERE quantity > 0
UNION ALL
SELECT
    order_item_id,
    product_id,
    unit_no + 1,
    total_units
FROM rv_order_item_units
WHERE unit_no < total_units;

-- 13.4. Помесячное развертывание периода действия договоров.
CREATE OR REPLACE RECURSIVE VIEW rv_contract_months (
    contract_id,
    supplier_id,
    month_start,
    contract_end
) AS
SELECT
    contract_id,
    supplier_id,
    date_trunc('month', start_date)::DATE,
    end_date
FROM lab_supplier_contracts
UNION ALL
SELECT
    contract_id,
    supplier_id,
    (month_start + INTERVAL '1 month')::DATE,
    contract_end
FROM rv_contract_months
WHERE (month_start + INTERVAL '1 month')::DATE <= date_trunc('month', contract_end)::DATE;

-- 13.5. Почасовое развертывание окон поставки.
CREATE OR REPLACE RECURSIVE VIEW rv_restock_hour_slots (
    window_id,
    product_id,
    hour_point,
    slot_end
) AS
SELECT
    window_id,
    product_id,
    date_trunc('hour', slot_start),
    slot_end
FROM lab_restock_windows
UNION ALL
SELECT
    window_id,
    product_id,
    hour_point + INTERVAL '1 hour',
    slot_end
FROM rv_restock_hour_slots
WHERE hour_point + INTERVAL '1 hour' < slot_end;


-- ФИНАЛЬНЫЙ ANALYZE
-- Обновляю статистику, чтобы оптимизатор PostgreSQL видел
-- актуальное состояние таблиц после подготовки данных.
ANALYZE lab_products;
ANALYZE lab_product_stock;
ANALYZE lab_customer_orders;
ANALYZE lab_order_items;
ANALYZE lab_supplier_requests;
ANALYZE lab_order_events;
ANALYZE lab_shipments;
ANALYZE lab_shipment_orders;
ANALYZE lab_product_search_profiles;
