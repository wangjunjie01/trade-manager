-- 上游供应链管理表结构

-- 1. 供应商基本信息表
CREATE TABLE IF NOT EXISTS suppliers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    legal_person TEXT,
    phone TEXT,
    credit_code TEXT,
    bank_name TEXT,
    bank_account TEXT,
    business_desc TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. 供应商人员信息表
CREATE TABLE IF NOT EXISTS supplier_contacts (
    id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL,
    name TEXT NOT NULL,
    position TEXT,
    company TEXT,
    phone TEXT,
    wechat TEXT,
    remark TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
);

-- 3. 供应商物料信息表
CREATE TABLE IF NOT EXISTS supplier_materials (
    id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL,
    name TEXT NOT NULL,
    spec TEXT,
    unit TEXT,
    price_excl_tax REAL DEFAULT 0,
    tax_rate REAL DEFAULT 0.13,
    price_incl_tax REAL DEFAULT 0,
    includes_freight TEXT DEFAULT '否',
    remark TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
);

-- 启用 RLS
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_materials ENABLE ROW LEVEL SECURITY;

-- 创建 RLS 策略（允许匿名读写）
CREATE POLICY anon_suppliers_all ON suppliers FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY anon_contacts_all ON supplier_contacts FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY anon_materials_all ON supplier_materials FOR ALL TO anon USING (true) WITH CHECK (true);
