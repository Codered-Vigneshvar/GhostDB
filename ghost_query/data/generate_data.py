import duckdb
import os

def build_mega_disaster_data():
    db_path = 'ghost_physics.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    con = duckdb.connect(db_path)

    print("🏗️  Building 5M Customers...")
    con.execute("CREATE TABLE customers AS SELECT range::BIGINT as cust_id, 'SEGMENT_' || (range % 50)::VARCHAR as segment FROM range(5000000);")

    print("🏗️  Building 20M Sales...")
    con.execute("""
    CREATE TABLE sales AS 
    SELECT 
        range::BIGINT as sale_id,
        (random() * 5000000)::BIGINT as cust_id,
        random() * 100 as amount,
        '2026-04-01 ' || lpad((range % 24)::VARCHAR, 2, '0') || ':00:00' as sale_time_str
    FROM range(20000000);
    """)

    print("🏗️  Building 1M Market Trends (The Multiplier)...")
    con.execute("""
    CREATE TABLE market_trends AS 
    SELECT 
        'SEGMENT_' || (range % 50)::VARCHAR as segment, -- Matches customers
        random() as trend_index,
        repeat('heavy_json_blob_', 10) as detail_padding
    FROM range(1000000); 
    """)

    print(f"✅ Database created at {db_path}. Prepared for 2-hour bottleneck.")
    con.close()

if __name__ == "__main__":
    build_mega_disaster_data()