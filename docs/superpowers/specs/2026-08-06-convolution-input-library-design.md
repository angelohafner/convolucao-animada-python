# Convolution Input Library Design

## Context

The project currently generates a didactic MP4 animation of a convolution.
The default case is a unit-step input applied to a second-order underdamped
system. The user asked to add impulse, ramp, and sinusoidal inputs while keeping
one file per input and one file per transfer-function model.

## Design

Create an `inputs/` package. Each input lives in its own module and exposes an
`input_function(time, dt, reference_frequency)` function:

- `inputs/unit_step.py`
- `inputs/unit_impulse.py`
- `inputs/unit_ramp.py`
- `inputs/sine_0_7_resonance.py`
- `inputs/sine_0_8_resonance.py`
- `inputs/sine_0_9_resonance.py`
- `inputs/sine_1_0_resonance.py`
- `inputs/sine_1_1_resonance.py`
- `inputs/sine_1_2_resonance.py`
- `inputs/sine_1_3_resonance.py`

Create a `transfer_functions/` package. The current system moves to:

- `transfer_functions/second_order_underdamped.py`

`convolution_animation.py` remains the orchestration file for configuration,
calculation, plotting, animation, and CLI execution.

## Frequency Reference

For the default second-order system,

```text
H(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
```

use the resonance frequency

```text
omega_r = wn * sqrt(1 - 2*zeta^2)
```

when `zeta < 1 / sqrt(2)`.

If a transfer function has no resonance frequency, use `omega_ref = wn` as the
documented fallback. For the current default values, `zeta = 0.2` and
`wn = 2 rad/s`, the resonance exists.

## Selection

Add `input_name` and `transfer_function_name` to `AnimationConfig`.
The default remains `input_name = "unit_step"` and
`transfer_function_name = "second_order_underdamped"`.

The seven sinusoidal inputs are pure, non-causal, unit-amplitude signals:

```text
x(t) = sin(multiplier * omega_ref * t)
```

with multipliers `0.7` through `1.3`.

The numerical impulse is a discrete approximation with unit area:

```text
x[index closest to t = 0] = 1 / dt
sum(x) * dt = 1
```

## Documentation

Update `README.md` and `PROJECT_CONTEXT.md` with the folder structure,
available input names, active default model, resonance criterion, fallback
criterion, validation commands, and measured validation results.
