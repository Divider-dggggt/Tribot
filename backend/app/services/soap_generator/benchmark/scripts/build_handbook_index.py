#!/usr/bin/env python3
from __future__ import annotations

import argparse

from benchmark.handbook_index import build_handbook_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a retrievable local handbook index from the ETEK PDF.")
    parser.add_argument("--pdf", required=True, help="Path to handbook PDF.")
    parser.add_argument("--out_dir", required=True, help="Output index directory.")
    args = parser.parse_args()

    outputs = build_handbook_index(pdf_path=args.pdf, out_dir=args.out_dir)
    print("Handbook index written:")
    for k, v in outputs.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
