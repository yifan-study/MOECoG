#!/usr/bin/env python3
"""Merge result CSVs computed elsewhere into the repository's stores.

    python scripts/merge_results.py results/reference_motor_basic.csv /path/from/cluster/reference_motor_basic.csv
    python scripts/merge_results.py --replace results/reference_motor_basic.csv other.csv

Rows are matched on (dataset, subject, session, pipeline, paradigm, evaluation); by default only combinations
the target has not computed are added, ``--replace`` lets the incoming rows win.
"""

from __future__ import annotations

import argparse

from moecog.analysis import ResultsStore


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="store CSV to update (created if missing)")
    ap.add_argument("sources", nargs="+", help="CSVs to merge in")
    ap.add_argument("--replace", action="store_true")
    args = ap.parse_args()
    store = ResultsStore(args.target)
    for src in args.sources:
        added = store.merge_from(src, replace=args.replace)
        print(f"{src}: {len(added)} rows {'replaced/added' if args.replace else 'added'}")
    print(f"{args.target}: {len(store.to_dataframe())} rows")


if __name__ == "__main__":
    main()
