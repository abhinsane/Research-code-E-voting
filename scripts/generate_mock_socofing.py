from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/SOCOFing_mock"))
    parser.add_argument("--samples", type=int, default=40)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    for i in range(args.samples):
        file = args.out / f"{i+1:03d}__Left_index_finger.BMP"
        file.write_bytes((f"mock-fingerprint-{i}" * 20).encode())

    print(f"Generated {args.samples} mock BMP files at {args.out}")


if __name__ == "__main__":
    main()
