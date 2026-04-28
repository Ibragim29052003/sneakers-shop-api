SET search_path TO lab_store, public;

-- =========================================================
-- ЛАБОРАТОРНАЯ РАБОТА №6: Транзакции и триггеры
-- Тема проекта: интернет-магазин (заказы, доставки, маршруты)
-- ОСНОВНОЙ ФАЙЛ: только структура, функции, триггеры
-- =========================================================

DROP TABLE IF EXISTS lab6_delivery_assignments CASCADE;
DROP TABLE IF EXISTS lab6_order_deliveries CASCADE;
DROP TABLE IF EXISTS lab6_order_items CASCADE;
DROP TABLE IF EXISTS lab6_orders CASCADE;
DROP TABLE IF EXISTS lab6_deliveries CASCADE;
DROP TABLE IF EXISTS lab6_routes CASCADE;
DROP TABLE IF EXISTS lab6_vehicle_slots CASCADE;
DROP TABLE IF EXISTS lab6_vehicles CASCADE;
DROP TABLE IF EXISTS lab6_vehicles_audit CASCADE;
DROP TABLE IF EXISTS lab6_row_change_log CASCADE;

-- Базовые таблицы
CREATE TABLE lab6_vehicles (
    vehicle_code TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    slots_count INTEGER NOT NULL CHECK (slots_count > 0),
    capacity_kg INTEGER NOT NULL CHECK (capacity_kg > 0),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE lab6_vehicle_slots (
    vehicle_code TEXT NOT NULL,
    slot_no TEXT NOT NULL,
    slot_type TEXT NOT NULL CHECK (slot_type IN ('small', 'medium', 'large')),
    PRIMARY KEY (vehicle_code, slot_no),
    FOREIGN KEY (vehicle_code) REFERENCES lab6_vehicles(vehicle_code)
);

CREATE TABLE lab6_routes (
    route_no TEXT PRIMARY KEY,
    from_hub TEXT NOT NULL,
    to_hub TEXT NOT NULL,
    duration_min INTEGER NOT NULL CHECK (duration_min > 0)
);

CREATE TABLE lab6_deliveries (
    delivery_id SERIAL PRIMARY KEY,
    route_no TEXT NOT NULL REFERENCES lab6_routes(route_no) ON UPDATE CASCADE,
    vehicle_code TEXT NOT NULL REFERENCES lab6_vehicles(vehicle_code),
    status TEXT NOT NULL DEFAULT 'Planned' CHECK (status IN ('Planned', 'Packing', 'Dispatched', 'Delivered', 'Cancelled')),
    scheduled_departure TIMESTAMP NOT NULL,
    scheduled_arrival TIMESTAMP NOT NULL,
    actual_departure TIMESTAMP,
    actual_arrival TIMESTAMP,
    CHECK (scheduled_arrival > scheduled_departure)
);

CREATE TABLE lab6_orders (
    order_ref TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    order_date TIMESTAMP NOT NULL DEFAULT NOW(),
    total_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0)
);

CREATE TABLE lab6_order_items (
    item_no TEXT PRIMARY KEY,
    order_ref TEXT NOT NULL REFERENCES lab6_orders(order_ref) ON DELETE CASCADE,
    product_name TEXT NOT NULL,
    discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (discount_pct >= 0 AND discount_pct <= 30),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE lab6_order_deliveries (
    item_no TEXT NOT NULL REFERENCES lab6_order_items(item_no) ON DELETE CASCADE,
    delivery_id INTEGER NOT NULL REFERENCES lab6_deliveries(delivery_id) ON DELETE CASCADE,
    line_amount NUMERIC(10,2) NOT NULL CHECK (line_amount >= 0),
    PRIMARY KEY (item_no, delivery_id)
);

CREATE TABLE lab6_delivery_assignments (
    item_no TEXT NOT NULL,
    delivery_id INTEGER NOT NULL,
    assignment_no INTEGER,
    slot_no TEXT NOT NULL,
    PRIMARY KEY (item_no, delivery_id),
    FOREIGN KEY (item_no, delivery_id) REFERENCES lab6_order_deliveries(item_no, delivery_id)
);

CREATE TABLE lab6_vehicles_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    vehicle_code TEXT NOT NULL,
    old_model TEXT,
    new_model TEXT,
    old_slots_count INTEGER,
    new_slots_count INTEGER,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    changed_by TEXT NOT NULL DEFAULT CURRENT_USER
);

