"""Dimensional FitzHugh-Nagumo (FHN) Neuron Model Solver.

Provides a mathematically rigorous, dimensionally documented, and numerically stable
implementation of the two-variable conductance-based FitzHugh-Nagumo reduction.

Equations:
    C_m * dV/dt = -g_L * (V - V_rest) + k_v * (V - V_rest) * (V - V_th) * (V_peak - V) - w + I(t)
    tau_w * dw/dt = a_w * (V - V_rest) - w

Dimensional Units:
    V          : Somatic membrane potential [mV]
    w          : Recovery / adaptation variable [pA]
    t          : Time [ms]
    I(t)       : Injected intracellular current [pA]
    C_m        : Membrane capacitance [pF]
    g_L        : Leak conductance [nS]
    V_rest     : Resting membrane potential [mV]
    V_th       : Apparent action potential threshold parameter [mV]
    V_peak     : Action potential peak parameter [mV]
    k_v        : Cubic non-linearity scaling coefficient [nS/mV^2 = pA/mV^3]
    tau_w      : Recovery variable time constant [ms]
    a_w        : Recovery-voltage coupling conductance [nS = pA/mV]

Dimensional Consistency:
    C_m * dV/dt   : [pF] * [mV/ms] = 10^-12 F * (10^-3 V / 10^-3 s) = 10^-12 A = [pA]
    g_L * dV      : [nS] * [mV]    = 10^-9 S * 10^-3 V              = 10^-12 A = [pA]
    k_v * dV^3    : [nS/mV^2] * [mV^3] = [nS] * [mV]               = 10^-12 A = [pA]
    w             : [pA]
    I(t)          : [pA]
    tau_w * dw/dt : [ms] * [pA/ms]                                  = 10^-12 A = [pA]
    a_w * dV      : [nS] * [mV]                                     = 10^-12 A = [pA]
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence, Union
import numpy as np


@dataclass(frozen=True)
class FHNParameters:
    """Dimensional parameters for the 2D FitzHugh-Nagumo neuron model."""

    C_m: float = 100.0        # Membrane capacitance [pF]
    g_L: float = 5.0          # Leak conductance [nS]
    V_rest: float = -75.0     # Resting potential [mV]
    V_th: float = -50.0       # Threshold parameter [mV]
    V_peak: float = 20.0      # Peak parameter [mV]
    k_v: float = 0.005        # Cubic scaling coefficient [nS/mV^2]
    tau_w: float = 20.0       # Recovery time constant [ms]
    a_w: float = 2.0          # Recovery-voltage coupling conductance [nS]

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate parameter positivity and physical ordering."""
        if self.C_m <= 0.0:
            raise ValueError(f"Capacitance C_m must be strictly positive, got {self.C_m} pF")
        if self.g_L <= 0.0:
            raise ValueError(f"Leak conductance g_L must be strictly positive, got {self.g_L} nS")
        if self.tau_w <= 0.0:
            raise ValueError(f"Recovery time constant tau_w must be strictly positive, got {self.tau_w} ms")
        if self.a_w < 0.0:
            raise ValueError(f"Recovery coupling a_w must be non-negative, got {self.a_w} nS")
        if self.k_v <= 0.0:
            raise ValueError(f"Cubic non-linearity k_v must be strictly positive, got {self.k_v} nS/mV^2")
        if not (self.V_rest < self.V_th < self.V_peak):
            raise ValueError(
                f"Voltage parameters must satisfy V_rest < V_th < V_peak. "
                f"Got V_rest={self.V_rest} mV, V_th={self.V_th} mV, V_peak={self.V_peak} mV"
            )

    @property
    def effective_input_resistance_mohm(self) -> float:
        """Analytical input resistance at resting equilibrium in megaohms [MΩ].
        
        Linearizing dV/dt = 0 and dw/dt = 0 at (V_rest, 0) yields:
            g_eff = g_L + a_w + k_v * (V_th - V_rest) * (V_peak - V_rest)  [nS]
            R_in = 1 / g_eff = 1000 / g_eff  [MΩ]
        """
        k_rest = self.k_v * (self.V_th - self.V_rest) * (self.V_peak - self.V_rest)
        g_eff = self.g_L + self.a_w + k_rest
        return 1000.0 / g_eff

    @property
    def resting_jacobian(self) -> np.ndarray:
        """Jacobian matrix at resting equilibrium (V_rest, 0) in units of [1/ms]."""
        k_rest = self.k_v * (self.V_th - self.V_rest) * (self.V_peak - self.V_rest)
        j11 = -(self.g_L + k_rest) / self.C_m
        j12 = -1.0 / self.C_m
        j21 = self.a_w / self.tau_w
        j22 = -1.0 / self.tau_w
        return np.array([[j11, j12], [j21, j22]], dtype=float)

    @property
    def resting_eigenvalues(self) -> tuple[complex, complex]:
        """Eigenvalues of Jacobian at resting equilibrium."""
        j = self.resting_jacobian
        eigs = np.linalg.eigvals(j)
        return (complex(eigs[0]), complex(eigs[1]))

    @property
    def is_resting_point_stable(self) -> bool:
        """True if real parts of both resting Jacobian eigenvalues are strictly negative."""
        e1, e2 = self.resting_eigenvalues
        return e1.real < 0.0 and e2.real < 0.0


