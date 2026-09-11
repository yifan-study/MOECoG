# MOECoG leaderboard

Generated 2026-09-10 from `results/*.csv` at commit `80ebcee` by `scripts/build_leaderboard.py`. Values are mean ± sd over subjects of the per-subject fold mean. Headline metrics: kappa (trials), Pearson r (kinematics). Chronological folds unless noted; see `docs/baselines.md` for protocol details.

## BCICompIII-1

| evaluation | session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|---|
| cross_session | test | HighGamma + LDA | 1 | 0.000 ± 0.000 | 0.500 ± 0.000 | 0.500 ± 0.000 | chronological, leave_one_session_out |
| cross_session | test | LogBandPower + LDA | 1 | 0.180 ± 0.000 | 0.590 ± 0.000 | 0.590 ± 0.000 | chronological, leave_one_session_out |
| cross_session | test | LogBandPower + LogReg | 1 | 0.040 ± 0.000 | 0.520 ± 0.000 | 0.520 ± 0.000 | chronological, leave_one_session_out |
| cross_session | test | Riemann TS + LogReg | 1 | 0.520 ± 0.000 | 0.760 ± 0.000 | 0.760 ± 0.000 | chronological, leave_one_session_out |
| cross_session | train | HighGamma + LDA | 1 | 0.000 ± 0.000 | 0.500 ± 0.000 | 0.500 ± 0.000 | chronological, leave_one_session_out |
| cross_session | train | LogBandPower + LDA | 1 | 0.532 ± 0.000 | 0.766 ± 0.000 | 0.766 ± 0.000 | chronological, leave_one_session_out |
| cross_session | train | LogBandPower + LogReg | 1 | 0.446 ± 0.000 | 0.723 ± 0.000 | 0.723 ± 0.000 | chronological, leave_one_session_out |
| cross_session | train | Riemann TS + LogReg | 1 | 0.576 ± 0.000 | 0.788 ± 0.000 | 0.788 ± 0.000 | chronological, leave_one_session_out |
| within_subject | test | HighGamma + LDA | 1 | 0.811 ± 0.000 | 0.910 ± 0.000 | 0.906 ± 0.000 | chronological, leave_one_session_out |
| within_subject | test | LogBandPower + LDA | 1 | 0.855 ± 0.000 | 0.930 ± 0.000 | 0.927 ± 0.000 | chronological, leave_one_session_out |
| within_subject | test | LogBandPower + LogReg | 1 | 0.836 ± 0.000 | 0.920 ± 0.000 | 0.919 ± 0.000 | chronological, leave_one_session_out |
| within_subject | test | Riemann TS + LogReg | 1 | 0.835 ± 0.000 | 0.920 ± 0.000 | 0.923 ± 0.000 | chronological, leave_one_session_out |
| within_subject | train | HighGamma + LDA | 1 | 0.507 ± 0.000 | 0.755 ± 0.000 | 0.754 ± 0.000 | chronological, leave_one_session_out |
| within_subject | train | LogBandPower + LDA | 1 | 0.747 ± 0.000 | 0.874 ± 0.000 | 0.875 ± 0.000 | chronological, leave_one_session_out |
| within_subject | train | LogBandPower + LogReg | 1 | 0.746 ± 0.000 | 0.874 ± 0.000 | 0.873 ± 0.000 | chronological, leave_one_session_out |
| within_subject | train | Riemann TS + LogReg | 1 | 0.811 ± 0.000 | 0.906 ± 0.000 | 0.905 ± 0.000 | chronological, leave_one_session_out |

## Miller2019-faces_basic

| evaluation | session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|---|
| within_subject | faceshouses | HighGamma + LDA | 14 | 0.638 ± 0.253 | 0.818 ± 0.128 | 0.820 ± 0.125 | chronological |
| within_subject | faceshouses | LogBandPower + LDA | 14 | 0.682 ± 0.251 | 0.841 ± 0.126 | 0.841 ± 0.124 | chronological |
| within_subject | faceshouses | LogBandPower + LogReg | 14 | 0.667 ± 0.249 | 0.834 ± 0.125 | 0.834 ± 0.124 | chronological |
| within_subject | faceshouses | Riemann TS + LogReg | 14 | 0.608 ± 0.252 | 0.804 ± 0.127 | 0.805 ± 0.126 | chronological |

## Miller2019-fingerflex

| evaluation | session | pipeline | n | pearson_r | r2 | folds |
|---|---|---|---|---|---|---|
| within_subject | 0 | HighGamma + Ridge | 9 | 0.283 ± 0.074 | -0.139 ± 0.343 | chronological |
| within_subject | 0 | LogBandPower + Ridge | 9 | 0.265 ± 0.079 | -0.207 ± 0.353 | chronological |

## Miller2019-gestures

