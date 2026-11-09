# INCM Phase 5E — Final Research Manuscript Export and Formatting Report

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Active Branch:** `ashish-work`  
**Evaluation Target:** Formatting, Styling, and Camera-Ready PDF Export of `results/phase5/FINAL_RESEARCH_REPORT.md`  
**Date of Export:** 2026-11-09  
**Export Status:** Complete, Visually Inspected, and Verified  

---

## 1. Executive Summary

Phase 5E completed the professional academic manuscript formatting, publication styling, and camera-ready PDF export for the authoritative research report:
`results/phase5/FINAL_RESEARCH_REPORT.md` ("How Much Biological Detail Does a Neuron Model Need? Evaluating Conductance-Based Multi-Compartment versus Dimensional FitzHugh–Nagumo Reductions Across Four Mouse Visual Cortex Populations").

The resulting publication deliverables provide an academic-grade, camera-ready document featuring mixed portrait and landscape pagination, fully pre-rendered KaTeX vector equations, integrated publication figures, clean table layouts (resolving the 15-column Table 4 width constraint), and consistent bibliographic formatting without altering any underlying scientific content or quantitative findings.

---

## 2. Deliverables Created in Phase 5E

| Deliverable File Path | File Size | Format / Scope | Functional Role & Verification Status |
| :--- | :---: | :---: | :--- |
| `results/phase5/manuscript_style.css` | $8,703\text{ B}$ | Print-Friendly CSS3 | Academic typography, Paged Media `@page` definitions (A4 portrait & landscape), table booktabs styling, figure containers, monospace boxes. |
| `results/phase5/FINAL_RESEARCH_REPORT.html` | $429,909\text{ B}$ | Standalone HTML5 | Semantic HTML manuscript with embedded KaTeX CSS and pre-rendered vector math spans; completely self-contained with offline assets. |
| `results/phase5/FINAL_RESEARCH_REPORT.pdf` | $7,862,671\text{ B}$ | 19-Page PDF | Publication-quality compiled PDF generated via Headless Chromium with mixed orientation (Page 8 in A4 landscape for Table 4). |
| `results/phase5/PHASE5E_MANUSCRIPT_EXPORT_REPORT.md` | *This file* | Markdown Report | Phase 5E audit record, layout QA verification, renderer documentation, and integrity confirmation. |

---

## 3. Export Method and Toolchain Documentation

- **Rendering Engine:** Google Chrome Headless
  - **Binary:** `C:\Program Files\Google\Chrome\Application\chrome.exe`
  - **Version:** `156.0.8078.80` (Official Build, 64-bit)
- **Math Pre-Rendering Engine:** KaTeX
  - **Engine:** Node.js v24 (`C:\Program Files\nodejs\node.exe`) executing local KaTeX v0.16.27
  - **Mode:** Pre-rendered HTML (`output: 'html'`) with inlined KaTeX CSS
  - **Equation Success Rate:** 100% (13/13 display equations, 352/352 inline math expressions rendered with 0 errors)
