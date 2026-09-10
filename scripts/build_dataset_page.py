#!/usr/bin/env python3
# ruff: noqa: E501
"""Render docs/decodable_datasets.json as a self-contained, filterable HTML page (the shareable atlas).

    python scripts/build_dataset_page.py --json docs/decodable_datasets.json --out docs/decodable_datasets.html
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

TEMPLATE = r"""<title>MOECoG Dataset Atlas</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
  :root {
    --ground: #F1F4F6; --surface: #FFFFFF; --surface-2: #E7ECF0; --line: #CBD4DB; --ink: #15202B; --muted: #5A6874;
    --accent: #0E6F7C; --accent-ink: #FFFFFF; --accent-soft: #D7ECEF;
    --ok: #2E7D4F; --ok-soft: #DDF1E4; --warn: #9A6B00; --warn-soft: #F6ECCB; --bad: #9C3B3B; --bad-soft: #F4DCDC;
    --chip: #EEF2F5; --focus: #0E6F7C;
    --sans: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
    --display: "Archivo", "IBM Plex Sans", Arial, sans-serif;
    --mono: "IBM Plex Mono", "SFMono-Regular", Menlo, Consolas, monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --ground: #0F151B; --surface: #171F27; --surface-2: #1F2932; --line: #33414C; --ink: #E6ECF1; --muted: #98A6B2;
      --accent: #3FB4C2; --accent-ink: #06232A; --accent-soft: #123A40;
      --ok: #5FC48A; --ok-soft: #173A27; --warn: #E0B24A; --warn-soft: #3B2F0E; --bad: #E07A7A; --bad-soft: #3F1E1E;
      --chip: #222D37; --focus: #3FB4C2;
    }
  }
  :root[data-theme="dark"] {
    --ground: #0F151B; --surface: #171F27; --surface-2: #1F2932; --line: #33414C; --ink: #E6ECF1; --muted: #98A6B2;
    --accent: #3FB4C2; --accent-ink: #06232A; --accent-soft: #123A40;
    --ok: #5FC48A; --ok-soft: #173A27; --warn: #E0B24A; --warn-soft: #3B2F0E; --bad: #E07A7A; --bad-soft: #3F1E1E;
    --chip: #222D37; --focus: #3FB4C2;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--ground); color: var(--ink); font: 14px/1.45 var(--sans); }
  a { color: var(--accent); }
  :focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
  header { padding: 28px clamp(16px, 4vw, 48px) 18px; border-bottom: 1px solid var(--line); background: var(--surface); }
  .eyebrow { font: 500 11px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
  h1 { font: 700 clamp(26px, 3.4vw, 38px)/1.05 var(--display); margin: 8px 0 8px; letter-spacing: -.01em; text-wrap: balance; }
  .lede { max-width: 68ch; color: var(--muted); margin: 0; }
  .stats { display: flex; flex-wrap: wrap; gap: 8px 28px; margin-top: 18px; font-variant-numeric: tabular-nums; }
  .stat b { font: 600 22px/1 var(--display); display: block; }
  .stat span { font-size: 12px; color: var(--muted); }
  .controls { position: sticky; top: 0; z-index: 3; display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: center;
              padding: 12px clamp(16px, 4vw, 48px); background: var(--ground); border-bottom: 1px solid var(--line); }
  .controls input[type=search] { flex: 1 1 220px; max-width: 360px; padding: 8px 10px; border: 1px solid var(--line);
              border-radius: 6px; background: var(--surface); color: var(--ink); font: inherit; }
  .group { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
  .group .lbl { font: 500 11px/1 var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); margin-right: 4px; }
  .tog { border: 1px solid var(--line); background: var(--surface); color: var(--ink); border-radius: 999px; padding: 4px 10px;
         font: 500 12px/1.2 var(--sans); cursor: pointer; }
  .tog[aria-pressed="true"] { background: var(--accent); color: var(--accent-ink); border-color: var(--accent); }
  .tog.fit { font-family: var(--mono); }
  main { padding: 0 clamp(16px, 4vw, 48px) 40px; }
  .tablewrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); margin-top: 16px; }
  table { border-collapse: collapse; width: 100%; min-width: 1180px; font-variant-numeric: tabular-nums; }
  thead th { position: sticky; top: 0; background: var(--surface-2); text-align: left; font: 600 11px/1.2 var(--mono);
             letter-spacing: .05em; text-transform: uppercase; color: var(--muted); padding: 10px 10px; border-bottom: 1px solid var(--line);
             cursor: pointer; white-space: nowrap; user-select: none; }
  thead th[aria-sort="ascending"]::after { content: " \2191"; color: var(--accent); }
  thead th[aria-sort="descending"]::after { content: " \2193"; color: var(--accent); }
  tbody tr.fam { background: var(--ground); }
  tbody tr.fam td { font: 600 13px/1.2 var(--display); padding: 10px 10px 6px; color: var(--ink); border-top: 1px solid var(--line); }
  tbody tr.fam td small { font: 400 12px/1 var(--sans); color: var(--muted); margin-left: 8px; }
  tbody td { padding: 8px 10px; border-top: 1px solid var(--line); vertical-align: top; }
  tbody tr.row { cursor: pointer; }
  tbody tr.row:hover td { background: color-mix(in srgb, var(--accent-soft) 45%, transparent); }
  td.id { font: 500 12px/1.4 var(--mono); white-space: nowrap; }
  td.num { text-align: right; white-space: nowrap; }
  td.title { min-width: 220px; max-width: 320px; }
  td.target { min-width: 220px; max-width: 340px; color: var(--ink); }
  .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font: 500 11px/1.4 var(--mono); white-space: nowrap; }
  .pill.ok { background: var(--ok-soft); color: var(--ok); }
  .pill.unsupported { background: var(--warn-soft); color: var(--warn); }
  .pill.blocked, .pill.error { background: var(--bad-soft); color: var(--bad); }
  .pill.pending { background: var(--chip); color: var(--muted); }
  .chip { display: inline-block; padding: 1px 7px; border-radius: 4px; background: var(--chip); color: var(--ink);
          font: 500 11px/1.5 var(--mono); margin-right: 3px; }
  .chip.fitR { background: var(--accent-soft); color: var(--accent); }
  .kappa { font: 500 12px/1 var(--mono); color: var(--muted); margin-left: 6px; }
  tr.detail td { background: var(--ground); color: var(--muted); font-size: 13px; padding: 6px 10px 12px 10px; }
  tr.detail b { color: var(--ink); font-weight: 500; }
  .empty { padding: 32px; text-align: center; color: var(--muted); }
  footer { padding: 16px clamp(16px, 4vw, 48px) 36px; color: var(--muted); font-size: 12.5px; max-width: 80ch; }
  footer dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 12px; margin: 8px 0 0; }
  footer dt { font-family: var(--mono); color: var(--ink); }
  footer dd { margin: 0; }
  @media (prefers-reduced-motion: no-preference) { .tog, tbody tr.row td { transition: background .12s ease; } }
