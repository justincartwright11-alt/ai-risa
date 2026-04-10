# Stoppage Bias Audit Report

Total false stoppages: 1
Total missed stoppages: 1

## False Stoppages (predicted stoppage, actual decision):
- goodman_vs_ruiz_prediction | winner: Sam Goodman vs goodman | conf: 70.0 | stop_prop: None | round_tend: None

## Missed Stoppages (predicted decision, actual stoppage):
- fighter_israel_adesanya_vs_fighter_joe_pyfer | winner: fighter_alfonso_franklin vs jhonoven_ureña | conf: 60.0 | stop_prop: 0.5733 | round_tend: 0.5

## Common Feature Patterns:
False stoppages by confidence: Counter({70.0: 1})
Missed stoppages by confidence: Counter({60.0: 1})
False stoppages by stoppage_propensity: Counter({None: 1})
Missed stoppages by stoppage_propensity: Counter({0.5733: 1})
False stoppages by round_finish_tendency: Counter({None: 1})
Missed stoppages by round_finish_tendency: Counter({0.5: 1})

Recommended next step: Tune threshold for stoppage assignment based on these feature patterns.
