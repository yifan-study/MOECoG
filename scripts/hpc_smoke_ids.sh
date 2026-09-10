#!/bin/bash
# Run the smoke test for the ids given as arguments (data expected on the archive).
export MOECOG_DATA_DIR=/mnt/archive/home/yyu2024/moecog_data
export MOECOG_MILLER_DIR=/mnt/archive/home/yyu2024/PLaCT_data
cd ~/PLaCT/MOECoG || exit 1
~/moecog-venv/bin/python scripts/smoke_test.py --ids "$@" --out results/smoke --skip-done
