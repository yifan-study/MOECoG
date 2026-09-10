# Decodable ECoG / iEEG datasets

Generated 2026-09-10 by `scripts/build_dataset_list.py` from the catalog registry, the smoke-test records and the OpenNeuro metadata snapshots. One row per catalog entry; channels, rate and duration are those of the first subject's first run as loaded by MOECoG (a subset, not the whole dataset). Sizes are the full deposits. 'Fit' says which of our decoder lines apply: R = continuous regression (finger flexion, cursor, force, audio), C = trial classification, S = speech/audio decoding, P = pretraining / self-supervised only.

130 entries, 106 load today, about 10.0 TB of public deposits in total (9.4 TB behind the entries that load).

## Size by modality

Not all of it is subdural ECoG. *modality* comes from the channel types in the downloaded subset's channels.tsv (ECoG = at least 80 % ECOG channels, sEEG = at least 80 % SEEG/DBS, mixed = both, unverified = channels typed EEG/other) where a subset is on this machine, otherwise from the curated notes; 'features' and 'µECoG' are curated.

| modality | entries | load | total size |
|---|---|---|---|
| sEEG | 23 | 19 | 4.96 TB |
| mixed | 28 | 21 | 2.72 TB |
| ECoG | 64 | 54 | 2.05 TB |
| uECoG | 3 | 2 | 0.21 TB |
| unverified | 6 | 4 | 0.05 TB |
| features | 4 | 4 | 0.02 TB |
| LFP+ECoG | 2 | 2 | 0.01 TB |

One archive dominates the total: SWEC-ETHZ long-term clinical sEEG on Hugging Face (4.6 TB). The RAM memory sets (depth electrodes with some grids and strips, 1.5 TB across the family) and AJILE12 (0.85 TB of continuous subdural ECoG) are the next largest; the motor-decoding sets our regression line targets are small in bytes (the whole Miller library is 7.5 GB, BCI IV-4 is 220 MB).

## Motor (movement, kinematics, force) (11)

| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| merk-gripforce | Merk grip-force ECoG + STN (Dataverse) | LFP+ECoG | 11 | 10 @ 1000, 130 s | 1.4 GB |  | grip force (continuous) | regression | R | ok |  | intraoperative Parkinson's; ECoG strips + STN LFP |
| ds005931 | Visuomotor_task | ECoG (100 % ECoG, 0 % sEEG) | 8 | 64 @ 1000, 428 s | 857 MB | CC0 | visuomotor game events | classification | C | ok |  |  |
| stolk-sensorimotor | Stolk sensorimotor alpha/beta, high-density ECoG (OSF z4hfm) | ECoG | 3 | 120 @ 512, 196 s | 320 MB |  | cued movement condition code | classification | C | ok | 0.18 | high-density grids; trialinfo semantics to confirm with the authors' code |
| bci-iv-4 | BCI Competition IV dataset 4 (finger flexion) | ECoG | 3 | 62 @ 1000, 600 s | 220 MB |  | finger flexion (5 fingers, dataglove) | regression | R | ok |  | fixed train/test split; winner r 0.46 |
| bci-iii-1 | BCI Competition III dataset I (ECoG motor imagery) | ECoG | 1 | 64 @ 1000, 834 s | 50 MB |  | imagined pinky vs tongue | classification | C | ok | 0.75 | one patient, sessions a week apart |
| miller-motor_basic | Miller library motor_basic | ECoG | 19 | 47 @ 1000, 376 s |  |  | hand vs tongue movement (cued) | classification | C | ok | 0.96 | 19 patients; kappa 0.90 with band power + LDA |
| miller-imagery_basic | Miller library imagery_basic | ECoG | 7 | 46 @ 1000, 376 s |  |  | overt vs imagined hand/tongue | classification | C | ok | 0.51 | part of the 7.5 GB Miller library (7 patients) |
| miller-fingerflex | Miller library fingerflex | ECoG | 9 | 46 @ 1000, 610 s |  |  | dataglove flexion of 5 fingers | regression | R | ok |  | the PACE/TRACE benchmark; 9 patients; cue channel gives finger id too |
| miller-gestures | Miller library gestures | ECoG | 5 | 84 @ 1000, 130 s |  |  | 4 hand gestures (rock/paper/scissors + rest) | classification | C | ok | 0.63 | part of the 7.5 GB Miller library (5 patients) |
| miller-joystick_track | Miller library joystick_track | ECoG | 4 | 60 @ 1000, 373 s |  |  | joystick cursor position/velocity | regression | R | ok |  | part of the 7.5 GB Miller library (4 patients) |
| miller-mouse_track | Miller library mouse_track | ECoG | 4 | 61 @ 1000, 248 s |  |  | mouse cursor position/velocity | regression | R | ok |  | part of the 7.5 GB Miller library (4 patients) |