@dataclass(frozen=True)
class FHNSimulationConfig:
    """Numerical integration settings for the FHN solver."""

    dt_ms: float = 0.025            # Integration step size [ms]
    t_stop_ms: float = 1000.0       # Total duration [ms]
    V_init_mv: Optional[float] = None  # Initial membrane potential [mV] (defaults to V_rest)
    w_init_pa: Optional[float] = None  # Initial recovery current [pA] (defaults to 0.0)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate time step and duration constraints."""
        if self.dt_ms <= 0.0:
            raise ValueError(f"Integration time step dt_ms must be positive, got {self.dt_ms} ms")
        if self.t_stop_ms <= self.dt_ms:
            raise ValueError(
                f"Simulation duration t_stop_ms ({self.t_stop_ms} ms) must be greater than dt_ms ({self.dt_ms} ms)"
            )


@dataclass
class FHNResult:
    """Output trajectory of an FHN simulation run."""

    time_ms: np.ndarray             # Time vector [ms]
    v_mv: np.ndarray                # Membrane potential trajectory [mV]
    w_pa: np.ndarray                # Recovery current trajectory [pA]
    i_stim_pa: np.ndarray           # Applied stimulus current [pA]
    parameters: FHNParameters      # Model parameters used
    config: FHNSimulationConfig     # Simulation configuration used

    @property
    def n_points(self) -> int:
        return len(self.time_ms)

    def detect_spikes(self, threshold_mv: float = 0.0) -> np.ndarray:
        """Detect action potential peak times using positive threshold crossing.
        
        Returns array of spike times in ms.
        """
        crossings = np.where((self.v_mv[:-1] < threshold_mv) & (self.v_mv[1:] >= threshold_mv))[0]
        spike_times = []
        for idx in crossings:
            # Look ahead up to 2 ms to find the local peak
            window_pts = int(round(2.0 / self.config.dt_ms))
            end_idx = min(idx + window_pts, len(self.v_mv))
            peak_idx = idx + int(np.argmax(self.v_mv[idx:end_idx]))
            spike_times.append(self.time_ms[peak_idx])
        return np.array(spike_times, dtype=float)


