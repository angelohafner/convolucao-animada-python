from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def input_function(
    time: FloatArray,
    dt: float = 1e-2,
    reference_frequency: float = 1.0,
) -> FloatArray:
    if dt <= 0.0:
        raise ValueError("dt must be positive")
    if time.size == 0:
        raise ValueError("time must contain at least one sample")

    signal = np.zeros_like(time, dtype=float)
    origin_index = int(np.argmin(np.abs(time)))
    signal[origin_index] = 1.0 / dt
    return signal
