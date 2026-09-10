#!/usr/bin/env python3
"""Aggregate results/smoke/*.json into docs/smoke_tests.md."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/smoke")
    ap.add_argument("--out", default="docs/smoke_tests.md")
    args = ap.parse_args()
    from moecog.catalog import ENTRIES

    recs = {}
    for f in sorted(Path(args.results).glob("*.json")):
        recs[f.stem] = json.loads(f.read_text())
    rows, counts = [], {"ok": 0, "error": 0, "unsupported": 0, "blocked": 0, "pending": 0}
    for eid, e in ENTRIES.items():
        r = recs.get(eid)
        if e.blocked:
            # Entry.blocked is either a reason string or True with the reason carried in Entry.notes
            status, detail = "blocked", e.blocked if isinstance(e.blocked, str) else (e.notes or "blocked")
        elif r is None:
            status, detail = "pending", ""
        else:
            status = r.get("status", "error")
            if status == "ok":
                ses = r.get("sessions", {})
                first = next(iter(ses.values()), {})
                cls = first.get("classes", {})
                qb = r.get("quick_baseline") or {}
                if "score" in qb and qb["score"] != qb["score"]:  # NaN: every fold had a single-class test set
                    score = (f"{qb['metric']} undefined ({qb.get('n_undefined_folds', '?')}/{qb.get('n_folds', '?')} "
                             f"folds single-class, n={qb['n_trials']})")
                elif "score" in qb:
                    score = f"{qb['metric']} {qb['score']:.2f} (n={qb['n_trials']})"
                else:
                    score = qb.get("note", "")
                el = r.get("electrodes")
                el_s = f"{el['n']} ({el['frame']})" if isinstance(el, dict) else "none"
                detail = (f"{r.get('subjects_found')} subj; {len(ses)} file(s); {first.get('n_ecog')} ch @ "
                          f"{first.get('sfreq', 0):.0f} Hz; {first.get('duration_s', 0):.0f} s; "
                          f"{first.get('n_annotations')} events in {len(cls)} classes; electrodes {el_s}; {score}")
            else:
                detail = r.get("error", "")[:160]
        counts[status] = counts.get(status, 0) + 1
        rows.append((eid, e.source, e.title[:60], status, detail.replace("|", "/"), (r or {}).get("seconds", "")))
    lines = ["# Smoke tests of the catalog", "",
             f"Generated {dt.date.today().isoformat()} by `scripts/build_smoke_table.py` from `results/smoke/*.json`. "
             "Each entry downloads a one-subject (or one-file) subset, loads it through the MOECoG loader, "
             "reports what it found, and, when a trial-classification paradigm applies, scores "
             "LogBandPower+LDA with 3 chronological folds on the first subject. Numbers are sanity checks, "
             "not benchmark results.", "",
             "Status: " + ", ".join(f"{v} {k}" for k, v in counts.items()) + f" out of {len(rows)} entries.", "",
             "| entry | source | title | status | what was found / why not | s |", "|---|---|---|---|---|---|"]
    for eid, src, title, status, detail, sec in rows:
        lines.append(f"| {eid} | {src} | {title} | {status} | {detail} | {sec} |")
    Path(args.out).write_text("\n".join(lines) + "\n")
    print(f"wrote {args.out}: {counts}")


if __name__ == "__main__":
    main()