CREATE TABLE lab6_row_change_log (
    log_id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    attribute_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ЗАДАНИЕ 1
-- 1.1 Проверка свободных слотов перед назначением заказа
CREATE OR REPLACE FUNCTION trg_lab6_check_free_slots()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_vehicle TEXT;
    v_capacity INT;
    v_used INT;
BEGIN
    SELECT d.vehicle_code INTO v_vehicle FROM lab6_deliveries d WHERE d.delivery_id = NEW.delivery_id;
    IF v_vehicle IS NULL THEN
        RAISE EXCEPTION 'Доставка % не найдена', NEW.delivery_id;
    END IF;

    SELECT COUNT(*) INTO v_capacity FROM lab6_vehicle_slots s WHERE s.vehicle_code = v_vehicle;
    SELECT COUNT(*) INTO v_used FROM lab6_delivery_assignments a WHERE a.delivery_id = NEW.delivery_id;

    IF v_used >= v_capacity THEN
        RAISE EXCEPTION 'Нет свободных слотов: delivery_id=%, занято=% из %', NEW.delivery_id, v_used, v_capacity;
    END IF;

    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_check_free_slots
BEFORE INSERT ON lab6_delivery_assignments
FOR EACH ROW EXECUTE FUNCTION trg_lab6_check_free_slots();

-- 1.2 Авто-отмена доставки при удалении всех привязок
CREATE OR REPLACE FUNCTION trg_lab6_cancel_delivery_if_empty()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM lab6_order_deliveries od WHERE od.delivery_id = OLD.delivery_id) THEN
        UPDATE lab6_deliveries SET status = 'Cancelled'
        WHERE delivery_id = OLD.delivery_id AND status <> 'Cancelled';
    END IF;
    RETURN OLD;
END; $$;

CREATE TRIGGER trg_lab6_cancel_delivery_if_empty
AFTER DELETE ON lab6_order_deliveries
FOR EACH ROW EXECUTE FUNCTION trg_lab6_cancel_delivery_if_empty();

-- 1.3 Минимальный интервал между выездами одной машины
CREATE OR REPLACE FUNCTION trg_lab6_check_min_delivery_interval()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM lab6_deliveries d
        WHERE d.vehicle_code = NEW.vehicle_code
          AND d.delivery_id <> COALESCE(NEW.delivery_id, -1)
          AND NEW.scheduled_departure < (d.scheduled_arrival + INTERVAL '30 minutes')
          AND NEW.scheduled_arrival > (d.scheduled_departure - INTERVAL '30 minutes')
    ) THEN
        RAISE EXCEPTION 'Интервал между доставками машины % меньше 30 минут', NEW.vehicle_code;
    END IF;
    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_check_min_delivery_interval
BEFORE INSERT OR UPDATE ON lab6_deliveries
FOR EACH ROW EXECUTE FUNCTION trg_lab6_check_min_delivery_interval();

-- 1.4 Пересчет total_amount заказа
CREATE OR REPLACE FUNCTION trg_lab6_recalc_order_total()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE v_order_ref TEXT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        SELECT oi.order_ref INTO v_order_ref FROM lab6_order_items oi WHERE oi.item_no = OLD.item_no;
    ELSE
        SELECT oi.order_ref INTO v_order_ref FROM lab6_order_items oi WHERE oi.item_no = NEW.item_no;
    END IF;

    IF v_order_ref IS NOT NULL THEN
        UPDATE lab6_orders o
        SET total_amount = COALESCE(x.total_amount, 0)
        FROM (
            SELECT oi.order_ref, SUM(od.line_amount)::NUMERIC(12,2) total_amount
            FROM lab6_order_items oi
            JOIN lab6_order_deliveries od ON od.item_no = oi.item_no
            WHERE oi.order_ref = v_order_ref
            GROUP BY oi.order_ref
        ) x
        WHERE o.order_ref = x.order_ref;

        UPDATE lab6_orders o
        SET total_amount = 0
        WHERE o.order_ref = v_order_ref
          AND NOT EXISTS (
              SELECT 1
              FROM lab6_order_items oi
              JOIN lab6_order_deliveries od ON od.item_no = oi.item_no
              WHERE oi.order_ref = o.order_ref
          );
    END IF;

    RETURN COALESCE(NEW, OLD);
END; $$;

