from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evoting_system.pipeline import EVotingPipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--voters", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("reports/run_results.json"))
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--election-id", type=str, default="thesis_demo_2026")
    args = parser.parse_args()

    random.seed(args.seed)
    pipeline = EVotingPipeline(args.dataset, max_voters=args.voters, election_id=args.election_id)
    pipeline.enroll_voters()

    candidates = ["Alice", "Bob", "Carol"]
    receipts = []
    for voter in pipeline.voters:
        receipt = pipeline.cast_vote(voter.voter_id, random.choice(candidates))
        receipts.append(receipt.__dict__)

    out = {
        "enrolled": len(pipeline.voters),
        "he_backend": pipeline.tally_crypto.backend,
        "chain_valid": pipeline.chain.validate_chain(),
        "nullifiers_unique": pipeline.chain.validate_unique_nullifiers(),
        "tally": pipeline.decrypt_results(),
        "receipts_preview": receipts[:5],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
