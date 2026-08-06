from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from numpy.typing import NDArray

from transfer_functions.second_order_underdamped import (
    FrequencyReference,
    impulse_function as second_order_impulse_function,
    reference_frequency as second_order_reference_frequency,
)

FloatArray = NDArray[np.float64]
ImpulseFunction = Callable[[FloatArray, float, float], FloatArray]
ReferenceFunction = Callable[[float, float], FrequencyReference]


@dataclass(frozen=True)
class TransferFunctionDefinition:
    name: str
    display_name: str
    transfer_function: str
    impulse_function: ImpulseFunction
    reference_frequency: ReferenceFunction


_TRANSFER_FUNCTION_DEFINITIONS: dict[str, TransferFunctionDefinition] = {
    "second_order_underdamped": TransferFunctionDefinition(
        name="second_order_underdamped",
        display_name="Segunda ordem subamortecido",
        transfer_function="wn^2 / (s^2 + 2*zeta*wn*s + wn^2)",
        impulse_function=second_order_impulse_function,
        reference_frequency=second_order_reference_frequency,
    ),
}


def available_transfer_function_names() -> tuple[str, ...]:
    return tuple(_TRANSFER_FUNCTION_DEFINITIONS.keys())


def get_transfer_function_definition(name: str) -> TransferFunctionDefinition:
    try:
        return _TRANSFER_FUNCTION_DEFINITIONS[name]
    except KeyError as error:
        available = ", ".join(available_transfer_function_names())
        raise ValueError(
            f"Unknown transfer_function_name '{name}'. Available: {available}"
        ) from error
