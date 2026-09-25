"""Regenerate MANIFEST.csv: every file of the repository with its size and SHA-256."""
import csv
import hashlib

from common import ROOT

SKIP = {"__pycache__", ".git", ".pbi"}


def main():
    rows = []
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and not SKIP & set(p.parts) and p.name != "MANIFEST.csv":
            rows.append([p.relative_to(ROOT).as_posix(), p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()])
    with open(ROOT / "MANIFEST.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path", "size_bytes", "sha256"])
        w.writerows(rows)
    print(f"MANIFEST.csv: {len(rows)} files")


if __name__ == "__main__":
    main()
