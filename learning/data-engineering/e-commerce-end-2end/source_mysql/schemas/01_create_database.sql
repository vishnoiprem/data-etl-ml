-- ============================================================
-- E-Commerce Platform: MySQL Source Database Schema
-- Modeled after Shopee/Lazada style marketplace
-- ============================================================

CREATE DATABASE IF NOT EXISTS ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ecommerce_db;

-- Enable binlog for CDC (set in my.cnf)
-- log_bin = ON
-- binlog_format = ROW
-- binlog_row_image = FULL

-- ============================================================
-- USERS & AUTHENTICATION
-- ============================================================
CREATE TABLE users (
    user_id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(100) NOT NULL UNIQUE,
    email          VARCHAR(255) NOT NULL UNIQUE,
    phone          VARCHAR(20),
    password_hash  VARCHAR(255) NOT NULL,
    full_name      VARCHAR(200),
    gender         ENUM('M','F','Other') DEFAULT 'Other',
    date_of_birth  DATE,
    avatar_url     VARCHAR(500),
    user_type      ENUM('buyer','seller','both') DEFAULT 'buyer',
    status         ENUM('active','inactive','banned') DEFAULT 'active',
    is_verified    TINYINT(1) DEFAULT 0,
    country_code   CHAR(2) DEFAULT 'TH',
    language_pref  VARCHAR(10) DEFAULT 'en',
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at  DATETIME,
    INDEX idx_email (email),
    INDEX idx_user_type (user_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- ============================================================
-- ADDRESSES
-- ============================================================
CREATE TABLE user_addresses (
    address_id     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id        BIGINT UNSIGNED NOT NULL,
    label          VARCHAR(50) DEFAULT 'Home',
    recipient_name VARCHAR(200),
    phone          VARCHAR(20),
    address_line1  VARCHAR(300) NOT NULL,
    address_line2  VARCHAR(300),
    city           VARCHAR(100),
    state          VARCHAR(100),
    postal_code    VARCHAR(20),
    country_code   CHAR(2) DEFAULT 'TH',
    is_default     TINYINT(1) DEFAULT 0,
    latitude       DECIMAL(10,8),
    longitude      DECIMAL(11,8),
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB;

-- ============================================================
-- SELLERS / SHOPS
-- ============================================================
CREATE TABLE sellers (
    seller_id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL,
    shop_name       VARCHAR(200) NOT NULL,
    shop_slug       VARCHAR(200) NOT NULL UNIQUE,
    description     TEXT,
    logo_url        VARCHAR(500),
    banner_url      VARCHAR(500),
    seller_type     ENUM('individual','enterprise') DEFAULT 'individual',
    status          ENUM('active','suspended','pending') DEFAULT 'pending',
    rating          DECIMAL(3,2) DEFAULT 0.00,
    total_reviews   INT UNSIGNED DEFAULT 0,
    total_sales     BIGINT UNSIGNED DEFAULT 0,
    response_rate   DECIMAL(5,2) DEFAULT 0.00,
    response_time   INT DEFAULT 0 COMMENT 'avg response time in minutes',
    joined_date     DATE,
    warehouse_city  VARCHAR(100),
    country_code    CHAR(2) DEFAULT 'TH',
    commission_rate DECIMAL(5,2) DEFAULT 5.00,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_rating (rating)
) ENGINE=InnoDB;

-- ============================================================
-- CATEGORIES
-- ============================================================
CREATE TABLE categories (
    category_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    parent_id     INT UNSIGNED DEFAULT NULL,
    name          VARCHAR(200) NOT NULL,
    slug          VARCHAR(200) NOT NULL UNIQUE,
    description   TEXT,
    icon_url      VARCHAR(500),
    image_url     VARCHAR(500),
    level         TINYINT UNSIGNED DEFAULT 1,
    sort_order    INT DEFAULT 0,
    is_active     TINYINT(1) DEFAULT 1,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id),
    INDEX idx_parent_id (parent_id),
    INDEX idx_level (level)
) ENGINE=InnoDB;

-- ============================================================
-- BRANDS
-- ============================================================
CREATE TABLE brands (
    brand_id    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(200) NOT NULL UNIQUE,
    slug        VARCHAR(200) NOT NULL UNIQUE,
    logo_url    VARCHAR(500),
    country     CHAR(2),
    is_active   TINYINT(1) DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- PRODUCTS (SPU - Standard Product Unit)
-- ============================================================
CREATE TABLE products (
    product_id     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    seller_id      BIGINT UNSIGNED NOT NULL,
    category_id    INT UNSIGNED NOT NULL,
    brand_id       INT UNSIGNED,
    name           VARCHAR(500) NOT NULL,
    slug           VARCHAR(500),
    description    TEXT,
    status         ENUM('active','inactive','draft','deleted') DEFAULT 'draft',
    condition_type ENUM('new','used','refurbished') DEFAULT 'new',
    min_price      DECIMAL(15,2) DEFAULT 0.00,
    max_price      DECIMAL(15,2) DEFAULT 0.00,
    total_sold     BIGINT UNSIGNED DEFAULT 0,
    total_views    BIGINT UNSIGNED DEFAULT 0,
    rating         DECIMAL(3,2) DEFAULT 0.00,
    review_count   INT UNSIGNED DEFAULT 0,
    is_featured    TINYINT(1) DEFAULT 0,
    tags           JSON,
    seo_title      VARCHAR(300),
    seo_description VARCHAR(500),
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (brand_id) REFERENCES brands(brand_id),
    INDEX idx_seller_id (seller_id),
    INDEX idx_category_id (category_id),
    INDEX idx_status (status),
    INDEX idx_rating (rating),
    FULLTEXT INDEX ft_name (name)
) ENGINE=InnoDB;

-- ============================================================
-- PRODUCT SKUS (SKU - Stock Keeping Unit)
-- ============================================================
CREATE TABLE product_skus (
    sku_id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    product_id      BIGINT UNSIGNED NOT NULL,
    sku_code        VARCHAR(100) NOT NULL UNIQUE,
    variant_name    VARCHAR(300),
    attributes      JSON COMMENT '{"color":"Red","size":"XL"}',
    price           DECIMAL(15,2) NOT NULL,
    original_price  DECIMAL(15,2),
    cost_price      DECIMAL(15,2),
    stock_quantity  INT DEFAULT 0,
    reserved_qty    INT DEFAULT 0,
    weight_kg       DECIMAL(8,3) DEFAULT 0.000,
    length_cm       DECIMAL(8,2),
    width_cm        DECIMAL(8,2),
    height_cm       DECIMAL(8,2),
    image_url       VARCHAR(500),
    barcode         VARCHAR(100),
    status          ENUM('active','inactive','out_of_stock') DEFAULT 'active',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_product_id (product_id),
    INDEX idx_sku_code (sku_code),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- ============================================================
-- WAREHOUSES
-- ============================================================
CREATE TABLE warehouses (
    warehouse_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(200) NOT NULL,
    code           VARCHAR(50) NOT NULL UNIQUE,
    type           ENUM('fulfillment','seller','returns') DEFAULT 'fulfillment',
    address        VARCHAR(500),
    city           VARCHAR(100),
    state          VARCHAR(100),
    country_code   CHAR(2) DEFAULT 'TH',
    latitude       DECIMAL(10,8),
    longitude      DECIMAL(11,8),
    capacity_sqm   DECIMAL(10,2),
    is_active      TINYINT(1) DEFAULT 1,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- INVENTORY
-- ============================================================
CREATE TABLE inventory (
    inventory_id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sku_id         BIGINT UNSIGNED NOT NULL,
    warehouse_id   INT UNSIGNED NOT NULL,
    quantity       INT DEFAULT 0,
    reserved_qty   INT DEFAULT 0,
    reorder_point  INT DEFAULT 10,
    reorder_qty    INT DEFAULT 100,
    last_restock   DATETIME,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (sku_id) REFERENCES product_skus(sku_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
    UNIQUE KEY uk_sku_warehouse (sku_id, warehouse_id),
    INDEX idx_sku_id (sku_id),
    INDEX idx_warehouse_id (warehouse_id)
) ENGINE=InnoDB;

-- ============================================================
-- ORDERS
-- ============================================================
CREATE TABLE orders (
    order_id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_no          VARCHAR(50) NOT NULL UNIQUE,
    user_id           BIGINT UNSIGNED NOT NULL,
    seller_id         BIGINT UNSIGNED NOT NULL,
    status            ENUM('pending','confirmed','processing','shipped','delivered','cancelled','returned','refunded') DEFAULT 'pending',
    payment_status    ENUM('pending','paid','failed','refunded') DEFAULT 'pending',
    payment_method    ENUM('credit_card','debit_card','bank_transfer','wallet','cod','installment') DEFAULT 'cod',
    subtotal          DECIMAL(15,2) DEFAULT 0.00,
    shipping_fee      DECIMAL(10,2) DEFAULT 0.00,
    platform_fee      DECIMAL(10,2) DEFAULT 0.00,
    discount_amount   DECIMAL(10,2) DEFAULT 0.00,
    voucher_discount  DECIMAL(10,2) DEFAULT 0.00,
    total_amount      DECIMAL(15,2) DEFAULT 0.00,
    currency          CHAR(3) DEFAULT 'THB',
    shipping_address  JSON,
    notes             TEXT,
    cancel_reason     VARCHAR(300),
    confirmed_at      DATETIME,
    shipped_at        DATETIME,
    delivered_at      DATETIME,
    cancelled_at      DATETIME,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id),
    INDEX idx_user_id (user_id),
    INDEX idx_seller_id (seller_id),
    INDEX idx_status (status),
    INDEX idx_payment_status (payment_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- ============================================================
-- ORDER ITEMS
-- ============================================================
CREATE TABLE order_items (
    item_id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id       BIGINT UNSIGNED NOT NULL,
    product_id     BIGINT UNSIGNED NOT NULL,
    sku_id         BIGINT UNSIGNED NOT NULL,
    quantity       INT UNSIGNED NOT NULL,
    unit_price     DECIMAL(15,2) NOT NULL,
    original_price DECIMAL(15,2),
    discount       DECIMAL(10,2) DEFAULT 0.00,
    subtotal       DECIMAL(15,2) NOT NULL,
    warehouse_id   INT UNSIGNED,
    status         ENUM('pending','confirmed','shipped','delivered','cancelled','returned') DEFAULT 'pending',
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (sku_id) REFERENCES product_skus(sku_id),
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id),
    INDEX idx_sku_id (sku_id)
) ENGINE=InnoDB;

-- ============================================================
-- PAYMENTS
-- ============================================================
CREATE TABLE payments (
    payment_id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id         BIGINT UNSIGNED NOT NULL,
    payment_ref      VARCHAR(100) UNIQUE,
    payment_method   VARCHAR(50),
    gateway          VARCHAR(50) COMMENT 'omise, scb, kbank, etc',
    amount           DECIMAL(15,2) NOT NULL,
    currency         CHAR(3) DEFAULT 'THB',
    status           ENUM('pending','success','failed','cancelled','refunded') DEFAULT 'pending',
    gateway_txn_id   VARCHAR(200),
    gateway_response JSON,
    paid_at          DATETIME,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    INDEX idx_order_id (order_id),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- ============================================================
-- SHIPMENTS
-- ============================================================
CREATE TABLE shipments (
    shipment_id      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id         BIGINT UNSIGNED NOT NULL,
    tracking_no      VARCHAR(100),
    carrier          VARCHAR(100) COMMENT 'Kerry, Flash, J&T, SCG, etc',
    carrier_code     VARCHAR(20),
    status           ENUM('pending','picked_up','in_transit','out_for_delivery','delivered','failed','returned') DEFAULT 'pending',
    weight_kg        DECIMAL(8,3),
    shipping_fee     DECIMAL(10,2),
    estimated_date   DATE,
    actual_date      DATE,
    from_address     JSON,
    to_address       JSON,
    shipped_at       DATETIME,
    delivered_at     DATETIME,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    INDEX idx_order_id (order_id),
    INDEX idx_tracking_no (tracking_no),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- ============================================================
-- REVIEWS
-- ============================================================
CREATE TABLE reviews (
    review_id      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id       BIGINT UNSIGNED NOT NULL,
    product_id     BIGINT UNSIGNED NOT NULL,
    user_id        BIGINT UNSIGNED NOT NULL,
    rating         TINYINT UNSIGNED NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title          VARCHAR(200),
    content        TEXT,
    images         JSON,
    helpful_count  INT UNSIGNED DEFAULT 0,
    status         ENUM('published','hidden','pending') DEFAULT 'pending',
    seller_reply   TEXT,
    replied_at     DATETIME,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_product_id (product_id),
    INDEX idx_user_id (user_id),
    INDEX idx_rating (rating)
) ENGINE=InnoDB;

-- ============================================================
-- VOUCHERS / PROMOTIONS
-- ============================================================
CREATE TABLE vouchers (
    voucher_id     INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code           VARCHAR(50) NOT NULL UNIQUE,
    name           VARCHAR(200),
    type           ENUM('percentage','fixed','free_shipping') DEFAULT 'percentage',
    value          DECIMAL(10,2) NOT NULL,
    min_order      DECIMAL(10,2) DEFAULT 0.00,
    max_discount   DECIMAL(10,2),
    usage_limit    INT DEFAULT 0 COMMENT '0 = unlimited',
    used_count     INT DEFAULT 0,
    per_user_limit INT DEFAULT 1,
    scope          ENUM('platform','seller','product') DEFAULT 'platform',
    seller_id      BIGINT UNSIGNED,
    start_date     DATETIME,
    end_date       DATETIME,
    is_active      TINYINT(1) DEFAULT 1,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_code (code),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB;

-- ============================================================
-- USER BEHAVIOR (CLICKSTREAM)
-- ============================================================
CREATE TABLE user_events (
    event_id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id        BIGINT UNSIGNED,
    session_id     VARCHAR(100),
    event_type     ENUM('view','click','add_to_cart','remove_cart','search','purchase','wishlist','share') NOT NULL,
    entity_type    ENUM('product','category','seller','search','page') DEFAULT 'product',
    entity_id      BIGINT UNSIGNED,
    search_query   VARCHAR(500),
    page_url       VARCHAR(1000),
    referrer       VARCHAR(500),
    device_type    ENUM('mobile','desktop','tablet') DEFAULT 'mobile',
    platform       ENUM('ios','android','web') DEFAULT 'web',
    ip_address     VARCHAR(45),
    user_agent     VARCHAR(500),
    extra_data     JSON,
    created_at     DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_event_type (event_type),
    INDEX idx_entity_id (entity_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- ============================================================
-- CART
-- ============================================================
CREATE TABLE cart_items (
    cart_item_id  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id       BIGINT UNSIGNED NOT NULL,
    sku_id        BIGINT UNSIGNED NOT NULL,
    product_id    BIGINT UNSIGNED NOT NULL,
    quantity      INT UNSIGNED DEFAULT 1,
    added_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE KEY uk_user_sku (user_id, sku_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB;

-- ============================================================
-- FLASH SALES
-- ============================================================
CREATE TABLE flash_sales (
    flash_sale_id  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(200) NOT NULL,
    start_time     DATETIME NOT NULL,
    end_time       DATETIME NOT NULL,
    status         ENUM('upcoming','active','ended') DEFAULT 'upcoming',
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE flash_sale_items (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    flash_sale_id   INT UNSIGNED NOT NULL,
    sku_id          BIGINT UNSIGNED NOT NULL,
    sale_price      DECIMAL(15,2) NOT NULL,
    quota           INT UNSIGNED NOT NULL,
    sold_count      INT UNSIGNED DEFAULT 0,
    FOREIGN KEY (flash_sale_id) REFERENCES flash_sales(flash_sale_id),
    FOREIGN KEY (sku_id) REFERENCES product_skus(sku_id)
) ENGINE=InnoDB;
