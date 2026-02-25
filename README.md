# Hybrid E-Voting Research Prototype (Blockchain + ZKP + HE + Cancellable Biometrics + PQC)

This project provides an end-to-end research prototype integrating:

- Blockchain integrity for ballot audit trails.
- Schnorr-style ZKP voter authentication.
- Homomorphic encrypted tallying with a **SEAL(BFV)-via-TenSEAL backend when available**.
- Cancellable biometric templates from SOCOFing-compatible fingerprints.
- **Dilithium/Kyber wrappers via liboqs** (with simulation fallback only when liboqs is unavailable).
- Nullifier-based anti-replay one-person-one-vote enforcement.

> Research-only implementation: cryptography and attack evaluation are designed for experimentation and thesis workflows.

## Project layout

```text
attacks/
  simulate_attacks.py
scripts/
  generate_mock_socofing.py
  run_pipeline.py
  analyze_biometric_quality.py
  run_full_system.py
evoting_system/
  biometric.py
  blockchain.py
  crypto_primitives.py
  dataset.py
  pipeline.py
  system.py
reports/
```

## Run

```bash
python scripts/generate_mock_socofing.py --out data/SOCOFing_mock --samples 50
python scripts/run_pipeline.py --dataset data/SOCOFing_mock --voters 30 --output reports/run_results.json
python attacks/simulate_attacks.py --dataset data/SOCOFing_mock --voters 30 --output reports/attack_results.json
python scripts/analyze_biometric_quality.py --dataset data/SOCOFing_mock --voters 50 --output reports/biometric_quality.json
python scripts/run_full_system.py --dataset data/SOCOFing_mock --voters 30 --output reports/full_system_report.json
```

## Implemented improvements

1. **Dilithium/Kyber integration path**
   - `DilithiumSignature` and `KyberKEM` now call `python-oqs` (`liboqs`) when available.
2. **Anti-replay nullifier enforcement**
   - Unique nullifier per voter + election + template.
   - Duplicate nullifier submissions are rejected in the voting pipeline and auditable via chain checks.
3. **HE backend upgrade path**
   - `HomomorphicTally` auto-selects TenSEAL BFV (SEAL-backed) when installed.
4. **Biometric quality metrics**
   - FAR/FRR/EER script on SOCOFing-style subject splits.
5. **Expanded attack suite**
   - Replay, tamper, template inversion, hill-climbing, presentation attack, collusion, node compromise.

## Recommended dependencies for full mode

```bash
pip install oqs-python tenseal
```

If these are absent, the system still runs in fallback mode for reproducibility.

## Full system code entrypoint

Use this single command to execute the complete workflow (election + attacks + biometric quality) and generate one integrated report:

```bash
python scripts/run_full_system.py --dataset data/SOCOFing_mock --voters 30 --output reports/full_system_report.json
```
