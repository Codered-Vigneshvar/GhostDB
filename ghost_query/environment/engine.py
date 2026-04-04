import duckdb
import os
import glob

class DBEngine:
    def __init__(self):
        # We always start a fresh in-memory session per the rules
        self.conn = duckdb.connect(':memory:')
        self._load_all_parquets()

    def _load_all_parquets(self):
        """
        Dynamically finds all .parquet files in ghost_query/data/ and loads them.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        
        # Fallback if running from a different root
        if not os.path.exists(data_dir):
            data_dir = os.path.join(os.getcwd(), "ghost_query", "data")
            
        parquet_files = glob.glob(os.path.join(data_dir, "*.parquet"))
        
        if not parquet_files:
            print(f"⚠️ No Parquet files found in {data_dir}.")
            return
            
        for path in parquet_files:
            # Table name is the filename without extension
            table_name = os.path.splitext(os.path.basename(path))[0]
            try:
                self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{path}')")
                print(f"📦 Loaded table '{table_name}' from Parquet.")
            except Exception as e:
                print(f"❌ Failed to load {table_name}: {str(e)}")

    def reload(self):
        """
        Wipes the database by completely recreating the connection and loading data.
        """
        self.conn.close()
        self.conn = duckdb.connect(':memory:')
        self._load_all_parquets()

    def execute(self, query: str):
        return self.conn.execute(query)

    def close(self):
        self.conn.close()
