import duckdb
import os

def generate_and_export():
    db_path = 'temp_generate.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    con = duckdb.connect(db_path)
    
    print("🏗️  Building 5M Customers...")
    con.execute("CREATE TABLE customers AS SELECT range::BIGINT as cust_id, 'SEGMENT_' || (range % 50)::VARCHAR as segment FROM range(5000000);")
    
    # Scale down slightly to 1M to keep execution fast for local testing, 
    # but still perfectly compliant with the schema expectation.
    print("🏗️  Building 1M Sales...")
    con.execute("""
    CREATE TABLE sales AS 
    SELECT 
        range::BIGINT as sale_id,
        (random() * 5000000)::BIGINT as cust_id,
        random() * 100 as amount,
        '2026-04-01 ' || lpad((range % 24)::VARCHAR, 2, '0') || ':00:00' as sale_time_str
    FROM range(1000000);
    """)

    print("🏗️  Building 200k Market Trends...")
    con.execute("""
    CREATE TABLE market_trends AS 
    SELECT 
        'SEGMENT_' || (range % 50)::VARCHAR as segment, 
        random() as trend_index,
        repeat('heavy_json_blob_', 10) as detail_padding
    FROM range(200000); 
    """)
    
    print("📦 Exporting to Parquet in data/...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    con.execute(f"COPY customers TO '{base_dir}/customers.parquet' (FORMAT PARQUET)")
    con.execute(f"COPY sales TO '{base_dir}/sales.parquet' (FORMAT PARQUET)")
    con.execute(f"COPY market_trends TO '{base_dir}/market_trends.parquet' (FORMAT PARQUET)")
    
    print("✅ Export complete!")
    con.close()
    os.remove(db_path)

if __name__ == "__main__":
    generate_and_export()