# Phase 5F — Literature Evidence Matrix (Layer 5 and Layer 6a)

**Branch:** `ashish-work` · **Base commit:** `5509ddd`
**Companion documents:** `PHASE5F_L5_L6A_LITERATURE_REVIEW.md` (narrative), `PHASE5F_REFERENCE_VERIFICATION.md` (bibliographic checks).

**Evidence-type key**

| Code | Meaning |
| :---: | :--- |
| **M** | Measured in this project's frozen recordings or derived from them read-only |
| **A** | Allen database metadata or feature |
| **L-P** | Literature, primary research |
| **L-R** | Literature, review, theory or viewpoint |
| **DP** | Detailed-model prediction (frozen) |
| **RP** | Reduced (FHN) model prediction (frozen) |
| **H** | Hypothesis |

**Relevance key**
- **Direct:** mouse V1 and the same cell class.
- **Indirect:** another area or species, or a population-level property.
- **Context:** general framework or theory.

---

## 1. Canonical Hierarchy and Cell Classes

| Topic | Claim | Source | Evidence type | Relevance | Confidence / limitation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| Canonical circuit | Thalamus → L4 → L2/3 → L5 → output; L6 returns CT feedback | Douglas & Martin 2004; Thomson 2010; Harris & Mrsic-Flogel 2013 | L-R | Context | High as a simplification; reviews themselves list exceptions (thalamic input to deep layers). |
| Projection classes | Excitatory neurons divide into IT, PT/ET and CT classes, largely conserved across areas | Harris & Shepherd 2015; Baker et al. 2018; Shepherd 2013 | L-R | Context | High; class boundaries are partly graded. |
| Transcriptomic classes | Mouse V1 contains L5 IT, L5 PT (ET), L5 NP, L6 IT, L6 CT and L6b subclasses | Tasic et al. 2016, 2018 | L-P | Direct (V1) | High; specimen-level transcriptome not available for C or D. |
| Allen e/m-types | Multiple e-types and m-types exist within each V1 layer | Gouwens et al. 2019 | L-P | Direct (same database) | High; neither specimen's e-type label was used in this project. |
| Pop placement | A=L4 (Rorb), B=L2/3 (Nr5a1), C=L5 (Rbp4-KL100), D=L6a (Ntsr1-GN220) | Allen metadata | A | Direct | High for the layer annotation; the Nr5a1/L2/3 mismatch is flagged for the L2/3 owner. |

## 2. Layer 5 (Population C)

