"""
One command to rebuild everything from scratch:

    python run_pipeline.py

generate -> clean -> validate (raw vs clean) -> load SQLite -> reporting tables
-> Power BI exports + PBIP -> visuals -> SQL test suite -> manifest
"""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
STEPS = [
    ("Generate synthetic raw exports", "generate_synthetic_data.py"),
    ("Clean and conform", "clean_data.py"),
    ("Validate raw vs clean", "validate_data.py"),
    ("Load SQLite + views", "load_to_sqlite.py"),
    ("Build reporting tables", "build_reporting_tables.py"),
    ("Export Power BI tables", "export_powerbi_data.py"),
    ("Build Power BI project (TMDL) and DAX docs", "build_powerbi_project.py"),
    ("Draw technical proofs (database, SQL, model)", "make_visuals.py"),
    ("Build Power BI proofs from the report screenshots", "build_powerbi_proofs.py"),
    ("Run SQL files and integrity tests", "run_sql_tests.py"),
    ("Write MANIFEST.csv", "build_manifest.py"),
]

for i, (label, script) in enumerate(STEPS, 1):
    print(f"\n=== [{i}/{len(STEPS)}] {label} ({script})", flush=True)
    result = subprocess.run([sys.executable, script], cwd=SRC)
    if result.returncode != 0:
        sys.exit(f"Pipeline stopped at step {i}: {script} failed")
print("\nPipeline completed successfully.")
