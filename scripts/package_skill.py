#!/usr/bin/env python3
"""Build a portable ZIP from manifest.txt without packaging ignored files."""
import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "northstar.zip")
    args = parser.parse_args()
    files = [line.strip() for line in (ROOT / "manifest.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    missing = [path for path in files if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("manifest files missing: " + ", ".join(missing))
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(ROOT / path, Path("northstar") / path)
    print(args.output)

if __name__ == "__main__":
    main()
