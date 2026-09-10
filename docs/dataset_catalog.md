# Catalog of obtainable ECoG and intracranial datasets

Compiled 2026-09-09/10 for MOECoG. Method: API sweeps of OpenNeuro (74 datasets
with an iEEG modality, GraphQL), DANDI (628 dandisets scanned by name and
metadata), DABI (38 public projects), figshare, Harvard Dataverse, OSF, G-Node
GIN and CRCNS, plus the openlists/ElectrophysiologyData and data2bids lists,
data-availability statements of the main decoding papers, and lab pages. Raw
snapshots are in `docs/catalog/*.json`. Zenodo's API rejected every query that
day; its entries come from paper links.

Every entry answers the same questions: where is it, who may use it, what was
recorded, what task, how big, which numbers were published on it, what the
source paper did to the signal, and what MOECoG will do with it. "Baseline"
means the number the source group reports; "verify" flags numbers quoted from
memory that must be checked against the paper before we print them.

Tiers:

- **T1 Human ECoG, task-based** (subdural grids/strips, cued or continuous
  behaviour): the core of MOECoG.
- **T2 Human iEEG task datasets with sEEG or mixed contacts**: same loaders,
  channel type tagged; inclusion is a scope decision (PRSNL-75).
- **T3 Naturalistic and long-term human recordings**.
- **T4 Rest, sleep, stimulation and clinical (seizure) datasets**: controls,
  pretraining corpora, and a possible clinical tier.
- **T5 Non-human ECoG**: methods development and cross-species questions.
- **T6 By request or restricted**: the outreach list.

## T1 Human ECoG, task-based

