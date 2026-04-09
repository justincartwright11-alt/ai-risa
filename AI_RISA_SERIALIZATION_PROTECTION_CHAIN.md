# AI-RISA Serialization Protection Chain

## Protected Checkpoint SHAs
- Freeze baseline: 9c0320fd0a559d5371ac6f9327dd93ca61ec212d
- Regression hardening: 6a6ab35e3676001927f6f054e5d22215ded9b7e3
- Protected merge: bdd98fd13a06a0af10323677e2d0a03aebb67267

## Evidence Bundle (snapshotted under merge SHA)
- out1.json
- out2.json
- out3.json
- ops/accuracy/accuracy_ledger.json
- ops/accuracy/accuracy_ledger.csv
- ops/accuracy/stoppage_bias_audit_report.md

## CI/Branch Policy Gate
Enforced via GitHub Actions (required status check before merge):
- py -3.10 -m pytest tests/test_prediction_record_regression.py
- py -3.10 -m py_compile ai_risa_prediction_adapter.py
- py -3.10 -m py_compile run_single_fight_premium_report.py
- All three sparse-case report commands
- build_accuracy_ledger.py
- score_accuracy_ledger.py
- stoppage_bias_audit.py

---

This document marks the closure of the serialization contract lane. All future changes require passing this gate and explicit justification. Engineering is now redirected to empirical calibration against real fight outcomes.