## Brain-computer interface control (2)

| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dandi-001535 | Natraj/Ganguly long-term ECoG BCI, BRAVO1 neural features (DANDI 00153 | features | 1 | 256 @ 100, 2685 s | 4.7 GB |  | BCI target id (7 targets) from neural features | classification | C | ok | 0.39 | features only (high-gamma + low-frequency), no voltage |
| miller-imagery_feedback | Miller library imagery_feedback | ECoG | 4 | 40 @ 1000, 180 s |  |  | imagery-driven cursor feedback cue | classification | C | ok | 0.46 | part of the 7.5 GB Miller library (4 patients) |

## Speech production and naming (14)

| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dandi-000019 | Bouchard/Chang CV syllables (sub-EC9 B15) | ECoG | 4 | 256 @ 3052, 195 s | 55.6 GB |  | consonant-vowel syllables (read aloud) | classification | C S | ok | -0.04 | 256-ch vSMC grids, 4 patients |
| ds006910 | Auditory Naming | ECoG | 121 | 48 @ 1000, 1175 s | 47.9 GB | CC0 | auditory naming: question vs answer epochs | classification | C S | ok | 0.89 | 121 paediatric patients; kappa 0.89 on the smoke subject |
| ds006234 | Auditory naming | ECoG | 119 | 2 @ 1000, 3442 s | 47.2 GB | CC0 | auditory naming events | classification | C S | ok | 0.64 |  |
| ds005545 | auditory | ECoG | 106 | 2 @ 1000, 935 s | 42.9 GB | CC0 | auditory naming events | classification | C S | ok | 0.67 |  |
| ds006914 | Picture naming | ECoG | 110 | 48 @ 1000, 291 s | 18.8 GB | CC0 | picture naming events | classification | C S | ok | 0.23 |  |
| ds006233 | Picture naming | ECoG | 108 | 2 @ 1000, 777 s | 18.6 GB | CC0 | picture naming events | classification | C S | ok | 0.17 |  |
| duin | Du-IN Mandarin word sEEG (sub 001 run 1) | sEEG | 12 | 104 @ 1000, 1257 s | 12.0 GB |  | 61 Mandarin words (read aloud) | classification | C S | ok | 0.02 | 12 patients, 2 kHz; Du-IN reports about 62 % 61-way |
| ds005007 | Auditory naming task with questions that begin or end with a wh-interr | ECoG (100 % ECoG, 0 % sEEG) | 40 | 83 @ 1000, 880 s | 8.9 GB | CC0 | wh-question answering | classification | C S | ok |  |  |
| verwoert-speech | Verwoert single-word production sEEG (iBIDS) | sEEG | 10 | 127 @ 1024, 300 s | 2.8 GB |  | 100 Dutch words / audio spectrogram | classification | C S R | ok | 0.53 | events.tsv trial_type gives speech vs rest; word identity in the stimulus column |
| dandi-001193 | Shao IFG syntax/semantics high gamma | features | 1 | 256 @ 400, 74 s | 1.4 GB |  | syntax/semantics conditions (IFG high gamma) | classification | C S | ok |  |  |
| miller-speech_basic | Miller library speech_basic | ECoG | 7 | 48 @ 1000, 545 s |  |  | cued speech vs rest / word class | classification | C S | ok |  | part of the 7.5 GB Miller library (7 patients) |
| miller-speech_lists | Miller library speech_lists | ECoG | 3 | 48 @ 1000, 138 s |  |  | word lists (overt reading) | classification | C S | ok |  | part of the 7.5 GB Miller library (3 patients) |
| dandi-001638 | Cogan µECoG pseudoword repetition | uECoG |  |  |  |  | pseudoword repetition (Cogan lab) | classification | C S | blocked |  | no assets yet |
| metzger-2023 | Chang lab neuroprosthesis deposit (Zenodo restricted) | ECoG |  |  |  |  | sentences, phonemes, avatar (speech neuroprosthesis) | classification | C S | blocked |  | restricted Zenodo deposit |

## Auditory and language perception (6)

| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ds004703 | PassiveListen | unverified (0 % ECoG, 39 % sEEG) | 10 | 110 @ 1024, 1044 s | 13.3 GB | CC0 | natural speech (passive listening) | continuous | S R | ok |  | licence forbids ML training: check before use |
| tonal-speech | Li tonal speech perception ECoG, 4 awake-craniotomy patients (ScienceD | ECoG | 4 | 128 @ 400, 182 s | 6.1 GB |  | tone/syllable/word features of heard Mandarin | continuous | S R | ok |  |  |
| ds005574 | The "Podcast" ECoG dataset for modeling neural activity during natural | ECoG (90 % ECoG, 0 % sEEG) | 9 | 82 @ 512, 1800 s | 3.5 GB | CC0 | linguistic features of a 30-min podcast (encoding/decoding) | continuous | S R P | ok |  |  |
| ds005691 | SpinalExpect_Invasive | unverified (0 % ECoG, 0 % sEEG) | 8 | 7 @ 2500, 1602 s | 758 MB | CC0 | auditory deviant counting (oddball) | classification | C | ok |  |  |
| bellier-music | Bellier music reconstruction HFA, 29 patients (Zenodo 7876019) | features | 29 | 64 @ 100, 191 s | 400 MB |  | 32-band song spectrogram from HFA | regression | R S | ok |  | preprocessed HFA at 100 Hz, 29 patients |
| ds004993 | WIRED ICM Sample Dataset - Workshop on Intracranial Recordings in Huma | mixed (38 % ECoG, 62 % sEEG) | 3 | 148 @ 512, 68 s | 320 MB | CC0 | TIMIT sentences, movie trailers | continuous | S R | ok |  |  |

## Visual stimuli (11)

| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mindeye-ieeg | mindeye iEEG NSD high-frequency broadband | features | 12 | 130 @ 1, 9 s | 12.0 GB |  | NSD image identity/CLIP embedding from broadband | regression | R C | ok |  |  |
| ds004194 | Visual ECoG dataset | mixed (62 % ECoG, 22 % sEEG) | 14 | 140 @ 512, 59 s | 8.4 GB | CC0 | pRF stimuli, pattern/contrast conditions | classification | C | ok | 0.23 |  |
| dandi-000576 | Rutishauser amygdala aversive stimuli | sEEG | 9 | 2 @ 2000, 442 s | 2.2 GB |  | aversive vs neutral images | classification | C | ok | -0.25 |  |
| ds005953 | iEEG_visual | ECoG (100 % ECoG, 0 % sEEG) | 2 | 118 @ 3052, 234 s | 605 MB | CC0 | grating vs noise stimuli | classification | C | ok |  |  |
| ds003374 | Dataset of neurons and intracranial EEG from human amygdala during ave | sEEG (0 % ECoG, 100 % sEEG) | 9 | 4 @ 2000, 522 s | 175 MB | CC0 | visual stimuli | classification | C | ok |  |  |
| miller-faces_basic | Miller library faces_basic | ECoG | 14 | 46 @ 1000, 271 s |  |  | face vs house images | classification | C | ok | 0.27 | part of the 7.5 GB Miller library (14 patients) |
| miller-visual_search | Miller library visual_search | ECoG | 5 | 8 @ 1000, 510 s |  |  | attended direction in visual search | classification | C | ok | 0.16 | part of the 7.5 GB Miller library (5 patients) |
| miller-faces_noise | Miller library faces_noise | ECoG | 7 | 41 @ 1000, 268 s |  |  | face/house at 21 noise levels | classification | C | ok | 0.41 | part of the 7.5 GB Miller library (7 patients) |
| ds006253 | MetaRDK | sEEG (0 % ECoG, 100 % sEEG) | 21 |  | 1 MB | CC0 | random-dot motion decision and confidence | classification | C | unsupported |  | snapshot ships no recordings |
| cogitate | Cogitate iEEG release 1 | mixed | 38 |  | 300.0 GB |  | faces/objects/letters/false fonts, task relevance | classification | C | blocked |  | 38 patients; registration |
| dandi-001616 | SUMMER movie single-neuron | ECoG | 29 |  | 2.4 GB |  | visual stimuli | classification | C | blocked |  | single-unit spike times only; no field potentials or voltage in the NWB files (verified 2026-09-10 by opening the files) |

## Memory and cognition (19)

| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ds004789 | Delayed Free Recall of Word Lists | mixed | 280 | 88 @ 500, 4699 s | 618.8 GB | CC0 | free recall: encoding events, recalled vs forgotten | classification | C P | ok | 0.12 | RAM FR1, 280 patients |
| ds004809 | Categorized Free Recall: Delayed Free Recall of Word Lists Organized b | mixed | 258 | 162 @ 1600, 5400 s | 512.4 GB | CC0 | categorised free recall events | classification | C P | ok | 0.08 | RAM catFR1, 258 patients |
| ds005059 | Paired Associates Learning: Memory for Word Pairs in Cued Recall | mixed | 72 | 88 @ 500, 3647 s | 179.6 GB | CC0 | paired-associate learning events | classification | C | ok | -0.00 | RAM PAL1 |
| ds005411 | Free Recall of Word Lists with Repeated Items | mixed | 48 | 118 @ 1000, 4213 s | 169.0 GB | CC0 | repeated free recall events | classification | C | ok | 0.18 | RAM RepFR1 |
| ds005522 | Spatial Navigation Memory of Object Locations | mixed | 58 | 120 @ 500, 2361 s | 115.4 GB | CC0 | spatial navigation: position log, object location memory | continuous | R C | ok | 0.50 | RAM YC1; events.tsv is a dense position log |
| dandi-000574 | Rutishauser verbal WM + iEEG (sub-05 ses-01) | sEEG | 21 | 32 @ 32000, 400 s | 107.3 GB |  | verbal working-memory load | classification | C | ok | 0.02 |  |
| ds004865 | pyFR: Delayed Free Recall of Word Lists, Preliminary Cognitive Electro | mixed | 49 | 94 @ 400, 3102 s | 105.0 GB | CC0 | free recall events | classification | C | ok | 0.12 | RAM pyFR |
| ds005523 | Spatial Memory of Object Locations with Open-Loop Stimulation at Encod | mixed | 22 | 133 @ 500, 3421 s | 74.8 GB | CC0 | spatial navigation with stimulation | continuous | R C | ok | 0.59 | RAM YC2 |
| ds005624 | Color Change Detection Task | sEEG (0 % ECoG, 100 % sEEG) | 24 | 74 @ 512, 3280 s | 14.8 GB | CC0 | colour change detection | classification | C | ok |  |  |
| ds004752 | Dataset of intracranial EEG, scalp EEG and beamforming sources from ep | sEEG (0 % ECoG, 100 % sEEG) | 15 | 48 @ 2000, 400 s | 11.0 GB | CC0 | Sternberg working-memory load | classification | C | ok |  |  |
| ds004770 | iEEG on children during gameplay | ECoG (100 % ECoG, 0 % sEEG) | 10 | 126 @ 1000, 3755 s | 9.3 GB | CC0 | visuospatial working-memory game events | classification | C | ok | 0.40 |  |
| ds005415 | Numbers | sEEG (0 % ECoG, 100 % sEEG) | 13 | 188 @ 1000, 1449 s | 8.0 GB | CC0 | symbolic vs non-symbolic numbers, auditory vs visual | classification | C | ok |  |  |
| ds004473 | sEEG Forced Two-Choice Task | sEEG (0 % ECoG, 99 % sEEG) | 8 | 128 @ 999, 3646 s | 6.8 GB | CC0 | forced two-choice response | classification | C | ok |  |  |
| ds004859 | iEEG on children during Stroop task | ECoG (100 % ECoG, 0 % sEEG) | 7 | 108 @ 1000, 1040 s | 2.4 GB | CC0 | Stroop congruent vs incongruent | classification | C | ok |  |  |
| ds006136 | OWM-Dataset | unverified (0 % ECoG, 0 % sEEG) | 13 | 8 @ 1000, 1021 s | 300 MB | CC0 | object working memory (load 3) | classification | C | ok |  |  |
| miller-memory_nback | Miller library memory_nback | ECoG | 4 | 40 @ 1000, 360 s |  |  | n-back target vs non-target | classification | C | ok | 0.18 | part of the 7.5 GB Miller library (4 patients) |
| dandi-000469 | Rutishauser Sternberg WM | ECoG | 6 |  | 9.8 GB |  | memory task events | classification | C | blocked |  | single-unit spike times only; no field potentials or voltage in the NWB files (verified 2026-09-10 by opening the files) |
| dandi-000004 | Rutishauser declarative memory | ECoG | 59 |  | 6.2 GB |  | memory task events | classification | C | blocked |  | single-unit spike times only; no field potentials or voltage in the NWB files (verified 2026-09-10 by opening the files) |
| ebrains-* | EBRAINS memory+pupillometry, EEG+stimulation | sEEG |  |  |  |  | memory tasks with pupillometry | classification | C | blocked |  | EBRAINS account |

## Naturalistic, long-term (8)

| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dandi-000055 | AJILE12 (sub-04 ses-3) | ECoG | 12 | 84 @ 500, 600 s | 845.9 GB |  | wrist movement events, pose, behavioural state (55 days) | continuous | R C P | ok |  | AJILE12; 846 GB, subset mode |
| braintreebank | Brain Treebank (sub_1 trial000) | sEEG | 10 | 156 @ 2048, 600 s | 130.0 GB |  | Neuroprobe tasks: speech vs non-speech, pitch, volume, sentence onset, faces | classification | C S P | ok |  | 10 subjects, 43 h, 130 GB |
| dandi-000623 | Keles/Rutishauser movie watching (CS62) | sEEG | 1 | 56 @ 1000, 600 s | 27.7 GB |  | movie encoding vs recognition | classification | C P | ok |  |  |
| peterson-reach | Peterson naturalistic reach epochs (subj 01 day 3) | ECoG | 12 | 94 @ 500, 1716 s | 17.0 GB |  | reach events (epochs) | classification | C | ok |  |  |
| ds003688 | Open multimodal iEEG-fMRI dataset from naturalistic stimulation with a | mixed | 63 | 101 @ 2048, 420 s | 16.3 GB | CC0 | audiovisual film features; rest | continuous | S R P | ok | 0.10 |  |
| peterson-pose | Peterson ECoG + arm pose (EC02) | ECoG | 12 | 87 @ 250, 1672 s | 10.8 GB |  | 2-D arm pose trajectories | regression | R | ok |  |  |
| peterson-moverest | Peterson naturalistic move vs rest (EC09) | ECoG | 12 | 126 @ 250, 1208 s | 10.7 GB |  | move vs rest (video-derived wrist events) | classification | C | ok | 0.46 |  |
| dandi-001613 | Nentwich/Parra movies + eye tracking | sEEG |  |  | 5.9 GB |  | movies, images, eye tracking | continuous | C P | blocked |  | stimuli only so far |

## Non-human (5)

| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ds004127 | Somatosensory Cortex Rat DISC Data | uECoG | 8 | 104 @ 20000, 300 s | 201.4 GB | CC0 | rat somatosensory stimulation | classification | C | ok |  |  |
| ds006890 | Longitudinal Multitask Wireless ECoG Data from Two Fully Implanted Mac | ECoG | 2 | 31 @ 1000, 718 s | 44.2 GB | CC0 | button pressing, reaching, listening vs rest (macaque) | classification | C R | ok | 0.00 |  |
| ds008610 | FUS and Tactile Neuromodulation in NHP VPL - Electrophysiology | LFP+ECoG | 2 | 32 @ 1000, 71 s | 5.4 GB | CC0 | focused-ultrasound vs tactile stimulation (NHP thalamus) | classification | C | ok |  |  |
| neurotycho | Neurotycho macaque ECoG | ECoG | 4 |  | 50.0 GB |  | 3-D reach kinematics (motion capture), visual gratings, sleep/anaesthesia | regression | R C P | blocked |  | macaque 128-ch; Chao 2010 r 0.7-0.8 |
| crcns | CRCNS ECoG/LFP sets | ECoG |  |  |  |  | auditory/visual stimulation (various species) | classification | C | blocked |  | account |

## Electrical stimulation (CCEP, closed loop) (21)

| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ds004080 | CCEP ECoG dataset across age 4-51 | ECoG | 74 | 96 @ 512, 7200 s | 289.0 GB | CC0 | CCEP responses to single-pulse stimulation | classification | C | ok |  | 74 patients, 289 GB |
| ds005489 | Free Recall with Open-Loop Stimulation at Encoding | mixed | 38 | 88 @ 500, 4865 s | 69.7 GB | CC0 | free recall with open-loop stimulation | classification | C | ok | 0.08 | RAM FR2 |
| ds005448 | STReEF | ECoG | 13 | 112 @ 2048, 3245 s | 48.0 GB | CC0 | CCEP responses | classification | C | ok |  |  |
| ds005557 | Free Recall with Closed-Loop Stimulation at Encoding (Encoding Classif | mixed | 18 | 120 @ 1000, 3071 s | 37.2 GB | CC0 | free recall, closed-loop stimulation | classification | C | ok | 0.04 | RAM FR3 |
| ds004370 | PRIOS | ECoG | 7 | 48 @ 2048, 2359 s | 29.6 GB | CC0 | CCEP responses | classification | C | ok |  |  |
| ds005494 | Cued Recall of Paired Associates with Open-Loop Stimulation at Encodin | mixed | 20 | 114 @ 500, 2463 s | 28.3 GB | CC0 | paired associates with stimulation | classification | C | ok | 0.03 | RAM PAL2 |
| ds004774 | Automatic Evoked Response Detection (ER-Detect) dataset | ECoG | 14 | 76 @ 2048, 600 s | 26.6 GB | CC0 | CCEP responses | classification | C | ok |  | MEF3 |
| ds005491 | Categorized Free Recall with Open-Loop Stimulation at Encoding | mixed | 19 | 177 @ 500, 3499 s | 24.2 GB | CC0 | categorised recall with stimulation | classification | C | ok | 0.27 | RAM catFR2 |
| ds004696 | HAPwave_bids | ECoG | 8 | 162 @ 2048, 600 s | 15.2 GB | CC0 | CCEP responses | classification | C | ok |  | MEF3 |
| ds005558 | Categorized Free Recall with Closed-Loop Stimulation at Encoding (Enco | ECoG (86 % ECoG, 14 % sEEG) | 9 | 122 @ 1000, 3004 s | 13.1 GB | CC0 | categorised recall, closed-loop stimulation | classification | C | ok | 0.11 | RAM catFR3 |
| ds004457 | Electrical stimulation of temporal and limbic circuitry produces disti | mixed | 5 | 154 @ 2048, 600 s | 11.7 GB | CC0 | CCEP responses | classification | C | ok |  | MEF3 |
| ds005169 | Dataset of intracranial EEG during cortical stimulation evoking visual | sEEG (0 % ECoG, 100 % sEEG) | 20 | 29 @ 4096, 21 s | 4.3 GB | CC0 | stimulation responses | classification | C | ok |  |  |
| ds004977 | CARLA: Adjusted common average referencing for cortico-cortical evoked | sEEG (0 % ECoG, 93 % sEEG) | 4 | 210 @ 4800, 543 s | 1.6 GB | CC0 | CCEP responses | classification | C | ok |  | MEF3 |
| ds006519 | Dataset of intracranial EEG during cortical stimulations evoking negat | sEEG (0 % ECoG, 100 % sEEG) | 21 | 63 @ 4096, 30 s | 1.1 GB | CC0 | stimulation responses | classification | C | ok |  |  |
| ds003708 | Basis profile curve identification to understand electrical stimulatio | ECoG (85 % ECoG, 13 % sEEG) | 1 | 76 @ 2048, 600 s | 650 MB | CC0 | CCEP responses | classification | C | ok |  | MEF3 |
| ds006392 | HED schema library for SCORE annotations example | mixed | 1 | 194 @ 512, 191 s | 34 MB | CC0 | photic stimulation responses | classification | C | ok |  | MEF3 |
| dandi-000571 | Mayo CorTec BrainInterchange (MEF3) | ECoG |  |  | 21.6 GB |  | CorTec BrainInterchange device recordings (BCI2000 tasks) | classification | C P | blocked |  | MEF3 folders on DANDI |
| ds007703 | Single pulse electrical stimulation in white matter modulates iEEG vis | unverified | 2 |  | 12.3 GB | CC0 | stimulation responses | classification | C | blocked |  |  |
| dabi-* | DABI public projects (MGH stimulation/conversation, UTSW motor, Sheth, | mixed |  |  |  |  | single-pulse and theta-burst stimulation; UTSW motor tasks with DBS | classification | C R | blocked |  | DABI account required to download |
| ds006254 | IEEG CCEP Recording | mixed | 30 |  | 168.3 GB | CC0 | CCEP on anti-seizure medication | classification | C | error |  | files served with GET only |
| ds004624 | Intracranial recordings using BCI2000 and the CorTec BrainInterchange | ECoG | 3 |  | 20.7 GB | CC0 | CorTec BrainInterchange recordings | pretraining | P | error |  | MEF3, intraoperative |

## Clinical (seizures, HFO, artefacts) (18)

| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swec | SWEC long-term iEEG (ID01 part 1) | sEEG | 68 | 88 @ 512, 600 s | 4600.0 GB |  | seizure onset (long-term) | classification | P C | ok |  | 4.6 TB on Hugging Face; research-only licence |
| omni-edf | Omni-iEEG raw EDF (Pt1) | mixed | 55 | 38 @ 2000, 601 s | 159.0 GB |  | HFO / spike / artefact labels | classification | C P | ok |  |  |
| ds003848 | Dataset Clinical Epilepsy iEEG to BIDS - RESPect_longterm_iEEG | mixed | 6 | 54 @ 2048, 3187 s | 69.8 GB | CC0 | long-term epilepsy monitoring | pretraining | P | ok | 0.48 |  |
| ds003498 | iEEG Interictal Asleep HFO Dataset | mixed | 20 | 50 @ 2000, 300 s | 48.0 GB | CC0 | interictal HFO annotations | classification | C P | ok |  |  |
| ds004100 | ds004100 | ECoG (100 % ECoG, 0 % sEEG) | 57 | 59 @ 500, 378 s | 14.2 GB | CC0 | ictal vs interictal | classification | C P | ok |  |  |
| ds003078 | PROBE iEEG | sEEG | 6 | 130 @ 512, 584 s | 11.8 GB | CC0 | none documented (PROBE clinical iEEG) | pretraining | P | ok |  |  |
| ds003029 | iEEG Fragility Epileptogenic Zone | ECoG (92 % ECoG, 0 % sEEG) | 35 | 126 @ 1000, 142 s | 11.1 GB | CC0 | ictal vs interictal, seizure onset zone | classification | C P | ok |  |  |
| ds003876 | Epilepsy-iEEG-Interictal-Multicenter-Dataset | mixed (41 % ECoG, 59 % sEEG) | 39 | 186 @ 1024, 573 s | 5.4 GB | CC0 | interictal | pretraining | P | ok |  |  |
| ds003844 | RESPect | mixed (62 % ECoG, 0 % sEEG) | 6 | 31 @ 2048, 325 s | 2.8 GB | CC0 | acute epilepsy monitoring | pretraining | P | ok | 0.00 |  |
| ds004642 | Intraoperative recordings of medianus stimulation with low and high im | ECoG (100 % ECoG, 0 % sEEG) | 10 | 8 @ 20000, 672 s | 1.3 GB | CC0 | seizure / interictal events | classification | C P | ok |  |  |
| ds004819 | Flexible, Scalable, High Channel Count Stereo-Electrode for Recording  | sEEG (0 % ECoG, 100 % sEEG) | 1 | 64 @ 30000, 25 s | 722 MB | CC0 | none (high channel-count electrode demonstration) | pretraining | P | ok |  |  |
| ds007095 | RNS_Epilepsy-iBIDS | sEEG (0 % ECoG, 100 % sEEG) | 8 | 2 @ 200, 91 s | 522 MB | CC0 | chronic RNS recordings | pretraining | P | ok |  |  |
| ds004944 | Dataset of BCI2000-compatible intraoperative ECoG with neuromorphic en | ECoG (100 % ECoG, 0 % sEEG) | 22 | 15 @ 2000, 500 s | 473 MB | CC0 | HFO / epileptiform detection, pre vs post resection | classification | C P | ok |  |  |
| ds005083 | Safety and Accuracy of Stereoelectroencephalography for Pediatric Pati | sEEG | 60 |  | 0 MB | CC0 | none (paediatric sEEG safety cohort) | none |  | unsupported |  | snapshot ships no recordings |
| kaggle-seizure | UPenn/Mayo and Melbourne seizure competitions | mixed |  |  |  |  | seizure detection / prediction (humans + dogs) | classification | C | blocked |  | Kaggle API token + competition rules |
| ieeg-org | iEEG.org | mixed |  |  |  |  | seizures, clinical annotations | classification | C P | blocked |  | account |
| epilepsiae | EPILEPSIAE | mixed |  |  |  |  | long-term seizure recordings (275 patients) | classification | C P | blocked |  | restricted |
| gin-usz | GIN USZ intraoperative HFO | ECoG |  |  |  |  | intraoperative HFO | classification | C | blocked |  | duplicate of ds004944 |

## Rest and sleep (unlabeled) (15)

| entry | dataset | modality | subjects | first run: ch @ Hz, s | size | licence | decoding target | kind | fit | MOECoG status | quick kappa | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ds005398 | Open iEEG Dataset | ECoG | 185 | 56 @ 1000, 304 s | 109.7 GB | CC0 | none (interictal sleep) | pretraining | P | ok |  | 185 paediatric patients |
| ds004551 | testMIproject | ECoG | 114 | 117 @ 1000, 1925 s | 74.0 GB | CC0 | none (interictal sleep) | pretraining | P | ok |  |  |
| ds007118 | iEEG_comprehensive_HFA_model_part1 | ECoG | 65 | 106 @ 1000, 2269 s | 36.3 GB | CC0 | none (interictal sleep) | pretraining | P | ok |  |  |
| ds007120 | iEEG_comprehensive_HFA_model_part2 | ECoG | 65 | 128 @ 1000, 1605 s | 35.4 GB | CC0 | none (interictal sleep) | pretraining | P | ok |  |  |
| ds007119 | iEEG_comprehensive_HFA_model_part3 | ECoG | 103 | 132 @ 1000, 3367 s | 35.0 GB | CC0 | none (interictal sleep) | pretraining | P | ok |  |  |
| ds006107 | iEEG_Neural_spatial_volatility | ECoG (100 % ECoG, 0 % sEEG) | 166 | 100 @ 1000, 320 s | 12.8 GB | CC0 | none (interictal sleep) | pretraining | P | ok |  |  |
| ds006065 | TSS_iEEG | sEEG (0 % ECoG, 100 % sEEG) | 7 | 168 @ 500, 1570 s | 10.3 GB | CC0 | none (rest/sleep) | pretraining | P | ok |  |  |
| rogers-uecog | Rogers submillimeter µECoG windows (S2) | uECoG | 4 | 44 @ 4000, 652 s | 6.4 GB |  | none (unlabeled 2 s windows) | pretraining | P | ok |  |  |
| ds005670 | SEEG Resting State Recording | unverified | 2 | 238 @ 2000, 433 s | 743 MB | CC0 | none (rest/sleep) | pretraining | P | ok |  |  |
| miller-fixation_PAC | Miller library fixation_PAC | ECoG | 10 | 46 @ 1000, 130 s |  |  | none (fixation rest) | pretraining | P | ok |  | part of the 7.5 GB Miller library (10 patients) |
| miller-fixation_pwrlaw | Miller library fixation_pwrlaw | ECoG | 20 | 32 @ 1000, 130 s |  |  | none (fixation rest) | pretraining | P | ok |  | part of the 7.5 GB Miller library (20 patients) |
| miller-fixation_highfreq | Miller library fixation_highfreq | ECoG | 4 | 32 @ 10000, 130 s |  |  | none (fixation rest) | pretraining | P | ok |  | part of the 7.5 GB Miller library (4 patients) |
| ds002799 | Human es-fMRI Resource: Concurrent deep-brain stimulation and whole-br | unverified | 26 |  | 19.9 GB | CC0 | none (rest/sleep) | pretraining | P | unsupported |  |  |
| ds005592 | ds005592 | ECoG |  |  | 0 MB | None | none (interictal sleep) | pretraining | P | blocked |  | deleted duplicate of ds006107 |
| mni-atlas | MNI Open iEEG Atlas | mixed | 106 |  |  |  | none (normal wake/sleep iEEG atlas) | pretraining | P | blocked |  | HTTP 401: registration |

## Reading the table

- *kind*: regression = a continuous behavioural signal is recorded alongside (finger flexion, cursor, force, pose, audio spectrogram); classification = discrete trials with labels; continuous = naturalistic signal with time-aligned annotations (encoding/decoding both possible); pretraining = no behavioural labels.
- *status*: ok = downloaded, loaded and (when a trial paradigm applies) scored by `scripts/smoke_test.py`; unsupported = the files hold no usable field potentials or use a format we cannot read yet; blocked = account, DUA or a repository problem (see `docs/dataset_catalog.md`).
- *quick kappa*: LogBandPower + LDA, 3 chronological folds, one subject. A sanity check, not a benchmark.
