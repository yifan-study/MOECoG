# MOECoG leaderboard

Generated 2026-09-11 from `results/*.csv` at commit `3f00dbc` by `scripts/build_leaderboard.py`. Values are mean ± sd over subjects of the per-subject fold mean. Headline metrics: kappa (trials), Pearson r (kinematics). Chronological folds unless noted; see `docs/baselines.md` for protocol details.

## BCICompIII-1

| evaluation | session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|---|
| cross_session | test | HighGamma + LDA | 1 | 0.000 ± 0.000 | 0.500 ± 0.000 | 0.500 ± 0.000 | chronological, leave_one_session_out |
| cross_session | test | LogBandPower + LDA | 1 | 0.180 ± 0.000 | 0.590 ± 0.000 | 0.590 ± 0.000 | chronological, leave_one_session_out |
| cross_session | test | LogBandPower + LogReg | 1 | 0.040 ± 0.000 | 0.520 ± 0.000 | 0.520 ± 0.000 | chronological, leave_one_session_out |
| cross_session | test | Riemann HG TS + LogReg | 1 | 0.360 ± 0.000 | 0.680 ± 0.000 | 0.680 ± 0.000 | chronological, leave_one_session_out |
| cross_session | test | Riemann TS + LogReg | 1 | 0.520 ± 0.000 | 0.760 ± 0.000 | 0.760 ± 0.000 | chronological, leave_one_session_out |
| cross_session | train | HighGamma + LDA | 1 | 0.000 ± 0.000 | 0.500 ± 0.000 | 0.500 ± 0.000 | chronological, leave_one_session_out |
| cross_session | train | LogBandPower + LDA | 1 | 0.532 ± 0.000 | 0.766 ± 0.000 | 0.766 ± 0.000 | chronological, leave_one_session_out |
| cross_session | train | LogBandPower + LogReg | 1 | 0.446 ± 0.000 | 0.723 ± 0.000 | 0.723 ± 0.000 | chronological, leave_one_session_out |
| cross_session | train | Riemann HG TS + LogReg | 1 | 0.000 ± 0.000 | 0.500 ± 0.000 | 0.500 ± 0.000 | chronological, leave_one_session_out |
| cross_session | train | Riemann TS + LogReg | 1 | 0.576 ± 0.000 | 0.788 ± 0.000 | 0.788 ± 0.000 | chronological, leave_one_session_out |
| within_subject | test | HighGamma + LDA | 1 | 0.811 ± 0.000 | 0.910 ± 0.000 | 0.906 ± 0.000 | chronological, leave_one_session_out |
| within_subject | test | LogBandPower + LDA | 1 | 0.855 ± 0.000 | 0.930 ± 0.000 | 0.927 ± 0.000 | chronological, leave_one_session_out |
| within_subject | test | LogBandPower + LogReg | 1 | 0.836 ± 0.000 | 0.920 ± 0.000 | 0.919 ± 0.000 | chronological, leave_one_session_out |
| within_subject | test | Riemann HG TS + LogReg | 1 | 0.652 ± 0.000 | 0.830 ± 0.000 | 0.833 ± 0.000 | chronological, leave_one_session_out |
| within_subject | test | Riemann TS + LogReg | 1 | 0.835 ± 0.000 | 0.920 ± 0.000 | 0.923 ± 0.000 | chronological, leave_one_session_out |
| within_subject | train | HighGamma + LDA | 1 | 0.507 ± 0.000 | 0.755 ± 0.000 | 0.754 ± 0.000 | chronological, leave_one_session_out |
| within_subject | train | LogBandPower + LDA | 1 | 0.747 ± 0.000 | 0.874 ± 0.000 | 0.875 ± 0.000 | chronological, leave_one_session_out |
| within_subject | train | LogBandPower + LogReg | 1 | 0.746 ± 0.000 | 0.874 ± 0.000 | 0.873 ± 0.000 | chronological, leave_one_session_out |
| within_subject | train | Riemann HG TS + LogReg | 1 | 0.585 ± 0.000 | 0.795 ± 0.000 | 0.793 ± 0.000 | chronological, leave_one_session_out |
| within_subject | train | Riemann TS + LogReg | 1 | 0.811 ± 0.000 | 0.906 ± 0.000 | 0.905 ± 0.000 | chronological, leave_one_session_out |

## Miller2019-faces_basic