| Topic | Claim | Source | Evidence type | Relevance | Confidence / limitation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| L5 types in V1 | CC, CS and CC-NS L5 types differ in connectivity, morphology, physiology and visual responses | Kim, E. J. et al. 2015 | L-P | Direct (mouse V1) | High; specimen C cannot be assigned to a type. |
| Projection-specific coding | Corticotectal, corticostriatal and corticocortical L5 cells encode visual features differently | Lur et al. 2016 | L-P | Direct (mouse V1) | Medium–high; in vivo population imaging. |
| Driver output | L5 PT input to higher-order thalamus is driver-type | Sherman & Guillery 1998 | L-R | Context | Theory/review framework. |
| Morphology–firing | Thick-tufted L5 cells burst; thin-tufted cells do not | Mason & Larkman 1990 | L-P | Indirect (rat V1) | High in rat; specimen C showed no doublets [M]. |
| Area conservation | Two L5 types have mostly cell-type-specific rather than area-specific properties | Groh et al. 2010 | L-P | Direct (mouse V1 + S1) | Medium; "important exceptions" noted by the authors. |
| Dendritic electrogenesis | BAC firing/Ca²⁺ spikes require active apical dendrites | Larkum et al. 1999; Larkum 2013; Hay et al. 2011 | L-P / L-R | Indirect (rat S1, model) | High; not testable with somatic-step data or perisomatic/single-compartment models. |
| IT vs PT physiology | IT accommodates and has low I_h; PT accelerates, resonates and has high I_h | Dembrow et al. 2010; Sheets et al. 2011; Hattox & Nelson 2007; Baker et al. 2018 | L-P / L-R | Indirect (PFC, M1, S1) | Medium for V1: projection-identified physiology in V1 is not established here. |
| Rbp4-Cre_KL100 | Labels L5 broadly, including both IT and PT neurons | Gerfen et al. 2013; Harris, J. A. et al. 2014, 2019 | L-P | Direct (line) | Medium–high; the statement in Harris 2019 is from the full text. |
| C: firing class | Regular-spiking, strongly adapting (ISI ratio up to 11.27×), no burst doublets | Frozen spike times; Allen `has_burst=False` | M / A | Direct | High for this cell; n = 1. |
| C: sag | 0.63 mV at −110 pA (Allen sag ratio 0.0468) | Frozen sweep; Allen | M / A | Direct | High; mechanism not identified. |
| C: R_in | Test-pulse 31.3 MΩ; 1000-ms step 90.6 MΩ; Allen 94.38 MΩ | Frozen CSVs; Allen | M / A | Direct | High; the two R_in definitions differ ≈ 3×. |
| C: identity | IT-like | Physiology vs literature | **H** | — | Not a classification: mixed-line genotype, no axon data, cross-area literature, n = 1. |
| C: detailed model | Overall RMSE 4.73 mV; +4.71 mV median baseline offset; +60 pA rheobase shift | Phase 3B CSVs | DP | Direct | High (frozen). |
| C: FHN | Overall RMSE 4.81 mV; TP10/FP2/FN1/TN21; stationary limit cycle (no SFA); bistable (360.03, 385.33) pA | Phase 4B/4C/4C.3 CSVs | RP | Direct | High (frozen). |

## 3. Layer 6a (Population D)

