"""Validate the frozen M5 scope and emit a metadata-only preparation manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.data.m5_ca1_foods import build_preparation_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=REPOSITORY_ROOT / "data/raw/m5")
    parser.add_argument("--config", type=Path, default=REPOSITORY_ROOT / "configs/data/m5_ca1_foods.yaml")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "data/manifests/m5_ca1_foods_preparation_manifest.json",
    )
    args = parser.parse_args()
    manifest = build_preparation_manifest(args.raw_dir, args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Validated {manifest['scope']['item_store_series']} frozen CA_1/FOODS series.")
    print(f"Wrote metadata-only preparation manifest: {args.output}")
    print("Test sales values were not read.")


if __name__ == "__main__":
    main()