| evaluation | session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|---|
| within_subject | faceshouses | HighGamma + LDA | 14 | 0.638 ± 0.253 | 0.818 ± 0.128 | 0.820 ± 0.125 | chronological |
| within_subject | faceshouses | LogBandPower + LDA | 14 | 0.682 ± 0.251 | 0.841 ± 0.126 | 0.841 ± 0.124 | chronological |
| within_subject | faceshouses | LogBandPower + LogReg | 14 | 0.667 ± 0.249 | 0.834 ± 0.125 | 0.834 ± 0.124 | chronological |
| within_subject | faceshouses | Riemann HG TS + LogReg | 14 | 0.738 ± 0.220 | 0.869 ± 0.111 | 0.870 ± 0.109 | chronological |
| within_subject | faceshouses | Riemann TS + LogReg | 14 | 0.608 ± 0.252 | 0.804 ± 0.127 | 0.805 ± 0.126 | chronological |
| within_subject | faceshouses | ShallowFBCSPNet s0 | 14 | 0.763 ± 0.198 | 0.882 ± 0.099 | 0.882 ± 0.099 | chronological |
| within_subject | faceshouses | ShallowFBCSPNet s1 | 14 | 0.749 ± 0.203 | 0.875 ± 0.102 | 0.875 ± 0.101 | chronological |

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
| within_subject | fingerflex | Riemann HG TS + LogReg | 3 | 0.233 ± 0.245 | 0.383 ± 0.204 | 0.404 ± 0.209 | chronological |
| within_subject | fingerflex | Riemann TS + LogReg | 3 | 0.080 ± 0.089 | 0.254 ± 0.067 | 0.265 ± 0.091 | chronological |
| within_subject | fingerflex | ShallowFBCSPNet s0 | 3 | 0.078 ± 0.110 | 0.256 ± 0.093 | 0.253 ± 0.088 | chronological |
| within_subject | glovefingersgrasp | HighGamma + LDA | 1 | 0.292 ± 0.000 | 0.411 ± 0.000 | 0.369 ± 0.000 | chronological |
| within_subject | glovefingersgrasp | LogBandPower + LDA | 1 | 0.287 ± 0.000 | 0.411 ± 0.000 | 0.349 ± 0.000 | chronological |
| within_subject | glovefingersgrasp | LogBandPower + LogReg | 1 | 0.256 ± 0.000 | 0.383 ± 0.000 | 0.332 ± 0.000 | chronological |
| within_subject | glovefingersgrasp | Riemann HG TS + LogReg | 1 | 0.142 ± 0.000 | 0.311 ± 0.000 | 0.234 ± 0.000 | chronological |
| within_subject | glovefingersgrasp | Riemann TS + LogReg | 1 | 0.111 ± 0.000 | 0.289 ± 0.000 | 0.223 ± 0.000 | chronological |
| within_subject | glovefingersgrasp | ShallowFBCSPNet s0 | 1 | 0.044 ± 0.000 | 0.222 ± 0.000 | 0.172 ± 0.000 | chronological |
| within_subject | mot_TH | HighGamma + LDA | 1 | 0.793 ± 0.000 | 0.900 ± 0.000 | 0.898 ± 0.000 | chronological |
| within_subject | mot_TH | LogBandPower + LDA | 1 | 0.797 ± 0.000 | 0.900 ± 0.000 | 0.898 ± 0.000 | chronological |
| within_subject | mot_TH | LogBandPower + LogReg | 1 | 0.797 ± 0.000 | 0.900 ± 0.000 | 0.898 ± 0.000 | chronological |
| within_subject | mot_TH | Riemann HG TS + LogReg | 1 | 0.692 ± 0.000 | 0.850 ± 0.000 | 0.853 ± 0.000 | chronological |
| within_subject | mot_TH | Riemann TS + LogReg | 1 | 0.788 ± 0.000 | 0.900 ± 0.000 | 0.894 ± 0.000 | chronological |
| within_subject | mot_TH | ShallowFBCSPNet s0 | 1 | 0.156 ± 0.000 | 0.583 ± 0.000 | 0.582 ± 0.000 | chronological |
| within_subject | rh_lh | HighGamma + LDA | 1 | 0.635 ± 0.000 | 0.768 ± 0.000 | 0.776 ± 0.000 | chronological |
| within_subject | rh_lh | LogBandPower + LDA | 1 | 0.631 ± 0.000 | 0.767 ± 0.000 | 0.761 ± 0.000 | chronological |
| within_subject | rh_lh | LogBandPower + LogReg | 1 | 0.628 ± 0.000 | 0.767 ± 0.000 | 0.761 ± 0.000 | chronological |
| within_subject | rh_lh | Riemann HG TS + LogReg | 1 | 0.507 ± 0.000 | 0.674 ± 0.000 | 0.711 ± 0.000 | chronological |
| within_subject | rh_lh | Riemann TS + LogReg | 1 | 0.144 ± 0.000 | 0.390 ± 0.000 | 0.451 ± 0.000 | chronological |
| within_subject | rh_lh | ShallowFBCSPNet s0 | 1 | 0.246 ± 0.000 | 0.500 ± 0.000 | 0.515 ± 0.000 | chronological |
| within_subject | thumbfore | HighGamma + LDA | 2 | 0.580 ± 0.420 | 0.733 ± 0.267 | 0.800 ± 0.200 | chronological |
| within_subject | thumbfore | LogBandPower + LDA | 2 | 0.353 ± 0.613 | 0.658 ± 0.325 | 0.667 ± 0.317 | chronological |
| within_subject | thumbfore | LogBandPower + LogReg | 2 | 0.541 ± 0.361 | 0.742 ± 0.208 | 0.777 ± 0.177 | chronological |
| within_subject | thumbfore | Riemann HG TS + LogReg | 2 | 0.370 ± 0.630 | 0.633 ± 0.367 | 0.675 ± 0.325 | chronological |
| within_subject | thumbfore | Riemann TS + LogReg | 2 | 0.409 ± 0.249 | 0.683 ± 0.150 | 0.715 ± 0.115 | chronological |
| within_subject | thumbfore | ShallowFBCSPNet s0 | 2 | -0.114 ± 0.046 | 0.425 ± 0.025 | 0.433 ± 0.033 | chronological |

