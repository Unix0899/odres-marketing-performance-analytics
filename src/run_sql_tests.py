"""
Execute every statement of sql/03..07 and tests/integrity_tests.sql against the database.

- analysis files: each statement must run without error and return rows
- integrity tests: each statement must return failures = 0
Writes data/processed/sql_run_log.csv. Exit code 1 on any error or failed test.
"""
import re
import sqlite3
import time

import pandas as pd

from common import DB, PROCESSED, ROOT, SQL, get_logger

log = get_logger("sql-tests")
ANALYSIS_FILES = ["03_data_quality.sql", "04_kpi_queries.sql", "05_campaign_analysis.sql",
                  "06_funnel_analysis.sql", "07_revenue_analysis.sql"]


def statements(path):
    """Split a SQL file into statements, keeping the preceding comment as a label."""
    buf, label = "", ""
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"--\s*(Q[\w+\-]+\.?.*)", line.strip())
        if m and not buf.strip():
            label = m.group(1)[:70]
        buf += line + "\n"
        if sqlite3.complete_statement(buf):
            if re.sub(r"--.*", "", buf).strip():
                yield label, buf
            buf, label = "", ""


def main():
    conn = sqlite3.connect(DB)
    rows, errors = [], 0
    for name in ANALYSIS_FILES:
        for i, (label, sql) in enumerate(statements(SQL / name), 1):
            t = time.perf_counter()
            try:
                result = conn.execute(sql).fetchall()
                ok = len(result) > 0
                status = "PASS" if ok else "EMPTY"
            except sqlite3.Error as e:
                result, status = [], f"ERROR: {e}"
            errors += status != "PASS"
            rows.append({"file": name, "statement": i, "label": label, "rows_returned": len(result),
                         "ms": round(1000 * (time.perf_counter() - t), 1), "status": status})
            if status != "PASS":
                log.error(f"{name} #{i} {label}: {status}")
        log.info(f"{name:<26} {sum(r['file'] == name for r in rows):>2} statements executed")

    for i, (label, sql) in enumerate(statements(ROOT / "tests" / "integrity_tests.sql"), 1):
        test, failures = conn.execute(sql).fetchone()
        status = "PASS" if failures == 0 else "FAIL"
        errors += status == "FAIL"
        rows.append({"file": "integrity_tests.sql", "statement": i, "label": test, "rows_returned": 1,
                     "ms": 0, "status": status if failures == 0 else f"FAIL ({failures})"})
        log.info(f"[{status}] {test} (failures={failures})")
    conn.close()

    pd.DataFrame(rows).to_csv(PROCESSED / "sql_run_log.csv", index=False)
    if errors:
        raise SystemExit(f"{errors} SQL statement(s) failed")
    log.info(f"all {len(rows)} SQL statements and tests PASS")


if __name__ == "__main__":
    main()
