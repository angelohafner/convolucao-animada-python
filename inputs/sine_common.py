from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def sine_input(
    time: FloatArray,
    frequency_multiplier: float,
    reference_frequency: float,
) -> FloatArray:
    return np.sin(frequency_multiplier * reference_frequency * time)
