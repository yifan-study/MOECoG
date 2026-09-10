# MOECoG leaderboard

Generated 2026-09-09 from `results/*.csv` at commit `abd9491` by `scripts/build_leaderboard.py`. Values are mean ± sd over subjects of the per-subject fold mean. Headline metrics: kappa (trials), Pearson r (kinematics). Chronological folds unless noted; see `docs/baselines.md` for protocol details.

## Miller2019-faces_basic

| session | pipeline | n | kappa | accuracy | balanced_accuracy | pearson_r | r2 | folds |
|---|---|---|---|---|---|---|---|---|
| faceshouses | HighGamma+LDA | 14 | 0.638 ± 0.253 | 0.818 ± 0.128 | 0.820 ± 0.125 | nan | nan | chronological |
| faceshouses | LogBandPower+LDA | 14 | 0.682 ± 0.251 | 0.841 ± 0.126 | 0.841 ± 0.124 | nan | nan | chronological |

## Miller2019-fingerflex

| session | pipeline | n | kappa | accuracy | balanced_accuracy | pearson_r | r2 | folds |
|---|---|---|---|---|---|---|---|---|
| 0 | HighGamma+Ridge | 9 | nan | nan | nan | 0.283 ± 0.074 | -0.139 ± 0.343 | chronological |
| 0 | LogBandPower+Ridge | 9 | nan | nan | nan | 0.265 ± 0.079 | -0.207 ± 0.353 | chronological |

## Miller2019-imagery_basic

| session | pipeline | n | kappa | accuracy | balanced_accuracy | pearson_r | r2 | folds |
|---|---|---|---|---|---|---|---|---|
| im | HighGamma+LDA | 7 | 0.417 ± 0.193 | 0.710 ± 0.093 | 0.714 ± 0.096 | nan | nan | chronological |
| im | LogBandPower+LDA | 7 | 0.449 ± 0.191 | 0.724 ± 0.099 | 0.730 ± 0.101 | nan | nan | chronological |
| mot | HighGamma+LDA | 7 | 0.893 ± 0.111 | 0.948 ± 0.055 | 0.954 ± 0.048 | nan | nan | chronological |
| mot | LogBandPower+LDA | 7 | 0.860 ± 0.089 | 0.931 ± 0.044 | 0.934 ± 0.043 | nan | nan | chronological |

## Miller2019-motor_basic

| session | pipeline | n | kappa | accuracy | balanced_accuracy | pearson_r | r2 | folds |
|---|---|---|---|---|---|---|---|---|
| 0 | HighGamma+LDA | 19 | 0.877 ± 0.166 | 0.939 ± 0.085 | 0.944 ± 0.075 | nan | nan | chronological, stratified_fallback |
| 0 | LogBandPower+LDA | 19 | 0.917 ± 0.091 | 0.960 ± 0.045 | 0.960 ± 0.044 | nan | nan | chronological, stratified_fallback |

## How to add a row

Run `scripts/run_baseline.py` (or any script that writes the same columns) into `results/<experiment>_<paradigm>.csv`, then `python scripts/build_leaderboard.py` and commit both. External submissions: open a pull request with the CSV, the exact command, the package version and the random seeds.