| evaluation | session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|---|
| within_subject | fingerflex | HighGamma + LDA | 3 | 0.334 ± 0.329 | 0.466 ± 0.266 | 0.497 ± 0.251 | chronological |
| within_subject | fingerflex | LogBandPower + LDA | 3 | 0.287 ± 0.244 | 0.428 ± 0.199 | 0.451 ± 0.197 | chronological |
| within_subject | fingerflex | LogBandPower + LogReg | 3 | 0.252 ± 0.193 | 0.403 ± 0.155 | 0.421 ± 0.154 | chronological |
| within_subject | fingerflex | Riemann TS + LogReg | 3 | 0.080 ± 0.089 | 0.254 ± 0.067 | 0.265 ± 0.091 | chronological |
| within_subject | glovefingersgrasp | HighGamma + LDA | 1 | 0.292 ± 0.000 | 0.411 ± 0.000 | 0.369 ± 0.000 | chronological |
| within_subject | glovefingersgrasp | LogBandPower + LDA | 1 | 0.287 ± 0.000 | 0.411 ± 0.000 | 0.349 ± 0.000 | chronological |
| within_subject | glovefingersgrasp | LogBandPower + LogReg | 1 | 0.256 ± 0.000 | 0.383 ± 0.000 | 0.332 ± 0.000 | chronological |
| within_subject | glovefingersgrasp | Riemann TS + LogReg | 1 | 0.111 ± 0.000 | 0.289 ± 0.000 | 0.223 ± 0.000 | chronological |
| within_subject | mot_TH | HighGamma + LDA | 1 | 0.793 ± 0.000 | 0.900 ± 0.000 | 0.898 ± 0.000 | chronological |
| within_subject | mot_TH | LogBandPower + LDA | 1 | 0.797 ± 0.000 | 0.900 ± 0.000 | 0.898 ± 0.000 | chronological |
| within_subject | mot_TH | LogBandPower + LogReg | 1 | 0.797 ± 0.000 | 0.900 ± 0.000 | 0.898 ± 0.000 | chronological |
| within_subject | mot_TH | Riemann TS + LogReg | 1 | 0.788 ± 0.000 | 0.900 ± 0.000 | 0.894 ± 0.000 | chronological |
| within_subject | rh_lh | HighGamma + LDA | 1 | 0.635 ± 0.000 | 0.768 ± 0.000 | 0.776 ± 0.000 | chronological |
| within_subject | rh_lh | LogBandPower + LDA | 1 | 0.631 ± 0.000 | 0.767 ± 0.000 | 0.761 ± 0.000 | chronological |
| within_subject | rh_lh | LogBandPower + LogReg | 1 | 0.628 ± 0.000 | 0.767 ± 0.000 | 0.761 ± 0.000 | chronological |
| within_subject | rh_lh | Riemann TS + LogReg | 1 | 0.144 ± 0.000 | 0.390 ± 0.000 | 0.451 ± 0.000 | chronological |
| within_subject | thumbfore | HighGamma + LDA | 2 | 0.580 ± 0.420 | 0.733 ± 0.267 | 0.800 ± 0.200 | chronological |
| within_subject | thumbfore | LogBandPower + LDA | 2 | 0.353 ± 0.613 | 0.658 ± 0.325 | 0.667 ± 0.317 | chronological |
| within_subject | thumbfore | LogBandPower + LogReg | 2 | 0.541 ± 0.361 | 0.742 ± 0.208 | 0.777 ± 0.177 | chronological |
| within_subject | thumbfore | Riemann TS + LogReg | 2 | 0.409 ± 0.249 | 0.683 ± 0.150 | 0.715 ± 0.115 | chronological |

## Miller2019-imagery_basic

| evaluation | session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|---|
| within_subject | im | HighGamma + LDA | 7 | 0.417 ± 0.193 | 0.710 ± 0.093 | 0.714 ± 0.096 | chronological |
| within_subject | im | LogBandPower + LDA | 7 | 0.449 ± 0.191 | 0.724 ± 0.099 | 0.730 ± 0.101 | chronological |
| within_subject | im | LogBandPower + LogReg | 7 | 0.405 ± 0.213 | 0.700 ± 0.109 | 0.708 ± 0.110 | chronological |
| within_subject | im | Riemann TS + LogReg | 7 | 0.221 ± 0.196 | 0.598 ± 0.100 | 0.618 ± 0.107 | chronological |
| within_subject | mot | HighGamma + LDA | 7 | 0.893 ± 0.111 | 0.948 ± 0.055 | 0.954 ± 0.048 | chronological |
| within_subject | mot | LogBandPower + LDA | 7 | 0.860 ± 0.089 | 0.931 ± 0.044 | 0.934 ± 0.043 | chronological |
| within_subject | mot | LogBandPower + LogReg | 7 | 0.812 ± 0.117 | 0.907 ± 0.058 | 0.913 ± 0.055 | chronological |
| within_subject | mot | Riemann TS + LogReg | 7 | 0.603 ± 0.234 | 0.793 ± 0.129 | 0.818 ± 0.109 | chronological |

## Miller2019-motor_basic

| evaluation | session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|---|
| within_subject | 0 | HighGamma + LDA | 19 | 0.877 ± 0.166 | 0.939 ± 0.085 | 0.944 ± 0.075 | chronological, stratified_fallback |
| within_subject | 0 | LogBandPower + LDA | 19 | 0.917 ± 0.091 | 0.960 ± 0.045 | 0.960 ± 0.044 | chronological, stratified_fallback |
| within_subject | 0 | LogBandPower + LogReg | 19 | 0.880 ± 0.125 | 0.942 ± 0.061 | 0.942 ± 0.062 | chronological, stratified_fallback |
| within_subject | 0 | Riemann TS + LogReg | 19 | 0.702 ± 0.248 | 0.846 ± 0.131 | 0.861 ± 0.118 | chronological, stratified_fallback |
| within_subject | 0 | ShallowFBCSPNet s0 | 14 | 0.380 ± 0.339 | 0.687 ± 0.172 | 0.696 ± 0.170 | chronological, stratified_fallback |

## How to add a row

Run `scripts/run_baseline.py` (or any script that writes the same columns) into `results/<experiment>_<paradigm>.csv`, then `python scripts/build_leaderboard.py` and commit both. External submissions: open a pull request with the CSV, the exact command, the package version and the random seeds.
