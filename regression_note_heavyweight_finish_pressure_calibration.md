# Regression Note: Heavyweight Finish Pressure & Confidence Calibration (April 8, 2026)

## Summary
This regression note documents the results of the heavyweight finish-pressure and confidence calibration pass, validated on three anchor matchups. The calibration targeted more discriminative finish risk for heavyweights, disciplined confidence handling, and preservation of cautious explanation fields. No changes were made to the runner, serialization, output contract, or canonical IDs.

---

### 1. Volkov vs. Cortes-Acosta
- **Result:** Finish pressure became more discriminative for heavyweights, with a clearer risk signal.
- **Confidence:** No spike in confidence; explanation fields remain proportionate and cautious.

### 2. Chimaev vs. Strickland
- **Result:** Explanation layer stayed cautious, with low-confidence language preserved.
- **Confidence:** Model confidence remained disciplined, reflecting the narrow aggregate signal gap.

### 3. Adesanya vs. Pyfer
- **Result:** Signal separation stayed modest, with no artificial inflation of finish risk.
- **Confidence:** Confidence remained disciplined and low, as appropriate for a close fight.

---

#### Additional Notes
- **No runner changes**
- **No serialization changes**
- **No output-contract changes**
- **No canonical-ID regressions**

---

This branch is ready for commit and freeze. For the cleanest closeout, a one-page comparison note across the three fights is recommended as the next artifact.
