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


def test_rk4_fourth_order_on_smooth_reference_ode():
    """Verify standard fourth-order convergence (ratio ~ 16) on a smooth analytical ODE."""
    def rk4_step(y: float, dt: float) -> float:
        # dy/dt = -2y
        k1 = -2.0 * y
        k2 = -2.0 * (y + 0.5 * dt * k1)
        k3 = -2.0 * (y + 0.5 * dt * k2)
        k4 = -2.0 * (y + dt * k3)
        return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    def solve(dt: float, t_end: float = 1.0) -> float:
        n = int(round(t_end / dt))
        y = 1.0
        for _ in range(n):
            y = rk4_step(y, dt)
        return y

    exact = math.exp(-2.0)
    err_01 = abs(solve(0.1) - exact)
    err_005 = abs(solve(0.05) - exact)
    err_0025 = abs(solve(0.025) - exact)

    ratio1 = err_01 / err_005
    ratio2 = err_005 / err_0025

    # 4th order: ratio is approximately 2^4 = 16
    assert ratio1 > 15.0, f"Expected ratio > 15.0, got {ratio1}"
    assert ratio2 > 15.0, f"Expected ratio > 15.0, got {ratio2}"


def test_fhn_fourth_order_convergence_under_continuous_stimulus():
    """Under continuous stimulus without step discontinuities, FHN achieves 4th-order convergence."""
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    model = FitzHughNagumoModel(params)

    def run(dt: float) -> FHNResult:
        c = FHNSimulationConfig(dt_ms=dt, t_stop_ms=100.0)
        return model.simulate(c, stimulus=lambda t: 220.0)

    r_100 = run(0.1)
    r_050 = run(0.05)
    r_025 = run(0.025)

    eval_times = np.arange(0.0, 100.1, 0.1)
    idx_100 = [int(round(t / 0.1)) for t in eval_times]
    idx_050 = [int(round(t / 0.05)) for t in eval_times]
    idx_025 = [int(round(t / 0.025)) for t in eval_times]

    d1 = np.max(np.abs(r_100.v_mv[idx_100] - r_050.v_mv[idx_050]))
    d2 = np.max(np.abs(r_050.v_mv[idx_050] - r_025.v_mv[idx_025]))

    ratio = d1 / d2
    # Confirms RK4 4th-order convergence (ratio ~ 16) on smooth FHN trajectories
    assert ratio > 15.0, f"Expected convergence ratio > 15.0, got {ratio}"


def test_analytical_unique_unstable_equilibrium_at_220pa():
    """Verify algebraic uniqueness and unstable focus classification of the equilibrium at 220 pA."""
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    # At V* = V_th = -50.0 mV: cubic is identically 0.
    # f_V(-50) = -1.0 * (-50 - (-70)) = -20.0 pA.
    # w* = 10.0 * 20.0 = 200.0 pA.
    # dV/dt = (-20 - 200 + 220) / 50 = 0.
    v_star = -50.0
    w_star = 200.0
    model = FitzHughNagumoModel(params)
    dv, dw = model.derivatives(v_star, w_star, 220.0)
    assert abs(dv) < 1e-12
    assert abs(dw) < 1e-12

    # Verify uniqueness: quadratic factor u^2 - 90u + 2200 has negative discriminant
    # u = V - V_rest; Delta = 90^2 - 4 * 2200 = 8100 - 8800 = -700 < 0
    disc = 90.0**2 - 4.0 * 2200.0
    assert disc < 0.0

    # Jacobian at (-50, 200):
    # df_V/dV = -1.0 + 0.005 * 20 * 70 = 6.0 nS
    # Tr(J) = 6.0 / 50 - 1 / 15 = 0.05333 > 0
    # Det(J) = (10 - 6) / (50 * 15) = 4 / 750 > 0
    df_dv = -params.g_L + params.k_v * (v_star - params.V_rest) * (params.V_peak - v_star)
    assert pytest.approx(df_dv) == 6.0
    tr = df_dv / params.C_m - 1.0 / params.tau_w
    det = (params.a_w - df_dv) / (params.C_m * params.tau_w)
    assert tr > 0.0
    assert det > 0.0


def test_bistability_near_subcritical_hopf_bifurcation():
    """Verify subcritical Hopf bistability at I = 194 pA (coexistence of rest state and limit cycle)."""
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    model = FitzHughNagumoModel(params)

    # 1. Starting near resting equilibrium (-55 mV, 150 pA): settles to stable focus without spikes
    c_rest = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=500.0, V_init_mv=-55.0, w_init_pa=150.0)
    r_rest = model.simulate(c_rest, stimulus=lambda t: 194.0)
    assert len(r_rest.detect_spikes(threshold_mv=0.0)) == 0

    # 2. Starting on excited branch (0 mV, 300 pA): sustains limit cycle firing
    c_exc = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=500.0, V_init_mv=0.0, w_init_pa=300.0)
    r_exc = model.simulate(c_exc, stimulus=lambda t: 194.0)
    assert len(r_exc.detect_spikes(threshold_mv=0.0)) >= 4


