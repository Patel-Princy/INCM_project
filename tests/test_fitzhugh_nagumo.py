"""Tests for the Dimensional FitzHugh-Nagumo (FHN) Neuron Model Solver.

Verifies:
1. Exact zero-current resting equilibrium preservation.
2. Recovery-variable steady-state alignment.
3. Constant-current integration.
4. Step-current protocol response (hyperpolarizing vs depolarizing).
5. Deterministic reproducibility across multiple identical executions.
6. Rejection of invalid parameter combinations and invalid simulation configs.
7. Numerical convergence under time-step refinement (dt = 0.1, 0.05, 0.025 ms).
8. Dimensional and output array consistency (time, voltage, recovery, current).
9. Finite outputs and absence of numerical overflow.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from src.models.fitzhugh_nagumo import (
    FHNParameters,
    FHNSimulationConfig,
    FHNResult,
    FitzHughNagumoModel,
)


def test_default_parameters_valid():
    params = FHNParameters()
    assert params.C_m == 100.0
    assert params.g_L == 5.0
    assert params.V_rest == -75.0
    assert params.V_th == -50.0
    assert params.V_peak == 20.0
    assert params.k_v == 0.005
    assert params.tau_w == 20.0
    assert params.a_w == 2.0
    assert params.is_resting_point_stable


def test_parameter_validation_rejects_invalid_values():
    # Negative capacitance
    with pytest.raises(ValueError, match="Capacitance C_m must be strictly positive"):
        FHNParameters(C_m=-10.0)

    # Zero leak conductance
    with pytest.raises(ValueError, match="Leak conductance g_L must be strictly positive"):
        FHNParameters(g_L=0.0)

    # Negative tau_w
    with pytest.raises(ValueError, match="Recovery time constant tau_w must be strictly positive"):
        FHNParameters(tau_w=-5.0)

    # Negative a_w
    with pytest.raises(ValueError, match="Recovery coupling a_w must be non-negative"):
        FHNParameters(a_w=-1.0)

    # Negative k_v
    with pytest.raises(ValueError, match="Cubic non-linearity k_v must be strictly positive"):
        FHNParameters(k_v=-0.01)

    # Inverted voltage ordering: V_rest >= V_th
    with pytest.raises(ValueError, match="Voltage parameters must satisfy V_rest < V_th < V_peak"):
        FHNParameters(V_rest=-50.0, V_th=-50.0, V_peak=20.0)

    # Inverted voltage ordering: V_th >= V_peak
    with pytest.raises(ValueError, match="Voltage parameters must satisfy V_rest < V_th < V_peak"):
        FHNParameters(V_rest=-75.0, V_th=30.0, V_peak=20.0)


def test_config_validation_rejects_invalid_values():
    with pytest.raises(ValueError, match="Integration time step dt_ms must be positive"):
        FHNSimulationConfig(dt_ms=0.0)

    with pytest.raises(ValueError, match="Integration time step dt_ms must be positive"):
        FHNSimulationConfig(dt_ms=-0.05)

    with pytest.raises(ValueError, match="Simulation duration t_stop_ms .* must be greater than dt_ms"):
        FHNSimulationConfig(dt_ms=0.1, t_stop_ms=0.05)


def test_zero_current_resting_equilibrium():
    """At I=0 with V(0) = V_rest and w(0) = 0, state must remain exactly at equilibrium."""
    params = FHNParameters(V_rest=-70.0, V_th=-45.0, V_peak=25.0)
    model = FitzHughNagumoModel(params)
    config = FHNSimulationConfig(dt_ms=0.05, t_stop_ms=500.0)

    res = model.simulate(config, stimulus=None)

    assert len(res.time_ms) == int(500.0 / 0.05) + 1
    # Check that V(t) remains within 1e-10 of V_rest
    assert np.all(np.abs(res.v_mv - params.V_rest) < 1e-10)
    # Check that w(t) remains within 1e-10 of 0.0
    assert np.all(np.abs(res.w_pa) < 1e-10)


def test_resting_jacobian_and_stability():
    params = FHNParameters()
    assert params.is_resting_point_stable
    e1, e2 = params.resting_eigenvalues
    assert e1.real < 0.0
    assert e2.real < 0.0
    # Trace must be negative, determinant positive
    tr = np.trace(params.resting_jacobian)
    det = np.linalg.det(params.resting_jacobian)
    assert tr < 0.0
    assert det > 0.0


def test_subthreshold_input_resistance_matches_analytical():
    """A tiny current step must deflect voltage by approximately R_in * I_stim."""
    params = FHNParameters(C_m=100.0, g_L=4.0, a_w=1.0, k_v=0.002, V_rest=-75.0, V_th=-50.0, V_peak=20.0)
    model = FitzHughNagumoModel(params)
    r_in_analytical_mohm = params.effective_input_resistance_mohm

    # Inject small current step in linear regime: +2.0 pA for 500 ms
    config = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=600.0)
    i_amp = 2.0  # pA
    res = model.simulate_step_protocol(config, amplitude_pa=i_amp, onset_ms=50.0, duration_ms=500.0)

    # Measured steady-state deflection at t = 500 ms
    v_baseline = params.V_rest
    v_ss = res.v_mv[int(500.0 / 0.025)]
    delta_v_measured_mv = v_ss - v_baseline

    # R_in = delta_V (mV) / I (pA) in units of GΩ = 1000 MΩ
    # delta_V = R_in (MΩ) * I (pA) / 1000
    expected_delta_v_mv = (r_in_analytical_mohm * i_amp) / 1000.0

    # Linear regime relative error < 1%
    assert pytest.approx(delta_v_measured_mv, rel=0.01) == expected_delta_v_mv


def test_hyperpolarizing_step_response():
    """A negative step should hyperpolarize the cell without initiating action potentials."""
    params = FHNParameters()
    model = FitzHughNagumoModel(params)
    config = FHNSimulationConfig(dt_ms=0.05, t_stop_ms=400.0)

    res = model.simulate_step_protocol(config, amplitude_pa=-100.0, onset_ms=50.0, duration_ms=250.0)

    # Membrane must hyperpolarize below V_rest during the pulse
    during_pulse = (res.time_ms >= 100.0) & (res.time_ms <= 280.0)
    assert np.all(res.v_mv[during_pulse] < params.V_rest)

    # No spikes detected
    spikes = res.detect_spikes(threshold_mv=-20.0)
    assert len(spikes) == 0

    # Returns to rest after pulse
    post_pulse = res.time_ms >= 380.0
    assert np.all(np.abs(res.v_mv[post_pulse] - params.V_rest) < 0.1)


def test_depolarizing_suprathreshold_spiking():
    """A positive step current in the limit-cycle regime must elicit repetitive action potentials."""
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    model = FitzHughNagumoModel(params)
    config = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=800.0)

    res = model.simulate_step_protocol(config, amplitude_pa=220.0, onset_ms=50.0, duration_ms=700.0)

    spikes = res.detect_spikes(threshold_mv=0.0)
    assert len(spikes) >= 5, f"Expected repetitive spiking, got {len(spikes)} spikes"

    # Peak voltage must exceed 0 mV during action potentials
    assert np.max(res.v_mv) > 0.0


def test_deterministic_reproducibility():
    """Two identical runs must produce identical bitwise results."""
    params = FHNParameters()
    model = FitzHughNagumoModel(params)
    config = FHNSimulationConfig(dt_ms=0.05, t_stop_ms=300.0)

    res1 = model.simulate_step_protocol(config, amplitude_pa=80.0, onset_ms=50.0, duration_ms=200.0)
    res2 = model.simulate_step_protocol(config, amplitude_pa=80.0, onset_ms=50.0, duration_ms=200.0)

    np.testing.assert_array_equal(res1.v_mv, res2.v_mv)
    np.testing.assert_array_equal(res1.w_pa, res2.w_pa)
    np.testing.assert_array_equal(res1.time_ms, res2.time_ms)


def test_time_step_refinement_convergence():
    """Refining dt from 0.1 to 0.05 to 0.025 ms must converge with bounded difference."""
    params = FHNParameters(C_m=100.0, g_L=3.0, k_v=0.006, V_rest=-70.0, V_th=-50.0, V_peak=25.0, tau_w=20.0, a_w=2.0)
    model = FitzHughNagumoModel(params)
    t_stop = 200.0
    amp = 100.0

    # Coarse: dt = 0.1 ms
    c_coarse = FHNSimulationConfig(dt_ms=0.1, t_stop_ms=t_stop)
    res_coarse = model.simulate_step_protocol(c_coarse, amplitude_pa=amp, onset_ms=20.0, duration_ms=160.0)

    # Medium: dt = 0.05 ms
    c_medium = FHNSimulationConfig(dt_ms=0.05, t_stop_ms=t_stop)
    res_medium = model.simulate_step_protocol(c_medium, amplitude_pa=amp, onset_ms=20.0, duration_ms=160.0)

    # Fine: dt = 0.025 ms
    c_fine = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=t_stop)
    res_fine = model.simulate_step_protocol(c_fine, amplitude_pa=amp, onset_ms=20.0, duration_ms=160.0)

    # Compare at shared integer time points (every 1.0 ms)
    eval_times = np.arange(0.0, t_stop, 1.0)
    idx_c = [int(round(t / 0.1)) for t in eval_times]
    idx_m = [int(round(t / 0.05)) for t in eval_times]
    idx_f = [int(round(t / 0.025)) for t in eval_times]

    v_c = res_coarse.v_mv[idx_c]
    v_m = res_medium.v_mv[idx_m]
    v_f = res_fine.v_mv[idx_f]

    diff_coarse_medium = np.max(np.abs(v_c - v_m))
    diff_medium_fine = np.max(np.abs(v_m - v_f))

    # Error between medium (0.05) and fine (0.025) must be smaller than coarse (0.1) and medium (0.05)
    assert diff_medium_fine < diff_coarse_medium
    # Medium-fine difference must be tightly bounded (< 0.5 mV)
    assert diff_medium_fine < 0.5, f"Medium-fine difference was {diff_medium_fine} mV"


def test_finite_outputs_and_no_overflow():
    params = FHNParameters()
    model = FitzHughNagumoModel(params)
    config = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=500.0)

    res = model.simulate_step_protocol(config, amplitude_pa=50.0, onset_ms=50.0, duration_ms=300.0)

    assert np.all(np.isfinite(res.v_mv))
    assert np.all(np.isfinite(res.w_pa))
    assert np.all(np.isfinite(res.time_ms))
    assert len(res.v_mv) == len(res.time_ms)
    assert len(res.w_pa) == len(res.time_ms)
    assert len(res.i_stim_pa) == len(res.time_ms)
