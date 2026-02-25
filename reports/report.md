# Research Run Report (Updated Prototype)

## Integrated Components
- Blockchain vote log with PoW integrity checks and nullifier uniqueness audits.
- Schnorr-style ZKP for possession proof.
- Homomorphic tally abstraction using SEAL(BFV via TenSEAL) when available, otherwise toy HE fallback.
- Cancellable biometric templates.
- liboqs-based Dilithium/Kyber wrappers with constrained-environment fallback.

## Run Commands
```bash
python scripts/generate_mock_socofing.py --out data/SOCOFing_mock --samples 50
python scripts/run_pipeline.py --dataset data/SOCOFing_mock --voters 30 --output reports/run_results.json
python attacks/simulate_attacks.py --dataset data/SOCOFing_mock --voters 30 --output reports/attack_results.json
python scripts/analyze_biometric_quality.py --dataset data/SOCOFing_mock --voters 50 --output reports/biometric_quality.json
```

## Key Outcomes
- Replay/double-vote path is blocked by nullifier checks.
- Tamper and node-compromise edits are detected by chain validation.
- Biometric quality script now reports FAR/FRR/EER for SOCOFing-style subject splits.

## Next steps
- Install `oqs-python` and `tenseal` to run fully on liboqs + SEAL backend.
- Replace toy ZKP with circuit-based proofs for stronger privacy guarantees.