CREATE TRIGGER trg_lab6_recalc_order_total
AFTER INSERT OR UPDATE OR DELETE ON lab6_order_deliveries
FOR EACH ROW EXECUTE FUNCTION trg_lab6_recalc_order_total();

-- 1.5 Запрет изменения старых заказов после фактической доставки
CREATE OR REPLACE FUNCTION trg_lab6_lock_old_orders()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF (OLD.total_amount IS DISTINCT FROM NEW.total_amount OR OLD.order_date IS DISTINCT FROM NEW.order_date)
       AND EXISTS (
           SELECT 1
           FROM lab6_order_items oi
           JOIN lab6_order_deliveries od ON od.item_no = oi.item_no
           JOIN lab6_deliveries d ON d.delivery_id = od.delivery_id
           WHERE oi.order_ref = OLD.order_ref
             AND d.actual_arrival IS NOT NULL
       ) THEN
        RAISE EXCEPTION 'Заказ % нельзя менять: доставка уже завершена', OLD.order_ref;
    END IF;
    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_lock_old_orders
BEFORE UPDATE ON lab6_orders
FOR EACH ROW EXECUTE FUNCTION trg_lab6_lock_old_orders();

-- 1.6 Проверка, что slot_no есть у машины
CREATE OR REPLACE FUNCTION trg_lab6_validate_slot_exists()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE v_vehicle TEXT;
BEGIN
    SELECT d.vehicle_code INTO v_vehicle FROM lab6_deliveries d WHERE d.delivery_id = NEW.delivery_id;
    IF NOT EXISTS (
        SELECT 1 FROM lab6_vehicle_slots s
        WHERE s.vehicle_code = v_vehicle AND s.slot_no = NEW.slot_no
    ) THEN
        RAISE EXCEPTION 'Слот % не существует у машины %', NEW.slot_no, v_vehicle;
    END IF;
    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_validate_slot_exists
BEFORE INSERT OR UPDATE ON lab6_delivery_assignments
FOR EACH ROW EXECUTE FUNCTION trg_lab6_validate_slot_exists();

-- 1.7 Запрет двойного назначения slot_no в одной доставке
CREATE OR REPLACE FUNCTION trg_lab6_prevent_double_slot_assignment()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM lab6_delivery_assignments a
        WHERE a.delivery_id = NEW.delivery_id
          AND a.slot_no = NEW.slot_no
          AND (a.item_no <> NEW.item_no OR TG_OP = 'INSERT')
    ) THEN
        RAISE EXCEPTION 'Слот % в доставке % уже занят', NEW.slot_no, NEW.delivery_id;
    END IF;
    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_prevent_double_slot_assignment
BEFORE INSERT OR UPDATE ON lab6_delivery_assignments
FOR EACH ROW EXECUTE FUNCTION trg_lab6_prevent_double_slot_assignment();

-- 1.8 Автогенерация assignment_no
CREATE OR REPLACE FUNCTION trg_lab6_set_assignment_no()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.assignment_no IS NULL OR NEW.assignment_no <= 0 THEN
        SELECT COALESCE(MAX(a.assignment_no), 0) + 1
        INTO NEW.assignment_no
        FROM lab6_delivery_assignments a
        WHERE a.delivery_id = NEW.delivery_id;
    END IF;
    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_set_assignment_no
BEFORE INSERT ON lab6_delivery_assignments
FOR EACH ROW EXECUTE FUNCTION trg_lab6_set_assignment_no();

-- 1.9 Валидация фактического времени доставки
CREATE OR REPLACE FUNCTION trg_lab6_validate_actual_times()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.actual_departure IS NOT NULL
       AND NEW.actual_arrival IS NOT NULL
       AND NEW.actual_departure > NEW.actual_arrival THEN
        RAISE EXCEPTION 'Фактическая отправка не может быть позже прибытия (delivery_id=%)', COALESCE(NEW.delivery_id, -1);
    END IF;
    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_validate_actual_times
BEFORE INSERT OR UPDATE ON lab6_deliveries
FOR EACH ROW EXECUTE FUNCTION trg_lab6_validate_actual_times();

-- 1.10 Авто-статус Delivered
CREATE OR REPLACE FUNCTION trg_lab6_mark_delivered()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.actual_arrival IS NOT NULL THEN
        NEW.status := 'Delivered';
    END IF;
    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_mark_delivered
BEFORE INSERT OR UPDATE ON lab6_deliveries
FOR EACH ROW EXECUTE FUNCTION trg_lab6_mark_delivered();

