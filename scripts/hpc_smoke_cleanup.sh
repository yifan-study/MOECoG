#!/bin/bash
# Re-run every HPC smoke id that is not yet ok (plus the three ids that were first run on the Mac side).
# Submit with --mem=100G: the RAM ds0055xx subjects hold several hour-long 1 kHz runs and even two runs
# per session need ~30 GB once filtered and epoched, hence --max-runs 2.
export MOECOG_DATA_DIR=/mnt/archive/home/yyu2024/moecog_data
export MOECOG_MILLER_DIR=/mnt/archive/home/yyu2024/PLaCT_data
cd ~/PLaCT/MOECoG || exit 1
~/moecog-venv/bin/python scripts/smoke_test.py --ids $(tr "\n" " " < scripts/hpc_ids.txt) ds002799 rogers-uecog ds003688 \
    --out results/smoke --skip-done --max-runs 2
