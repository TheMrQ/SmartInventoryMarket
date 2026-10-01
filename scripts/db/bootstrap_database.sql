-- Smart Inventory Market - Local MySQL bootstrap
-- Purpose: create the local development database and grant access to the app user.
-- IMPORTANT: do not put real passwords in this tracked file.
-- Run these commands in MySQL Workbench while connected with an administrative account.

CREATE DATABASE IF NOT EXISTS smart_inventory_market
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;

-- Create the application user only if it does not already exist.
-- Replace CHANGE_ME with a strong local password when running manually.
-- If the user already exists, skip CREATE USER and use ALTER USER only if needed.
CREATE USER IF NOT EXISTS 'smart_inventory_app'@'localhost'
IDENTIFIED BY 'CHANGE_ME';

GRANT ALL PRIVILEGES
ON smart_inventory_market.*
TO 'smart_inventory_app'@'localhost';

FLUSH PRIVILEGES;

-- Verification
SHOW DATABASES;
SHOW GRANTS FOR 'smart_inventory_app'@'localhost';

USE smart_inventory_market;
SHOW TABLES;

-- Expected before Alembic P13 migration:
-- smart_inventory_market exists and SHOW TABLES may be empty.
-- Do NOT create application tables manually in Workbench.
-- SQLAlchemy models + Alembic migrations will create/manage them.
