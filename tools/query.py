#!/usr/bin/env python3
import argparse
from pathlib import Path

import duckdb  # type: ignore


def run_sql(db: Path, sql: str):
    con = duckdb.connect(str(db))
    try:
        res = con.execute(sql).fetchdf()
        print(res.to_string(index=False))
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser(description="Quick DuckDB queries over docking results")
    ap.add_argument("--db", default="data/results.duckdb")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_top = sub.add_parser("top", help="Top ligands by score")
    p_top.add_argument("-n", "--limit", type=int, default=10)

    p_tgt = sub.add_parser("target", help="Top ligands for a target")
    p_tgt.add_argument("name")
    p_tgt.add_argument("-n", "--limit", type=int, default=10)

    p_sql = sub.add_parser("sql", help="Run arbitrary SQL")
    p_sql.add_argument("query")

    args = ap.parse_args()
    db = Path(args.db)

    if args.cmd == "top":
        sql = f"SELECT ligand, target, score, xymove, best_affinity_kcal_per_mol AS dg FROM scored ORDER BY score DESC NULLS LAST LIMIT {args.limit}"
        run_sql(db, sql)
    elif args.cmd == "target":
        sql = (
            "SELECT ligand, score, xymove, best_affinity_kcal_per_mol AS dg "
            f"FROM scored WHERE target = '{args.name}' ORDER BY score DESC NULLS LAST LIMIT {args.limit}"
        )
        run_sql(db, sql)
    elif args.cmd == "sql":
        run_sql(db, args.query)


if __name__ == "__main__":
    main()

