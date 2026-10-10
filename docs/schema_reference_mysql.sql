-- ============================================================================
-- Smart Inventory Market
-- MySQL 8.x schema reference
-- CHECKPOINT-013 foundation plus later revisions through a91c2e6f4b20
-- ============================================================================
--
-- PURPOSE
-- -------
-- This file is a HUMAN-READABLE SQL REFERENCE so the student can quickly see
-- what each table contains and how the tables relate.
--
-- SOURCE OF TRUTH
-- ---------------
-- The real schema source of truth is:
--   1) backend/app/db/models/application.py
--   2) Alembic revisions through a91c2e6f4b20_add_auth_sessions.py
--
-- Do NOT manually edit the production/development schema with this file when
-- a schema change is needed. Change the SQLAlchemy models and create a new
-- Alembic migration instead.
--
-- MySQL may automatically create additional indexes required by foreign keys.
-- That is normal.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS smart_inventory_market
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE smart_inventory_market;

-- ============================================================================
-- 1. categories
-- Product categories such as FOOD, DRINK, etc.
-- ============================================================================

CREATE TABLE categories (
    id BIGINT NOT NULL AUTO_INCREMENT,
    code VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    CONSTRAINT pk_categories PRIMARY KEY (id),
    CONSTRAINT uq_categories_code UNIQUE (code)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================================
-- 2. forecast_runs
-- Metadata for one forecasting run.
-- The XGBoost model file itself is NOT stored in MySQL.
-- ============================================================================

CREATE TABLE forecast_runs (
    id BIGINT NOT NULL AUTO_INCREMENT,
    model_name VARCHAR(100) NOT NULL,
    feature_set VARCHAR(100) NOT NULL,
    model_version VARCHAR(100) NULL,
    history_end_date DATE NOT NULL,
    forecast_start_date DATE NOT NULL,
    horizon_days INT NOT NULL,
    generated_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,

    CONSTRAINT pk_forecast_runs PRIMARY KEY (id),
    CONSTRAINT ck_forecast_runs_horizon_positive
        CHECK (horizon_days > 0)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================================
-- 3. model_metrics
-- Stores compact model evaluation metrics such as MAE/RMSE/WAPE.
-- ============================================================================

CREATE TABLE model_metrics (
    id BIGINT NOT NULL AUTO_INCREMENT,
    model_name VARCHAR(100) NOT NULL,
    feature_set VARCHAR(100) NOT NULL,
    dataset_split VARCHAR(64) NOT NULL,
    mae DECIMAL(14,6) NULL,
    rmse DECIMAL(14,6) NULL,
    wape DECIMAL(14,6) NULL,
    evaluated_at DATETIME NOT NULL,
    notes TEXT NULL,

    CONSTRAINT pk_model_metrics PRIMARY KEY (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================================
-- 4. suppliers
-- Supplier master data.
-- ============================================================================

CREATE TABLE suppliers (
    id BIGINT NOT NULL AUTO_INCREMENT,
    code VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NULL,
    phone VARCHAR(64) NULL,
    address TEXT NULL,
    is_active BOOLEAN NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    CONSTRAINT pk_suppliers PRIMARY KEY (id),
    CONSTRAINT uq_suppliers_code UNIQUE (code)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================================
-- 5. users
-- Future application accounts.
-- Passwords are stored only as hashes.
-- ============================================================================

CREATE TABLE users (
    id BIGINT NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(15) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    CONSTRAINT pk_users PRIMARY KEY (id),
    CONSTRAINT user_role
        CHECK (role IN ('ADMIN', 'MANAGER', 'INVENTORY_STAFF'))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE UNIQUE INDEX ix_users_email
    ON users (email);


-- ============================================================================
-- auth_sessions
-- Opaque, revocable browser-session records; raw cookie tokens are not stored.
-- ============================================================================

CREATE TABLE auth_sessions (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME NULL,
    created_at DATETIME NOT NULL,

    CONSTRAINT pk_auth_sessions PRIMARY KEY (id),
    CONSTRAINT fk_auth_sessions_user_id_users
        FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE UNIQUE INDEX ix_auth_sessions_token_hash
    ON auth_sessions (token_hash);
CREATE INDEX ix_auth_sessions_user_id
    ON auth_sessions (user_id);
CREATE INDEX ix_auth_sessions_expires_at
    ON auth_sessions (expires_at);


-- ============================================================================
-- 6. products
-- Sellable products in the single-store MVP.
-- ============================================================================

CREATE TABLE products (
    id BIGINT NOT NULL AUTO_INCREMENT,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    category_id BIGINT NOT NULL,
    unit VARCHAR(32) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    CONSTRAINT pk_products PRIMARY KEY (id),

    CONSTRAINT fk_products_category_id_categories
        FOREIGN KEY (category_id)
        REFERENCES categories (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE INDEX ix_products_category_id
    ON products (category_id);

CREATE UNIQUE INDEX ix_products_sku
    ON products (sku);


-- ============================================================================
-- 7. purchase_orders
-- Purchase-order header and lifecycle state.
-- Creating a PO does NOT increase on-hand inventory.
-- ============================================================================

CREATE TABLE purchase_orders (
    id BIGINT NOT NULL AUTO_INCREMENT,
    po_number VARCHAR(64) NOT NULL,
    supplier_id BIGINT NOT NULL,
    status VARCHAR(10) NOT NULL,
    order_date DATE NULL,
    expected_arrival_date DATE NULL,
    received_at DATETIME NULL,
    created_by_user_id BIGINT NULL,
    approved_by_user_id BIGINT NULL,
    notes TEXT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    CONSTRAINT pk_purchase_orders PRIMARY KEY (id),

    CONSTRAINT purchase_order_status
        CHECK (
            status IN (
                'DRAFT',
                'APPROVED',
                'ORDERED',
                'IN_TRANSIT',
                'RECEIVED',
                'CANCELLED'
            )
        ),

    CONSTRAINT fk_purchase_orders_supplier_id_suppliers
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers (id),

    CONSTRAINT fk_purchase_orders_created_by_user_id_users
        FOREIGN KEY (created_by_user_id)
        REFERENCES users (id),

    CONSTRAINT fk_purchase_orders_approved_by_user_id_users
        FOREIGN KEY (approved_by_user_id)
        REFERENCES users (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE UNIQUE INDEX ix_purchase_orders_po_number
    ON purchase_orders (po_number);

CREATE INDEX ix_purchase_orders_status
    ON purchase_orders (status);


-- ============================================================================
-- 8. forecast_values
-- One predicted demand value for one product/date in one forecast run.
-- Forecast values stay decimal; they are not rounded just for storage.
-- ============================================================================

CREATE TABLE forecast_values (
    id BIGINT NOT NULL AUTO_INCREMENT,
    forecast_run_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    forecast_date DATE NOT NULL,
    horizon_day INT NOT NULL,
    predicted_demand DECIMAL(14,4) NOT NULL,
    created_at DATETIME NOT NULL,

    CONSTRAINT pk_forecast_values PRIMARY KEY (id),

    CONSTRAINT forecast_run_product_date
        UNIQUE (forecast_run_id, product_id, forecast_date),

    CONSTRAINT ck_forecast_values_horizon_day_positive
        CHECK (horizon_day > 0),

    CONSTRAINT ck_forecast_values_predicted_demand_nonnegative
        CHECK (predicted_demand >= 0),

    CONSTRAINT fk_forecast_values_forecast_run_id_forecast_runs
        FOREIGN KEY (forecast_run_id)
        REFERENCES forecast_runs (id),

    CONSTRAINT fk_forecast_values_product_id_products
        FOREIGN KEY (product_id)
        REFERENCES products (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE INDEX ix_forecast_values_forecast_run_id
    ON forecast_values (forecast_run_id);

CREATE INDEX ix_forecast_values_product_date
    ON forecast_values (product_id, forecast_date);


-- ============================================================================
-- 9. inventory
-- Current on-hand quantity.
-- There is intentionally NO freely editable on_order column.
-- Incoming stock is derived from eligible open purchase-order lines.
-- ============================================================================

CREATE TABLE inventory (
    product_id BIGINT NOT NULL,
    on_hand INT NOT NULL,
    updated_at DATETIME NOT NULL,

    CONSTRAINT pk_inventory PRIMARY KEY (product_id),

    CONSTRAINT ck_inventory_on_hand_nonnegative
        CHECK (on_hand >= 0),

    CONSTRAINT fk_inventory_product_id_products
        FOREIGN KEY (product_id)
        REFERENCES products (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================================
-- 10. purchase_order_items
-- Product lines inside purchase orders.
-- received_quantity may never exceed ordered_quantity.
-- ============================================================================

CREATE TABLE purchase_order_items (
    id BIGINT NOT NULL AUTO_INCREMENT,
    purchase_order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    ordered_quantity INT NOT NULL,
    received_quantity INT NOT NULL,
    unit_cost DECIMAL(12,2) NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    CONSTRAINT pk_purchase_order_items PRIMARY KEY (id),

    CONSTRAINT purchase_order_product
        UNIQUE (purchase_order_id, product_id),

    CONSTRAINT ck_purchase_order_items_ordered_quantity_positive
        CHECK (ordered_quantity > 0),

    CONSTRAINT ck_purchase_order_items_received_quantity_nonnegative
        CHECK (received_quantity >= 0),

    CONSTRAINT ck_purchase_order_items_received_not_over_ordered
        CHECK (received_quantity <= ordered_quantity),

    CONSTRAINT ck_purchase_order_items_unit_cost_nonnegative
        CHECK (unit_cost IS NULL OR unit_cost >= 0),

    CONSTRAINT fk_purchase_order_items_purchase_order_id_purchase_orders
        FOREIGN KEY (purchase_order_id)
        REFERENCES purchase_orders (id),

    CONSTRAINT fk_purchase_order_items_product_id_products
        FOREIGN KEY (product_id)
        REFERENCES products (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================================
-- 11. reorder_recommendations
-- Inventory decision-support snapshot for manager review.
-- ACCEPTED/MODIFIED does NOT directly increase inventory.
-- ============================================================================

CREATE TABLE reorder_recommendations (
    id BIGINT NOT NULL AUTO_INCREMENT,
    product_id BIGINT NOT NULL,
    forecast_run_id BIGINT NULL,
    status VARCHAR(8) NOT NULL,
    current_on_hand INT NOT NULL,
    incoming_quantity INT NOT NULL,
    lead_time_days INT NOT NULL,
    safety_stock INT NOT NULL,
    reorder_point INT NOT NULL,
    recommended_quantity INT NOT NULL,
    approved_quantity INT NULL,
    created_at DATETIME NOT NULL,
    expires_at DATETIME NULL,
    reviewed_at DATETIME NULL,
    reviewed_by_user_id BIGINT NULL,
    notes TEXT NULL,

    CONSTRAINT pk_reorder_recommendations PRIMARY KEY (id),

    CONSTRAINT recommendation_status
        CHECK (
            status IN (
                'NEW',
                'ACCEPTED',
                'MODIFIED',
                'REJECTED',
                'EXPIRED'
            )
        ),

    CONSTRAINT ck_reorder_recommendations_current_on_hand_nonnegative
        CHECK (current_on_hand >= 0),

    CONSTRAINT ck_reorder_recommendations_incoming_quantity_nonnegative
        CHECK (incoming_quantity >= 0),

    CONSTRAINT ck_reorder_recommendations_lead_time_positive
        CHECK (lead_time_days > 0),

    CONSTRAINT ck_reorder_recommendations_safety_stock_nonnegative
        CHECK (safety_stock >= 0),

    CONSTRAINT ck_reorder_recommendations_reorder_point_nonnegative
        CHECK (reorder_point >= 0),

    CONSTRAINT ck_reorder_recommendations_recommended_quantity_nonnegative
        CHECK (recommended_quantity >= 0),

    CONSTRAINT ck_reorder_recommendations_approved_quantity_nonnegative
        CHECK (approved_quantity IS NULL OR approved_quantity >= 0),

    CONSTRAINT fk_reorder_recommendations_product_id_products
        FOREIGN KEY (product_id)
        REFERENCES products (id),

    CONSTRAINT fk_reorder_recommendations_forecast_run_id_forecast_runs
        FOREIGN KEY (forecast_run_id)
        REFERENCES forecast_runs (id),

    CONSTRAINT fk_reorder_recommendations_reviewed_by_user_id_users
        FOREIGN KEY (reviewed_by_user_id)
        REFERENCES users (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE INDEX ix_reorder_recommendations_product_created
    ON reorder_recommendations (product_id, created_at);

CREATE INDEX ix_reorder_recommendations_status
    ON reorder_recommendations (status);


-- ============================================================================
-- 12. sales_daily
-- Normalized daily sales history.
-- One row = one product + one date + quantity sold.
-- ============================================================================

CREATE TABLE sales_daily (
    id BIGINT NOT NULL AUTO_INCREMENT,
    product_id BIGINT NOT NULL,
    sale_date DATE NOT NULL,
    quantity_sold INT NOT NULL,
      -- Retail daily selling price for frozen forecasting features; not supplier unit cost.
      sell_price DECIMAL(12,2) NULL,
    source VARCHAR(100) NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    CONSTRAINT pk_sales_daily PRIMARY KEY (id),

    CONSTRAINT product_sale_date
        UNIQUE (product_id, sale_date),

    CONSTRAINT ck_sales_daily_quantity_sold_nonnegative
        CHECK (quantity_sold >= 0),

      CONSTRAINT ck_sales_daily_sell_price_nonnegative
          CHECK (sell_price IS NULL OR sell_price >= 0),

    CONSTRAINT fk_sales_daily_product_id_products
        FOREIGN KEY (product_id)
        REFERENCES products (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================================
-- 13. supplier_products
-- Many-to-many supplier/product relationship with supplier-specific details.
-- ============================================================================

CREATE TABLE supplier_products (
    id BIGINT NOT NULL AUTO_INCREMENT,
    supplier_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    supplier_sku VARCHAR(100) NULL,
    unit_cost DECIMAL(12,2) NULL,
    lead_time_days INT NOT NULL,
    is_preferred BOOLEAN NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    CONSTRAINT pk_supplier_products PRIMARY KEY (id),

    CONSTRAINT supplier_product_pair
        UNIQUE (supplier_id, product_id),

    CONSTRAINT ck_supplier_products_lead_time_positive
        CHECK (lead_time_days > 0),

    CONSTRAINT ck_supplier_products_unit_cost_nonnegative
        CHECK (unit_cost IS NULL OR unit_cost >= 0),

    CONSTRAINT fk_supplier_products_supplier_id_suppliers
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers (id),

    CONSTRAINT fk_supplier_products_product_id_products
        FOREIGN KEY (product_id)
        REFERENCES products (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================================
-- 14. stock_transactions
-- Audit trail for stock movement.
-- Historical transactions should be treated as immutable by application logic.
-- ============================================================================

CREATE TABLE stock_transactions (
    id BIGINT NOT NULL AUTO_INCREMENT,
    product_id BIGINT NOT NULL,
    transaction_type VARCHAR(14) NOT NULL,
    quantity INT NOT NULL,
    occurred_at DATETIME NOT NULL,
    purchase_order_item_id BIGINT NULL,
    sales_daily_id BIGINT NULL,
    created_by_user_id BIGINT NULL,
    reason TEXT NULL,
    created_at DATETIME NOT NULL,

    CONSTRAINT pk_stock_transactions PRIMARY KEY (id),

    CONSTRAINT stock_transaction_type
        CHECK (
            transaction_type IN (
                'RECEIPT',
                'SALE',
                'ADJUSTMENT_IN',
                'ADJUSTMENT_OUT'
            )
        ),

    CONSTRAINT ck_stock_transactions_quantity_positive
        CHECK (quantity > 0),

    CONSTRAINT fk_stock_transactions_product_id_products
        FOREIGN KEY (product_id)
        REFERENCES products (id),

    CONSTRAINT fk_stock_transactions_purchase_order_item_id_purchase_order_items
        FOREIGN KEY (purchase_order_item_id)
        REFERENCES purchase_order_items (id),

    CONSTRAINT fk_stock_transactions_sales_daily_id_sales_daily
        FOREIGN KEY (sales_daily_id)
        REFERENCES sales_daily (id),

    CONSTRAINT fk_stock_transactions_created_by_user_id_users
        FOREIGN KEY (created_by_user_id)
        REFERENCES users (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE INDEX ix_stock_transactions_product_occurred
    ON stock_transactions (product_id, occurred_at);


-- ============================================================================
-- ALEMBIC INTERNAL TABLE
-- ============================================================================
--
-- Alembic also maintains its own table named:
--
--     alembic_version
--
-- It stores the current migration revision (currently f86d36b27719).
-- It is not an application business table, so it is intentionally not
-- recreated manually in this reference file.
--
-- ============================================================================
-- Useful inspection commands
-- ============================================================================

SHOW TABLES;

-- Example:
-- DESCRIBE products;
-- SHOW CREATE TABLE products;
-- SHOW INDEX FROM products;

-- Current migration should be checked with:
--     alembic current
--
-- Do not use this reference file instead of Alembic for future schema changes.
