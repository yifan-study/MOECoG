#!/usr/bin/env python3
"""Inventory the Stanford/Miller ECoG library on disk.

Prints, per experiment, the file layout, every ``.mat`` variable with dtype,
shape and value range, and per-file trial-block statistics of the cue-code
channel. This is the script behind ``docs/miller_library_map.md`` and the
registry in ``moecog/datasets/miller_library.py``; rerun it when a new library
revision is released to spot layout changes.

Usage::

    python scripts/inventory_miller_library.py --root /path/to/library [-e motor_basic ...]

Requires only numpy and scipy (h5py for v7.3 files).
"""

from __future__ import annotations

import argparse
import glob
import os
import warnings

import numpy as np
import scipy.io as sio

ALL_EXPERIMENTS = [
    "fingerflex", "joystick_track", "mouse_track", "motor_basic", "imagery_basic",
    "imagery_feedback", "gestures", "faces_basic", "faces_noise", "memory_nback",
    "visual_search", "speech_basic", "speech_lists", "fixation_PAC", "fixation_pwrlaw",
    "fixation_highfreq",
]
CODE_VARS = ("stim", "StimulusCode", "TargetCode", "cues", "cue", "target", "task")


def describe(v, depth=0, maxdepth=2):
    pad = "    " * depth
    if isinstance(v, np.ndarray):
        if v.dtype.names:
            out = [f"struct{v.shape} fields={list(v.dtype.names)}"]
            if depth < maxdepth and v.size > 0:
                el = v.flat[0]
                for name in v.dtype.names[:40]:
                    out.append(f"{pad}  .{name}: " + describe(el[name], depth + 1, maxdepth))
            return "\n".join(out)
        if v.dtype == object:
            s = f"cell{v.shape}"
            if v.size and depth < maxdepth:
                s += " first=" + describe(v.flat[0], depth + 1, maxdepth)[:120]
            return s
        s = f"{v.dtype}{v.shape}"
        if v.size and np.issubdtype(v.dtype, np.number):
            u = np.unique(v)
            if u.size <= 40:
                s += f" unique={u.tolist()}"
            else:
                s += f" min={v.min()} max={v.max()} nuniq={u.size}"
        elif v.dtype.kind in "US" and v.size <= 5:
            s += f" val={v.tolist()!r}"[:120]
        return s
    return repr(v)[:120]


def blocks(codes):
    """{code: (n_blocks, median_len, min_len, max_len)} of constant-code runs."""
    codes = np.asarray(codes).ravel().astype(int)
    change = np.flatnonzero(np.diff(codes) != 0) + 1
    starts, ends = np.r_[0, change], np.r_[change, len(codes)]
    out: dict[int, list[int]] = {}
    for s, e in zip(starts, ends):
        out.setdefault(int(codes[s]), []).append(int(e - s))
    return {c: (len(v), int(np.median(v)), min(v), max(v)) for c, v in sorted(out.items())}


def inventory_file(path, root):
    print(f"\n=== {os.path.relpath(path, root)}  ({os.path.getsize(path) / 1e6:.1f} MB)")
    try:
        m = sio.loadmat(path, squeeze_me=False, struct_as_record=True)
    except NotImplementedError:
        import h5py

        with h5py.File(path, "r") as f:
            def show(name, obj):
                if isinstance(obj, h5py.Dataset):
                    print(f"  {name}: {obj.dtype}{obj.shape}")

            f.visititems(show)
        return
    except Exception as ex:  # noqa: BLE001
        print("  ERROR", repr(ex)[:200])
        return
    for k, v in m.items():
        if k.startswith("__"):
            continue
        print(f"  {k}: " + describe(v))
    for var in CODE_VARS:
        if var in m and np.asarray(m[var]).size > 100:
            b = blocks(m[var])
            if len(b) <= 12:
                print(f"  blocks[{var}] code:(n, median, min, max) = {b}")
            else:
                nz = np.asarray(m[var]).ravel().astype(int)
                print(f"  blocks[{var}] (nonzero collapsed) = {blocks(nz > 0)}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", required=True, help="directory with the extracted experiment folders")
    ap.add_argument("-e", "--experiments", nargs="*", default=ALL_EXPERIMENTS)
    ap.add_argument("--max-per-dir", type=int, default=0, help="cap files per subfolder (0 = all)")
    args = ap.parse_args()
    warnings.filterwarnings("ignore")
    for ex in args.experiments:
        exdir = os.path.join(args.root, ex)
        print(f"\n\n################ {ex}")
        if not os.path.isdir(exdir):
            print("  MISSING")
            continue
        for d in sorted(glob.glob(os.path.join(exdir, "**/"), recursive=True)):
            if "__MACOSX" in d:
                continue
            n = len([f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))])
            print(f"  {os.path.relpath(d, exdir)}/ ({n} files)")
        files = [f for f in sorted(glob.glob(os.path.join(exdir, "**/*.mat"), recursive=True))
                 if "__MACOSX" not in f and "/brains/" not in f]
        if args.max_per_dir:
            seen: dict[str, int] = {}
            keep = []
            for f in files:
                d = os.path.dirname(f)
                if seen.get(d, 0) < args.max_per_dir:
                    keep.append(f)
                    seen[d] = seen.get(d, 0) + 1
            files = keep
        for f in files:
            inventory_file(f, args.root)


if __name__ == "__main__":
    main()
