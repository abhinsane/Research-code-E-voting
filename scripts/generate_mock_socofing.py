from __future__ import annotations

import argparse
from pathlib import Path


FINGERS = ["Left_index_finger", "Right_index_finger"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/SOCOFing_mock"))
    parser.add_argument("--samples", type=int, default=40)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    subjects = max(1, args.samples // 2)
    written = 0
    for sid in range(1, subjects + 1):
        for finger in FINGERS:
            if written >= args.samples:
                break
            file = args.out / f"{sid:03d}__{finger}.BMP"
            file.write_bytes((f"mock-fingerprint-subject-{sid}-{finger}" * 20).encode())
            written += 1

    print(f"Generated {written} mock BMP files at {args.out}")


if __name__ == "__main__":
    main()