class FitzHughNagumoModel:
    """Two-variable dimensional FitzHugh-Nagumo neuron model."""

    def __init__(self, parameters: Optional[FHNParameters] = None) -> None:
        self.params = parameters if parameters is not None else FHNParameters()

    def derivatives(self, v_mv: float, w_pa: float, i_stim_pa: float) -> tuple[float, float]:
        """Evaluate dV/dt [mV/ms] and dw/dt [pA/ms]."""
        p = self.params
        v_diff = v_mv - p.V_rest
        cubic = p.k_v * v_diff * (v_mv - p.V_th) * (p.V_peak - v_mv)
        i_leak = -p.g_L * v_diff
        dv_dt = (i_leak + cubic - w_pa + i_stim_pa) / p.C_m
        dw_dt = (p.a_w * v_diff - w_pa) / p.tau_w
        return dv_dt, dw_dt

    def v_nullcline(self, v_grid_mv: np.ndarray, i_stim_pa: float = 0.0) -> np.ndarray:
        """Calculate recovery current w [pA] on the V-nullcline (where dV/dt = 0)."""
        p = self.params
        v_diff = v_grid_mv - p.V_rest
        cubic = p.k_v * v_diff * (v_grid_mv - p.V_th) * (p.V_peak - v_grid_mv)
        i_leak = -p.g_L * v_diff
        return i_leak + cubic + i_stim_pa

    def w_nullcline(self, v_grid_mv: np.ndarray) -> np.ndarray:
        """Calculate recovery current w [pA] on the w-nullcline (where dw/dt = 0)."""
        p = self.params
        return p.a_w * (v_grid_mv - p.V_rest)

    def simulate(
        self,
        config: FHNSimulationConfig,
        stimulus: Union[Callable[[float], float], np.ndarray, None] = None,
    ) -> FHNResult:
        """Run fourth-order Runge-Kutta (RK4) integration.
        
        Args:
            config: Simulation settings (dt_ms, t_stop_ms, initial conditions).
            stimulus: Applied current in pA. Can be:
                      - None: zero current I(t) = 0.
                      - Callable: function I(t_ms) -> pA.
                      - np.ndarray: array of length n_points matching config.
        """
        p = self.params
        dt = config.dt_ms
        n_steps = int(round(config.t_stop_ms / dt))
        time_arr = np.linspace(0.0, config.t_stop_ms, n_steps + 1, dtype=float)

        # Build stimulus array
        if stimulus is None:
            i_stim = np.zeros(n_steps + 1, dtype=float)
        elif callable(stimulus):
            i_stim = np.array([stimulus(t) for t in time_arr], dtype=float)
        elif isinstance(stimulus, (np.ndarray, Sequence)):
            i_stim = np.asarray(stimulus, dtype=float)
            if len(i_stim) != len(time_arr):
                raise ValueError(
                    f"Stimulus array length ({len(i_stim)}) must match simulation time points ({len(time_arr)})"
                )
        else:
            raise TypeError(f"Unsupported stimulus type: {type(stimulus)}")

        # Initialize state arrays
        v_arr = np.zeros(n_steps + 1, dtype=float)
        w_arr = np.zeros(n_steps + 1, dtype=float)

        v_arr[0] = config.V_init_mv if config.V_init_mv is not None else p.V_rest
        w_arr[0] = config.w_init_pa if config.w_init_pa is not None else 0.0

        # RK4 Integration loop
        for n in range(n_steps):
            v_n = v_arr[n]
            w_n = w_arr[n]
            i_n = i_stim[n]
            i_next = i_stim[n + 1]
            i_mid = 0.5 * (i_n + i_next)

            # Stage 1
            k1_v, k1_w = self.derivatives(v_n, w_n, i_n)

            # Stage 2
            v_k2 = v_n + 0.5 * dt * k1_v
            w_k2 = w_n + 0.5 * dt * k1_w
            k2_v, k2_w = self.derivatives(v_k2, w_k2, i_mid)

            # Stage 3
            v_k3 = v_n + 0.5 * dt * k2_v
            w_k3 = w_n + 0.5 * dt * k2_w
            k3_v, k3_w = self.derivatives(v_k3, w_k3, i_mid)

            # Stage 4
            v_k4 = v_n + dt * k3_v
            w_k4 = w_n + dt * k3_w
            k4_v, k4_w = self.derivatives(v_k4, w_k4, i_next)

            # Update
            v_next = v_n + (dt / 6.0) * (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v)
            w_next = w_n + (dt / 6.0) * (k1_w + 2.0 * k2_w + 2.0 * k3_w + k4_w)

            # Sanity check for numerical overflow
            if not (np.isfinite(v_next) and np.isfinite(w_next)):
                raise FloatingPointError(
                    f"Simulation diverged at t = {time_arr[n]:.3f} ms. "
                    f"State: V = {v_next}, w = {w_next}. Reduce dt_ms or inspect parameters."
                )

            v_arr[n + 1] = v_next
            w_arr[n + 1] = w_next

        return FHNResult(
            time_ms=time_arr,
            v_mv=v_arr,
            w_pa=w_arr,
            i_stim_pa=i_stim,
            parameters=p,
            config=config,
        )

    def simulate_step_protocol(
        self,
        config: FHNSimulationConfig,
        amplitude_pa: float,
        onset_ms: float = 100.0,
        duration_ms: float = 800.0,
    ) -> FHNResult:
        """Simulate a single current clamp step protocol."""
        offset_ms = onset_ms + duration_ms

        def step_stim(t_ms: float) -> float:
            if onset_ms <= t_ms < offset_ms:
                return amplitude_pa
            return 0.0

        return self.simulate(config, stimulus=step_stim)