| Topic | Claim | Source | Evidence type | Relevance | Confidence / limitation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| CT origin | L6 is the sole source of CT feedback to first-order thalamus | Kirchgessner et al. 2020; Thomson 2010; Brumberg et al. 2003 | L-P / L-R | Direct (mouse visual) | High. |
| CT circuit | CT axons directly excite relay cells and indirectly inhibit them via TRN | Lam & Sherman 2010; Crandall et al. 2015 | L-P | Indirect (S1) | High in S1; assumed analogous for dLGN. |
| Modulator role | L6 CT input to first-order thalamus is modulatory, not driver | Sherman & Guillery 1998; Briggs & Usrey 2008; Sillito et al. 2006 | L-R | Context | Framework; widely used. |
| Frequency/state dependence | Suppression at low or sustained drive; enhancement at higher frequency (≈10 Hz) | Crandall et al. 2015; Kirchgessner et al. 2020 | L-P | Indirect (S1) / Direct (mouse visual) | High. |
| dLGN effects | Driving Ntsr1 projections reduced dLGN spikes; removal had mixed effects | Denman & Contreras 2015 | L-P | Direct (mouse visual) | High. |
| Spatial integration | CT feedback sharpens dLGN RFs and increases surround suppression | Born et al. 2021 | L-P | Direct (mouse visual) | High; the visTRN route is "probably". |
| Intracortical gain | L6 scales upper-layer visual gain without changing orientation tuning | Olsen et al. 2012 | L-P | Direct (mouse V1) | High. |
| Translaminar inhibition | L6 CT recruits translaminar FS interneurons | Bortone et al. 2014 | L-P | Direct (mouse V1) | High. |
| L6 → L5a | CT axons strongly excite L5a, weaker/suppressive onto L4 | Kim, J. et al. 2014 | L-P | Indirect (S1) | High. |
| CT vs CC in L6 | CT cells ultrasparse and sharply tuned in vivo; CC cells broadly tuned | Vélez-Fort et al. 2014 | L-P | Direct (mouse V1) | High; in vivo synaptic activity, not intrinsic excitability. |
| Corticofugal intrinsic properties | More excitable, narrower APs, smaller AHPs, similar R_in | Brumberg et al. 2003 | L-P | Direct (mouse V1) | High; antidromic identification. |
| L6a vs L6b | L6b is generally treated as the adult subplate remnant | Hoerder-Suabedissen & Molnár 2015 | L-R | Context | Medium; the abstract does not explicitly define L6b. |
| Ntsr1-Cre_GN220 | CT-selective at population level | Bortone et al. 2014; Gong et al. 2007; Gerfen et al. 2013; Denman & Contreras 2015 | L-P | Direct (mouse V1) | High at population level; not specimen-verified. |
| Delayed firing mechanism | A/D-type K⁺ currents delay L6a/CT spiking ("Kv4/Kv1.4 per literature") | none verified | **H** | — | No verified source; Allen `has_delay=False` [A]. |
| D: latency | Graded 113.82 ms (210 pA) → 27.37 ms (350 pA); FINEST +240 pA latencies 109.81–180.02 ms with 1 spike | Frozen spike times | M | Direct | High; the "> 1000 ms" claim is unsupported. |
| D: sag | 1.86 mV at −110 pA, the largest of the four specimens (Allen ratio 0.1228) | Frozen sweep; Allen | M / A | Direct | High; mechanism not identified. |
| D: R_in | Test-pulse 52.6 MΩ; step 125.5 MΩ; Allen 115.47 MΩ | Frozen CSVs; Allen | M / A | Direct | High. |
| D: identity | CT | Genotype + literature | **H** (plausible) | — | No axon or retrograde data; n = 1. |
| D: detailed model | Overall RMSE 2.23 mV; TP10/FP0/FN0/TN16; overfires FINEST +240 pA (11 vs 1) and +210 pA late spike (958.91 ms) | Phase 3B CSVs | DP | Direct | High (frozen). |
| D: FHN | Overall RMSE 9.03 mV; TP10/FP1/FN0/TN15; ≤ 4 spikes at ≥ 50 ms latency across 961 grid points | Phase 4B/4B.2/4C CSVs | RP | Direct | High (frozen). |

## 4. Modelling Interpretation (Cross-Laminar)

| Topic | Claim | Source | Evidence type | Relevance | Confidence / limitation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| R_in definition | Project R_in = 10-ms, 50-pA test pulse (apparent); steady-state R_in on 1000-ms steps is 2.4–3.0× the test-pulse value and 2.5–3.2× the FHN steady-state R_in | Frozen sweeps (read-only arithmetic) | M | Direct | High; this explains the FHN amplitude deficit. |
| FHN subthreshold | Matches the time course (r² ≥ 0.996) but under-predicts steady-state amplitude ≈ 3× | Frozen CSVs + derived | RP / M | Direct | High. |
| FHN "sag" | 0.00 mV is a hard-coded statement; the linearised FHN predicts a 1.7–4.1 mV transient undershoot that is not I_h | Analytic linearisation of frozen parameters | RP (derived) | Direct | Medium; requires formal simulation confirmation (not done, to respect the freeze). |
| SFA | Sustained SFA needs an additional slow variable | Benda & Herz 2003; Pospischil et al. 2008; Ermentrout 1998 | L-R / L-P | Context | High. |
| Reduced-model benchmarks | GLIF models with after-spike currents and threshold adaptation improve Allen-cell spike prediction | Teeter et al. 2018 | L-P | Direct (same database) | High. |
| Excitability class | A Hopf-type onset gives class-2-like, narrow-frequency-range firing | Prescott et al. 2008; Izhikevich 2007 | L-P / L-R | Context | High. |
| Detection trade-off | FHN: sens 92.5%, spec ≈ 89.9%; detailed: sens 60.0%, spec 100% (109 sweeps) | Phase 4C summary | RP / DP | Direct | High (frozen); FHN is not universally superior. |
