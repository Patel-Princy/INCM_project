# Project Methodology

## Research question

**How much biological detail does a neuron model need to reproduce a real neuron's
electrophysiological behaviour, and which behaviours are preserved or lost when a
detailed conductance-based model is reduced to a FitzHugh–Nagumo (FHN) model?**

---

## 1. Biological rationale for four layer-defined populations

Neurons in different layers of primary visual cortex (VISp) occupy distinct
positions in the cortical circuit and are expected to have distinguishable
electrophysiological phenotypes.

| Layer | Circuit role | Expected phenotype |
|-------|-------------|-------------------|
| L4 | Thalamorecipient; first cortical stage | Strong fast feed-forward response; reliable onset |
| L2/3 | Cortico-cortical output | Moderate adaptation; rate-coded response |
| L5 | Long-range subcortical output | Strong adaptation; burst potential; large dendritic tree |
| L6a | Corticothalamic feedback | Long membrane time constant; distinctive adaptation |

These are hypotheses for selection, not confirmed assignments. The Allen database
does not carry projection identity (IT/ET/PT/CT), so the populations are defined by
anatomical layer and dendrite morphology only.

---

## 2. Model hierarchy

Two model classes are compared at two scales:

**Detailed model (perisomatic biophysical):**
- Conductance-based Hodgkin-Huxley style model
- Published by the Allen Institute; fitted to one calibration sweep per neuron
- Template `329230710`; mechanisms: Ih, NaV, Kd, Kv2like, Kv3_1, K_T, Im_v2,
  SK, Ca_HVA, Ca_LVA, CaDynamics, g_pas
- Parameters: axial resistance (`ra`), membrane capacitance (`cm`), passive
  reversal potential (`e_pas`), and per-mechanism conductances

**Reduced model (FitzHugh–Nagumo):**
- Two-dimensional polynomial dynamical system (not yet implemented)
- Captures excitable dynamics (rest, threshold, spike, recovery) without ionic
  channel detail
- Cannot reproduce quantitative spike waveforms; evaluated on firing rate, spike
  count, latency, and adaptation

---

## 3. Evaluation framework

### 3.1 Calibration vs held-out separation

Each model is fitted (or parameterised) on a **calibration set** and evaluated on
a **held-out set**. The calibration/held-out split is derived from the fit
descriptor: the Allen fitting sweep is the calibration condition; all remaining
depolarising sweeps are held-out candidates.

Phase 0C established that 13/16 selected candidates have leakage-safe held-out
splits (at least two distinct depolarising amplitudes not seen in the fit).

### 3.2 Evaluation metrics

| Metric | Relevant to | Note |
|--------|-------------|------|
| Resting membrane potential | Both models | Measure at baseline before step |
| Input resistance | Both models | From subthreshold long-square sweeps |
| Membrane time constant | Both models | Exponential fit to hyperpolarising step |
| Rheobase | Both models | Interpolated from F-I curve |
| Spike count (F-I) | Both models | Per sweep, across amplitudes |
| First-spike latency | Both models | From step onset to first spike threshold crossing |
| Mean firing rate | Both models | Over step duration, conditional on spiking |
| Adaptation index | Both models | Ratio of first/last ISI |
| Spike amplitude | Detailed only | Sensitive to axon configuration |
| Spike half-width | Detailed only (200 kHz) | Requires 200 kHz; FHN not quantitatively comparable |
| AHP amplitude | Detailed model qualitative | FHN AHP shape is phenomenological |

FHN spike waveforms are phenomenological; spike-shape metrics are not used to
judge FHN accuracy.

### 3.3 Protocol considerations

- Long-square COARSE block (`C1LSCOARSE150216`): 20 pA steps, 1000 ms
- Long-square FINEST block (`C1LSFINEST150112`): 10 pA steps, 1000 ms
- The COARSE block is used as the calibration protocol (fitting sweep is a COARSE
  sweep for all 13 resolved candidates)
- The FINEST block is the held-out protocol (protocol-family split)
- Phase 2F established that COARSE and FINEST recordings at the same amplitude
  are not identical despite bit-identical stimulus arrays (excitability state
  difference between protocols is a measurable within-specimen effect)

---

## 4. Known scientific limitations

1. **Single calibration sweep per model.** Allen's perisomatic fitting uses one
   sweep. This is a narrow calibration; the model cannot be expected to reproduce
   all amplitudes equally.
2. **Axon configuration unpublished.** The original axon treatment used during
   fitting is not documented. Phase 2G-C showed that stub vs truncated axon gives
   qualitatively different excitability. This is a model provenance gap.
3. **Reconstruction mismatch in one candidate.** Specimen 382982932 (B group)
   uses a model fitted on a different morphological reconstruction. Model output
   reflects that reconstruction, not the cell's own.
4. **Layer identity is not projection identity.** No IT/ET/PT/CT claims are made.
   All four populations are described as "spiny excitatory neurons" in their
   respective layers.
5. **Sample sizes are small.** Four neurons per layer is sufficient for a
   preliminary characterisation but cannot support layer-level generalisations.
   Statistical comparisons across populations require a much larger study.
6. **FHN implementation not yet complete.** Phases 3–5 remain to be executed.
