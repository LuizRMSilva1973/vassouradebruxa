#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

import duckdb  # type: ignore
import pandas as pd  # type: ignore


def load_csv_optional(path: Path) -> pd.DataFrame | None:
    if path.exists() and path.stat().st_size > 0:
        return pd.read_csv(path)
    return None


def main():
    ap = argparse.ArgumentParser(description="Load docking CSVs into DuckDB using schema.sql")
    ap.add_argument("--db", default="data/results.duckdb", help="DuckDB file path")
    ap.add_argument("--schema", default="schema.sql", help="SQL schema file")
    args = ap.parse_args()

    dbp = Path(args.db)
    dbp.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(dbp))
    with open(args.schema, "r", encoding="utf-8") as f:
        con.execute(f.read())

    files = {
        "summary_affinities": Path("docking_results/summary_affinities.csv"),
        "summary_ddg": Path("docking_results/summary_ddg.csv"),
        "scored": Path("docking_results/scored.csv"),
        "ranking_overall": Path("docking_results/ranking_overall.csv"),
        "ligand_selectivity_summary": Path("docking_results/ligand_selectivity_summary.csv"),
    }

    for table, path in files.items():
        df = load_csv_optional(path)
        if df is None:
            print(f"[SKIP] {table}: missing or empty {path}")
            continue
        # Create a temp view and insert-replace
        con.register("tmp_df", df)
        # Replace contents
        con.execute(f"DELETE FROM {table}")
        con.execute(f"INSERT INTO {table} SELECT * FROM tmp_df")
        print(f"[OK] Loaded {len(df)} rows into {table}")

    con.close()
    print(f"[DONE] DuckDB updated at {dbp}")


if __name__ == "__main__":
    main()

