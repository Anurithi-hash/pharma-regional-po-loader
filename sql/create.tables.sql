CREATE TABLE IF NOT EXISTS stg_regional_po (
    po_number TEXT,
    region TEXT,
    supplier_id TEXT,
    material_code TEXT,
    ordered_qty INTEGER,
    unit_price_usd REAL,
    order_date TEXT,
    total_po_value REAL,
    source_file_name TEXT,
    loaded_at TEXT
);

CREATE TABLE IF NOT EXISTS etl_file_audit_log (
    file_name TEXT,
    rows_loaded INTEGER,
    load_status TEXT,
    error_message TEXT,
    processed_at TEXT
);