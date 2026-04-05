# Incident Report: 11f4c6af
        
## Summary
- **Status:** ❌ FAILED
- **Retries:** 0
- **Performance Optimization:** 114ms -> 126ms (Regression of 10.5%)
- **Root Cause (Hypothesis):** Unknown

## Recovery Performance
- **Runtime Before:** 114 ms
- **Runtime After:** 126 ms
- **Delta:** 12 ms

## Attempt History

## Validation Metrics Comparison
| Table | Rows (Before) | Rows (After) | Data Health (Post-Fix) |
|---|---|---|---|
| sales | 1000000 | 1000000 | Clean (No NULLs), Cardinality: 380969 |
| market_trends | 200000 | 200000 | Clean (No NULLs) |
| customers | 5000000 | 5000000 | Clean (No NULLs), Cardinality: 5000000 |
