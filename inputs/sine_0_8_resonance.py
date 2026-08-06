from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from inputs.sine_common import sine_input

FloatArray = NDArray[np.float64]
FREQUENCY_MULTIPLIER = 0.8


def input_function(
    time: FloatArray,
    dt: float = 1e-2,
    reference_frequency: float = 1.0,
) -> FloatArray:
    return sine_input(time, FREQUENCY_MULTIPLIER, reference_frequency)
