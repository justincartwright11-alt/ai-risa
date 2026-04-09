# Stoppage Bias Audit Report

Total false stoppages: 1
Total missed stoppages: 6

## False Stoppages (predicted stoppage, actual decision):
- goodman_vs_ruiz_prediction | winner: Sam Goodman vs goodman | conf: 70.0 | stop_prop: None | round_tend: None

## Missed Stoppages (predicted decision, actual stoppage):
- alfonso_franklin_vs_jhonoven_ureña_prediction | winner: Alfonso Franklin vs jhonoven_ureña | conf: 55.0 | stop_prop: None | round_tend: None
- don_madge_vs_tba_prediction | winner: Don Madge vs don_madge | conf: 55.0 | stop_prop: None | round_tend: None
- ioan_croft_vs_novak_radulovic_prediction | winner: Ioan Croft vs ioan_croft | conf: 60.0 | stop_prop: None | round_tend: None
- israel_adesanya_vs_dricus_du_plessis_prediction | winner: Israel Adesanya vs dricus_du_plessis | conf: 55.0 | stop_prop: None | round_tend: None
- jordan_thompson_vs_david_spilmont_prediction | winner: Jordan Thompson vs jordan_thompson | conf: 60.0 | stop_prop: None | round_tend: None
- tim_tszyu_vs_denis_nurja_prediction | winner: Tim Tszyu vs tim_tszyu | conf: 60.0 | stop_prop: None | round_tend: None

## Common Feature Patterns:
False stoppages by confidence: Counter({70.0: 1})
Missed stoppages by confidence: Counter({55.0: 3, 60.0: 3})
False stoppages by stoppage_propensity: Counter({None: 1})
Missed stoppages by stoppage_propensity: Counter({None: 6})
False stoppages by round_finish_tendency: Counter({None: 1})
Missed stoppages by round_finish_tendency: Counter({None: 6})

Recommended next step: Tune threshold for stoppage assignment based on these feature patterns.