| Dataset | Where / ID | Access | Patients, electrodes | Task | Size, format | Published results | Source preprocessing | MOECoG plan |
|---|---|---|---|---|---|---|---|---|
| Stanford/Miller ECoG library | purl.stanford.edu/zk881ps0522 | public, cite + ethics text | 34 (36 codes), 7-102 ch grids/strips, 1 kHz | 16 experiments: finger, joystick, mouse, hand/tongue, gestures, imagery, faces, n-back, visual search, speech, fixation | 7.5 GB, .mat | Miller 2007/2010/2012/2016 (neuroscience); TRACE 0.508 r Miller-9; PACE continuous tier; MOECoG baselines (`docs/baselines.md`) | scalp ref, CAR in scripts, broadband via PCA decoupling, 1-pole 0.15-200 Hz | **done** (all 16 loaders) |
| BCI Competition IV dataset 4 | bbci.de/competition/iv (also `BCI_Competion4_dataset4_data_fingerflexions.zip` in the Miller SDR deposit; Kaggle mirrors) | public, agree to cite | 3, 48-64 ch, 1 kHz | finger flexion regression, fixed 400 k / 200 k split | 222 MB .mat | Kubanek 2009; competition winner Liang & Bougrain r 0.46 (verify); FingerFlex 0.66; DTCNet 0.70; TRACE 0.724; PACE DTCNet-5M + channel dropout 0.732 (10 seeds) | Lomtev: 40 log-spaced Morlet 40-300 Hz, 100 Hz, robust scaling; band powers + LMP in classic work | wave 1 (reuse PACE loader) |
| BCI Competition III dataset I | bbci.de/competition/iii | public, agree to cite | 1, 64 ch 8x8 grid, 1 kHz | motor imagery left pinky vs tongue, 278 train / 100 test, sessions one week apart | small, ASCII/.mat | competition winner 91 % accuracy (Lal et al.; verify) | none published with the data; classic band-power + CSP | wave 1 (cross-session evaluation) |
| Bouchard/Chang CV syllables | DANDI 000019 | public, CC-BY-4.0 | 4, 256-ch high-density ECoG over vSMC | reading consonant-vowel syllables | 55.6 GB NWB | Bouchard 2013 Nature: vSMC somatotopy, CV decoding from high gamma (numbers: verify) | notch, CAR per 16-ch block, Hilbert high gamma 70-150 Hz (8 bands), z-score, 200-400 Hz | wave 2 (NWB loader; speech tier) |
| Naturalistic arm movements (Peterson/Brunton) | figshare project 78666: 12115728 (reach epochs, 17 GB .fif), 13010546 (move vs rest, 10.7 GB .nc), 16599782 (ECoG + 2-D pose, 10.8 GB .nc) | public, CC-BY-4.0 | 12, clinical grids, 500 Hz | wrist movement events from video pose; move vs rest classification; arm position | see left | Peterson 2021 eNeuro (variability); HTNet (Peterson 2021 JNE) move vs rest within/cross participant (verify numbers) | Hilbert envelopes in HTNet; CAR; 500 Hz | wave 1 (MNE .fif epochs load directly) |
| Grip-force decoding in Parkinson's (Merk/Neumann) | Harvard Dataverse doi:10.7910/DVN/IO2FLM | public, CC0 | 11, 6-contact ECoG strips over sensorimotor + STN LFP, intraoperative | grip-force regression during DBS surgery | 1.4 GB, 537 files (BIDS-like) | Merk 2022 eLife: ECoG > STN; XGBoost on py_neuromodulation features (R2: verify) | py_neuromodulation: 100 ms windows, band power 6 bands, Hjorth, sharp-wave features, 10 s normalisation | wave 2 (regression, clinical population) |
| Long-term ECoG BCI, tetraplegic participant (Natraj/Ganguly) | DANDI 001535 | public, CC-BY-4.0 | 1, 128-ch grid over sensorimotor, multi-day | imagined movements toward 7 targets, BCI control | 4.8 GB NWB | Natraj 2025 Cell: stable manifold, drift statistics (decoder accuracies: verify) | lab pipeline (Hilbert, delta + high gamma; verify) | wave 2 (temporal-stability evaluation) |
| Visual ECoG (Groen/Winawer/Flinker) | OpenNeuro ds004194 | public, CC0 | 14, ECoG + some sEEG, occipital | pRF mapping, spatial/temporal pattern, second-order contrast | 8.4 GB BIDS | Groen 2022 J Neurosci; Yuasa 2023 eLife; Brands 2024 (encoding models, not decoding) | CAR, broadband 70-150 Hz via multi-band, epoch baseline | wave 1 (BIDS loader) |
| Hermes visual (2 subjects) | OpenNeuro ds005953 | public, CC0 | 2 | visual gratings/noise | 0.6 GB BIDS | Hermes 2015/2017 | CAR, gamma/broadband | wave 1 test dataset for the BIDS loader |
| Detroit/Wayne State naming corpus (Asano lab) | ds006910 (121), ds006234 (119), ds005545 (106) auditory naming; ds006914 (110), ds006233 (108) picture naming; ds005007 (40) wh-questions; ds004770 (10) visuospatial WM game; ds004859 (7) Stroop; ds005931 (10) visuomotor game | public, CC0 | 100+ each, mostly paediatric subdural grids, MNI305 coordinates, EDF | naming (stimulus onset/offset, response onset codes 401/402/501), working memory, Stroop, visuomotor | 13-48 GB each | Kochi 2025, Kanno 2025 (dynamic tractography; no decoding baseline) | clinical montage, event codes in EDF | wave 2 (BIDS loader; largest ECoG language corpus anywhere) |
| Intraoperative ECoG, Zurich (Costa/Sarnthein) | OpenNeuro ds004944 | public, CC0 | 22 | pre/post resection, HFO/epileptiform detection | 0.5 GB BIDS | Costa 2024 Nat Commun (SNN detection) | BCI2000 stream, ADM encoding | T4 (clinical) |
| CCEP ECoG across age (van Blooijs/Hermes) | ds004080 (74); related ds004774 (14), ds005448 (13), ds004370 (7), ds004696 (8), ds004977 (4) | public, CC0 | 74, grids, ages 4-51 | single-pulse stimulation responses | 289 GB | van Blooijs 2023 (transmission speed) | CARLA referencing | T4 (stimulation tier, later) |
| CorTec BrainInterchange + BCI2000 (Mayo) | ds004624 / DANDI 000571 | public, CC0 | 3-5, intraoperative | device ecosystem recordings | 21 GB, MEF3 | Mivalt (in prep) | BCI2000 | later |
| Micro-ECoG, submillimeter (Rogers/Dayeh) | figshare 7633418 | public, CC-BY-4.0 | 2 human + 2 mouse | unlabeled 2 s windows | 6.4 GB .mat | Rogers 2019 PLoS CB (correlation structure) | none | unsupervised/pretraining only |
| Sensorimotor alpha/beta (Stolk) | OSF z4hfm | public | 3, high-density grids | motor task, rhythms | small | Stolk 2019 eLife | see paper | later |
| RAVE demo ECoG (Beauchamp) | DABI 1R24MH117529 | public | few | audiovisual speech | 5.9 GB | RAVE software paper | RAVE pipeline | later |

