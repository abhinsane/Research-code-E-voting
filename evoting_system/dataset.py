from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class VoterRecord:
    voter_id: str
    image_path: Path
    subject_id: str


def parse_subject_id(image_path: Path) -> str:
    """Parse SOCOFing-like subject id from filename prefix."""
    stem = image_path.stem.replace(" ", "_")
    if "__" in stem:
        return stem.split("__", 1)[0]
    if "_" in stem:
        return stem.split("_", 1)[0]
    return stem


def discover_socofing_records(dataset_root: Path, max_records: int = 100) -> List[VoterRecord]:
    if not dataset_root.exists():
        raise FileNotFoundError(f"SOCOFing dataset root not found: {dataset_root}")

    image_files: Iterable[Path] = list(dataset_root.glob("**/*.BMP")) + list(dataset_root.glob("**/*.bmp"))
    records: List[VoterRecord] = []
    for idx, img in enumerate(sorted(image_files)):
        if idx >= max_records:
            break
        stem = img.stem.replace(" ", "_")
        subject_id = parse_subject_id(img)
        voter_id = f"voter_{stem}"
        records.append(VoterRecord(voter_id=voter_id, image_path=img, subject_id=subject_id))

    if not records:
        raise ValueError("No BMP files discovered under dataset root.")
    return records


def get_record_by_voter_id(records: List[VoterRecord], voter_id: str) -> Optional[VoterRecord]:
    for record in records:
        if record.voter_id == voter_id:
            return record
    return None
