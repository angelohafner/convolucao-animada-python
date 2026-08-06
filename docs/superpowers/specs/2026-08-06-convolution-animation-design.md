# Design: animated convolution in Python

## Objective

Convert the supplied MATLAB convolution example to Python and generate a didactic MP4 that makes the convolution integral visually traceable. The default case remains a unit-step input applied to a second-order underdamped system.

## Selected approach

Use NumPy for signal generation and discrete convolution, Matplotlib for the plots and animation, and Matplotlib's `FFMpegWriter` for direct H.264 MP4 encoding. This approach is the closest Python equivalent to the MATLAB workflow while avoiding intermediate frame files.

The animation will improve on the original single-panel presentation by explicitly displaying the integrand `x(tau) * h(t - tau)`.

## Scope

The project will contain:

- `convolution_animation.py`: configuration, signal definitions, numerical convolution, analytical reference, plotting, animation, and command-line entry point.
- `tests/test_convolution_animation.py`: numerical and signal-definition tests.
- `requirements.txt`: Python dependencies.
- `README.md`: installation, execution, equations, outputs, and customization guidance.
- `PROJECT_CONTEXT.md`: persistent implementation and validation context.
- `outputs/convolucao_animada.mp4`: generated animation.
- `outputs/comparacao_numerica_analitica.png`: static validation figure.

The implementation will remain a small functional module rather than a package with many files because the calculation has one focused purpose.

## Numerical model

The time grid is

```text
dt = 0.01 s
t = -10 s, ..., 20 s
```

The default input is the unit step

```text
x(t) = u(t)
```

The default impulse response is

```text
h(t) = wn / sqrt(1 - zeta^2)
       * exp(-zeta * wn * t)
       * sin(wd * t)
       * u(t)

wd = wn * sqrt(1 - zeta^2)
zeta = 0.2
wn = 2 rad/s
```

The numerical convolution is calculated as

```text
y = convolve(x, h) * dt
```

and mapped from the full convolution time axis back to the original time grid using linear interpolation with zero outside the supported interval.

The analytical unit-step response used for validation is

```text
y_ref(t) = 1 - exp(-zeta * wn * t)
           * [cos(wd * t) + zeta / sqrt(1 - zeta^2) * sin(wd * t)]
```

for `t >= 0`, and zero otherwise.

## Animation design

The figure will use two vertically aligned panels with a shared horizontal range.

### Upper panel

- Plot the fixed input `x(tau)`.
- Plot the moving response `h(t - tau)` for the current animation time.
- Shade the signed product `x(tau) * h(t - tau)` relative to zero.
- Display the current values of `t` and the convolution integral.
- Label the horizontal axis as `tau` and retain explicit mathematical notation.

### Lower panel

- Show the full numerical response as a faint reference trace.
- Reveal the calculated response progressively up to the current time.
- Mark the current point `(t, y(t))`.
- Show the analytical response as a dashed validation trace.
- Label axes and units and include an unobtrusive legend.

Frames will include the first sample, every twentieth sample, and the final sample. With `dt = 0.01 s` and 25 frames per second, the resulting video duration will be approximately 6.1 seconds.

## MP4 encoding

The MP4 will be encoded with:

- codec: H.264 (`libx264`)
- pixel format: `yuv420p` for broad player compatibility
- frame rate: 25 fps
- output resolution: approximately 1400 x 900 pixels

The program will create the `outputs/` directory automatically. It will check whether Matplotlib can access FFmpeg and raise a concise actionable error if the writer is unavailable.

## Data flow

1. Build the time axis from the configuration.
2. Evaluate the selected input and impulse-response functions.
3. Calculate the numerical convolution and analytical reference.
4. Calculate validation-error metrics.
5. Save the static numerical-versus-analytical comparison.
6. Build and encode the two-panel animation.
7. Print the output paths and validation summary.

## Testing and validation

Automated tests will verify:

- the unit-step input is zero before the origin and one from the origin onward;
- the impulse response is causal;
- the impulse-response formula matches the expected value at selected positive times;
- the numerical output is causal within floating-point tolerance;
- the numerical convolution follows the analytical unit-step response within a tolerance consistent with the rectangular integration step `dt = 0.01 s`;
- the animation frame selection contains the first and final samples and is strictly increasing.

Final verification will include:

- `python -m pytest -q`;
- `python -m compileall convolution_animation.py tests`;
- execution of `python convolution_animation.py`;
- `ffprobe` inspection of codec, dimensions, frame rate, duration, and frame count;
- visual inspection of the static PNG and representative MP4 frames.

## Error handling and limitations

- Invalid configuration values such as non-positive `dt`, non-positive natural frequency, or damping outside `0 <= zeta < 1` will be rejected explicitly.
- The analytical reference applies only to the active unit-step/underdamped-second-order default case.
- Alternative signal examples may be documented, but they will not be hidden behind automatic analytical comparisons that do not apply.
- The numerical result includes the expected discretization error from rectangle-rule convolution.

## Acceptance criteria

The work is complete when:

1. The Python program runs from `D:/convolucao` with the documented command.
2. Both requested output files are generated.
3. The MP4 visibly shows `x(tau)`, moving `h(t - tau)`, the shaded product, and progressive `y(t)`.
4. The numerical and analytical responses agree within the documented tolerance.
5. Tests and compilation checks pass.
6. `ffprobe` confirms a playable H.264 MP4 at 25 fps.