## T2 Human iEEG task datasets (sEEG or mixed contacts)

| Dataset | Where / ID | Access | Patients | Task | Size | Published results | Source preprocessing | MOECoG plan |
|---|---|---|---|---|---|---|---|---|
| RAM (Restoring Active Memory, Kahana lab) | OpenNeuro ds004789 FR1 (280), ds004809 catFR1 (258), ds005059 PAL1 (72), ds004865 pyFR (49), ds005411 RepFR1 (48), ds005522 YC1 (58), stimulation sets ds005489 FR2, ds005491 catFR2, ds005494 PAL2, ds005523 YC2, ds005557 FR3, ds005558 catFR3; also memory.psych.upenn.edu/RAM_Public_Data | public, CC0 | 251+ , grids + depths | free recall, categorised recall, paired associates, spatial navigation; recalled vs forgotten classification | 0.1-0.6 TB per set | Ezzyat 2017/2018, Kragel 2017: encoding classifier AUC about 0.6-0.7 (verify) | Morlet log-power 8 bands 3-180 Hz, z-scored per session, L2 logistic regression | wave 2 (BIDS loader; memory tier) |
| Cogitate iEEG | cogitate-data.ae.mpg.de (registration) | public after registration | 38, ECoG + sEEG, 3 centres | faces/objects/letters/false fonts x 3 durations, Go/No-Go | BIDS | Sci Data 2025 (Seedat et al.); cog_ieeg package | notch, re-ref, HGA + ERP | wave 2 (visual categorisation) |
| Brain Treebank + Neuroprobe | braintreebank.dev; github insight-neuro/neuroprobe | public, CC-BY-4.0 | 10, sEEG, 2048 Hz, 43 h | Hollywood movies; Neuroprobe tasks (sentence onset, speech vs non-speech, volume, pitch, GPT-2 surprisal, word position, speaker, faces...) | 130 GB HDF5 | BrainBERT, PopT, MVPFormer, DIVER-1 on Neuroprobe (leaderboard) | Laplacian re-ref, STFT/superlets, 1 s windows | wave 3 (compare with foundation-model benchmarks) |
| Podcast ECoG (Zada/Hasson/Flinker) | OpenNeuro ds005574 (Zenodo mirror 18561340) | public, CC0 | 9, 1330 electrodes (grids + depths) | 30-min story listening; encoding of linguistic features | 3.5 GB BIDS | encoding models with LLM embeddings (tutorials) | notch, CAR, high gamma 70-200 Hz envelope, 512 Hz | wave 1 (BIDS loader; encoding paradigm) |
| Film iEEG-fMRI (Berezutskaya/Ramsey) | OpenNeuro ds003688 | public, non-commercial | 51 iEEG (ECoG + sEEG) + 30 fMRI | 6.5-min audiovisual film, rest | 16 GB BIDS | Berezutskaya 2020/2022 (speech/audio encoding) | CAR, high frequency band | wave 1 (BIDS loader) |
| Speech production sEEG (Verwoert/Herff) | OSF nrgx6 | public | 10, 1103 electrodes | reading 100 Dutch words, audio | BIDS-like | linear regression high gamma to spectrogram (r: verify) | Hilbert 70-170 Hz, 50 ms windows, context stacking | wave 2 (speech tier) |
| Du-IN (Liu lab) | huggingface.co/datasets/liulab-repository/Du-IN | public, CC-BY-4.0 | 12, sEEG 72-158 ch, 2 kHz | 61 Mandarin words x 50 reps, audio | large | Du-IN 2024: 61-way word classification about 62 % (verify) | 1-200 Hz, notch, VQ tokens | wave 3 |
| VocalMind | Sci Data 2025 (He et al.) | public | 1, sEEG | vocalised / mimed / imagined Mandarin | 68 min, CSV/npy | see paper | see paper | later |
| Music decoding (Bellier/Knight) | Zenodo 7876019 | public | 29, ECoG + depths | passive listening to a Pink Floyd song | preprocessed HFA 70-150 Hz at 100 Hz + spectrogram | Bellier 2023 PLoS Biol: MLP beats linear, spectrogram r up to about 0.4 (verify) | HFA Hilbert 70-150 Hz | wave 2 (auditory regression) |
| MGH conversation (Paulk) | DABI M6RES1N4MVA3 | public | many, sEEG | natural conversation with NLP annotations | 279 GB | Nat Commun 2025 | see paper | wave 3 |
| Verbal working memory (Dimakopoulos/Sarnthein) | ds004752 (+ GIN) | public, CC0 | 15, iEEG + scalp | modified Sternberg | 11 GB | eLife 2022 | see paper | later |
| Object working memory (Smith lab) | ds006136 | public, CC0 | 13 | load-3 OWM | 0.3 GB processed | NeuroImage 2026 | see paper | later |
| Colour change detection | ds005624 | public, CC0 | 24 | CCDT | 15 GB | ? | ? | later |
| Numbers (Rockhill/Raslan) | ds005415 | public, CC0 | 13 sEEG | symbolic/non-symbolic numbers, auditory + visual | 8 GB | ? | ? | later |
| Forced two-choice (Rockhill/Swann) | ds004473 | public, CC0 | 8 sEEG | choice response | 7 GB | Rockhill 2022 | ? | later |
| MetaRDK (Faivre lab, Grenoble) | ds006253 | public, CC0 | 21 | random-dot motion decision + confidence | ? | Goueytes 2024 bioRxiv | ? | later |
| Passive listening (Mai/Gentner) | ds004703 | public, non-commercial, no ML-training clause | 10 sEEG | natural speech | 13 GB | ? | ? | check licence before use |
| WIRED sample (Hamilton lab) | ds004993 | public, CC0 | 3 | movie trailers, TIMIT | 0.3 GB | tutorial | high gamma | loader test only |
| Memory tasks with pupillometry | EBRAINS 10.25493/GKNT-T3X | public | 10 sEEG | memory | ? | Sci Data 2021 | ? | later |
| Rutishauser single-neuron + iEEG sets | DANDI 000004, 000469, 000574, 000575, 000576, 000623, 000673, 001187, 001616; DABI mirrors | public, CC-BY-4.0 | 9-59 | memory, WM, movie watching | 2-107 GB NWB | many | see papers | macro-contact subsets only |
| Nentwich/Parra movies + eye tracking | DANDI 001613 | public (assets partly draft) | 46 | movies, images, rest | ? | ? | ? | check when complete |
| iEEG Natural Scenes (JOV 2024) | location to confirm | ? | 12 | 1000 NSD images | ? | JOV 2024 | ? | ask authors |
| Kuzovkin images (GIN) | gin.g-node.org/ilyakuzovkin/... | public | up to 100 (Lyon) | image categories | ? | Kuzovkin 2018 Comm Bio | processed gamma | verify contents |

