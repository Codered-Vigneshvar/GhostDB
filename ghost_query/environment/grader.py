import traceback
import hashlib
import pandas as pd

def verify_integrity(original_df: pd.DataFrame, optimized_df: pd.DataFrame) -> bool:
    """
    Verifies that two result sets are identical by sorting and comparing SHA-256 hashes.
    """
    try:
        if len(original_df) != len(optimized_df):
            return False
            
        columns = sorted(list(original_df.columns))
        if sorted(list(optimized_df.columns)) != columns:
            return False
            
        orig_sorted = original_df.sort_values(by=columns).reset_index(drop=True)
        opt_sorted = optimized_df.sort_values(by=columns).reset_index(drop=True)
        
        orig_json_str = orig_sorted.to_json(orient="records", double_precision=5).encode('utf-8')
        opt_json_str = opt_sorted.to_json(orient="records", double_precision=5).encode('utf-8')
        
        orig_hash = hashlib.sha256(orig_json_str).hexdigest()
        opt_hash = hashlib.sha256(opt_json_str).hexdigest()
        
        return orig_hash == opt_hash
    except Exception as e:
        print(f"Grader Evaluation Exception: {traceback.format_exc()}")
        return False