</style>

<header>
  <div class="eyebrow">MOECoG · catalog registry, smoke sweep of __DATE__</div>
  <h1>MOECoG Dataset Atlas</h1>
  <p class="lede">Every ECoG and intracranial dataset the catalog knows, with what was recorded, how much of it there is, what a decoder can predict from it, and whether MOECoG loads it today. Modality is measured from the channel types of the downloaded subset where one is on disk (ECoG = at least 80 % ECOG channels, sEEG = at least 80 % depth channels); channels and rate describe the first subject's first run as loaded, not the whole deposit.</p>
  <div class="stats" id="stats"></div>
</header>

<div class="controls">
  <input type="search" id="q" placeholder="Search ids, titles, targets, tasks" aria-label="Search datasets">
  <div class="group" id="fams"><span class="lbl">family</span></div>
  <div class="group" id="fits"><span class="lbl">fit</span>
    <button class="tog fit" data-fit="R" aria-pressed="false" title="continuous regression: finger flexion, cursor, force, pose, audio">R regression</button>
    <button class="tog fit" data-fit="C" aria-pressed="false" title="trial classification">C classification</button>
    <button class="tog fit" data-fit="S" aria-pressed="false" title="speech / audio decoding">S speech</button>
    <button class="tog fit" data-fit="P" aria-pressed="false" title="pretraining / self-supervised only">P pretraining</button>
  </div>
  <div class="group" id="statuses"><span class="lbl">status</span>
    <button class="tog" data-status="ok" aria-pressed="true">loads</button>
    <button class="tog" data-status="unsupported" aria-pressed="true">unsupported</button>
    <button class="tog" data-status="blocked" aria-pressed="true">blocked</button>
  </div>
  <div class="group" id="mods"><span class="lbl">modality</span></div>
  <div class="group"><span class="lbl">view</span>
    <button class="tog" id="grouped" aria-pressed="true">grouped by family</button>
  </div>
