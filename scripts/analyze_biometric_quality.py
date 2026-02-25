from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evoting_system.biometric import BiometricProcessor
from evoting_system.dataset import VoterRecord, discover_socofing_records


def similarity(a: bytes, b: bytes) -> float:
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return matches / min(len(a), len(b))


def build_pairs(records: List[VoterRecord], max_pairs: int = 400) -> Tuple[List[float], List[float]]:
    features = {
        r.voter_id: BiometricProcessor.extract_feature_vector(r.image_path)[:32]
        for r in records
    }
    genuine: List[float] = []
    impostor: List[float] = []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            r1 = records[i]
            r2 = records[j]
            sim = similarity(features[r1.voter_id], features[r2.voter_id])
            if r1.subject_id == r2.subject_id:
                genuine.append(sim)
            else:
                impostor.append(sim)
            if len(genuine) + len(impostor) >= max_pairs:
                return genuine, impostor
    return genuine, impostor


def compute_rates(genuine: List[float], impostor: List[float]) -> Dict[str, float]:
    if not genuine or not impostor:
        raise ValueError("Need both genuine and impostor pairs to compute FAR/FRR/EER.")

    thresholds = [i / 100.0 for i in range(0, 101)]
    best = {"gap": 1.0, "eer": 1.0, "threshold": 0.0, "far": 1.0, "frr": 1.0}
    for th in thresholds:
        far = sum(1 for s in impostor if s >= th) / len(impostor)
        frr = sum(1 for s in genuine if s < th) / len(genuine)
        gap = abs(far - frr)
        if gap < best["gap"]:
            best = {"gap": gap, "eer": (far + frr) / 2.0, "threshold": th, "far": far, "frr": frr}
    return {k: v for k, v in best.items() if k != "gap"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--voters", type=int, default=120)
    parser.add_argument("--max-pairs", type=int, default=400)
    parser.add_argument("--output", type=Path, default=Path("reports/biometric_quality.json"))
    args = parser.parse_args()

    records = discover_socofing_records(args.dataset, max_records=args.voters)
    genuine, impostor = build_pairs(records, max_pairs=args.max_pairs)
    rates = compute_rates(genuine, impostor)

    out = {
        "records": len(records),
        "genuine_pairs": len(genuine),
        "impostor_pairs": len(impostor),
        "threshold": rates["threshold"],
        "far": rates["far"],
        "frr": rates["frr"],
        "eer": rates["eer"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
