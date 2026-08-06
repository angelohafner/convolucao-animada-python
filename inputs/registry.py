from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from numpy.typing import NDArray

from inputs.sine_0_7_resonance import input_function as sine_0_7
from inputs.sine_0_8_resonance import input_function as sine_0_8
from inputs.sine_0_9_resonance import input_function as sine_0_9
from inputs.sine_1_0_resonance import input_function as sine_1_0
from inputs.sine_1_1_resonance import input_function as sine_1_1
from inputs.sine_1_2_resonance import input_function as sine_1_2
from inputs.sine_1_3_resonance import input_function as sine_1_3
from inputs.unit_impulse import input_function as unit_impulse
from inputs.unit_ramp import input_function as unit_ramp
from inputs.unit_step import input_function as unit_step

FloatArray = NDArray[np.float64]
InputFactory = Callable[[FloatArray, float, float], FloatArray]


@dataclass(frozen=True)
class InputDefinition:
    name: str
    display_name: str
    description: str
    input_function: InputFactory


_INPUT_DEFINITIONS: dict[str, InputDefinition] = {
    "unit_step": InputDefinition(
        name="unit_step",
        display_name="Degrau unitario",
        description="x(t) = u(t), incluindo t = 0.",
        input_function=unit_step,
    ),
    "unit_impulse": InputDefinition(
        name="unit_impulse",
        display_name="Impulso unitario numerico",
        description="Aproximacao discreta de delta(t) com area unitaria.",
        input_function=unit_impulse,
    ),
    "unit_ramp": InputDefinition(
        name="unit_ramp",
        display_name="Rampa unitaria",
        description="x(t) = t*u(t).",
        input_function=unit_ramp,
    ),
    "sine_0_7_resonance": InputDefinition(
        name="sine_0_7_resonance",
        display_name="Seno 0.7 omega_ref",
        description="x(t) = sin(0.7*omega_ref*t).",
        input_function=sine_0_7,
    ),
    "sine_0_8_resonance": InputDefinition(
        name="sine_0_8_resonance",
        display_name="Seno 0.8 omega_ref",
        description="x(t) = sin(0.8*omega_ref*t).",
        input_function=sine_0_8,
    ),
    "sine_0_9_resonance": InputDefinition(
        name="sine_0_9_resonance",
        display_name="Seno 0.9 omega_ref",
        description="x(t) = sin(0.9*omega_ref*t).",
        input_function=sine_0_9,
    ),
    "sine_1_0_resonance": InputDefinition(
        name="sine_1_0_resonance",
        display_name="Seno 1.0 omega_ref",
        description="x(t) = sin(omega_ref*t).",
        input_function=sine_1_0,
    ),
    "sine_1_1_resonance": InputDefinition(
        name="sine_1_1_resonance",
        display_name="Seno 1.1 omega_ref",
        description="x(t) = sin(1.1*omega_ref*t).",
        input_function=sine_1_1,
    ),
    "sine_1_2_resonance": InputDefinition(
        name="sine_1_2_resonance",
        display_name="Seno 1.2 omega_ref",
        description="x(t) = sin(1.2*omega_ref*t).",
        input_function=sine_1_2,
    ),
    "sine_1_3_resonance": InputDefinition(
        name="sine_1_3_resonance",
        display_name="Seno 1.3 omega_ref",
        description="x(t) = sin(1.3*omega_ref*t).",
        input_function=sine_1_3,
    ),
}


def available_input_names() -> tuple[str, ...]:
    return tuple(_INPUT_DEFINITIONS.keys())


def get_input_definition(name: str) -> InputDefinition:
    try:
        return _INPUT_DEFINITIONS[name]
    except KeyError as error:
        available = ", ".join(available_input_names())
        raise ValueError(f"Unknown input_name '{name}'. Available: {available}") from error


def get_input_signal(
    name: str,
    time: FloatArray,
    dt: float,
    reference_frequency: float,
) -> FloatArray:
    definition = get_input_definition(name)
    return definition.input_function(time, dt, reference_frequency)