-- 1.11 Каскадное обновление route_no
CREATE OR REPLACE FUNCTION trg_lab6_cascade_route_no()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.route_no IS DISTINCT FROM NEW.route_no THEN
        UPDATE lab6_deliveries SET route_no = NEW.route_no WHERE route_no = OLD.route_no;
    END IF;
    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_cascade_route_no
AFTER UPDATE OF route_no ON lab6_routes
FOR EACH ROW EXECUTE FUNCTION trg_lab6_cascade_route_no();

-- 1.12 Аудит машин доставки
CREATE OR REPLACE FUNCTION trg_lab6_audit_vehicles()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.model IS DISTINCT FROM NEW.model
       OR OLD.slots_count IS DISTINCT FROM NEW.slots_count THEN
        INSERT INTO lab6_vehicles_audit(
            vehicle_code, old_model, new_model,
            old_slots_count, new_slots_count,
            changed_at, changed_by
        ) VALUES (
            NEW.vehicle_code, OLD.model, NEW.model,
            OLD.slots_count, NEW.slots_count,
            NOW(), CURRENT_USER
        );
    END IF;
    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_audit_vehicles
AFTER UPDATE ON lab6_vehicles
FOR EACH ROW EXECUTE FUNCTION trg_lab6_audit_vehicles();

-- 1.13 Скидка за повторные заказы за 30 дней
CREATE OR REPLACE FUNCTION trg_lab6_apply_loyalty_discount()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE v_recent INT;
BEGIN
    SELECT COUNT(*) INTO v_recent
    FROM lab6_order_items oi
    WHERE oi.product_name = NEW.product_name
      AND oi.item_no <> NEW.item_no
      AND oi.created_at >= (NEW.created_at - INTERVAL '30 days');

    IF v_recent > 0 THEN
        UPDATE lab6_order_items
        SET discount_pct = GREATEST(discount_pct, 10)
        WHERE item_no = NEW.item_no;
    END IF;
    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_apply_loyalty_discount
AFTER INSERT ON lab6_order_items
FOR EACH ROW EXECUTE FUNCTION trg_lab6_apply_loyalty_discount();

-- ЗАДАНИЕ 2
ALTER TABLE lab6_vehicle_slots
DROP CONSTRAINT IF EXISTS lab6_vehicle_slots_vehicle_code_fkey;

ALTER TABLE lab6_vehicle_slots
ADD CONSTRAINT lab6_vehicle_slots_vehicle_code_fkey
FOREIGN KEY (vehicle_code)
REFERENCES lab6_vehicles(vehicle_code)
ON DELETE CASCADE;

ALTER TABLE lab6_delivery_assignments
DROP CONSTRAINT IF EXISTS lab6_delivery_assignments_item_no_delivery_id_fkey;

ALTER TABLE lab6_delivery_assignments
ADD CONSTRAINT lab6_delivery_assignments_item_no_delivery_id_fkey
FOREIGN KEY (item_no, delivery_id)
REFERENCES lab6_order_deliveries(item_no, delivery_id)
ON DELETE CASCADE;

-- ЗАДАНИЕ 3
CREATE OR REPLACE FUNCTION trg_lab6_log_delivery_changes()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO lab6_row_change_log(table_name, attribute_name, old_value, new_value, changed_at)
        VALUES ('lab6_deliveries', 'status', OLD.status, NEW.status, NOW());
    END IF;

    IF OLD.actual_departure IS DISTINCT FROM NEW.actual_departure THEN
        INSERT INTO lab6_row_change_log(table_name, attribute_name, old_value, new_value, changed_at)
        VALUES ('lab6_deliveries', 'actual_departure', OLD.actual_departure::TEXT, NEW.actual_departure::TEXT, NOW());
    END IF;

    IF OLD.actual_arrival IS DISTINCT FROM NEW.actual_arrival THEN
        INSERT INTO lab6_row_change_log(table_name, attribute_name, old_value, new_value, changed_at)
        VALUES ('lab6_deliveries', 'actual_arrival', OLD.actual_arrival::TEXT, NEW.actual_arrival::TEXT, NOW());
    END IF;

    RETURN NEW;
END; $$;

CREATE TRIGGER trg_lab6_log_delivery_changes
AFTER UPDATE ON lab6_deliveries
FOR EACH ROW EXECUTE FUNCTION trg_lab6_log_delivery_changes();