## T3 Naturalistic and long-term

| Dataset | Where / ID | Access | Patients | Content | Size | Published results | MOECoG plan |
|---|---|---|---|---|---|---|---|
| AJILE12 (Peterson/Brunton) | DANDI 000055 | public, CC-BY-4.0 | 12, grids, 500 Hz, 55 days | continuous ECoG + pose + wrist movement events + behavioural states | 846 GB NWB | Peterson 2022 Sci Data; HTNet | wave 2 (NWB loader, subset mode) |
| Brain Treebank, Podcast, film, Nentwich | see T2 | | | | | | |

## T4 Rest, sleep, stimulation, clinical

| Dataset | Where / ID | Access | Patients | Content | Size | Notes |
|---|---|---|---|---|---|---|
| MNI Open iEEG Atlas | mni-open-ieegatlas.research.mcgill.ca | public | 106 wake, 91 sleep | curated normal iEEG | ? | reference for normal spectra |
| Detroit paediatric sleep corpora | ds005398 (185), ds004551 (114), ds006107 (166), ds007118-120 (233) | public, CC0 | 100+ each | interictal sleep iEEG, MNI305 | 13-110 GB | pretraining and control tier |
| Multicentre resting/sleep (Nejedly, Mayo/Brno) | figshare c.4681208 | public | 39 | annotated artefacts/graphoelements | ? | Sci Data 2020 |
| SWEC-ETHZ iEEG | ieeg-swez.ethz.ch | public | 16-18 | long-term, seizures | large | seizure detection benchmark |
| Epilepsy multicentre (Li/Crone), HUP, interictal | ds003029 (35), ds004100 (57), ds003876 (39) | public, CC0 | 130 | ictal/interictal | 5-14 GB | fragility papers |
| RESPect (Utrecht) | ds003844 (6), ds003848 (6) | public, CC0 | 12 | acute/long-term epilepsy | 73 GB | |
| HFO datasets | ds003498 (20), GIN USZ_NCH intraoperative (22), figshare 26131978 IEDs (25) | public | 67 | interictal HFO/IED annotations | 48 GB | |
| RNS chronic | ds007095 | public, CC0 | 8 | responsive neurostimulation ECoG | 0.5 GB | |
| Kaggle seizure sets | UPenn/Mayo (2 humans + 5 dogs), Melbourne (3 humans, months) | Kaggle terms | 5 | seizure detection/prediction | large | |
| Bern-Barcelona | Andrzejak 2012 | public | 5 | focal vs non-focal pairs | small | |
| EPILEPSIAE | restricted | 275 | long-term | huge | request |
| iEEG.org | portal account | many | clinical | huge | |
| Stimulation: MGH single pulse (DABI W4SNQ7HR49RL, 52 pts, 462 GB), theta-burst (DQQ4HVHLTRS6), UTSW cortex-basal ganglia intraoperative ECoG + DBS motor tasks (DABI 1U01NS098961, 236 GB), es-fMRI ds002799 (26), CCEP sets above | DABI/OpenNeuro | public | | | | UTSW set has motor tasks: check |

