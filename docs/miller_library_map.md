# Map of the Stanford/Miller ECoG library for MOECoG

Inventory taken 2026-09-09 on the FAU Athene archive copy
(`/mnt/archive/home/yyu2024/PLaCT_data`, extracted from the Stanford Digital
Repository zips, MD5-verified 2026-07-16). Reproduce with
`python scripts/inventory_miller_library.py --root <root>`. The registry in
`moecog/datasets/miller_library.py` encodes everything below.

Source: Miller, K. J. "A library of human electrocorticographic data and
analyses." *Nature Human Behaviour* 3, 1225-1235 (2019),
https://purl.stanford.edu/zk881ps0522. Any publication that uses these data
must reproduce Miller's ethics statement verbatim (it is in every experiment's
`README_*_dataset_notes.docx`).

## The answer to "where do the per-patient epoched trials live?"

There are no hidden trial files. Every cued experiment stores its labels as a
**sample-wise code channel inside the same per-patient `.mat` file as the
ECoG** (`stim`, `StimulusCode`, `TargetCode`, `cues`, plus `target`/`task` for
n-back and `tr_fh`/`tr_coh` for the noisy faces run). A trial is a contiguous
block of a constant code; the rest blocks are code 0. Miller's scripts
catalogue trials exactly that way (`trialnr` increments when
`stim(n) ~= stim(n-1)`, see `mot_th_master.m`, `fh_get_events.m`,
`vispac_master.m`). The top-level `ns_1k_1_300_filt.mat` in most folders is the
amplifier's amplitude roll-off curve (a 300-point vector), not data.

Common properties (all experiments except `fixation_highfreq`):

- 1000 Hz, one-pole analog band-pass 0.15-200 Hz, scalp reference,
  1 amplifier unit = 0.0298 microvolts (`data` is int16/int32; the visual and
  n-back files are float64, three faces patients (aa, ha, jt) have a much larger
  range, presumably a different gain).
- `data` is time x channels. Bad channels were **not** rejected except where
  the notes say so (motor_basic, imagery_*: "attempted to remove contaminated
  channels"; visual_search: common-average referenced and restricted to
  occipital strips).
- Montages differ between experiments for the same patient (amplifier limits,
  re-implantation, or only one region kept). Never assume channel i means the
  same electrode across experiment folders.
- Patient codes are two letters and are not initials. 36 codes appear on disk;
  Miller's patient table lists 34 (gw and h0 appear only in fixation_pwrlaw).

## Per-experiment map

Sizes are the extracted folders. "Blocks" are (count, length) of the constant
code runs at 1 kHz from the inventory.