def test_poincare_return_map_limit_cycle_convergence():
    """Verify that successive crossings on the Poincare section contract geometrically to a periodic orbit."""
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    model = FitzHughNagumoModel(params)
    config = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=1000.0)
    res = model.simulate(config, stimulus=lambda t: 220.0)

    # Crossings of V = 0 mV with dV/dt > 0
    crossings = np.where((res.v_mv[:-1] < 0.0) & (res.v_mv[1:] >= 0.0))[0]
    assert len(crossings) >= 8

    w_crossings = []
    for idx in crossings:
        v0, v1 = res.v_mv[idx], res.v_mv[idx + 1]
        w0, w1 = res.w_pa[idx], res.w_pa[idx + 1]
        frac = (0.0 - v0) / (v1 - v0)
        w_crossings.append(w0 + frac * (w1 - w0))

    # Successive difference between final crossings must contract tightly
    diff_last = abs(w_crossings[-1] - w_crossings[-2])
    assert diff_last < 0.01, f"Poincare return map difference was {diff_last} pA"


def test_exact_analytical_hopf_bifurcation_point():
    """Verify exact analytical Hopf bifurcation current I_H1 = 195.3113 pA and pure imaginary eigenvalues."""
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    # Exact analytical root: u_H1 = (110 - 10*sqrt(41)) / 3
    u_h1 = (110.0 - 10.0 * math.sqrt(41.0)) / 3.0
    v_h1 = params.V_rest + u_h1
    i_h1 = 0.005 * u_h1**3 - 0.55 * u_h1**2 + 20.0 * u_h1

    assert pytest.approx(v_h1, abs=1e-4) == -54.6771
    assert pytest.approx(i_h1, abs=1e-4) == 195.3113

    # Check Jacobian trace and determinant at exact Hopf point
    df_dv = -0.015 * u_h1**2 + 1.1 * u_h1 - 10.0
    assert pytest.approx(df_dv) == 10.0 / 3.0
    tr = (df_dv - params.C_m / params.tau_w) / params.C_m
    det = (params.a_w - df_dv) / (params.C_m * params.tau_w)
    assert abs(tr) < 1e-15
    assert pytest.approx(det) == 2.0 / 225.0


def test_analytical_first_lyapunov_coefficient_is_positive():
    """Verify exact first Lyapunov coefficient l_1 = +1.575e-4 > 0, proving subcritical Hopf bifurcation."""
    Cm, gL, kv = 50.0, 1.0, 0.005
    tau_w, aw = 15.0, 10.0
    u_h1 = (110.0 - 10.0 * np.sqrt(41.0)) / 3.0
    d2f = 0.1 * np.sqrt(41.0)
    d3f = -0.030

    A = np.array([[1.0 / tau_w, -1.0 / Cm], [aw / tau_w, -1.0 / tau_w]])
    omega0 = np.sqrt(np.linalg.det(A))
    q = np.array([1.0, Cm * (1.0 / tau_w - 1j * omega0)])
    p_raw = np.array([-(aw / tau_w) / (1.0 / tau_w + 1j * omega0), 1.0])
    p = p_raw / np.conj(np.vdot(p_raw, q))

    def b_vec(x, y):
        return np.array([(d2f / Cm) * x[0] * y[0], 0.0 + 0j])

    def c_vec(x, y, z):
        return np.array([(d3f / Cm) * x[0] * y[0] * z[0], 0.0 + 0j])

    t1 = np.vdot(p, c_vec(q, q, np.conj(q)))
    t2 = -2.0 * np.vdot(p, b_vec(q, np.linalg.solve(A, b_vec(q, np.conj(q)))))
    t3 = np.vdot(p, b_vec(np.conj(q), np.linalg.solve(2j * omega0 * np.eye(2) - A, b_vec(q, q))))

    l1 = 0.5 * np.real(t1 + t2 + t3)
    assert l1 > 0.0
    assert pytest.approx(l1, abs=1e-6) == 1.575e-4


def test_fold_of_limit_cycles_bistability_boundary():
    """Verify that bistability terminates below I_LPC ~ 191.0 pA where the stable limit cycle disappears."""
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    model = FitzHughNagumoModel(params)

    # At I = 191.0 pA: inside bistable window, sustained limit cycle from excited state
    c_191 = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=800.0, V_init_mv=0.0, w_init_pa=300.0)
    r_191 = model.simulate(c_191, stimulus=lambda t: 191.0)
    assert len(r_191.detect_spikes(threshold_mv=0.0)) >= 6

    # At I = 180.0 pA: below fold of limit cycles, collapses to resting state without spikes
    c_180 = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=800.0, V_init_mv=0.0, w_init_pa=300.0)
    r_180 = model.simulate(c_180, stimulus=lambda t: 180.0)
    assert len(r_180.detect_spikes(threshold_mv=0.0)) == 0
    assert abs(r_180.v_mv[-1] - (-56.76)) < 0.5


def test_reproducibility_220pa_orbit_across_independent_initial_conditions():
    """Verify that widely separated initial conditions all converge to the identical stable periodic orbit."""
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    model = FitzHughNagumoModel(params)

    for v0, w0 in [(-70.0, 0.0), (10.0, 500.0), (-85.0, -100.0)]:
        c = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=1000.0, V_init_mv=v0, w_init_pa=w0)
        res = model.simulate(c, stimulus=lambda t: 220.0)
        spikes = res.detect_spikes(threshold_mv=0.0)
        late_spikes = spikes[spikes > 400.0]
        isis = np.diff(late_spikes)
        assert abs(np.mean(isis) - 82.77) < 0.05
        assert np.std(isis) < 0.02