## T5 Non-human ECoG

| Dataset | Where | Access | Animals | Content | Notes |
|---|---|---|---|---|---|
| Neurotycho (RIKEN, Fujii lab) | neurotycho.org/download | public | macaques (128-ch subdural, epidural), marmoset | food tracking with motion capture (3-D reach decoding), visual grating, social, emotional movie, sleep, anaesthesia, auditory oddball, fixation, EEG+ECoG, spatial map | continuous reach decoding baseline: Chao 2010, Chen 2013 (r about 0.7-0.8; verify) |
| Longitudinal wireless ECoG, two macaques (Osaka) | OpenNeuro ds006890 | public, CC0 | 2 | rest, SEP, button pressing, listening, reaching over hundreds of days | 44 GB BIDS; Sci Data 2026 |
| PtNRGrids rat barrel cortex (Dayeh) | DANDI 000465/000554 | public, CC-BY-4.0 | 4 rats | 1024-ch 150-um pitch µECoG | 129 GB |
| Rat DISC somatosensory | ds004127 | public | 8 | 201 GB | |
| GIN rat ITD/ECoG (Escabi), CRCNS sets | GIN, crcns.org | public | | auditory | |

## T6 By request or restricted (outreach list)

| Dataset / group | What exists | Status | Why we want it |
|---|---|---|---|
| Chang lab speech neuroprosthesis (Metzger 2023 Zenodo 8200782; Moses 2021; Anumanchipalli 2019) | 253-ch ECoG, sentences, avatar | restricted deposit / on request | speech tier anchor; published WER/CER baselines |
| NYU Flinker lab (Chen 2024 Nat Mach Intell, 48 participants, 5 speech tasks) | ECoG grids + depths | code public, example data only | largest speech-production ECoG cohort |
| HUST-MIND Mandarin sEEG (Tongji) | sEEG speech | on request | tonal-language speech |
| Duke Cogan/Viventi µECoG speech (Duraivel 2023) | 128/256-ch LCP µECoG, 20 kHz, 4 participants | source data only | high-density speech |
| UCSD Dayeh human PtNRGrids (Sci Transl Med 2022) | 1024-2048-ch µECoG intraoperative | not deposited | high-density motor/sensory |
| Utrecht HD-ECoG gestures (Branco 2017; Bleichner 2016) and UNP home-use BCI (Vansteensel 2016) | HD grids, 4 gestures; chronic BCI | on request | gesture tier; chronic implant |
| Chestek (Michigan) µECoG finger; Slutzky (Northwestern) speech/motor ECoG; Crone (JHU) finger/speech; Leuthardt (WashU); Ball/Pistohl (Freiburg) grasp; Schalk/Brunner (NCAN) cursor/P300 | classic motor ECoG | on request | historical motor benchmarks |
| Osaka (Yanagisawa/Kishima) human ECoG BCI, video semantics | ECoG | on request | Japanese cohort |
| Kai Miller (Mayo) newer datasets, DANDI 000571 tasks | | ask | continuity with the library |
| Cogitate experiment 2 (video game) | forthcoming | wait | |
| Precision Neuroscience, Synchron, Paradromics | commercial | unlikely | |

