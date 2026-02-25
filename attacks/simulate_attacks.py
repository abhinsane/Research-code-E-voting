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
    """Attempt to replay an existing payload and expect duplicate detection externally.

    In this prototype, replay attack is considered successful if chain remains valid
    despite re-adding the exact payload (shows need for nonce/timestamp binding).
    """
    payload = pipeline.chain.chain[-1].payload.copy()
    pipeline.chain.add_block(payload)
    return pipeline.chain.validate_chain()


def tamper_attack(pipeline: EVotingPipeline) -> bool:
    """Try modifying a block and check if validation catches it."""
    if len(pipeline.chain.chain) < 3:
        return False
    target = pipeline.chain.chain[2]
    target.payload["candidate"] = "Mallory"
    target.hash = target.compute_hash()
    return pipeline.chain.validate_chain()


def template_inversion_attack(pipeline: EVotingPipeline) -> bool:
    """Try recovering original template bytes from cancellable template only."""
    voter_id, templ = next(iter(pipeline.templates.items()))
    guessed_original = bytes(a ^ b for a, b in zip(templ.transformed, b"\x00" * len(templ.transformed)))
    original = BiometricProcessor.extract_feature_vector(pipeline.voters[0].image_path)[:32]
    _ = voter_id
    return guessed_original == original


def run_experiment(dataset_root: Path, voters: int, seed: int = 11) -> Dict[str, object]:
    random.seed(seed)
    pipeline = EVotingPipeline(dataset_root=dataset_root, max_voters=voters)
    pipeline.enroll_voters()

    candidates = ["Alice", "Bob", "Carol"]
    for voter in pipeline.voters:
        pipeline.cast_vote(voter.voter_id, random.choice(candidates))

    results = pipeline.decrypt_results()
    replay_ok = replay_attack(pipeline)
    tamper_ok = tamper_attack(pipeline)
    inversion_success = template_inversion_attack(pipeline)

    report = {
        "num_voters": len(pipeline.voters),
        "chain_valid_after_attacks": pipeline.chain.validate_chain(),
        "vote_results": results,
        "attack_outcomes": {
            "replay_attack_not_detected": replay_ok,
            "tamper_attack_undetected": tamper_ok,
            "template_inversion_success": inversion_success,
        },
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--voters", type=int, default=30)
    parser.add_argument("--output", type=Path, default=Path("reports/attack_results.json"))
    args = parser.parse_args()

    report = run_experiment(args.dataset, args.voters)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