</div>

<main>
  <div class="tablewrap">
    <table id="t">
      <thead><tr>
        <th data-k="id">entry</th><th data-k="title">dataset</th><th data-k="modality">modality</th>
        <th data-k="n_subjects" class="num">subjects</th><th data-k="channels">first run</th><th data-k="size_gb" class="num">size</th>
        <th data-k="licence">licence</th><th data-k="target">decoding target</th><th data-k="kind">kind</th><th data-k="fit">fit</th>
        <th data-k="status">status</th>
      </tr></thead>
      <tbody id="rows"></tbody>
    </table>
    <div class="empty" id="empty" hidden>No dataset matches these filters.</div>
  </div>
</main>

<footer>
  <b>How to read it.</b> <em>fit</em> names the decoder lines that apply: R = continuous regression (the PACE / TRACE finger-flexion line: dataglove, cursor, force, pose, audio spectrogram), C = trial classification, S = speech and audio decoding, P = pretraining or self-supervised only. <em>quick kappa</em> next to a status is LogBandPower + LDA with 3 chronological folds on one subject: a sanity check that the labels line up, never a benchmark. Click a row for its notes.
  <dl>
    <dt>ok</dt><dd>downloaded, loaded and, when a trial paradigm applies, scored by <code>scripts/smoke_test.py</code></dd>
    <dt>unsupported</dt><dd>the deposit holds no field potentials (spikes or features only), no recordings at all, or was deleted</dd>
    <dt>blocked</dt><dd>account, data-use agreement or repository problem; reasons in <code>docs/dataset_catalog.md</code></dd>
  </dl>
  <p>Source of truth: <code>docs/decodable_datasets.md</code> in yifan-study/MOECoG, regenerated by <code>scripts/build_dataset_list.py</code> after each sweep.</p>
</footer>

<script>
const ROWS = __DATA__;
const FAM_ORDER = ["motor","bci","speech","auditory","visual","memory","naturalistic","animal","stimulation","clinical","rest_sleep","other"];
const FAM_TITLE = {motor:"Motor (movement, kinematics, force)", bci:"Brain-computer interface control", speech:"Speech production and naming",
  auditory:"Auditory and language perception", visual:"Visual stimuli", memory:"Memory and cognition", naturalistic:"Naturalistic, long-term",
  animal:"Non-human", stimulation:"Electrical stimulation", clinical:"Clinical (seizures, HFO, artefacts)", rest_sleep:"Rest and sleep (unlabeled)", other:"Other"};
const state = {q:"", fams:new Set(), fits:new Set(), mods:new Set(), statuses:new Set(["ok","unsupported","blocked"]), grouped:true, sort:{k:null, dir:1}};
const MOD_ORDER = ["ECoG","mixed","sEEG","uECoG","features","LFP+ECoG","unverified"];
const MOD_TITLE = {ECoG:"subdural ECoG", mixed:"ECoG + sEEG", sEEG:"sEEG (depth)", uECoG:"µECoG", features:"features only", "LFP+ECoG":"ECoG + DBS LFP", unverified:"unverified"};

function fmtSize(gb){ if(gb==null) return ""; if(gb>=1000) return (gb/1000).toFixed(1)+" TB"; if(gb>=1) return gb.toFixed(1)+" GB"; return Math.round(gb*1000)+" MB"; }
function fmtRun(r){ if(r.channels==="" || r.channels==null) return ""; return `${r.channels} ch @ ${Math.round(r.sfreq)} Hz · ${Math.round(r.duration_s)} s`; }
function statusOf(r){ return r.status==="error" ? "blocked" : r.status; }
function esc(s){ return String(s==null?"":s).replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }

