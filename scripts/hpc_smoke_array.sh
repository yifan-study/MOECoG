#!/bin/bash
# SLURM array over scripts/hpc_ids.txt: one catalog entry per task.
export MOECOG_DATA_DIR=/mnt/archive/home/yyu2024/moecog_data
export MOECOG_MILLER_DIR=/mnt/archive/home/yyu2024/PLaCT_data
cd ~/PLaCT/MOECoG || exit 1
mapfile -t IDS < scripts/hpc_ids.txt
ID=${IDS[$SLURM_ARRAY_TASK_ID]}
echo "task $SLURM_ARRAY_TASK_ID -> $ID on $(hostname)"
~/moecog-venv/bin/python scripts/smoke_test.py --ids "$ID" --out results/smoke --skip-done
