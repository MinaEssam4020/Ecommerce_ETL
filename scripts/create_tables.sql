USE ecommerce_dw;
GO

-- ── Dimension: Geography ─────────────────────────────────────
CREATE TABLE dim_geography (
    geography_key   INT IDENTITY(1,1) PRIMARY KEY,
    country         NVARCHAR(100)  NOT NULL,
    region          NVARCHAR(100),
    subregion       NVARCHAR(100),
    currency        NVARCHAR(10),
    CONSTRAINT uq_country UNIQUE (country)
);

-- ── Dimension: Product ───────────────────────────────────────
CREATE TABLE dim_product (
    product_key      INT IDENTITY(1,1) PRIMARY KEY,
    product_name     NVARCHAR(200)  NOT NULL,
    product_category NVARCHAR(100)  NOT NULL,
    CONSTRAINT uq_product UNIQUE (product_name)
);

-- ── Dimension: Customer ──────────────────────────────────────
CREATE TABLE dim_customer (
    customer_key    INT IDENTITY(1,1) PRIMARY KEY,
    customer_id     NVARCHAR(100)  NOT NULL,
    customer_name   NVARCHAR(200),
    email           NVARCHAR(200),
    country         NVARCHAR(100),
    currency        NVARCHAR(10),
    CONSTRAINT uq_customer UNIQUE (customer_id)
);

-- ── Dimension: Date ──────────────────────────────────────────
CREATE TABLE dim_date (
    date_key        INT PRIMARY KEY,   -- format: YYYYMMDD e.g. 20260419
    full_date       DATE NOT NULL,
    year            INT,
    quarter         INT,
    month           INT,
    month_name      NVARCHAR(20),
    week_number     INT,
    day_of_week     INT,
    day_name        NVARCHAR(20),
    is_weekend      BIT
);

-- ── Fact: Orders ─────────────────────────────────────────────
CREATE TABLE fact_orders (
    order_key             INT IDENTITY(1,1) PRIMARY KEY,
    order_id              NVARCHAR(100)  NOT NULL,
    customer_key          INT  REFERENCES dim_customer(customer_key),
    product_key           INT  REFERENCES dim_product(product_key),
    geography_key         INT  REFERENCES dim_geography(geography_key),
    date_key              INT  REFERENCES dim_date(date_key),
    quantity              INT,
    unit_price            DECIMAL(10,2),
    total_order_value     DECIMAL(10,2),
    total_order_value_usd DECIMAL(10,2),
    currency              NVARCHAR(10),
    status                NVARCHAR(50),
    is_returned           BIT,
    ingested_at           DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_order UNIQUE (order_id)
);

-- ── Fact: Returns ────────────────────────────────────────────
CREATE TABLE fact_returns (
    return_key            INT IDENTITY(1,1) PRIMARY KEY,
    order_id              NVARCHAR(100),
    customer_key          INT  REFERENCES dim_customer(customer_key),
    product_key           INT  REFERENCES dim_product(product_key),
    geography_key         INT  REFERENCES dim_geography(geography_key),
    date_key              INT  REFERENCES dim_date(date_key),
    total_order_value_usd DECIMAL(10,2),
    ingested_at           DATETIME DEFAULT GETDATE()
);