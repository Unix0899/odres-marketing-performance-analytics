"""
Load the clean layer into a fresh SQLite database.

1. create the schema (sql/01_schema.sql: keys + business-rule CHECK constraints)
2. insert the clean tables in dependency order, with foreign keys enforced
3. create the reporting views (sql/02_views.sql)
4. write the full SQL dump (sql/odres_full_database_dump.sql)
"""
import sqlite3

import pandas as pd

from common import CLEAN, DB, DISCLOSURE, SQL, get_logger

log = get_logger("load")

LOAD_ORDER = ["dim_date", "dim_channel", "dim_campaign", "dim_region", "fact_marketing_daily", "fact_leads",
              "fact_opportunities", "dim_customer", "fact_customer_monthly"]


def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()                                   # the database is a build artefact: rebuilt every run
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript((SQL / "01_schema.sql").read_text(encoding="utf-8"))

    for table in LOAD_ORDER:
        df = pd.read_csv(CLEAN / f"{table}.csv")
        df = df.astype(object).where(df.notna(), None)          # NaN -> NULL
        cols = ", ".join(df.columns)
        marks = ", ".join("?" * len(df.columns))
        conn.executemany(f"INSERT INTO {table} ({cols}) VALUES ({marks})", df.itertuples(index=False, name=None))
        log.info(f"{table:<22} {len(df):>6,} rows loaded")
    conn.commit()

    fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_errors:
        raise SystemExit(f"foreign key violations: {fk_errors[:5]}")
    conn.executescript((SQL / "02_views.sql").read_text(encoding="utf-8"))
    views = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")]
    log.info(f"views created: {', '.join(views)}")

    with open(SQL / "odres_full_database_dump.sql", "w", encoding="utf-8") as f:
        f.write(f"-- ODRES synthetic portfolio database dump\n-- {DISCLOSURE}\n-- No real ODRES data.\n\n")
        for line in conn.iterdump():
            f.write(line + "\n")
    conn.close()
    log.info(f"database ready: {DB.name} ({DB.stat().st_size / 1024:,.0f} KB) + full dump")


if __name__ == "__main__":
    main()
