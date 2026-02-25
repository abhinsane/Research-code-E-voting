from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evoting_system.system import FullEVotingSystem


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--voters", type=int, default=30)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--election-id", type=str, default="thesis_demo_2026")
    parser.add_argument("--max-pairs", type=int, default=400)
    parser.add_argument("--output", type=Path, default=Path("reports/full_system_report.json"))
    args = parser.parse_args()

    system = FullEVotingSystem(
        dataset_root=args.dataset,
        voters=args.voters,
        election_id=args.election_id,
        seed=args.seed,
    )
    result = system.run_full(max_pairs=args.max_pairs)
    FullEVotingSystem.save_result(result, args.output)

    print(
        json.dumps(
            {
                "output": str(args.output),
                "enrolled": result.election["enrolled"],
                "he_backend": result.election["he_backend"],
                "chain_valid": result.election["chain_valid"],
                "nullifiers_unique": result.election["nullifiers_unique"],
                "eer": result.biometric_quality["eer"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