| Experiment | Files (patients) | Code channel and classes | Trial structure | Extra variables | Electrodes |
|---|---|---|---|---|---|
| `fingerflex` | `data/{s}/{s}_fingerflex.mat` + `{s}_stim.mat` (bp cc ht jc jp mv wc wm zt) | `stim` in `_stim.mat`: 1-5 thumb, index, middle, ring, little (movement-aligned); `cue` in the main file is the screen cue | 2 s cues, 30 per finger, 2 s rest | `flex` (time x 5 dataglove, 40 ms blocks) | `locs` + `elec_regions` inside the file (native surface); BCI-IV subjects are derived from bp, cc, zt |
| `joystick_track` | `data/{s}_joystick.mat` (fp gf rh rr) | none (continuous) | ~1 min circle tracking | `CursorPosX/Y`, `TargetPosX/Y` (uint16, 0-32767) | `electrodes` in file (Talairach) |
| `mouse_track` | `data/{s}_mouse.mat` (fp gf rh rr) | none | same as joystick | same | same |
| `motor_basic` | `data/{s}_mot_t_h.mat` (19: bp ca cc de fp gc gf hh hl jc jf jm jp jt rh rr ug wc zt) | `stim`: 11 tongue, 12 hand; gf also 13 (undocumented), zt also 15 (say "move") | 3 s cue blocks, 30 per class (cc 15, jp 18/20, ug 45; jf 2 s blocks 30/36), 3 s rest between | jp: `dg` (time x 5) and `electrodes` | `locs/{s}_electrodes.mat` (Talairach); `brains/` CTMR surfaces for 7 |
| `imagery_basic` | `data/{s}_mot_t_h.mat` + `{s}_im_t_h.mat` (bp fp hh jc jm rh rr) | `stim`: 11 tongue, 12 hand (overt in `mot`, kinesthetic imagery in `im`) | 3 s cues, 30 per class per file, 3 s rest | none | `locs/{s}_electrodes.mat` (Talairach) |
| `imagery_feedback` | `data/{s}/{s}_{task}.mat`: al (fb_shrug, im_ih_shrug, mot_ih_shrug), fp (fbLR_hand, fbUD_tongue, im_t_h, mot_t_h), hh (fb_tongue, im_t, mot_t), jc (fb_mov, mot_l_mov) | mot/im: `StimulusCode` 11 tongue, 12 hand (ipsilateral in `_ih_`), 15 say "move", 16 hip (inferred from `_l_`), 19 shrug; fb: `TargetCode` 1 target A, 2 target B | mot/im: 3 s cues, 30 per class (hh: tongue only); fb: 9-20 trials per target, 2.4-22 s each (cursor control), 1 s ITI | fb: `Cursor`, `Result` (0/1/2 hit), `ITI` | `locs/{s}_locs_{n}.mat` var `electrodes` (Talairach) |
| `gestures` (unpublished) | `data/{s}/{s}_{task}.mat`: bp (base, fingerflex, freeform, pinch, rh_lh), ca (base, fingerflex, freeform, mot_TH, pinch), cc (base, freeform, pinch, thumbfore), de (base, freeform, glovefingersgrasp), wm (base, fingerflex, freeform, pinch, thumbfore) | `stim` + `stimtext` (1-based index into `stimtext`): fingerflex 1-5 fingers; thumbfore 1 thumb, 2 index; pinch 1; freeform 1 gesture; rh_lh 5 right, 6 left, 7 both (codes 5-7, not 1-3 as the notes say); mot_TH 1 tongue, 2 hand; glovefingersgrasp 1-5 fingers, 6/8 pinch, 7/9 fist | 2 s cues (rh_lh, mot_TH 3 s), 20-30 per class (wm fingerflex 18-27, thumbfore 7-8), 2 s rest | `dg` (time x 5) in every file, `srate`; bp: `EMG_FlexorCarpi`, `EMG_ExtensorCarpi` in some files | `locs/{s}_locs.mat` for bp ca de (Talairach); `brains/` CTMR for the others |
| `faces_basic` | `data/{s}/{s}_faceshouses.mat` (14: aa ap ca de fp ha ja jm jt mv rn rr wc zt) | `stim`: 1-50 house picture id, 51-100 face picture id, 101 ISI, 0 outside runs | 400 ms pictures, 150 faces + 150 houses (rr 100 + 100), 400 ms ISI | `srate` | `locs/{s}_xslocs.mat`: `locs` are **MRI voxel indices** (with `brains/{s}/*.nii`), `elcode` anatomical code (labels in `fhpred_master.m` `area_lbls`) |
| `faces_noise` | `data/{s}/{s}_faceshouses.mat` (localizer, as above) + `{s}_fhnoisy.mat` (ap ca ha ja mv wc zt) | fhnoisy `stim`: trial index 1-630 (0 between runs); class in `tr_fh` (630 x 1: 1 house, 2 face); noise level in `tr_coh` (0-100 % in 5 % steps) | 6 runs x 105 one-second trials, no ISI, ~6 s between runs | `key` (keypress per sample) | as faces_basic |
| `memory_nback` | `data/{s}_nback.mat` (al ca cc ug) | `stim` 1-40 house picture id; `target` 1 non-target, 2 target; `task` -1 fixation, 0/1/2 n-back level | 600 ms pictures, 1.6 s ISI, 50 per run; ca cc ug: base, 2x0-back, 2x1-back, 2x2-back, base (300 stimuli); al: one run each (150) | `response` (time x 5 dataglove; ca cc only) | `locs/{s}_electrodes.mat` (Talairach); `brains/` for ca cc |
| `visual_search` | `data/{s}/{s}_vissearch.mat` (jm jt rn rr wc) | `stim`: 1-10 right, 11-20 left, 21-30 down, 31-40 up (the notes' "12-30/13-40" is a typo; `vispac_master.m` uses `floor((stim-1)/10)+1`), 41 ISI | 2 s search arrays, 30 per direction, 2 s ISI | `brain`, `locs` inside the file; data already CAR'd, occipital strips only (7-24 channels) | in file (native) |
| `speech_basic` | `data/{s}_verbs.mat` (bp hl in jc wc ww zt) and `{s}_nouns.mat` (jc wc ww zt) | `cues`: 1 while the noun is on screen; task is the file (nouns = read aloud, verbs = generate a verb) | 1.6 s cue / 1.6 s ISI, 40 cues (bp 6.4 s cues; hl 33 cues of 2 s; in 12) | `stimsites`, `ecssites` (clinical stimulation mapping) | `brains/{s}_brain.mat` (`brain`, `locs`, native) for 7 |
| `speech_lists` | `data/{s}/{s}_{nouns,verbs}_L{1,2}_R{1,2,3}.mat` (jc wc ww) + `{s}_base.mat` (jc wc, variable `signal`) | `stim`: word id 1-40 in `list1.mat`/`list2.mat`; run order nouns L1 R1-3, verbs L1 R1-3, nouns L2, verbs L2 | 1.6 s cue / 1.6 s ISI, 40 words per run, 12 runs | `stim/{s}_stim.m` scripts give ECS sites | `brains/` for 3 |
| `fixation_PAC` | `data/{s}/{s}_base.mat` (bp cc hl jc jm jp ug wc wm zt) | none (rest) | 2-3 min eyes-open fixation | `brain`, `locs`, `el_codes` (column 2 = region code) | in file (native) |
| `fixation_pwrlaw` | `data/{s}_base.mat` (20: al ca cc de fp gc gf gw h0 hh jc jm jp mv rh rr ug wc wm zt) | none | 2-3 min fixation | `locs` (Talairach) | in file |
| `fixation_highfreq` | `data/s{1-4}_10kbase.mat` | none | 2 min at **10 kHz**, 4x8 arrays | roll-off in `ns_10k_1_4000_filt.mat`; bad electrodes listed in `ten_k_master.m` | none distributed |

Region codes (`elec_regions`, `el_codes[:, 1]`): 1 dorsal M1, 3 dorsal S1,
4 ventral sensorimotor, 6 frontal (non-rolandic), 7 parietal, 8 temporal,
9 occipital.

Channel counts per file range from 7 (visual_search jt) to 102 (faces_basic
jt); most motor files have 39-64 channels.

## What this means for the classification tier

- **Every discrete experiment is epochable with one mechanism**: cue-code
  transitions to annotations (`annotations_from_codes`), then
  `mne.Epochs`. The `MillerLibrary` loader does this for all 204 files.
- **Class balance**: motor/imagery/gestures/visual are balanced by design
  (equal cue counts, interleaved). faces_basic is balanced; n-back target vs
  non-target is 1:4 (use balanced accuracy or kappa); faces_noise is balanced
  in class but graded in difficulty (`coherence`).
- **Trial counts are small** (15-45 per class in the motor files, 150 per
  class for faces, 300 pictures for n-back): use trial-level CV within each
  file, report kappa or balanced accuracy, and multi-seed error bars for any
  deep model.
- **Sessions**: MOECoG treats each task file as a session (`mot` vs `im`,
  `nouns` vs `verbs`, each gesture task) and pools repeated runs (speech_lists
  R1-R3). Cross-condition questions (execution vs imagery transfer, read vs
  generate) are cross-session evaluations, not within-session classes.
- **Rest is available everywhere**: `MillerLibrary(..., include_rest=True)`
  annotates the code-0 blocks, which gives a movement-vs-rest task in every
  motor file and a cue-vs-rest task in the speech files.
- **Anatomy**: Talairach coordinates exist for the motor family, n-back,
  cursor, and fixation_pwrlaw; faces use voxel indices in patient MRI space
  (needs `nibabel` + the `.nii` to convert); visual_search, speech, fixation_PAC
  and fingerflex ship native surface coordinates with the CTMR brain mesh.
  Cross-patient work should start with the Talairach subset.

## Open items

- Code 13 in motor_basic gf (31 blocks of 3 s) is not documented; it is
  exposed as cue `code_13` and excluded by the named paradigms.
- Code 16 in imagery_feedback jc_mot_l_mov is named `hip` from the file name
  (`_l` = hip adduction/abduction in the notes); confirm against the PNAS 2010
  supplement before publishing numbers on it.
- The three faces patients with a ~1000x larger amplitude range (aa, ha, jt)
  need a per-file gain check before any pooled analysis.
- gestures `wm_base.mat` `dg` holds only a few distinct values (glove not
  worn); ignore its dataglove.
