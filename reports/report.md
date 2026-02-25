# Research Report: Hybrid E-Voting Prototype (Blockchain + ZKP + FHE + Cancellable Biometrics + PQC)

## 1. Objective

Design and implement an end-to-end research prototype that combines:

- Blockchain integrity layer
- Zero-knowledge authentication proof
- Homomorphic encrypted vote tallying
- Cancellable biometric templates
- PQC-style signing/KEM wrappers
- SOCOFing dataset-based enrollment workflow

## 2. Experimental Setup

- Dataset source: SOCOFing-compatible BMP fingerprints (mock-generated for reproducibility in this run).
- Number of voters in run: 30
- Candidates: Alice, Bob, Carol

Commands used:

```bash
python scripts/generate_mock_socofing.py --out data/SOCOFing_mock --samples 50
python scripts/run_pipeline.py --dataset data/SOCOFing_mock --voters 30 --output reports/run_results.json
python attacks/simulate_attacks.py --dataset data/SOCOFing_mock --voters 30 --output reports/attack_results.json
```

## 3. Core Workflow

1. **Enrollment**
   - Fingerprint BMP is hashed into feature vector.
   - Cancellable transform is applied and stored as template ID + tokenized transform.

2. **Voting**
   - Voter proves secret knowledge through Schnorr-style NIZK.
   - Vote count is encrypted via additive-homomorphic toy scheme.
   - On-chain payload includes template ID, ZKP proof, and PQ-style signature/KEM artifacts.

3. **Tally**
   - Aggregation is performed over ciphertexts.
   - Decryption reveals only candidate totals.

## 4. Results

### 4.1 Pipeline output (`reports/run_results.json`)

- Enrolled voters: 30
- Blockchain validity: `true`
- Decrypted tally:
  - Alice: 8
  - Bob: 8
  - Carol: 14

### 4.2 Attack simulation (`reports/attack_results.json`)

- Replay attack not detected by base chain logic: `true`
  - Indicates need for anti-replay nonce and per-voter one-time ballot constraints.
- Tamper attack undetected: `false`
  - Tampering is detected (desired behavior).
- Template inversion success: `false`
  - Cancellable template prevented direct inversion in this simplistic test.
- Chain valid after all attacks: `false`
  - Final state indicates tampering was caught by validation.

## 5. Security Interpretation

- **Strength observed**:
  - Tamper evidence works under block edit attack.
  - Cancellable templates improve revocability and unlinkability.
  - ZKP gate ensures possession proof without leaking secret.
- **Gaps to address**:
  - Replay vulnerability still exists in base simulation.
  - PQ components are wrappers and should be replaced by standardized PQC algorithms.
  - Toy homomorphic encryption should be replaced with production FHE libraries.

## 6. Recommended Next Steps for Thesis/Publication

1. Replace PQ wrappers with Dilithium/Kyber via liboqs.
2. Introduce nullifier-based one-person-one-vote anti-replay enforcement.
3. Use OpenFHE/SEAL for robust encrypted tallying.
4. Add FAR/FRR/EER biometric quality analysis on real SOCOFing splits.
5. Expand attack suite: hill-climbing, presentation attack, collusion and node compromise.

## 7. Reproducibility

All scripts and outputs are committed in this repository:

- `evoting_system/` : full code
- `scripts/` : runners and dataset mock utility
- `attacks/` : attack experiments
- `reports/` : generated artifacts and this report
