# Reference benchmark analysis

Generated 2026-09-10 by `scripts/build_analysis.py` from `results/reference_*.csv`. Scores are per patient (mean over folds); tests are paired across patients (sign-flip permutation below 20 patients, Wilcoxon signed-rank otherwise, one-sided, combined with Stouffer weights); effect sizes are Cohen's d_z of the paired differences. See `docs/moabb_review.md`, section 7.

## bci_iii_1 (cross_session, kappa, 1 patients)

| pipeline | mean | sd | median | patients |
|---|---|---|---|---|
| Riemann TS + LogReg | 0.548 | nan | 0.548 | 1 |
| LogBandPower + LDA | 0.356 | nan | 0.356 | 1 |
| LogBandPower + LogReg | 0.243 | nan | 0.243 | 1 |
| HighGamma + LDA | 0.000 | nan | 0.000 | 1 |

## bci_iii_1 (within_subject, kappa, 1 patients)

| pipeline | mean | sd | median | patients |
|---|---|---|---|---|
| Riemann TS + LogReg | 0.823 | nan | 0.823 | 1 |
| LogBandPower + LDA | 0.801 | nan | 0.801 | 1 |
| LogBandPower + LogReg | 0.791 | nan | 0.791 | 1 |
| HighGamma + LDA | 0.659 | nan | 0.659 | 1 |

## faces_basic (within_subject, kappa, 14 patients)

| pipeline | mean | sd | median | patients |
|---|---|---|---|---|
| LogBandPower + LDA | 0.682 | 0.260 | 0.792 | 14 |
| LogBandPower + LogReg | 0.667 | 0.259 | 0.780 | 14 |
| HighGamma + LDA | 0.638 | 0.262 | 0.736 | 14 |
| Riemann TS + LogReg | 0.608 | 0.262 | 0.639 | 14 |

Mean rank (1 = best), Friedman p = 0.194: LogBandPower + LDA 1.93, LogBandPower + LogReg 2.43, HighGamma + LDA 2.71, Riemann TS + LogReg 2.93

Significant pairwise differences (row beats column, p < 0.05):

- LogBandPower + LDA > HighGamma + LDA: p = 0.0436, d_z = 0.50

![faces_basic_within_subject scores](figures/faces_basic_within_subject_scores.png)

![faces_basic_within_subject summary](figures/faces_basic_within_subject_summary.png)

## fingerflex (within_subject, pearson_r, 9 patients)

| pipeline | mean | sd | median | patients |
|---|---|---|---|---|
| HighGamma + Ridge | 0.283 | 0.078 | 0.290 | 9 |
| LogBandPower + Ridge | 0.265 | 0.083 | 0.267 | 9 |

Mean rank (1 = best): HighGamma + Ridge 1.22, LogBandPower + Ridge 1.78

Significant pairwise differences (row beats column, p < 0.05):

- HighGamma + Ridge > LogBandPower + Ridge: p = 0.0156, d_z = 1.06

![fingerflex_within_subject scores](figures/fingerflex_within_subject_scores.png)

![fingerflex_within_subject summary](figures/fingerflex_within_subject_summary.png)

## gestures (within_subject, kappa, 5 patients)

| pipeline | mean | sd | median | patients |
|---|---|---|---|---|
| HighGamma + LDA | 0.518 | 0.332 | 0.395 | 5 |
| LogBandPower + LogReg | 0.468 | 0.292 | 0.446 | 5 |
| LogBandPower + LDA | 0.454 | 0.374 | 0.423 | 5 |
| Riemann TS + LogReg | 0.287 | 0.243 | 0.175 | 5 |

Mean rank (1 = best), Friedman p = 0.106: HighGamma + LDA 1.60, LogBandPower + LDA 2.40, LogBandPower + LogReg 2.40, Riemann TS + LogReg 3.60

No pairwise difference reaches p < 0.05.

![gestures_within_subject scores](figures/gestures_within_subject_scores.png)

![gestures_within_subject summary](figures/gestures_within_subject_summary.png)

## imagery_basic (within_subject, kappa, 7 patients)

| pipeline | mean | sd | median | patients |
|---|---|---|---|---|
| HighGamma + LDA | 0.655 | 0.123 | 0.666 | 7 |
| LogBandPower + LDA | 0.654 | 0.118 | 0.603 | 7 |
| LogBandPower + LogReg | 0.609 | 0.132 | 0.556 | 7 |
| Riemann TS + LogReg | 0.412 | 0.169 | 0.361 | 7 |

Mean rank (1 = best), Friedman p = 0.0071: HighGamma + LDA 1.57, LogBandPower + LDA 1.86, LogBandPower + LogReg 2.86, Riemann TS + LogReg 3.71

Significant pairwise differences (row beats column, p < 0.05):

- HighGamma + LDA > Riemann TS + LogReg: p = 0.0155, d_z = 1.61
- LogBandPower + LDA > LogBandPower + LogReg: p = 0.0155, d_z = 2.20
- LogBandPower + LDA > Riemann TS + LogReg: p = 0.031, d_z = 1.12
- LogBandPower + LogReg > Riemann TS + LogReg: p = 0.031, d_z = 0.89

![imagery_basic_within_subject scores](figures/imagery_basic_within_subject_scores.png)

![imagery_basic_within_subject summary](figures/imagery_basic_within_subject_summary.png)

## motor_basic (within_subject, kappa, 19 patients)

| pipeline | mean | sd | median | patients |
|---|---|---|---|---|
| LogBandPower + LDA | 0.917 | 0.094 | 0.967 | 19 |
| LogBandPower + LogReg | 0.880 | 0.129 | 0.852 | 19 |
| HighGamma + LDA | 0.877 | 0.171 | 0.933 | 19 |
| Riemann TS + LogReg | 0.702 | 0.255 | 0.767 | 19 |
| ShallowFBCSPNet s0 | 0.380 | 0.352 | 0.373 | 14 |

Mean rank (1 = best), Friedman p = 2.55e-06: LogBandPower + LDA 2.04, HighGamma + LDA 2.43, LogBandPower + LogReg 2.43, Riemann TS + LogReg 3.43, ShallowFBCSPNet s0 4.68

Significant pairwise differences (row beats column, p < 0.05):

- LogBandPower + LDA > ShallowFBCSPNet s0: p = 0.0003, d_z = 1.67
- LogBandPower + LogReg > ShallowFBCSPNet s0: p = 0.0003, d_z = 1.67
- Riemann TS + LogReg > ShallowFBCSPNet s0: p = 0.0003, d_z = 1.44
- HighGamma + LDA > ShallowFBCSPNet s0: p = 0.0012, d_z = 1.15
- LogBandPower + LDA > Riemann TS + LogReg: p = 0.0012, d_z = 0.96
- LogBandPower + LogReg > Riemann TS + LogReg: p = 0.004, d_z = 0.89
- LogBandPower + LDA > LogBandPower + LogReg: p = 0.0311, d_z = 0.58
- HighGamma + LDA > Riemann TS + LogReg: p = 0.0346, d_z = 0.54

![motor_basic_within_subject scores](figures/motor_basic_within_subject_scores.png)

![motor_basic_within_subject summary](figures/motor_basic_within_subject_summary.png)
