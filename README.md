# Animated Convolution in Python

A Python project for generating educational MP4 animations of continuous-time
convolution. The animation shows the input signal, the shifted impulse response,
their product, the signed integration area, and the progressive construction of
the output signal.

Public repository: [angelohafner/convolucao-animada-python](https://github.com/angelohafner/convolucao-animada-python)

## Purpose

The project provides a visual and reproducible way to study:

- convolution in the time domain;
- impulse, step, and ramp responses;
- sinusoidal steady-state behavior;
- the relationship between time-domain responses and frequency response;
- Bode magnitude and phase diagrams.

The default system is a second-order underdamped system. Input signals and
transfer functions are organized in independent registries so the project can
be extended without mixing signal definitions, numerical calculations, and
animation logic.

## Mathematical model

The default transfer function is

```text
H(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
```

with the current parameters

```text
zeta = 0.1
wn = 2 rad/s
```

Its impulse response is

```text
h(t) = wn / sqrt(1 - zeta^2)
       * exp(-zeta * wn * t)
       * sin(wd * t)
       * u(t)

wd = wn * sqrt(1 - zeta^2)
```

Continuous convolution is approximated numerically as

```text
y(t) = integral x(tau) * h(t - tau) d(tau)
y_num = convolve(x, h) * dt
```

The default numerical time step is

```text
dt = 0.01 s
```

## Reference frequency

For the default second-order system, a resonance frequency exists when

```text
zeta < 1 / sqrt(2)
```

The reference frequency is then

```text
omega_0 = omega_r = wn * sqrt(1 - 2*zeta^2)
```

For `zeta=0.1` and `wn=2 rad/s`:

```text
omega_0 = 1.97989899 rad/s
```

If a future system has no resonance peak, the natural frequency is used as the
fallback reference:

```text
omega_0 = wn
```

## Project structure

```text
D:/convolucao/
|-- convolution_animation.py
|-- inputs/
|   |-- unit_step.py
|   |-- unit_impulse.py
|   |-- unit_ramp.py
|   |-- sine_common.py
|   |-- sine_0_7_resonance.py
|   |-- sine_0_8_resonance.py
|   |-- sine_0_9_resonance.py
|   |-- sine_1_0_resonance.py
|   |-- sine_1_1_resonance.py
|   |-- sine_1_2_resonance.py
|   |-- sine_1_3_resonance.py
|   `-- registry.py
|-- transfer_functions/
|   |-- second_order_underdamped.py
|   `-- registry.py
|-- tests/
|   `-- test_convolution_animation.py
|-- outputs/
|-- docs/
|-- PROJECT_CONTEXT.md
|-- requirements.txt
`-- README.md
```

## Available input signals

Use these names with `AnimationConfig(input_name=...)` or `--input-name`:

```text
unit_step
unit_impulse
unit_ramp
sine_0_7_resonance
sine_0_8_resonance
sine_0_9_resonance
sine_1_0_resonance
sine_1_1_resonance
sine_1_2_resonance
sine_1_3_resonance
```

### Numerical unit impulse

The unit impulse is represented by one numerical sample at the index closest
to `t=0`:

```text
x[k0] = 1 / dt
sum(x) * dt = 1
```

For `dt=0.01 s`, the sample amplitude is `100`, preserving unit area. In the
animation, the impulse is drawn as a unit-height arrow so the system impulse
response remains readable. This visual convention does not change the numerical
calculation.

### Sinusoidal inputs

The individual sinusoidal inputs are pure, noncausal, unit-amplitude signals:

```text
x(t) = sin(n * omega_0 * t)
```

The default multi-sine sequence uses

```text
n = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8]
```

Each sine wave is processed independently. The signals are not summed into one
input. This makes it possible to associate each time-domain response with a
specific point on the frequency-response diagram.

## Available transfer functions

Use the following name with `AnimationConfig(transfer_function_name=...)` or
`--transfer-function-name`:

```text
second_order_underdamped
```

The implementation is located in
`transfer_functions/second_order_underdamped.py`.

## Installation

Create and activate a virtual environment if desired, then install the Python
dependencies:

```powershell
cd D:\convolucao
python -m pip install -r requirements.txt
```

FFmpeg must also be installed and available on `PATH`:

```powershell
ffmpeg -version
ffprobe -version
```

## Generating animations

### Generate all registered single-input cases

```powershell
python convolution_animation.py
```

The batch workflow generates impulse, step, ramp, and registered sine cases in
numbered subdirectories under `outputs/`.

### Generate one input case

Unit impulse:

```powershell
python convolution_animation.py --input-name unit_impulse
```

Unit step:

```powershell
python convolution_animation.py --input-name unit_step
```

Unit ramp:

```powershell
python convolution_animation.py --input-name unit_ramp
```

Single-input outputs are written to

```text
outputs/convolucao_animada.mp4
outputs/comparacao_numerica_analitica.png
```

### High-resolution impulse animation

```powershell
python convolution_animation.py `
  --input-name unit_impulse `
  --start-time -10 `
  --end-time 10 `
  --dt 0.005 `
  --frame-stride 10 `
  --fps 60 `
  --dpi 300 `
  --output-dir outputs/unit_impulse_dt005_60fps_dpi300
```

This configuration is computationally expensive because it combines a small
time step, many animation frames, 60 fps, and publication-scale resolution.

## Multi-sine frequency-response animation

Run the default sequence with

```powershell
python convolution_animation.py --sine-sequence
```

Use custom frequency multipliers with

```powershell
python convolution_animation.py `
  --sine-sequence `
  --sine-multipliers 0.4,0.8,1.0,1.2,1.6
```

The animation contains three panels:

1. convolution construction using `x(tau)`, `h(t-tau)`, their product, and the
   signed integration area;
2. overlaid time-domain responses, preserving responses from previous sine
   waves;
3. theoretical Bode magnitude and phase curves with colored markers at each
   simulated frequency.

The interface uses English labels and LaTeX notation such as `$n\omega_0$`.
Sine colors are assigned with the `jet` colormap according to frequency and are
kept consistent across the input, output, and Bode markers. The theoretical
transfer-function curves are gray.

The sequence generates

```text
outputs/convolucao_senoides_com_convolucao.mp4
outputs/comparacao_senoides.png
```

### Default render settings

The CLI defaults for the multi-sine workflow are

```text
start_time = -10 s
end_time = 10 s
dt = 0.01 s
frame_stride = 10
fps = 60
dpi = 60
```

With `dt=0.01 s` and `frame_stride=10`, consecutive animation states are
separated by `0.1 s` of simulated time.

### High-resolution multi-sine render

```powershell
python convolution_animation.py `
  --sine-sequence `
  --start-time -10 `
  --end-time 10 `
  --frame-stride 20 `
  --fps 30 `
  --dpi 300 `
  --output-dir outputs/sequence_final_30fps_dpi300
```

This configuration produces approximately 909 animation frames at about
`4200 x 3300` pixels and may require several hours. For normal review, use
`--dpi 60` or `--dpi 100`.

## Validation

Run the automated tests and compile checks with

```powershell
python -m pytest -q
python -m compileall convolution_animation.py inputs transfer_functions tests
```

Inspect a generated MP4 with

```powershell
ffprobe -v error -select_streams v:0 -count_frames `
  -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames,duration `
  -of default=noprint_wrappers=1 outputs/convolucao_animada.mp4
```

The most recent automated test run recorded `55 passed`.

## Adding an input signal

1. Create a module in `inputs/`, for example `inputs/my_signal.py`.
2. Implement the expected factory function:

```python
def input_function(
    time: FloatArray,
    dt: float,
    reference_frequency: float,
) -> FloatArray:
    ...
```

3. Register it in `inputs/registry.py`.
4. Add tests in `tests/test_convolution_animation.py`.
5. Document the signal definition and units.

## Adding a transfer function

1. Create a module in `transfer_functions/`.
2. Implement its impulse response.
3. Implement its reference-frequency criterion.
4. Register it in `transfer_functions/registry.py`.
5. Add numerical tests and document assumptions, units, and limitations.

## Limitations

- The analytical reference currently applies only to the unit-step response of
  `second_order_underdamped`.
- Other inputs use numerical convolution without an analytical overlay.
- The numerical impulse approximation depends on `dt`.
- High DPI, small `dt`, and small `frame_stride` values can make rendering take
  several hours.
- FFmpeg must be installed and accessible from the command line.

## License and contribution

Contributions, validation cases, and documentation improvements are welcome.
Open an issue or pull request in the public GitHub repository.
