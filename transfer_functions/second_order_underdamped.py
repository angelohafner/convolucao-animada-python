from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class FrequencyReference:
    value: float
    has_resonance: bool
    source: str
    description: str


def impulse_function(
    time: FloatArray,
    damping_ratio: float = 0.2,
    natural_frequency: float = 2.0,
) -> FloatArray:
    # H(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
    damped_frequency = natural_frequency * np.sqrt(1.0 - damping_ratio**2)
    response = np.zeros_like(time, dtype=float)
    causal = time >= 0.0
    causal_time = time[causal]
    response[causal] = (
        natural_frequency
        / np.sqrt(1.0 - damping_ratio**2)
        * np.exp(-damping_ratio * natural_frequency * causal_time)
        * np.sin(damped_frequency * causal_time)
    )
    return response


def resonance_frequency(
    damping_ratio: float = 0.2,
    natural_frequency: float = 2.0,
) -> float | None:
    if damping_ratio < 1.0 / np.sqrt(2.0):
        return float(natural_frequency * np.sqrt(1.0 - 2.0 * damping_ratio**2))
    return None


def reference_frequency(
    damping_ratio: float = 0.2,
    natural_frequency: float = 2.0,
) -> FrequencyReference:
    resonance = resonance_frequency(damping_ratio, natural_frequency)
    if resonance is not None:
        return FrequencyReference(
            value=resonance,
            has_resonance=True,
            source="resonance_frequency",
            description="omega_ref = omega_r = wn*sqrt(1 - 2*zeta^2)",
        )
    return FrequencyReference(
        value=float(natural_frequency),
        has_resonance=False,
        source="natural_frequency_fallback",
        description="omega_ref = wn because this damping ratio has no resonance peak",
    )
