from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from attacks.simulate_attacks import run_experiment as run_attack_experiment
from evoting_system.pipeline import EVotingPipeline
from scripts.analyze_biometric_quality import build_pairs, compute_rates


@dataclass
class FullSystemResult:
    election: Dict[str, object]
    attacks: Dict[str, object]
    biometric_quality: Dict[str, object]


class FullEVotingSystem:
    """High-level orchestrator for the full research e-voting prototype."""

    def __init__(
        self,
        dataset_root: Path,
        voters: int = 30,
        election_id: str = "thesis_demo_2026",
        seed: int = 11,
    ) -> None:
        self.dataset_root = dataset_root
        self.voters = voters
        self.election_id = election_id
        self.seed = seed

    def run_election(self) -> Dict[str, object]:
        random.seed(self.seed)
        pipeline = EVotingPipeline(self.dataset_root, max_voters=self.voters, election_id=self.election_id)
        pipeline.enroll_voters()

        candidates = ["Alice", "Bob", "Carol"]
        receipts: List[Dict[str, object]] = []
        for voter in pipeline.voters:
            receipt = pipeline.cast_vote(voter.voter_id, random.choice(candidates))
            receipts.append(receipt.__dict__)

        return {
            "enrolled": len(pipeline.voters),
            "he_backend": pipeline.tally_crypto.backend,
            "chain_valid": pipeline.chain.validate_chain(),
            "nullifiers_unique": pipeline.chain.validate_unique_nullifiers(),
            "tally": pipeline.decrypt_results(),
            "receipts_preview": receipts[:10],
        }

    def run_attacks(self) -> Dict[str, object]:
        return run_attack_experiment(self.dataset_root, voters=self.voters, seed=self.seed)

    def run_biometric_quality(self, max_pairs: int = 400) -> Dict[str, object]:
        random.seed(self.seed)
        pipeline = EVotingPipeline(self.dataset_root, max_voters=self.voters, election_id=self.election_id)
        records = pipeline.voters
        genuine, impostor = build_pairs(records, max_pairs=max_pairs)
        rates = compute_rates(genuine, impostor)
        return {
            "records": len(records),
            "genuine_pairs": len(genuine),
            "impostor_pairs": len(impostor),
            "threshold": rates["threshold"],
            "far": rates["far"],
            "frr": rates["frr"],
            "eer": rates["eer"],
        }

    def run_full(self, max_pairs: int = 400) -> FullSystemResult:
        election = self.run_election()
        attacks = self.run_attacks()
        biometric_quality = self.run_biometric_quality(max_pairs=max_pairs)
        return FullSystemResult(election=election, attacks=attacks, biometric_quality=biometric_quality)

    @staticmethod
    def save_result(result: FullSystemResult, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "election": result.election,
            "attacks": result.attacks,
            "biometric_quality": result.biometric_quality,
        }
        output_path.write_text(json.dumps(payload, indent=2))
