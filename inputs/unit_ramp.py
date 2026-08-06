from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def input_function(
    time: FloatArray,
    dt: float = 1e-2,
    reference_frequency: float = 1.0,
) -> FloatArray:
    return np.where(time >= 0.0, time, 0.0)
