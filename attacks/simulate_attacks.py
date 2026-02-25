from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evoting_system.biometric import BiometricProcessor
from evoting_system.pipeline import EVotingPipeline


def replay_attack(pipeline: EVotingPipeline) -> bool:
    """Replay the last payload; should be flagged by nullifier uniqueness checks."""
    payload = pipeline.chain.chain[-1].payload.copy()
    pipeline.chain.add_block(payload)
    return not pipeline.chain.validate_unique_nullifiers()


def tamper_attack(pipeline: EVotingPipeline) -> bool:
    if len(pipeline.chain.chain) < 3:
        return False
    target = pipeline.chain.chain[2]
    target.payload["candidate"] = "Mallory"
    target.hash = target.compute_hash()
    return pipeline.chain.validate_chain()


def template_inversion_attack(pipeline: EVotingPipeline) -> bool:
    _, templ = next(iter(pipeline.templates.items()))
    guessed_original = bytes(a ^ b for a, b in zip(templ.transformed, b"\x00" * len(templ.transformed)))
    original = BiometricProcessor.extract_feature_vector(pipeline.voters[0].image_path)[:32]
    return guessed_original == original


def hill_climbing_attack(pipeline: EVotingPipeline) -> bool:
    """Randomly mutate transformed template bytes and search for high similarity."""
    _, templ = next(iter(pipeline.templates.items()))
    target = BiometricProcessor.extract_feature_vector(pipeline.voters[0].image_path)[:32]
    best = 0
    for _ in range(200):
        candidate = bytearray(templ.transformed)
        pos = random.randrange(len(candidate))
        candidate[pos] ^= random.randrange(1, 255)
        score = sum(1 for a, b in zip(candidate, target) if a == b)
        if score > best:
            best = score
    return best > 24


def presentation_attack(pipeline: EVotingPipeline) -> bool:
    """Attempt to vote with synthetic replay identity and stolen template id."""
    victim = pipeline.voters[0]
    fake_id = f"spoof_{victim.voter_id}"
    try:
        pipeline.cast_vote(fake_id, "Alice")
    except KeyError:
        return False
    return True


def collusion_attack(pipeline: EVotingPipeline) -> bool:
    """Two insiders try to submit extra vote for same voter."""
    voter = pipeline.voters[0]
    try:
        pipeline.cast_vote(voter.voter_id, "Bob")
    except RuntimeError:
        return False
    return True


def node_compromise_attack(pipeline: EVotingPipeline) -> bool:
    """Compromised node rewrites a block and re-mines locally; validation should fail due to linkage."""
    if len(pipeline.chain.chain) < 4:
        return False
    compromised = pipeline.chain.chain[2]
    compromised.payload["candidate"] = "Eve"
    compromised.nonce = 0
    compromised.hash = compromised.compute_hash()
    while not compromised.hash.startswith(pipeline.chain.difficulty_prefix):
        compromised.nonce += 1
        compromised.hash = compromised.compute_hash()
    return pipeline.chain.validate_chain()


def run_experiment(dataset_root: Path, voters: int, seed: int = 11) -> Dict[str, object]:
    random.seed(seed)
    pipeline = EVotingPipeline(dataset_root=dataset_root, max_voters=voters)
    pipeline.enroll_voters()

    candidates = ["Alice", "Bob", "Carol"]
    for voter in pipeline.voters:
        pipeline.cast_vote(voter.voter_id, random.choice(candidates))

    results = pipeline.decrypt_results()
    replay_protected = replay_attack(pipeline)
    tamper_undetected = tamper_attack(pipeline)
    inversion_success = template_inversion_attack(pipeline)
    hill_climbing_success = hill_climbing_attack(pipeline)
    presentation_success = presentation_attack(pipeline)
    collusion_success = collusion_attack(pipeline)
    node_compromise_undetected = node_compromise_attack(pipeline)

    report = {
        "num_voters": len(pipeline.voters),
        "he_backend": pipeline.tally_crypto.backend,
        "chain_valid_after_attacks": pipeline.chain.validate_chain(),
        "nullifiers_unique_after_attacks": pipeline.chain.validate_unique_nullifiers(),
        "vote_results": results,
        "attack_outcomes": {
            "replay_attack_blocked": replay_protected,
            "tamper_attack_undetected": tamper_undetected,
            "template_inversion_success": inversion_success,
            "hill_climbing_success": hill_climbing_success,
            "presentation_attack_success": presentation_success,
            "collusion_attack_success": collusion_success,
            "node_compromise_undetected": node_compromise_undetected,
        },
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--voters", type=int, default=30)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--output", type=Path, default=Path("reports/attack_results.json"))
    args = parser.parse_args()

    report = run_experiment(args.dataset, args.voters, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
