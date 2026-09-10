# Smoke tests of the catalog

Generated 2026-09-10 by `scripts/build_smoke_table.py` from `results/smoke/*.json`. Each entry downloads a one-subject (or one-file) subset, loads it through the MOECoG loader, reports what it found, and, when a trial-classification paradigm applies, scores LogBandPower+LDA with 3 chronological folds on the first subject. Numbers are sanity checks, not benchmark results.

Status: 93 ok, 3 error, 12 unsupported, 22 blocked, 0 pending out of 130 entries.

| entry | source | title | status | what was found / why not | s |
|---|---|---|---|---|---|
| ds002799 | openneuro | Human es-fMRI Resource: Concurrent deep-brain stimulation an | unsupported | ValueError: Subjects ['292'] not in /mnt/archive/home/yyu2024/moecog_data/openneuro/ds002799 and nothing else readable | 0.2 |
| ds003029 | openneuro | iEEG Fragility Epileptogenic Zone | ok | 1 subj; 4 file(s); 126 ch @ 1000 Hz; 142 s; 21 events in 15 classes; electrodes none;  | 2.1 |
| ds003078 | openneuro | PROBE iEEG | ok | 1 subj; 12 file(s); 130 ch @ 512 Hz; 584 s; 662 events in 14 classes; electrodes none;  | 5.5 |
| ds003374 | openneuro | Dataset of neurons and intracranial EEG from human amygdala  | ok | 1 subj; 1 file(s); 4 ch @ 2000 Hz; 522 s; 17 events in 2 classes; electrodes 4 (other);  | 0.1 |
| ds003498 | openneuro | iEEG Interictal Asleep HFO Dataset | ok | 1 subj; 28 file(s); 50 ch @ 2000 Hz; 300 s; 4223 events in 15 classes; electrodes none;  | 25.1 |
| ds003688 | openneuro | Open multimodal iEEG-fMRI dataset from naturalistic stimulat | ok | 1 subj; 2 file(s); 101 ch @ 2048 Hz; 420 s; 15 events in 4 classes; electrodes 103 (acpc); kappa 0.10 (n=17) | 13.1 |
| ds003708 | openneuro | Basis profile curve identification to understand electrical  | unsupported | NotImplementedError: MEF3 (.mefd) needs pymef; not supported | 0.7 |
| ds003844 | openneuro | RESPect | ok | 1 subj; 5 file(s); 31 ch @ 2048 Hz; 325 s; 20 events in 2 classes; electrodes 32 (other); kappa 0.00 (n=8) | 11.2 |
| ds003848 | openneuro | Dataset Clinical Epilepsy iEEG to BIDS - RESPect_longterm_iE | ok | 1 subj; 3 file(s); 54 ch @ 2048 Hz; 3187 s; 588 events in 3 classes; electrodes 133 (other); kappa 0.48 (n=617) | 101.4 |
| ds003876 | openneuro | Epilepsy-iEEG-Interictal-Multicenter-Dataset | ok | 1 subj; 1 file(s); 186 ch @ 1024 Hz; 573 s; 1 events in 1 classes; electrodes none;  | 0.7 |
| ds004100 | openneuro | ds004100 | ok | 1 subj; 5 file(s); 59 ch @ 500 Hz; 378 s; 2 events in 2 classes; electrodes 59 (fsaverage);  | 0.4 |
| ds004127 | openneuro | Somatosensory Cortex Rat DISC Data | ok | 1 subj; 9 file(s); 104 ch @ 20000 Hz; 300 s; 450 events in 1 classes; electrodes none;  | 64.3 |
| ds004194 | openneuro | Visual ECoG dataset | ok | 1 subj; 12 file(s); 140 ch @ 512 Hz; 59 s; 36 events in 15 classes; electrodes 124 (other); kappa 0.23 (n=432) | 4.8 |
| ds004080 | openneuro | CCEP ECoG dataset across age 4-51 | ok | 1 subj; 8 file(s); 96 ch @ 512 Hz; 7200 s; 517 events in 3 classes; electrodes 133 (fsaverage);  | 42.5 |
| ds004370 | openneuro | PRIOS | ok | 1 subj; 2 file(s); 48 ch @ 2048 Hz; 2359 s; 372 events in 3 classes; electrodes 68 (unknown);  | 19.0 |
| ds004457 | openneuro | Electrical stimulation of temporal and limbic circuitry prod | unsupported | NotImplementedError: MEF3 (.mefd) needs pymef; not supported | 3.0 |
| ds004473 | openneuro | sEEG Forced Two-Choice Task | ok | 1 subj; 1 file(s); 128 ch @ 999 Hz; 3646 s; 808 events in 4 classes; electrodes 119 (acpc);  | 141.6 |
| ds004551 | openneuro | testMIproject | ok | 1 subj; 1 file(s); 117 ch @ 1000 Hz; 1925 s; 5 events in 5 classes; electrodes 94 (unknown);  | 2.4 |
| ds004624 | openneuro | Intracranial recordings using BCI2000 and the CorTec BrainIn | unsupported | NotImplementedError: MEF3 (.mefd) needs pymef; not supported | 10.0 |
| ds004642 | openneuro | Intraoperative recordings of medianus stimulation with low a | ok | 1 subj; 1 file(s); 8 ch @ 20000 Hz; 672 s; 0 events in 0 classes; electrodes none;  | 24.6 |
| ds004696 | openneuro | HAPwave_bids | unsupported | NotImplementedError: MEF3 (.mefd) needs pymef; not supported | 0.5 |
| ds004703 | openneuro | PassiveListen | ok | 1 subj; 1 file(s); 110 ch @ 1024 Hz; 1044 s; 4531 events in 1 classes; electrodes none;  | 3.6 |
| ds004752 | openneuro | Dataset of intracranial EEG, scalp EEG and beamforming sourc | ok | 1 subj; 4 file(s); 48 ch @ 2000 Hz; 400 s; 50 events in 1 classes; electrodes 48 (unknown);  | 26.3 |
| ds004770 | openneuro | iEEG on children during gameplay | ok | 1 subj; 2 file(s); 126 ch @ 1000 Hz; 3755 s; 62 events in 3 classes; electrodes 97 (unknown); kappa 0.40 (n=342) | 241.8 |
| ds004774 | openneuro | Automatic Evoked Response Detection (ER-Detect) dataset | unsupported | NotImplementedError: MEF3 (.mefd) needs pymef; not supported | 0.3 |
| ds004789 | openneuro | Delayed Free Recall of Word Lists | ok | 1 subj; 2 file(s); 88 ch @ 500 Hz; 4699 s; 756 events in 15 classes; electrodes 88 (mni152nlin6asym); kappa 0.12 (n=713) | 44.5 |
| ds004809 | openneuro | Categorized Free Recall: Delayed Free Recall of Word Lists O | ok | 1 subj; 1 file(s); 162 ch @ 1600 Hz; 5400 s; 739 events in 15 classes; electrodes 120 (mni152nlin6asym); kappa 0.08 (n=697) | 176.6 |
| ds004819 | openneuro | Flexible, Scalable, High Channel Count Stereo-Electrode for  | ok | 1 subj; 8 file(s); 64 ch @ 30000 Hz; 25 s; 20 events in 1 classes; electrodes 64 (unknown);  | 54.8 |
| ds004859 | openneuro | iEEG on children during Stroop task | ok | 1 subj; 1 file(s); 108 ch @ 1000 Hz; 1040 s; 264 events in 15 classes; electrodes 108 (unknown);  | 31.6 |
| ds004865 | openneuro | pyFR: Delayed Free Recall of Word Lists, Preliminary Cogniti | ok | 1 subj; 1 file(s); 94 ch @ 400 Hz; 3102 s; 367 events in 9 classes; electrodes 94 (talairach); kappa 0.12 (n=365) | 13.9 |
| ds004944 | openneuro | Dataset of BCI2000-compatible intraoperative ECoG with neuro | ok | 1 subj; 2 file(s); 15 ch @ 2000 Hz; 500 s; 175 events in 1 classes; electrodes 28 (unknown);  | 0.3 |
| ds004977 | openneuro | CARLA: Adjusted common average referencing for cortico-corti | unsupported | NotImplementedError: MEF3 (.mefd) needs pymef; not supported | 0.3 |
| ds004993 | openneuro | WIRED ICM Sample Dataset - Workshop on Intracranial Recordin | ok | 1 subj; 1 file(s); 148 ch @ 512 Hz; 68 s; 1 events in 1 classes; electrodes 148 (acpc);  | 5.4 |
| ds005007 | openneuro | Auditory naming task with questions that begin or end with a | ok | 1 subj; 1 file(s); 83 ch @ 1000 Hz; 880 s; 443 events in 15 classes; electrodes 64 (unknown);  | 22.6 |
| ds005059 | openneuro | Paired Associates Learning: Memory for Word Pairs in Cued Re | ok | 1 subj; 2 file(s); 88 ch @ 500 Hz; 3647 s; 1279 events in 15 classes; electrodes 88 (mni152nlin6asym); kappa -0.00 (n=1088) | 35.5 |
| ds005083 | openneuro | Safety and Accuracy of Stereoelectroencephalography for Pedi | unsupported | ValueError: Subjects ['SLCHRETRO002'] not in /Users/johnsmith/moecog_data/openneuro/ds005083 and nothing else readable | 0.0 |
| ds005169 | openneuro | Dataset of intracranial EEG during cortical stimulation evok | ok | 1 subj; 1 file(s); 29 ch @ 4096 Hz; 21 s; 3 events in 1 classes; electrodes 67 (scanras);  | 6.2 |
| ds005398 | openneuro | Open iEEG Dataset | ok | 1 subj; 1 file(s); 56 ch @ 1000 Hz; 304 s; 0 events in 0 classes; electrodes 56 (mni152lin);  | 12.4 |
| ds005411 | openneuro | Free Recall of Word Lists with Repeated Items | ok | 1 subj; 2 file(s); 118 ch @ 1000 Hz; 4213 s; 799 events in 10 classes; electrodes 118 (mni152nlin6asym); kappa 0.18 (n=799) | 96.7 |
| ds005415 | openneuro | Numbers | ok | 1 subj; 1 file(s); 188 ch @ 1000 Hz; 1449 s; 509 events in 5 classes; electrodes 174 (acpc);  | 77.4 |
| ds005448 | openneuro | STReEF | ok | 1 subj; 2 file(s); 112 ch @ 2048 Hz; 3245 s; 571 events in 4 classes; electrodes 133 (other);  | 85.9 |
| ds005489 | openneuro | Free Recall with Open-Loop Stimulation at Encoding | ok | 1 subj; 2 file(s); 88 ch @ 500 Hz; 4865 s; 826 events in 15 classes; electrodes 88 (mni152nlin6asym); kappa 0.08 (n=784) | 52.3 |
| ds005491 | openneuro | Categorized Free Recall with Open-Loop Stimulation at Encodi | ok | 1 subj; 1 file(s); 177 ch @ 500 Hz; 3499 s; 767 events in 15 classes; electrodes 128 (talairach); kappa 0.27 (n=723) | 31.6 |
| ds005494 | openneuro | Cued Recall of Paired Associates with Open-Loop Stimulation  | ok | 1 subj; 2 file(s); 114 ch @ 500 Hz; 2463 s; 1018 events in 15 classes; electrodes 100 (mni152nlin6asym); kappa 0.03 (n=889) | 54.2 |
| ds005522 | openneuro | Spatial Navigation Memory of Object Locations | ok | 1 subj; 1 file(s); 120 ch @ 500 Hz; 2361 s; 58159 events in 8 classes; electrodes 120 (mni152nlin6asym); kappa 0.50 (n=58159) | 423.4 |
| ds005523 | openneuro | Spatial Memory of Object Locations with Open-Loop Stimulatio | ok | 1 subj; 2 file(s); 133 ch @ 500 Hz; 3421 s; 43216 events in 8 classes; electrodes 123 (mni152nlin6asym); kappa 0.59 (n=43216) | 786.5 |
| ds005545 | openneuro | auditory | ok | 1 subj; 3 file(s); 2 ch @ 1000 Hz; 935 s; 267 events in 3 classes; electrodes 123 (unknown); kappa 0.67 (n=265) | 23.7 |
| ds005557 | openneuro | Free Recall with Closed-Loop Stimulation at Encoding (Encodi | ok | 1 subj; 2 file(s); 120 ch @ 1000 Hz; 3071 s; 1290 events in 15 classes; electrodes 120 (mni152nlin6asym); kappa 0.04 (n=1237) | 137.0 |
| ds005558 | openneuro | Categorized Free Recall with Closed-Loop Stimulation at Enco | ok | 1 subj; 1 file(s); 122 ch @ 1000 Hz; 3004 s; 1320 events in 15 classes; electrodes 90 (mni152nlin6asym); kappa 0.11 (n=1263) | 50.5 |
| ds005574 | openneuro | The "Podcast" ECoG dataset for modeling neural activity duri | ok | 1 subj; 1 file(s); 82 ch @ 512 Hz; 1800 s; 0 events in 0 classes; electrodes 75 (other);  | 21.9 |
| ds005592 | openneuro | ds005592 | unsupported | RuntimeError: Query failed when retrieving metadata for ds005592: "Dataset ds005592 has been deleted. Reason: duplicate dataset." | 1.3 |
| ds005624 | openneuro | Color Change Detection Task | ok | 1 subj; 4 file(s); 74 ch @ 512 Hz; 3280 s; 0 events in 0 classes; electrodes none;  | 120.2 |
| ds005670 | openneuro | SEEG Resting State Recording | ok | 1 subj; 1 file(s); 238 ch @ 2000 Hz; 433 s; 4 events in 4 classes; electrodes 238 (mni152lin);  | 51.6 |
| ds005691 | openneuro | SpinalExpect_Invasive | ok | 1 subj; 1 file(s); 7 ch @ 2500 Hz; 1602 s; 1205 events in 5 classes; electrodes none;  | 8.9 |
| ds005931 | openneuro | Visuomotor_task | ok | 1 subj; 1 file(s); 64 ch @ 1000 Hz; 428 s; 122 events in 1 classes; electrodes 118 (unknown);  | 0.4 |
| ds005953 | openneuro | iEEG_visual | ok | 1 subj; 1 file(s); 118 ch @ 3052 Hz; 234 s; 420 events in 8 classes; electrodes 118 (acpc);  | 0.6 |
| ds006065 | openneuro | TSS_iEEG | ok | 1 subj; 10 file(s); 168 ch @ 500 Hz; 1570 s; 0 events in 0 classes; electrodes 168 (mni152nlin2009casym);  | 154.9 |
| ds006107 | openneuro | iEEG_Neural_spatial_volatility | ok | 1 subj; 1 file(s); 100 ch @ 1000 Hz; 320 s; 0 events in 0 classes; electrodes 100 (unknown);  | 16.4 |
| ds006136 | openneuro | OWM-Dataset | ok | 1 subj; 1 file(s); 8 ch @ 1000 Hz; 1021 s; 0 events in 0 classes; electrodes 8 (mni152lin);  | 5.0 |
| ds006233 | openneuro | Picture naming | ok | 1 subj; 3 file(s); 2 ch @ 1000 Hz; 777 s; 120 events in 2 classes; electrodes 128 (unknown); kappa 0.17 (n=120) | 15.5 |
| ds006234 | openneuro | Auditory naming | ok | 1 subj; 3 file(s); 2 ch @ 1000 Hz; 3442 s; 402 events in 3 classes; electrodes 100 (unknown); kappa 0.64 (n=402) | 50.9 |
| ds006253 | openneuro | MetaRDK | unsupported | ValueError: Subjects ['10'] not in /Users/johnsmith/moecog_data/openneuro/ds006253 and nothing else readable | 0.0 |
| ds006254 | openneuro | IEEG CCEP Recording | blocked | 30 subjects; tasks CCEP_OnASM; 168.3 GB; BLOCKED: OpenNeuro returns HTTP 403 for every file of snapshot 1.0.0 (checked 2026-09-10) | 3.5 |
| ds006392 | openneuro | HED schema library for SCORE annotations example | unsupported | NotImplementedError: MEF3 (.mefd) needs pymef; not supported | 0.1 |
| ds006519 | openneuro | Dataset of intracranial EEG during cortical stimulations evo | ok | 1 subj; 1 file(s); 63 ch @ 4096 Hz; 30 s; 2 events in 1 classes; electrodes 128 (scanras);  | 7.3 |
| ds006890 | openneuro | Longitudinal Multitask Wireless ECoG Data from Two Fully Imp | ok | 1 subj; 225 file(s); 31 ch @ 1000 Hz; 718 s; 53 events in 1 classes; electrodes 32 (other); kappa 0.00 (n=54) | 1220.4 |
| ds006910 | openneuro | Auditory Naming | ok | 1 subj; 1 file(s); 48 ch @ 1000 Hz; 1175 s; 150 events in 3 classes; electrodes 58 (other); kappa 0.89 (n=150) | 17.9 |
| ds006914 | openneuro | Picture naming | ok | 1 subj; 1 file(s); 48 ch @ 1000 Hz; 291 s; 240 events in 14 classes; electrodes 58 (other); kappa 0.23 (n=119) | 9.3 |
| ds007095 | openneuro | RNS_Epilepsy-iBIDS | ok | 1 subj; 886 file(s); 2 ch @ 200 Hz; 91 s; 3 events in 1 classes; electrodes 2 (acpc);  | 86.3 |
| ds007118 | openneuro | iEEG_comprehensive_HFA_model_part1 | ok | 1 subj; 1 file(s); 106 ch @ 1000 Hz; 2269 s; 0 events in 0 classes; electrodes 104 (fsaverage);  | 17.5 |
| ds007119 | openneuro | iEEG_comprehensive_HFA_model_part3 | ok | 1 subj; 1 file(s); 132 ch @ 1000 Hz; 3367 s; 0 events in 0 classes; electrodes 132 (fsaverage);  | 37.0 |
| ds007120 | openneuro | iEEG_comprehensive_HFA_model_part2 | ok | 1 subj; 1 file(s); 128 ch @ 1000 Hz; 1605 s; 0 events in 0 classes; electrodes 128 (fsaverage);  | 25.3 |
| ds007703 | openneuro | Single pulse electrical stimulation in white matter modulate | blocked | 2 subjects; tasks Visual stimuli + CCEPs,Cortico-cortical evoked potentials - CCEPs,Cortico cortical Evoked Potentials, CCEPs,Cortico Cortical Evoked Potentials; 12.3 GB; BLOCKED: OpenNeuro returns HTTP 403 for every file of snapshot 1.0.0 and the snapshot lists only sidecar files, no ieeg recordings (checked 2026-09-10) | 31.6 |
| ds008610 | openneuro | FUS and Tactile Neuromodulation in NHP VPL - Electrophysiolo | ok | 1 subj; 31 file(s); 32 ch @ 1000 Hz; 71 s; 5 events in 1 classes; electrodes 96 (other); no scorable session (fewer than two classes per session) | 50.3 |
| dandi-000019 | dandi | Bouchard/Chang CV syllables (sub-EC9 B15) | ok | 1 subj; 1 file(s); 256 ch @ 3052 Hz; 195 s; 96 events in 15 classes; electrodes 256 (unknown); kappa -0.04 (n=96) | 24.5 |
| dandi-001193 | dandi | Shao IFG syntax/semantics high gamma | ok | 10 subj; 1 file(s); 256 ch @ 400 Hz; 74 s; 0 events in 0 classes; electrodes none;  | 17.7 |
| dandi-000623 | dandi | Keles/Rutishauser movie watching (CS62) | ok | 1 subj; 1 file(s); 56 ch @ 1000 Hz; 600 s; 19 events in 2 classes; electrodes 56 (unknown); kappa nan (n=18) | 54.6 |
| dandi-000574 | dandi | Rutishauser verbal WM + iEEG (sub-05 ses-01) | ok | 1 subj; 1 file(s); 32 ch @ 32000 Hz; 400 s; 150 events in 15 classes; electrodes 32 (unknown); kappa 0.02 (n=120) | 64.4 |
| dandi-000576 | dandi | Rutishauser amygdala aversive stimuli | ok | 9 subj; 1 file(s); 2 ch @ 2000 Hz; 442 s; 17 events in 2 classes; electrodes 2 (unknown); kappa -0.25 (n=17) | 8.0 |
| dandi-001535 | dandi | Natraj/Ganguly long-term ECoG BCI | unsupported | ValueError: No ElectricalSeries in /mnt/archive/home/yyu2024/moecog_data/dandi/001535/sub-BRAVO1/sub-BRAVO1.nwb | 67.4 |
| dandi-000055 | dandi | AJILE12 (sub-04 ses-3) | ok | 1 subj; 1 file(s); 84 ch @ 500 Hz; 600 s; 1 events in 1 classes; electrodes 84 (unknown);  | 1.9 |
| dandi-000469 | dandi | Rutishauser Sternberg WM | blocked | NWB files hold spike times only (no ElectricalSeries) | 7.3 |
| dandi-000004 | dandi | Rutishauser declarative memory | blocked | NWB files hold spike times only (no ElectricalSeries) | 8.7 |
| dandi-001616 | dandi | SUMMER movie single-neuron | blocked | NWB files hold spike times only (no ElectricalSeries) | 8.5 |
| dandi-000571 | dandi | Mayo CorTec BrainInterchange (MEF3) | blocked | MEF3 format needs pymef; not supported yet |  |
| dandi-001638 | dandi | Cogan µECoG pseudoword repetition | blocked | dandiset has no assets yet (empty on 2026-09-09) |  |
| dandi-001613 | dandi | Nentwich/Parra movies + eye tracking | blocked | only stimulus videos uploaded so far; no NWB assets |  |
| miller-motor_basic | miller | Miller library motor_basic | ok | 1 subj; 1 file(s); 47 ch @ 1000 Hz; 376 s; 60 events in 2 classes; electrodes 47 (talairach); kappa 0.96 (n=60) | 3.2 |
| miller-imagery_basic | miller | Miller library imagery_basic | ok | 1 subj; 2 file(s); 46 ch @ 1000 Hz; 376 s; 60 events in 2 classes; electrodes 46 (talairach); kappa 0.51 (n=60) | 5.3 |
| miller-faces_basic | miller | Miller library faces_basic | ok | 1 subj; 1 file(s); 46 ch @ 1000 Hz; 271 s; 300 events in 2 classes; electrodes 46 (voxel); kappa 0.27 (n=300) | 2.6 |
| miller-fingerflex | miller | Miller library fingerflex | ok | 1 subj; 1 file(s); 46 ch @ 1000 Hz; 610 s; 439 events in 7 classes; electrodes 46 (native);  | 5.0 |
| miller-visual_search | miller | Miller library visual_search | ok | 1 subj; 1 file(s); 8 ch @ 1000 Hz; 510 s; 120 events in 4 classes; electrodes 8 (native); kappa 0.16 (n=120) | 1.8 |
| miller-memory_nback | miller | Miller library memory_nback | ok | 1 subj; 1 file(s); 40 ch @ 1000 Hz; 360 s; 150 events in 2 classes; electrodes 40 (talairach); kappa 0.18 (n=150) | 2.4 |
| miller-gestures | miller | Miller library gestures | ok | 1 subj; 5 file(s); 84 ch @ 1000 Hz; 130 s; 0 events in 0 classes; electrodes 84 (talairach); kappa 0.63 (n=150) | 18.9 |
| miller-imagery_feedback | miller | Miller library imagery_feedback | ok | 1 subj; 3 file(s); 40 ch @ 1000 Hz; 180 s; 27 events in 2 classes; electrodes 40 (talairach); kappa 0.46 (n=27) | 5.7 |
| miller-faces_noise | miller | Miller library faces_noise | ok | 1 subj; 2 file(s); 41 ch @ 1000 Hz; 268 s; 300 events in 2 classes; electrodes 41 (voxel); kappa 0.41 (n=300) | 9.9 |
| miller-speech_basic | miller | Miller library speech_basic | ok | 1 subj; 1 file(s); 48 ch @ 1000 Hz; 545 s; 40 events in 1 classes; electrodes 48 (native); no scorable session (fewer than two classes per session) | 2.1 |
| miller-speech_lists | miller | Miller library speech_lists | ok | 1 subj; 13 file(s); 48 ch @ 1000 Hz; 138 s; 40 events in 1 classes; electrodes 48 (native); no scorable session (fewer than two classes per session) | 11.1 |
| miller-joystick_track | miller | Miller library joystick_track | ok | 1 subj; 1 file(s); 60 ch @ 1000 Hz; 373 s; 0 events in 0 classes; electrodes 60 (talairach);  | 1.7 |
| miller-mouse_track | miller | Miller library mouse_track | ok | 1 subj; 1 file(s); 61 ch @ 1000 Hz; 248 s; 0 events in 0 classes; electrodes 61 (talairach);  | 1.3 |
| miller-fixation_PAC | miller | Miller library fixation_PAC | ok | 1 subj; 1 file(s); 46 ch @ 1000 Hz; 130 s; 0 events in 0 classes; electrodes 46 (native);  | 1.3 |
| miller-fixation_pwrlaw | miller | Miller library fixation_pwrlaw | ok | 1 subj; 1 file(s); 32 ch @ 1000 Hz; 130 s; 0 events in 0 classes; electrodes 32 (talairach);  | 0.5 |
| miller-fixation_highfreq | miller | Miller library fixation_highfreq | ok | 1 subj; 1 file(s); 32 ch @ 10000 Hz; 130 s; 0 events in 0 classes; electrodes none;  | 1.9 |
| bci-iv-4 | bbci | BCI Competition IV dataset 4 (finger flexion) | ok | 3 subj; 1 file(s); 62 ch @ 1000 Hz; 600 s; 2 events in 2 classes; electrodes none;  | 1.9 |
| bci-iii-1 | bbci | BCI Competition III dataset I (ECoG motor imagery) | ok | 1 subj; 1 file(s); 64 ch @ 1000 Hz; 834 s; 278 events in 2 classes; electrodes none; kappa 0.75 (n=278) | 9.7 |
| peterson-moverest | figshare | Peterson naturalistic move vs rest (EC09) | ok | 1 subj; 1 file(s); 126 ch @ 250 Hz; 1208 s; 302 events in 2 classes; electrodes none; kappa 0.46 (n=302) | 7.9 |
| peterson-reach | figshare | Peterson naturalistic reach epochs (subj 01 day 3) | ok | 1 subj; 1 file(s); 94 ch @ 500 Hz; 1716 s; 156 events in 1 classes; electrodes none;  | 0.8 |
| peterson-pose | figshare | Peterson ECoG + arm pose (EC02) | ok | 1 subj; 1 file(s); 87 ch @ 250 Hz; 1672 s; 418 events in 1 classes; electrodes none;  | 0.6 |
| rogers-uecog | figshare | Rogers submillimeter µECoG windows (S2) | ok | 1 subj; 1 file(s); 44 ch @ 4000 Hz; 652 s; 326 events in 1 classes; electrodes none;  | 10.5 |
| verwoert-speech | osf | Verwoert single-word production sEEG (iBIDS) | error | BadZipFile: File is not a zip file | 0.6 |
| merk-gripforce | dataverse | Merk grip-force ECoG + STN (Dataverse) | ok | 16 subj; 4 file(s); 10 ch @ 1000 Hz; 130 s; 0 events in 0 classes; electrodes none;  | 25.3 |
| duin | huggingface | Du-IN Mandarin word sEEG (sub 001 run 1) | error | ModuleNotFoundError: No module named 'utils.DotDict'; 'utils' is not a package | 0.0 |
| swec | huggingface | SWEC long-term iEEG (ID01 part 1) | error | OSError: Can't synchronously read data (can't open directory (/usr/local/hdf5/lib/plugin). Please verify its existence) | 0.1 |
| omni-edf | huggingface | Omni-iEEG raw EDF (Pt1) | ok | 1 subj; 1 file(s); 38 ch @ 2000 Hz; 601 s; 3 events in 3 classes; electrodes none;  | 0.5 |
| mindeye-ieeg | huggingface | mindeye iEEG NSD high-frequency broadband | ok | 1 subj; 1 file(s); 130 ch @ 1 Hz; 9 s; 0 events in 0 classes; electrodes none;  | 2.1 |
| braintreebank | braintreebank | Brain Treebank (sub_1 trial000) | ok | 1 subj; 1 file(s); 156 ch @ 2048 Hz; 600 s; 0 events in 0 classes; electrodes none;  | 105.2 |
| stolk-sensorimotor | osf | Stolk sensorimotor alpha/beta (OSF) | blocked | MATLAB v7.3 segmented .mat; loader pending |  |
| bellier-music | zenodo | Bellier music reconstruction (Zenodo 7876019) | blocked | Zenodo API timed out on 2026-09-09; file list pending |  |
| tonal-speech | zenodo | Li tonal speech perception ECoG (Zenodo) | blocked | Zenodo record id not yet located |  |
| cogitate | blocked | Cogitate iEEG release 1 | blocked | portal registration + terms |  |
| dabi-* | blocked | DABI public projects (MGH stimulation/conversation, UTSW mot | blocked | DABI account required to download |  |
| ebrains-* | blocked | EBRAINS memory+pupillometry, EEG+stimulation | blocked | EBRAINS account |  |
| kaggle-seizure | blocked | UPenn/Mayo and Melbourne seizure competitions | blocked | Kaggle API token + competition rules |  |
| mni-atlas | blocked | MNI Open iEEG Atlas | blocked | HTTP 401: registration |  |
| neurotycho | blocked | Neurotycho macaque ECoG | blocked | download list behind registration (expdatalist) |  |
| ieeg-org | blocked | iEEG.org | blocked | account |  |
| crcns | blocked | CRCNS ECoG/LFP sets | blocked | account |  |
| epilepsiae | blocked | EPILEPSIAE | blocked | restricted |  |
| metzger-2023 | blocked | Chang lab neuroprosthesis deposit (Zenodo restricted) | blocked | restricted deposit; request |  |
| gin-usz | blocked | GIN USZ intraoperative HFO | blocked | git-annex content; same data as ds004944 |  |
