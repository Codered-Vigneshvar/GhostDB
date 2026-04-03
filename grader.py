import traceback
import hashlib
import pandas as pd

def verify_integrity(original_df: pd.DataFrame, optimized_df: pd.DataFrame) -> bool:
    """
    Verifies that two result sets are identical by sorting and comparing SHA-256 hashes.
    Ensures that the optimized query returns exact bit-fidelity logic compared to baseline.
    """
    try:
        # Quick row count check
        if len(original_df) != len(optimized_df):
            return False
            
        columns = sorted(list(original_df.columns))
        # Ensure identical column sets
        if sorted(list(optimized_df.columns)) != columns:
            return False
            
        # Sort values over all columns to handle order-agnostic queries
        orig_sorted = original_df.sort_values(by=columns).reset_index(drop=True)
        opt_sorted = optimized_df.sort_values(by=columns).reset_index(drop=True)
        
        # It's safest to convert to string JSON representation and hash
        orig_json_str = orig_sorted.to_json(orient="records", double_precision=5).encode('utf-8')
        opt_json_str = opt_sorted.to_json(orient="records", double_precision=5).encode('utf-8')
        
        orig_hash = hashlib.sha256(orig_json_str).hexdigest()
        opt_hash = hashlib.sha256(opt_json_str).hexdigest()
        
        return orig_hash == opt_hash
    except Exception as e:
        print(f"Grader Evaluation Exception: {traceback.format_exc()}")
        return False
