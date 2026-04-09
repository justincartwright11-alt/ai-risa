# Method Bias Report

## Decision vs Stoppage Confusion Matrix:
|            | Actual Decision | Actual Stoppage |
|------------|-----------------|-----------------|
| Pred Decision | 5              | 4               |
| Pred Stoppage | 2              | 4               |

## Method Hit Rate: 6/15 (40.0%)

## Stoppage Over/Underprediction:
- Overpredicted stoppage: 5/15 (33%)
- Underpredicted decision: 4/15 (27%)

## Key Findings:
- Model is more likely to call decision when actual is stoppage than vice versa.
- Stoppage calls are less accurate than decision calls.
