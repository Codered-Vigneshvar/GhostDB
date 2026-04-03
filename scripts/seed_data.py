import duckdb
import random
import string
from datetime import datetime, timedelta

def generate_random_string(length: int) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_messy_sales_data(conn: duckdb.DuckDBPyConnection, row_count: int = 100000):
    """
    Generates a realistic, messy dataset intentionally structured to challenge SQL optimizers.
    Includes duplicates, explicit nulls, and non-indexed patterns.
    """
    print(f"Seeding {row_count} rows of messy Sales data...")
    
    # Create the base table structure
    conn.execute("""
        CREATE TABLE Sales (
            transaction_id VARCHAR,
            region_id INTEGER,
            customer_id VARCHAR,
            amount DOUBLE,
            transaction_date DATE,
            status VARCHAR,
            notes VARCHAR
        )
    """)
    
    # We will insert data in chunks to optimize seeding time
    chunk_size = 10000
    for chunk_start in range(0, row_count, chunk_size):
        records = []
        for i in range(chunk_size):
            # Duplicate transaction ids (messy data)
            t_id = f"TXN_{chunk_start + i if random.random() > 0.1 else chunk_start + i - 1}"
            
            # Skewed regions
            r_id = random.choice([1, 1, 1, 2, 3, 4, None, None])
            
            # String parsing targets
            c_id = f"CUST_{random.randint(1000, 5000)}" if random.random() > 0.05 else None
            
            amount = round(random.uniform(10.0, 5000.0), 2) if random.random() > 0.05 else None
            
            date_val = (datetime(2025, 1, 1) + timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
            
            status = random.choice(['COMPLETED', 'PENDING', 'FAILED', 'REFUNDED', 'completed', 'Completed'])
            
            notes = generate_random_string(20) if random.random() > 0.5 else None
            
            records.append((t_id, r_id, c_id, amount, date_val, status, notes))
            
        # Bulk insert the chunk using appender
        conn.executemany("""
            INSERT INTO Sales (transaction_id, region_id, customer_id, amount, transaction_date, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, records)
        
    print("Seeding complete.")

if __name__ == "__main__":
    # Test seeding directly
    conn = duckdb.connect(':memory:')
    generate_messy_sales_data(conn, 10000)
    res = conn.execute("SELECT COUNT(*) FROM Sales").fetchone()
    print(f"Total rows verified: {res[0]}")
