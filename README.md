# Hybrid E-Voting Research Prototype (Blockchain + ZKP + FHE + Cancellable Biometrics + PQC)

This repository now contains a **research-oriented reference implementation** of an e-voting pipeline designed for experimentation with:

- Blockchain-backed vote log integrity
- Zero-Knowledge Proof (ZKP) voter authentication (knowledge proof)
- Toy Fully Homomorphic Encryption-style additive tallying (homomorphic tally simulation)
- Cancellable biometric templates
- Post-Quantum Cryptography (PQC) style signature/KEM wrappers (simulation fallback)
- SOCOFing dataset integration for biometric enrollment

> ⚠️ **Important**: This code is a **research prototype** and not production-secure. Real deployments must replace toy primitives with audited cryptographic libraries and formal threat modeling.

---

## Folder Structure

```text
Research-code-E-voting/
├── attacks/
│   └── simulate_attacks.py
├── evoting_system/
│   ├── __init__.py
│   ├── biometric.py
│   ├── blockchain.py
│   ├── crypto_primitives.py
│   ├── dataset.py
│   └── pipeline.py
├── reports/
│   ├── attack_results.json        # generated
│   ├── report.md                  # research-style summary
│   └── run_results.json           # generated
├── scripts/
│   ├── generate_mock_socofing.py
│   └── run_pipeline.py
└── README.md
```

---

## Architecture Overview

1. **Enrollment (SOCOFing)**
   - Loads `.BMP` fingerprint files.
   - Extracts hashed feature vectors.
   - Generates cancellable templates (`transformed`, `cancel_token`, `template_id`).

2. **Authentication + Privacy**
   - For each vote, generates a Schnorr-style Fiat-Shamir ZKP proving knowledge of a secret.
   - Stores only proof artifacts on-chain.

3. **Confidential Vote Processing**
   - Encrypts each vote as a homomorphic ciphertext.
   - Adds encrypted votes for candidate-wise tally without decrypting individual votes.

4. **Blockchain Audit Trail**
   - Every cast vote creates a mined block with PoW prefix.
   - Chain validation checks hash continuity and tamper evidence.

5. **PQC Layer**
   - Vote payloads are signed via PQ wrapper (`PQSignature`).
   - KEM encapsulation included (`PQKEM`) for session-key style integration.

6. **Attack Simulation**
   - Replay injection test
   - Chain tamper test
   - Template inversion attempt against cancellable templates

---

## How to Run

### 1) Optional: create mock SOCOFing-like data

```bash
python scripts/generate_mock_socofing.py --out data/SOCOFing_mock --samples 50
```

If you already have the real SOCOFing dataset, skip this and point `--dataset` to your dataset root.

### 2) Run full e-voting pipeline

```bash
python scripts/run_pipeline.py --dataset data/SOCOFing_mock --voters 30 --output reports/run_results.json
```

### 3) Run attack simulation

```bash
python attacks/simulate_attacks.py --dataset data/SOCOFing_mock --voters 30 --output reports/attack_results.json
```

### 4) Read generated outputs

- `reports/run_results.json`
- `reports/attack_results.json`
- `reports/report.md`

---

## Running with the Real SOCOFing Dataset

Use the dataset root that contains SOCOFing `.BMP` files.

Example:

```bash
python scripts/run_pipeline.py --dataset /path/to/SOCOFing/Real --voters 100
python attacks/simulate_attacks.py --dataset /path/to/SOCOFing/Real --voters 100
```

---

## Research Notes

- **PQC in biometric template flow**: template IDs and pipeline signing are PQ-wrapper protected; in production, replace with CRYSTALS-Dilithium/Falcon signatures and Kyber KEM via liboqs/PQClean bindings.
- **FHE**: current implementation is toy additive-homomorphic for transparent experimentation. For real FHE, integrate OpenFHE/SEAL/TFHE stack.
- **ZKP**: current proof is Schnorr-style PoK; extend to zk-SNARK/zk-STARK circuits for full private eligibility proofs.
- **Cancellable biometrics**: revocation/reissue supported by generating new transform token.

---

## Suggested Next Research Extensions

- Add liveness detection and spoof resistance module.
- Federated nodes with BFT consensus instead of toy PoW chain.
- Formal IND-CCA and unlinkability analysis.
- Differential privacy on aggregate result release.
- Red-team framework: hill-climbing, stolen template, model inversion, and side-channel attack simulations.