## Additions from the code-hosting sweep (GitHub, Hugging Face; 2026-09-10)

| Dataset | Where / ID | Access | Patients, electrodes | Task | Size, format | Notes | MOECoG plan |
|---|---|---|---|---|---|---|---|
| Tonal speech perception ECoG (Li lab) | github.com/yuanningli/ECoG_Tonal_Speech_Perception, data on Zenodo (record to locate) | public | 4 awake-craniotomy participants, 128-256-ch grids | listening to continuous Mandarin sentences (ASCCD corpus); word/syllable/tone/prosody annotations | NWB (BIDS-iEEG), high gamma 70-150 Hz at 400 Hz | described as a decoding benchmark; no paper located yet | wave 2 (NWB loader) |
| SWEC iEEG on Hugging Face | huggingface.co/datasets/NeuroTec/SWEC_iEEG_Dataset | public, CDLA-Permissive-2.0 (research only) | 68 patients, 64 ch, 512/1024 Hz, 9,328 h, 704 seizures | long-term clinical iEEG | 4.6 TB HDF5 (about 10 GB parts) | used to pretrain MVPFormer (Carzaniga 2025) | smoke test one part; clinical tier |
| Omni-iEEG | huggingface.co/datasets/Omni-iEEG/Omni-iEEG (+ Dadaism6/Omni-iEEG-Raw-Event-EDF) | public | multi-centre; 36k HFO waveform rows; 55 ten-minute EDF clips | HFO / spike / artefact labels | 159 GB parquet + EDF | BIDS-like derivatives with anatomical mapping and a train/test split | smoke test one EDF; clinical tier |
| iEEG Natural Scenes derivatives (mindeye_ieeg) | huggingface.co/datasets/rishab-iyer1/mindeye_ieeg | public | 12 patients (JOV 2024), 92 visually responsive electrodes | 1000 NSD images; high-frequency broadband per image | 12 GB npy + CLIP embeddings | the processed form of the iEEG NSD dataset the catalog could not locate | loader reads channel/stimulus tables; array optional |
| Cogan lab µECoG pseudoword repetition | DANDI 001638 | public licence declared, no assets yet | (Duraivel 2023 style µECoG) | speech repetition | empty on 2026-09-09 | re-check monthly | waiting |
| Du-IN, Verwoert mirrors | huggingface.co/datasets/liulab-repository/Du-IN (CC-BY-4.0, 184 files, about 1 GB per run); Terrycz/SEEG-singlewordDutch (unzipped Verwoert iBIDS) | public | | | | Du-IN files are pickled DotDict objects (shim in `moecog.datasets.misc`) | loaders written |
| Brain Treebank direct files | braintreebank.dev/data/subject_data/sub_N/trialNNN/sub_N_trialNNN.h5.zip + metadata zips | public, CC-BY-4.0 | 10 subjects | | one zip per movie viewing | | loader written; smoke test one trial |
| BR41N.IO hackathon ECoG sets (g.tec) | br41n.io (video watching; hand pose BCI) | on request to organisers | 1 patient each | visual features; hand pose | | | outreach list |
| Brunton lab AJILE12 NWB tools | github.com/BruntonUWBio/ajile12-nwb-data | code | | | | reference for the NWB loader | |
| insight-neuro/ieeg-data (brainsets) | github.com/insight-neuro/ieeg-data | code | | converts several iEEG datasets to the temporaldata format | | install currently broken by a brainsets deprecation (2026-09-10) | cross-check their roster later |

