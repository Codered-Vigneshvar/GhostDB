import duckdb
import random
import string
import os
from datetime import datetime, timedelta

class DBEngine:
    def __init__(self, connection_str: str = ':memory:'):
        self.conn = duckdb.connect(connection_str)
        self._setup_initial_state()

    def _setup_initial_state(self):
        # Placeholder for complex engine setup if needed
        pass

    def seed_data(self, row_count: int = 100000):
        """
        Generates a realistic, messy dataset intentionally structured to challenge SQL optimizers.
        """
        print(f"Seeding {row_count} rows of messy Sales data...")
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS Sales (
                transaction_id VARCHAR,
                region_id INTEGER,
                customer_id VARCHAR,
                amount DOUBLE,
                transaction_date DATE,
                status VARCHAR,
                notes VARCHAR
            )
        """)
        
        chunk_size = 10000
        for chunk_start in range(0, row_count, chunk_size):
            records = []
            for i in range(chunk_size):
                t_id = f"TXN_{chunk_start + i if random.random() > 0.1 else chunk_start + i - 1}"
                r_id = random.choice([1, 1, 1, 2, 3, 4, None, None])
                c_id = f"CUST_{random.randint(1000, 5000)}" if random.random() > 0.05 else None
                amount = round(random.uniform(10.0, 5000.0), 2) if random.random() > 0.05 else None
                date_val = (datetime(2025, 1, 1) + timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
                status = random.choice(['COMPLETED', 'PENDING', 'FAILED', 'REFUNDED', 'completed', 'Completed'])
                notes = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20)) if random.random() > 0.5 else None
                records.append((t_id, r_id, c_id, amount, date_val, status, notes))
                
            self.conn.executemany("""
                INSERT INTO Sales (transaction_id, region_id, customer_id, amount, transaction_date, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, records)
        
        print("Seeding complete.")

    def load_parquet_data(self, path: str, table_name: str):
        """
        Stub for loading external evaluation datasets.
        """
        if os.path.exists(path):
            self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{path}')")
            print(f"Loaded {table_name} from {path}")
        else:
            print(f"Warning: Parquet file {path} not found. Skipping load.")

    def execute(self, query: str):
        return self.conn.execute(query)

    def close(self):
        self.conn.close()
