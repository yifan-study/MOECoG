# MOECoG leaderboard

Generated 2026-09-09 from `results/*.csv` at commit `4dd3328` by `scripts/build_leaderboard.py`. Values are mean ± sd over subjects of the per-subject fold mean. Headline metrics: kappa (trials), Pearson r (kinematics). Chronological folds unless noted; see `docs/baselines.md` for protocol details.

## Miller2019-faces_basic

| session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|
| faceshouses | HighGamma+LDA | 14 | 0.638 ± 0.253 | 0.818 ± 0.128 | 0.820 ± 0.125 | chronological (legacy) |
| faceshouses | LogBandPower+LDA | 14 | 0.682 ± 0.251 | 0.841 ± 0.126 | 0.841 ± 0.124 | chronological (legacy) |

## Miller2019-imagery_basic

| session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|
| im | HighGamma+LDA | 7 | 0.417 ± 0.193 | 0.710 ± 0.093 | 0.714 ± 0.096 | chronological (legacy) |
| mot | HighGamma+LDA | 7 | 0.893 ± 0.111 | 0.948 ± 0.055 | 0.954 ± 0.048 | chronological (legacy) |

## Miller2019-motor_basic

| session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|
| 0 | HighGamma+LDA | 19 | 0.866 ± 0.171 | 0.937 ± 0.085 | 0.943 ± 0.075 | chronological (legacy) |
| 0 | LogBandPower+LDA | 19 | 0.903 ± 0.117 | 0.956 ± 0.049 | 0.958 ± 0.047 | chronological (legacy) |

## How to add a row

Run `scripts/run_baseline.py` (or any script that writes the same columns) into `results/<experiment>_<paradigm>.csv`, then `python scripts/build_leaderboard.py` and commit both. External submissions: open a pull request with the CSV, the exact command, the package version and the random seeds.