Search terms used: repositories "ECoG dataset", "electrocorticography dataset", "intracranial EEG dataset",
"sEEG dataset", "iEEG benchmark", "ECoG decoding", "ECoG BCI", "micro-ECoG", "AJILE12", "brain treebank",
"ECoG speech decoding"; topics ecog, electrocorticography, ieeg, intracranial-eeg, seeg; Hugging Face
dataset search ecog, electrocorticography, ieeg, intracranial, seeg. Papers with Code's dataset API did
not answer.

## Loader strategy

Three generic loaders cover most of this catalog:

1. **BIDS-iEEG** (`moecog.datasets.bids.BIDSiEEGDataset`): every OpenNeuro entry
   above (podcast, film, visual, naming corpus, RAM, CCEP, Cogitate after
   registration, ds006890, clinical sets). Events come from `*_events.tsv`,
   electrodes from `*_electrodes.tsv`, download through `openneuro-py`.
2. **NWB** (DANDI): AJILE12, Bouchard CV, Natraj BCI, Nentwich, CorTec.
3. **Format-specific**: Miller (done), BCI-IV/III (.mat/ASCII), Peterson
   figshare (.fif/.nc), Merk (BIDS-like), Verwoert (BIDS-like), Bellier (.npy),
   Brain Treebank (.h5), Du-IN (HF parquet), Neurotycho (.mat).

## Waves (proposal, PRSNL-72)

- **Wave 1 (this month, CPU only):** BIDS loader on ds005953 and ds004993;
  Podcast; film iEEG; Visual ECoG; BCI-IV via the PACE loader; BCI-III;
  Peterson move-vs-rest.
- **Wave 2:** NWB loader (Natraj, Bouchard CV, AJILE12 subset); naming corpus;
  RAM FR1 subset; Cogitate; Verwoert; Merk; Bellier.
- **Wave 3:** Brain Treebank/Neuroprobe cross-benchmark; Du-IN; MGH
  conversation; foundation-model comparisons.
- **Wave 4:** T6 datasets as they arrive from outreach; non-human tier if
  approved.

## Open items

- Verify every "verify" number against the paper before it appears in a table
  or a leaderboard.
- Licence review for the non-commercial and no-ML-training datasets (ds003688
  wording, ds004703 clause) before any pretraining use.
- Decide the tier policy (PRSNL-75): sEEG/mixed inclusion, non-human primates,
  clinical seizure sets.
- iEEG Natural Scenes Dataset and Kuzovkin GIN repository: confirm contents.