## Miller2019-imagery_basic

| evaluation | session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|---|
| within_subject | im | HighGamma + LDA | 7 | 0.417 ± 0.193 | 0.710 ± 0.093 | 0.714 ± 0.096 | chronological |
| within_subject | im | LogBandPower + LDA | 7 | 0.449 ± 0.191 | 0.724 ± 0.099 | 0.730 ± 0.101 | chronological |
| within_subject | im | LogBandPower + LogReg | 7 | 0.405 ± 0.213 | 0.700 ± 0.109 | 0.708 ± 0.110 | chronological |
| within_subject | im | Riemann HG TS + LogReg | 7 | 0.340 ± 0.277 | 0.671 ± 0.139 | 0.675 ± 0.145 | chronological |
| within_subject | im | Riemann TS + LogReg | 7 | 0.221 ± 0.196 | 0.598 ± 0.100 | 0.618 ± 0.107 | chronological |
| within_subject | im | ShallowFBCSPNet s0 | 7 | 0.051 ± 0.170 | 0.521 ± 0.091 | 0.530 ± 0.089 | chronological |
| within_subject | im | ShallowFBCSPNet s1 | 4 | 0.021 ± 0.089 | 0.508 ± 0.053 | 0.511 ± 0.047 | chronological |
| within_subject | mot | HighGamma + LDA | 7 | 0.893 ± 0.111 | 0.948 ± 0.055 | 0.954 ± 0.048 | chronological |
| within_subject | mot | LogBandPower + LDA | 7 | 0.860 ± 0.089 | 0.931 ± 0.044 | 0.934 ± 0.043 | chronological |
| within_subject | mot | LogBandPower + LogReg | 7 | 0.812 ± 0.117 | 0.907 ± 0.058 | 0.913 ± 0.055 | chronological |
| within_subject | mot | Riemann HG TS + LogReg | 7 | 0.898 ± 0.093 | 0.950 ± 0.045 | 0.956 ± 0.040 | chronological |
| within_subject | mot | Riemann TS + LogReg | 7 | 0.603 ± 0.234 | 0.793 ± 0.129 | 0.818 ± 0.109 | chronological |
| within_subject | mot | ShallowFBCSPNet s0 | 7 | 0.377 ± 0.376 | 0.669 ± 0.213 | 0.686 ± 0.204 | chronological |
| within_subject | mot | ShallowFBCSPNet s1 | 4 | 0.349 ± 0.243 | 0.675 ± 0.119 | 0.682 ± 0.131 | chronological |

## Miller2019-motor_basic

| evaluation | session | pipeline | n | kappa | accuracy | balanced_accuracy | folds |
|---|---|---|---|---|---|---|---|
| within_subject | 0 | HighGamma + LDA | 19 | 0.877 ± 0.166 | 0.939 ± 0.085 | 0.944 ± 0.075 | chronological, stratified_fallback |
| within_subject | 0 | LogBandPower + LDA | 19 | 0.917 ± 0.091 | 0.960 ± 0.045 | 0.960 ± 0.044 | chronological, stratified_fallback |
| within_subject | 0 | LogBandPower + LogReg | 19 | 0.880 ± 0.125 | 0.942 ± 0.061 | 0.942 ± 0.062 | chronological, stratified_fallback |
| within_subject | 0 | Riemann HG TS + LogReg | 19 | 0.936 ± 0.067 | 0.968 ± 0.033 | 0.971 ± 0.031 | chronological, stratified_fallback |
| within_subject | 0 | Riemann TS + LogReg | 19 | 0.702 ± 0.248 | 0.846 ± 0.131 | 0.861 ± 0.118 | chronological, stratified_fallback |
| within_subject | 0 | ShallowFBCSPNet s0 | 19 | 0.438 ± 0.361 | 0.718 ± 0.186 | 0.722 ± 0.183 | chronological, stratified_fallback |
| within_subject | 0 | ShallowFBCSPNet s1 | 19 | 0.449 ± 0.365 | 0.716 ± 0.196 | 0.727 ± 0.188 | chronological, stratified_fallback |

## How to add a row

Run `scripts/run_baseline.py` (or any script that writes the same columns) into `results/<experiment>_<paradigm>.csv`, then `python scripts/build_leaderboard.py` and commit both. External submissions: open a pull request with the CSV, the exact command, the package version and the random seeds.