- **PDF Compilation Command:**
  ```powershell
  & "C:\Program Files\Google\Chrome\Application\chrome.exe" `
    --headless `
    --no-sandbox `
    --disable-gpu `
    --no-pdf-header-footer `
    --run-all-compositor-stages-before-draw `
    --print-to-pdf="results/phase5/FINAL_RESEARCH_REPORT.pdf" `
    "results/phase5/FINAL_RESEARCH_REPORT.html"
  ```
- **Page Layout Architecture:** CSS3 Paged Media (`@page`)
  - **Default Page:** A4 Portrait ($210 \times 297\text{ mm}$ / $595.0 \times 841.9\text{ pt}$), margins $20\text{ mm}$ top/bottom, $18\text{ mm}$ left/right.
  - **Wide Table Page:** A4 Landscape ($297 \times 210\text{ mm}$ / $841.9 \times 595.0\text{ pt}$), margins $12\text{ mm}$ top/bottom, $15\text{ mm}$ left/right, dedicated to Table 4.
  - **Running Header:** Italicized article running title on upper right of pages 2–19 (`@top-right`).
  - **Running Footer:** Clean page number centered at bottom (`@bottom-center { content: counter(page); }`).

---

## 4. Visual Quality Assurance Audit

Every page of `FINAL_RESEARCH_REPORT.pdf` was rendered to high-resolution image previews via PyMuPDF (`1.28.2`) and inspected against seven quality criteria:

### 4.1 Page Census and Layout Overview (19 Total Pages)

| Page # | Orientation | Dimensions (pt) | Content Classification | Figures / Tables Present | Visual QA Verdict |
| :---: | :---: | :---: | :--- | :---: | :---: |
| **01** | Portrait | $595.0 \times 841.9$ | Title, Subtitle, Metadata Block, Abstract, §1 Introduction | None | **Pass** (Clean academic cover presentation) |
| **02** | Portrait | $595.0 \times 841.9$ | §2 Objectives, §3 Biological & Mathematical Background | Equations (HH, FHN) | **Pass** (Clean display equations & callouts) |
| **03** | Portrait | $595.0 \times 841.9$ | §4 Dataset & Specimen Selection, Laminar Diagram | **Table 1** (Specimens) | **Pass** (Table 1 formatted with booktabs) |
| **04** | Portrait | $595.0 \times 841.9$ | §5 Detailed Allen Biophysical Models, Provenance | **Table 2** (Morphologies) | **Pass** (Morphology donor table intact) |
| **05** | Portrait | $595.0 \times 841.9$ | §6 Dimensional FHN Formulation, State Variables | **Fig 1** (Calib Summary) | **Pass** (Full-width 4-panel calibration figure) |
| **06** | Portrait | $595.0 \times 841.9$ | §6.3 Frozen Calibrated Parameters | **Table 3** & **Fig 3** (Fits) | **Pass** (Table 3 + 2x2 calibration grid) |
| **07** | Portrait | $595.0 \times 841.9$ | §7 Methodology, Loss Breakdown, Contingency Schematic | **Fig 2** (Loss Breakdown) | **Pass** (Objective loss breakdown chart) |
| **08** | **Landscape** | $841.9 \times 595.0$ | **§8.1 Population-Level Held-Out Summary** | **Table 4 (15 Columns)** | **Pass** (Wide table fits with >41 pt margins) |
| **09** | Portrait | $595.0 \times 841.9$ | §8.2 Contingency Analysis, §9 Population A (Layer 4) | **Fig 4** (Pop A Traces) | **Pass** (Pop A 4-panel held-out traces) |
| **10** | Portrait | $595.0 \times 841.9$ | §9.2 Population B (Layer 2/3), Rate Capping Analysis | **Fig 5** (Pop B Traces) | **Pass** (Pop B held-out traces) |
| **11** | Portrait | $595.0 \times 841.9$ | §9.3 Population C (Layer 5), Extreme SFA Analysis | **Fig 6** (Pop C Traces) | **Pass** (Pop C adaptation traces) |
| **12** | Portrait | $595.0 \times 841.9$ | §9.4 Population D (Layer 6a), Latency Delay Analysis | **Fig 7** (Pop D Traces) | **Pass** (Pop D latency delay traces) |
| **13** | Portrait | $595.0 \times 841.9$ | §10 Taxonomy of Model Reduction, Tier 1 Integration | **Fig 9** ($I$–$V$ Curves) | **Pass** (Subthreshold $I$–$V$ linearity plot) |
| **14** | Portrait | $595.0 \times 841.9$ | §10 Tier 2 F–I Firing Rate Scaling & Saturation | **Fig 8** ($F$–$I$ Curves) | **Pass** (Full-width cross-population $F$–$I$ curves) |
| **15** | Portrait | $595.0 \times 841.9$ | §10 Tier 3 Waveform Mismatch, Tiers 4 & 5 | **Fig 10** (AP Kinetics) | **Pass** (Action-potential waveform overlay) |
| **16** | Portrait | $595.0 \times 841.9$ | §11 Bifurcation Analysis, Lyapunov Coefficients | **Table 5** ($l_1$ normal form) | **Pass** (Jacobian matrix & Table 5 intact) |
| **17** | Portrait | $595.0 \times 841.9$ | §11.3 Open Bistability Intervals, §12 Discussion | **Table 6** (Bistability) | **Pass** (Table 6 + Bistability schematic) |
| **18** | Portrait | $595.0 \times 841.9$ | §13 Limitations (12 Caveats), §14 Conclusion, §15 Future Work | None | **Pass** (Clear enumerated caveats & conclusions) |
| **19** | Portrait | $595.0 \times 841.9$ | §16 References (11 Entries), §17 Reproducibility Appendix | None | **Pass** (Numbered references + code repository links) |

---

## 5. Resolution of Specific Formatting Challenges

### 5.1 Resolution of Wide Table 4 (15 Columns)
- **Problem:** Table 4 spans 15 columns and 214 characters wide, which clips or truncates margins on standard portrait pages.
- **Remediation:** Placed Table 4 in a dedicated `@page landscape_page` container.
- **Observed Metrics:**
  - Printable width in landscape: $756.8\text{ pt}$ ($267\text{ mm}$).
  - Table content bounding box: $X \in [42.8, 800.2]\text{ pt}$, leaving $42.8\text{ pt}$ left margin and $41.7\text{ pt}$ right margin.
  - Font size set to $7.3\text{ pt}$ with $2.5\text{ pt}$ cell padding.
  - Zero columns, rows, or numerical values were omitted. All precision ($0.8036$, $12.73\text{ mV}$, etc.) and bold formatting are 100% preserved.

### 5.2 Embedding of Publication Figures (13 PNG Assets)
- All 13 publication figures from `results/phase4b/figures/` (6 figures) and `results/phase4c/figures/` (7 figures) were embedded at their direct conceptual positions.
- Each figure includes a formal, numbered academic caption with a bold prefix (`Figure X:`), concise title, and detailed physiological description.
- Image scaling constraints (`max-height: 440pt; max-width: 95%`) prevent vertical overflow and avoid pushing figure captions onto subsequent blank pages.

### 5.3 Mathematical Equations and KaTeX Rendering
- All 13 display math equations and 352 inline math expressions were rendered offline via KaTeX using the `output: 'html'` parameter.
- This eliminated hidden redundant MathML tags from contaminating PDF text selection and search.
- Display equations (Jacobian matrix, trace/determinant conditions, ODE formulations) render with vector-sharp brackets and balanced fractions.

### 5.4 Bibliographic Consistency and Missing Metadata Handling
- All 11 formal references in §16 are preserved with their original citation numbers `[1]` through `[11]`.
- In strict adherence to project restrictions against inventing DOI or publication metadata, References 2 through 11 (which omit explicit DOIs in the source manuscript) are explicitly marked:
  `[DOI/URL: Pending formal bibliographic verification]`
- Reference 1 retains its authoritative Allen Institute white paper URL (`celltypes.brain-map.org`).

---

## 6. Scientific Invariance Confirmation

- **Scientific Content Invariance:** **Confirmed 100% Unchanged.**
  - Zero modifications were made to `results/phase5/FINAL_RESEARCH_REPORT.md`.
  - Zero modifications were made to Phase 0–4 source code, unit tests, model parameters, or evaluation CSVs.
  - Zero numerical simulations, model fittings, or optimizations were run.
  - All quantitative metrics, parameter values, sweep IDs, denominators, and caveats in the HTML and PDF match the authoritative Phase 5 Markdown source bit-for-bit.

---

## 7. Git Working-Tree Status

- **Active Branch:** `ashish-work`
- **Remote Tracking:** `origin/ashish-work` (Synchronized)
- **Tracked Files:** Clean (no modifications to tracked repository files)
- **Phase 5 Deliverables on Disk:** 16 files present in `results/phase5/` (including newly created `manuscript_style.css`, `FINAL_RESEARCH_REPORT.html`, `FINAL_RESEARCH_REPORT.pdf`, and `PHASE5E_MANUSCRIPT_EXPORT_REPORT.md`).

