#!/usr/bin/env python3
"""初始化 Supabase 数据库表结构"""
import psycopg2

# Supabase 连接信息
SUPABASE_HOST = "tuzfagnvwmnsojxvdyvd.supabase.co"
SUPABASE_PORT = "5432"
SUPABASE_DB = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "PeCTb8/GbyRpaE-"

# SQL 创建表语句
CREATE_TABLES_SQL = """
-- 客户表
CREATE TABLE IF NOT EXISTS clients (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    contact VARCHAR(100),
    phone VARCHAR(50),
    address TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 产品表
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    spec VARCHAR(100),
    price DECIMAL(12, 2) DEFAULT 0,
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 送货单主表
CREATE TABLE IF NOT EXISTS deliveries (
    id VARCHAR(50) PRIMARY KEY,
    client_name VARCHAR(200) NOT NULL,
    delivery_date DATE NOT NULL,
    total DECIMAL(12, 2) DEFAULT 0,
    remark TEXT,
    status VARCHAR(20) DEFAULT 'unpaid',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 送货单明细表
CREATE TABLE IF NOT EXISTS delivery_items (
    id SERIAL PRIMARY KEY,
    delivery_id VARCHAR(50) REFERENCES deliveries(id) ON DELETE CASCADE,
    product_name VARCHAR(200),
    qty INTEGER DEFAULT 1,
    price DECIMAL(12, 2),
    subtotal DECIMAL(12, 2)
);

-- 打款记录表
CREATE TABLE IF NOT EXISTS payments (
    id VARCHAR(50) PRIMARY KEY,
    client_name VARCHAR(200) NOT NULL,
    payment_date DATE NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    delivery_id VARCHAR(50),
    remark TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引提升查询性能
CREATE INDEX IF NOT EXISTS idx_deliveries_client ON deliveries(client_name);
CREATE INDEX IF NOT EXISTS idx_deliveries_date ON deliveries(delivery_date);
CREATE INDEX IF NOT EXISTS idx_payments_client ON payments(client_name);
CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_delivery_items_delivery ON delivery_items(delivery_id);
"""

def init_database():
    """初始化数据库"""
    try:
        print("🔄 正在连接 Supabase...")
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            dbname=SUPABASE_DB,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("✅ 连接成功！")
        print("📝 正在创建数据表...")

        # 执行 SQL
        cursor.execute(CREATE_TABLES_SQL)

        print("✅ 数据表创建完成！")
        print("")
        print("📋 已创建以下表：")
        print("   - clients (客户表)")
        print("   - products (产品表)")
        print("   - deliveries (送货单主表)")
        print("   - delivery_items (送货单明细表)")
        print("   - payments (打款记录表)")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    init_database()
