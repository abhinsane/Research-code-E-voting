from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class VoterRecord:
    voter_id: str
    image_path: Path


def discover_socofing_records(dataset_root: Path, max_records: int = 100) -> List[VoterRecord]:
    """Find SOCOFing fingerprint image files and derive voter IDs from file names."""
    if not dataset_root.exists():
        raise FileNotFoundError(f"SOCOFing dataset root not found: {dataset_root}")

    image_files: Iterable[Path] = list(dataset_root.glob("**/*.BMP")) + list(dataset_root.glob("**/*.bmp"))
    records: List[VoterRecord] = []
    for idx, img in enumerate(sorted(image_files)):
        if idx >= max_records:
            break
        stem = img.stem.replace(" ", "_")
        voter_id = f"voter_{stem}"
        records.append(VoterRecord(voter_id=voter_id, image_path=img))

    if not records:
        raise ValueError("No BMP files discovered under dataset root.")
    return records