function filtered(){
  const q = state.q.trim().toLowerCase();
  return ROWS.filter(r => {
    if(!state.statuses.has(statusOf(r))) return false;
    if(state.fams.size && !state.fams.has(r.family)) return false;
    if(state.mods.size && !state.mods.has(r.modality)) return false;
    if(state.fits.size){ const f = (r.fit||"").split(" "); if(![...state.fits].every(x => f.includes(x))) return false; }
    if(q){ const hay = [r.id, r.title, r.target, r.tasks, r.note, r.modality, r.licence, r.catalog_notes].join(" ").toLowerCase(); if(!hay.includes(q)) return false; }
    return true;
  });
}
function sorted(rows){
  const {k, dir} = state.sort; if(!k) return rows;
  const num = new Set(["n_subjects","size_gb","channels"]);
  return [...rows].sort((a,b) => { let x=a[k], y=b[k];
    if(num.has(k)){ x = x===""||x==null ? -1 : +x; y = y===""||y==null ? -1 : +y; return (x-y)*dir; }
    return String(x||"").localeCompare(String(y||""))*dir; });
}
function render(){
  const rows = sorted(filtered());
  const tb = document.getElementById("rows"); tb.innerHTML = "";
  document.getElementById("empty").hidden = rows.length>0;
  const groups = state.grouped && !state.sort.k ? FAM_ORDER.map(f => [f, rows.filter(r => r.family===f)]).filter(g => g[1].length) : [[null, rows]];
  for(const [fam, list] of groups){
    if(fam){ const tr = document.createElement("tr"); tr.className="fam";
      const n = list.length, ok = list.filter(r=>r.status==="ok").length, gb = list.reduce((s,r)=>s+(r.size_gb||0),0);
      tr.innerHTML = `<td colspan="11">${esc(FAM_TITLE[fam])}<small>${n} datasets · ${ok} load · ${fmtSize(gb)}</small></td>`; tb.appendChild(tr); }
    for(const r of list){
      const tr = document.createElement("tr"); tr.className="row"; tr.tabIndex=0; tr.setAttribute("aria-expanded","false");
      const st = statusOf(r);
      const kappa = r.quick_kappa ? `<span class="kappa" title="quick kappa, LogBandPower+LDA, 3 folds">κ ${r.quick_kappa}</span>` : "";
      const fits = (r.fit||"").split(" ").filter(Boolean).map(f=>`<span class="chip fit${f}">${f}</span>`).join("");
      const modCell = r.ecog_pct==null ? esc(r.modality) : `${esc(r.modality)} <span class="kappa" title="channel types in the downloaded subset's channels.tsv">${r.ecog_pct}% ECoG · ${r.seeg_pct}% sEEG</span>`;
      tr.innerHTML = `<td class="id">${esc(r.id)}</td><td class="title">${esc(r.title)}</td><td>${modCell}</td>
        <td class="num">${esc(r.n_subjects)}</td><td>${esc(fmtRun(r))}</td><td class="num">${fmtSize(r.size_gb)}</td>
        <td>${esc(r.licence)}</td><td class="target">${esc(r.target)}</td><td>${esc(r.kind)}</td><td>${fits}</td>
        <td><span class="pill ${st}">${st==="ok"?"loads":st}</span>${kappa}</td>`;
      const det = document.createElement("tr"); det.className="detail"; det.hidden = true;
      const parts = [];
      if(r.note) parts.push(`<b>notes</b> ${esc(r.note)}`);
      if(r.tasks) parts.push(`<b>tasks</b> ${esc(r.tasks)}`);
      if(r.catalog_notes) parts.push(`<b>catalog</b> ${esc(r.catalog_notes)}`);
      if(r.electrodes!=="" && r.electrodes!=null) parts.push(`<b>electrodes with coordinates</b> ${esc(r.electrodes)}`);
      if(r.classes) parts.push(`<b>classes in first run</b> ${esc(r.classes)}`);
      parts.push(`<b>source</b> ${esc(r.source)}`);
      det.innerHTML = `<td colspan="11">${parts.join(" &nbsp;·&nbsp; ")}</td>`;
      const toggle = () => { det.hidden = !det.hidden; tr.setAttribute("aria-expanded", String(!det.hidden)); };
      tr.addEventListener("click", toggle); tr.addEventListener("keydown", e => { if(e.key==="Enter"||e.key===" "){ e.preventDefault(); toggle(); } });
      tb.appendChild(tr); tb.appendChild(det);
    }
  }
  const all = ROWS, ok = all.filter(r=>r.status==="ok");
  const tb_ = all.reduce((s,r)=>s+(r.size_gb||0),0), tbok = ok.reduce((s,r)=>s+(r.size_gb||0),0);
  const subj = ok.reduce((s,r)=>s+(+r.n_subjects||0),0);
  const ecogTB = all.filter(r=>r.modality==="ECoG").reduce((s,r)=>s+(r.size_gb||0),0);
  const seegTB = all.filter(r=>r.modality==="sEEG").reduce((s,r)=>s+(r.size_gb||0),0);
  document.getElementById("stats").innerHTML = [
    [all.length, "catalog entries"], [ok.length, "load in MOECoG today"], [fmtSize(tbok)+" of "+fmtSize(tb_), "public data behind loadable entries"],
    [fmtSize(ecogTB), "of it subdural ECoG"], [fmtSize(seegTB), "sEEG (4.6 TB is the SWEC clinical archive)"],
    [subj.toLocaleString(), "subjects across loadable entries"], [rows.length, "shown with these filters"]
  ].map(([b,s]) => `<div class="stat"><b>${b}</b><span>${s}</span></div>`).join("");
}
function modButtons(){
  const host = document.getElementById("mods");
  for(const m of MOD_ORDER){ if(!ROWS.some(r=>r.modality===m)) continue;
    const b = document.createElement("button"); b.className="tog"; b.textContent = MOD_TITLE[m] || m; b.setAttribute("aria-pressed","false");
    b.addEventListener("click", () => { state.mods.has(m) ? state.mods.delete(m) : state.mods.add(m); b.setAttribute("aria-pressed", String(state.mods.has(m))); render(); });
    host.appendChild(b); }
}
function famButtons(){
  const host = document.getElementById("fams");
  for(const f of FAM_ORDER){ if(!ROWS.some(r=>r.family===f)) continue;
    const b = document.createElement("button"); b.className="tog"; b.textContent = FAM_TITLE[f].split(" (")[0]; b.dataset.fam=f; b.setAttribute("aria-pressed","false");
    b.addEventListener("click", () => { state.fams.has(f) ? state.fams.delete(f) : state.fams.add(f); b.setAttribute("aria-pressed", String(state.fams.has(f))); render(); });
    host.appendChild(b); }
}
document.getElementById("q").addEventListener("input", e => { state.q = e.target.value; render(); });
document.querySelectorAll("#fits .tog").forEach(b => b.addEventListener("click", () => { const f=b.dataset.fit; state.fits.has(f)?state.fits.delete(f):state.fits.add(f); b.setAttribute("aria-pressed", String(state.fits.has(f))); render(); }));
document.querySelectorAll("#statuses .tog").forEach(b => b.addEventListener("click", () => { const s=b.dataset.status; state.statuses.has(s)?state.statuses.delete(s):state.statuses.add(s); b.setAttribute("aria-pressed", String(state.statuses.has(s))); render(); }));
document.getElementById("grouped").addEventListener("click", e => { state.grouped = !state.grouped; e.currentTarget.setAttribute("aria-pressed", String(state.grouped)); render(); });
document.querySelectorAll("thead th").forEach(th => th.addEventListener("click", () => {
  const k = th.dataset.k; if(state.sort.k===k){ state.sort.dir = state.sort.dir===1 ? -1 : 1; if(state.sort.dir===1){ state.sort.k=null; } } else { state.sort={k, dir:1}; }
  document.querySelectorAll("thead th").forEach(t => t.removeAttribute("aria-sort"));
  if(state.sort.k) th.setAttribute("aria-sort", state.sort.dir===1 ? "ascending" : "descending");
  render(); }));
famButtons(); modButtons(); render();
</script>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="docs/decodable_datasets.json")
    ap.add_argument("--out", default="docs/decodable_datasets.html")
    args = ap.parse_args()
    rows = json.loads(Path(args.json).read_text())
    html = TEMPLATE.replace("__DATA__", json.dumps(rows, ensure_ascii=False)).replace("__DATE__", dt.date.today().isoformat())
    Path(args.out).write_text(html)
    print(f"wrote {args.out}: {len(rows)} rows, {len(html) // 1024} KB")


if __name__ == "__main__":
    main()
