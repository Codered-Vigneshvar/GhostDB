# Incident Report: 63cf01da
        
## Summary
- **Status:** ❌ FAILED
- **Retries:** 0
- **Performance Optimization:** 118ms -> 132ms (Regression of 11.9%)
- **Root Cause (Hypothesis):** Unknown

## Recovery Performance
- **Runtime Before:** 118 ms
- **Runtime After:** 132 ms
- **Delta:** 14 ms

## Attempt History

## Validation Metrics Comparison
| Table | Rows (Before) | Rows (After) | Data Health (Post-Fix) |
|---|---|---|---|
| sales | 1000000 | 1000000 | Clean (No NULLs), Cardinality: 435162 |
| market_trends | 200000 | 200000 | Clean (No NULLs) |
| customers | 5000000 | 5000000 | Clean (No NULLs), Cardinality: 5000000 |
