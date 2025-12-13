/*
    SQL Server Initialization Script
    Run this manually or via a separate job after the container is up.
*/

CREATE DATABASE sales_dw;
GO

USE sales_dw;
GO

CREATE SCHEMA dw;
GO
CREATE SCHEMA control;
GO

-- Control Table for Watermarking
CREATE TABLE control.etl_watermark (
    table_name VARCHAR(100) PRIMARY KEY,
    last_watermark DATETIME2,
    last_batch_id INT,
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Dim Customers (SCD Type 1 for now)
CREATE TABLE dw.dim_customers (
    customer_sk INT IDENTITY(1,1) PRIMARY KEY,
    customer_id INT, -- Natural Key
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(150),
    phone VARCHAR(50),
    dw_created_at DATETIME2 DEFAULT GETDATE(),
    dw_updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Dim Products
CREATE TABLE dw.dim_products (
    product_sk INT IDENTITY(1,1) PRIMARY KEY,
    product_id INT, -- Natural Key
    product_name VARCHAR(200),
    category VARCHAR(100),
    current_price DECIMAL(10, 2),
    dw_created_at DATETIME2 DEFAULT GETDATE(),
    dw_updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Fact Sales
CREATE TABLE dw.fact_sales (
    sales_sk INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT,
    order_item_id INT,
    customer_sk INT FOREIGN KEY REFERENCES dw.dim_customers(customer_sk),
    product_sk INT FOREIGN KEY REFERENCES dw.dim_products(product_sk),
    order_date DATETIME2,
    quantity INT,
    unit_price DECIMAL(10, 2),
    total_amount DECIMAL(12, 2),
    status VARCHAR(50),
    dw_batch_id INT,
    dw_created_at DATETIME2 DEFAULT GETDATE()
);
GO
