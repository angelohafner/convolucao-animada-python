# Animated Convolution in Python Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and validate a Python program that generates a two-panel didactic MP4 of the convolution between a unit step and a second-order underdamped impulse response.

**Architecture:** Keep the small project in one importable functional module, `convolution_animation.py`, with immutable configuration and result dataclasses. Separate signal generation, numerical calculation, plotting, animation encoding, and orchestration into named functions so tests can exercise each responsibility without coupling to the command-line entry point.

**Tech Stack:** Python 3.11+, NumPy, Matplotlib, pytest, FFmpeg/ffprobe.

## Global Constraints

- Use Python 3.11 or newer.
- Use `dt = 0.01 s`, `t_start = -10 s`, and `t_end = 20 s` for the default case.
- Use `zeta = 0.2` and `wn = 2 rad/s` for the default underdamped system.
- Use H.264 (`libx264`), `yuv420p`, 25 fps, and a 1400 x 900 pixel figure for the MP4.
- Keep code identifiers, filenames, and code comments in English; visible plot text may be Portuguese.
- Do not use compound assignment operators in project code.
- Create `outputs/` automatically and never hard-code an absolute output path.
- Keep the analytical comparison restricted to the unit-step/second-order default case.
- Do not initialize Git or create commits unless the user explicitly requests it; this workspace is not currently a repository.

## File Map

- Create `convolution_animation.py`: configuration, data models, signals, numerical convolution, analytical solution, figures, MP4 generation, and CLI orchestration.
- Create `tests/test_convolution_animation.py`: unit and integration tests for calculations and generated artifacts.
- Create `requirements.txt`: bounded Python dependencies.
- Create `README.md`: setup, equations, execution, customization, and outputs.
- Create `PROJECT_CONTEXT.md`: durable engineering assumptions, validation results, and extension notes.
- Generate `outputs/convolucao_animada.mp4`: final H.264 animation.
- Generate `outputs/comparacao_numerica_analitica.png`: numerical-versus-analytical validation figure.

---

### Task 1: Configuration and Signal Definitions

**Files:**
- Create: `convolution_animation.py`
- Create: `tests/test_convolution_animation.py`

**Interfaces:**
- Produces: `AnimationConfig`, `build_time_axis(config)`, `input_function(time)`, and `impulse_function(time, damping_ratio, natural_frequency)`.
- Consumes: only NumPy and Python standard-library types.

- [ ] **Step 1: Write failing tests for configuration and signals**

Create `tests/test_convolution_animation.py` with:

```python
from __future__ import annotations

import numpy as np
import pytest

from convolution_animation import (
    AnimationConfig,
    build_time_axis,
    impulse_function,
    input_function,
)


def test_build_time_axis_includes_exact_endpoints() -> None:
    config = AnimationConfig(start_time=-1.0, end_time=1.0, dt=0.25)

    time = build_time_axis(config)

    np.testing.assert_allclose(time, np.linspace(-1.0, 1.0, 9))


def test_unit_step_is_causal_and_includes_origin() -> None:
    time = np.array([-1.0, -0.01, 0.0, 0.01, 1.0])

    signal = input_function(time)

    np.testing.assert_array_equal(signal, np.array([0.0, 0.0, 1.0, 1.0, 1.0]))


def test_impulse_response_is_causal() -> None:
    time = np.array([-1.0, -0.01, 0.0, 0.25, 1.0])

    response = impulse_function(time, damping_ratio=0.2, natural_frequency=2.0)

    np.testing.assert_array_equal(response[:3], np.zeros(3))
    assert response[3] > 0.0


def test_impulse_response_matches_formula() -> None:
    time = np.array([0.25, 0.75])
    damping_ratio = 0.2
    natural_frequency = 2.0
    damped_frequency = natural_frequency * np.sqrt(1.0 - damping_ratio**2)
    expected = (
        natural_frequency
        / np.sqrt(1.0 - damping_ratio**2)
        * np.exp(-damping_ratio * natural_frequency * time)
        * np.sin(damped_frequency * time)
    )

    response = impulse_function(time, damping_ratio, natural_frequency)

    np.testing.assert_allclose(response, expected)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("dt", 0.0),
        ("natural_frequency", 0.0),
        ("damping_ratio", -0.1),
        ("damping_ratio", 1.0),
        ("frame_stride", 0),
        ("fps", 0),
    ],
)
def test_invalid_configuration_is_rejected(field_name: str, value: float) -> None:
    values = {field_name: value}

    with pytest.raises(ValueError):
        AnimationConfig(**values)
```

- [ ] **Step 2: Run the tests and confirm the RED state**

Run:

```powershell
python -m pytest tests/test_convolution_animation.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'convolution_animation'`.

- [ ] **Step 3: Implement configuration and signal functions**

Create `convolution_animation.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
from numpy.typing import NDArray

matplotlib.use("Agg")

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class AnimationConfig:
    start_time: float = -10.0
    end_time: float = 20.0
    dt: float = 1e-2
    damping_ratio: float = 0.2
    natural_frequency: float = 2.0
    frame_stride: int = 20
    fps: int = 25
    figure_width: float = 14.0
    figure_height: float = 9.0
    dpi: int = 100
    output_dir: Path = Path("outputs")

    def __post_init__(self) -> None:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        if self.dt <= 0.0:
            raise ValueError("dt must be positive")
        if not 0.0 <= self.damping_ratio < 1.0:
            raise ValueError("damping_ratio must satisfy 0 <= zeta < 1")
        if self.natural_frequency <= 0.0:
            raise ValueError("natural_frequency must be positive")
        if self.frame_stride <= 0:
            raise ValueError("frame_stride must be positive")
        if self.fps <= 0:
            raise ValueError("fps must be positive")
        if self.dpi <= 0:
            raise ValueError("dpi must be positive")


def build_time_axis(config: AnimationConfig) -> FloatArray:
    sample_count = int(round((config.end_time - config.start_time) / config.dt)) + 1
    return np.linspace(config.start_time, config.end_time, sample_count, dtype=float)


def input_function(time: FloatArray) -> FloatArray:
    return (time >= 0.0).astype(float)


def impulse_function(
    time: FloatArray,
    damping_ratio: float = 0.2,
    natural_frequency: float = 2.0,
) -> FloatArray:
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
```

- [ ] **Step 4: Run Task 1 tests and confirm GREEN**

Run:

```powershell
python -m pytest tests/test_convolution_animation.py -q
```

Expected: all Task 1 tests pass.

- [ ] **Step 5: Review Task 1 changes**

Run:

```powershell
python -m compileall convolution_animation.py tests
```

Expected: both files compile successfully. No Git commit is made because the workspace is not a repository.

---

### Task 2: Numerical Convolution and Analytical Validation

**Files:**
- Modify: `convolution_animation.py`
- Modify: `tests/test_convolution_animation.py`

**Interfaces:**
- Consumes: `AnimationConfig`, `build_time_axis`, `input_function`, and `impulse_function`.
- Produces: `ConvolutionResult`, `analytical_step_response(...)`, `compute_convolution(...)`, and `calculate_default_case(config)`.

- [ ] **Step 1: Add failing numerical tests**

Append these imports and tests to `tests/test_convolution_animation.py`:

```python
from convolution_animation import (
    analytical_step_response,
    calculate_default_case,
    compute_convolution,
)


def test_convolution_of_unit_samples_scales_by_dt() -> None:
    time = np.array([0.0, 0.5, 1.0])
    x_signal = np.array([1.0, 1.0, 1.0])
    h_signal = np.array([1.0, 0.0, 0.0])

    result = compute_convolution(time, x_signal, h_signal, dt=0.5)

    np.testing.assert_allclose(result, np.array([0.5, 0.5, 0.5]))


def test_analytical_step_response_is_zero_before_origin() -> None:
    time = np.array([-1.0, -0.1, 0.0, 0.1])

    response = analytical_step_response(time, 0.2, 2.0)

    np.testing.assert_array_equal(response[:3], np.zeros(3))
    assert response[3] > 0.0


def test_default_numerical_response_matches_analytical_response() -> None:
    result = calculate_default_case(AnimationConfig())
    causal = result.time >= 0.0

    maximum_error = np.max(np.abs(result.output[causal] - result.analytical[causal]))

    assert maximum_error < 0.011
    np.testing.assert_allclose(result.output[result.time < 0.0], 0.0, atol=1e-12)
```

- [ ] **Step 2: Run the new tests and confirm the RED state**

Run:

```powershell
python -m pytest tests/test_convolution_animation.py::test_convolution_of_unit_samples_scales_by_dt tests/test_convolution_animation.py::test_analytical_step_response_is_zero_before_origin tests/test_convolution_animation.py::test_default_numerical_response_matches_analytical_response -q
```

Expected: collection fails because the three calculation interfaces do not exist.

- [ ] **Step 3: Implement calculation and result interfaces**

Add the following after `AnimationConfig` and the signal functions in `convolution_animation.py`:

```python
@dataclass(frozen=True)
class ConvolutionResult:
    time: FloatArray
    input_signal: FloatArray
    impulse_response: FloatArray
    output: FloatArray
    analytical: FloatArray
    maximum_absolute_error: float
    root_mean_square_error: float


def analytical_step_response(
    time: FloatArray,
    damping_ratio: float = 0.2,
    natural_frequency: float = 2.0,
) -> FloatArray:
    damped_frequency = natural_frequency * np.sqrt(1.0 - damping_ratio**2)
    response = np.zeros_like(time, dtype=float)
    causal = time > 0.0
    causal_time = time[causal]
    response[causal] = 1.0 - np.exp(
        -damping_ratio * natural_frequency * causal_time
    ) * (
        np.cos(damped_frequency * causal_time)
        + damping_ratio
        / np.sqrt(1.0 - damping_ratio**2)
        * np.sin(damped_frequency * causal_time)
    )
    return response


def compute_convolution(
    time: FloatArray,
    input_signal: FloatArray,
    impulse_response: FloatArray,
    dt: float,
) -> FloatArray:
    if not (time.size == input_signal.size == impulse_response.size):
        raise ValueError("time and signal arrays must have the same length")
    full_output = np.convolve(input_signal, impulse_response, mode="full") * dt
    full_time = 2.0 * time[0] + np.arange(full_output.size, dtype=float) * dt
    return np.interp(time, full_time, full_output, left=0.0, right=0.0)


def calculate_default_case(config: AnimationConfig) -> ConvolutionResult:
    time = build_time_axis(config)
    input_signal = input_function(time)
    impulse_response = impulse_function(
        time,
        config.damping_ratio,
        config.natural_frequency,
    )
    output = compute_convolution(time, input_signal, impulse_response, config.dt)
    analytical = analytical_step_response(
        time,
        config.damping_ratio,
        config.natural_frequency,
    )
    error = output - analytical
    return ConvolutionResult(
        time=time,
        input_signal=input_signal,
        impulse_response=impulse_response,
        output=output,
        analytical=analytical,
        maximum_absolute_error=float(np.max(np.abs(error))),
        root_mean_square_error=float(np.sqrt(np.mean(error**2))),
    )
```

- [ ] **Step 4: Run all tests and confirm GREEN**

Run:

```powershell
python -m pytest -q
```

Expected: all Task 1 and Task 2 tests pass and maximum causal error remains below `0.011`.

- [ ] **Step 5: Inspect validation metrics**

Run:

```powershell
python -c "from convolution_animation import AnimationConfig, calculate_default_case; r = calculate_default_case(AnimationConfig()); print(f'max={r.maximum_absolute_error:.8f}, rms={r.root_mean_square_error:.8f}')"
```

Expected: finite maximum and RMS errors, with maximum error below `0.011`. No Git commit is made.

---

### Task 3: Frame Selection and Static Comparison Figure

**Files:**
- Modify: `convolution_animation.py`
- Modify: `tests/test_convolution_animation.py`

**Interfaces:**
- Consumes: `ConvolutionResult` and `AnimationConfig`.
- Produces: `select_frame_indices(sample_count, stride)` and `save_comparison_figure(result, output_path)`.

- [ ] **Step 1: Add failing tests for frame selection and PNG output**

Append to `tests/test_convolution_animation.py`:

```python
from pathlib import Path

from convolution_animation import save_comparison_figure, select_frame_indices


def test_frame_indices_include_first_and_last_sample() -> None:
    indices = select_frame_indices(sample_count=101, stride=20)

    np.testing.assert_array_equal(indices, np.array([0, 19, 39, 59, 79, 99, 100]))
    assert np.all(np.diff(indices) > 0)


def test_comparison_figure_is_written(tmp_path: Path) -> None:
    result = calculate_default_case(
        AnimationConfig(start_time=-1.0, end_time=2.0, dt=0.02)
    )
    output_path = tmp_path / "comparison.png"

    returned_path = save_comparison_figure(result, output_path)

    assert returned_path == output_path
    assert output_path.is_file()
    assert output_path.stat().st_size > 1_000
```

- [ ] **Step 2: Run the new tests and confirm the RED state**

Run:

```powershell
python -m pytest tests/test_convolution_animation.py::test_frame_indices_include_first_and_last_sample tests/test_convolution_animation.py::test_comparison_figure_is_written -q
```

Expected: collection fails because `select_frame_indices` and `save_comparison_figure` do not exist.

- [ ] **Step 3: Implement frame selection and the static figure**

Add the plotting import after `matplotlib.use("Agg")`:

```python
import matplotlib.pyplot as plt
```

Add these functions after the calculation functions:

```python
def select_frame_indices(sample_count: int, stride: int) -> NDArray[np.int_]:
    if sample_count <= 0:
        raise ValueError("sample_count must be positive")
    if stride <= 0:
        raise ValueError("stride must be positive")
    indices = np.concatenate(
        (
            np.array([0], dtype=int),
            np.arange(stride - 1, sample_count, stride, dtype=int),
            np.array([sample_count - 1], dtype=int),
        )
    )
    return np.unique(indices)


def save_comparison_figure(
    result: ConvolutionResult,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(14.0, 5.0), constrained_layout=True)
    axis.plot(
        result.time,
        result.output,
        "--",
        linewidth=1.5,
        label="Convolucao numerica",
    )
    axis.plot(
        result.time,
        result.analytical,
        linewidth=1.5,
        label="Resposta analitica",
    )
    axis.set_xlabel(r"$t$ (s)")
    axis.set_ylabel("Amplitude")
    axis.set_title("Comparacao entre convolucao numerica e resposta analitica")
    axis.grid(True, alpha=0.3)
    axis.legend(loc="best")
    figure.savefig(output_path, dpi=150)
    plt.close(figure)
    return output_path
```

- [ ] **Step 4: Run all tests and confirm GREEN**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass and the temporary PNG test produces a non-empty image.

- [ ] **Step 5: Review static plotting output**

Run:

```powershell
python -c "from pathlib import Path; from convolution_animation import AnimationConfig, calculate_default_case, save_comparison_figure; save_comparison_figure(calculate_default_case(AnimationConfig()), Path('outputs/comparacao_numerica_analitica.png'))"
```

Expected: `outputs/comparacao_numerica_analitica.png` exists and contains labeled numerical and analytical curves. No Git commit is made.

---

### Task 4: Two-Panel MP4 Animation and Artifact Orchestration

**Files:**
- Modify: `convolution_animation.py`
- Modify: `tests/test_convolution_animation.py`

**Interfaces:**
- Consumes: `AnimationConfig`, `ConvolutionResult`, `impulse_function`, `select_frame_indices`, and `save_comparison_figure`.
- Produces: `create_animation(result, config, output_path)`, `generate_outputs(config)`, and `main()`.

- [ ] **Step 1: Add a failing real-FFmpeg integration test**

Append these imports and test to `tests/test_convolution_animation.py`:

```python
import matplotlib.animation as mpl_animation

from convolution_animation import create_animation, generate_outputs


@pytest.mark.skipif(
    not mpl_animation.writers.is_available("ffmpeg"),
    reason="FFmpeg is required for MP4 integration validation",
)
def test_small_animation_and_comparison_are_generated(tmp_path: Path) -> None:
    config = AnimationConfig(
        start_time=-0.2,
        end_time=0.4,
        dt=0.05,
        frame_stride=2,
        fps=5,
        figure_width=8.0,
        figure_height=5.0,
        dpi=80,
        output_dir=tmp_path,
    )

    mp4_path, png_path, result = generate_outputs(config)

    assert mp4_path == tmp_path / "convolucao_animada.mp4"
    assert png_path == tmp_path / "comparacao_numerica_analitica.png"
    assert mp4_path.is_file()
    assert mp4_path.stat().st_size > 1_000
    assert png_path.is_file()
    assert result.time.size == 13
```

- [ ] **Step 2: Run the integration test and confirm the RED state**

Run:

```powershell
python -m pytest tests/test_convolution_animation.py::test_small_animation_and_comparison_are_generated -q
```

Expected: collection fails because `create_animation` and `generate_outputs` do not exist.

- [ ] **Step 3: Implement the MP4 animation and orchestration**

Add this import beside `matplotlib.pyplot`:

```python
from matplotlib.animation import FFMpegWriter, FuncAnimation, writers
```

Add these functions near the end of `convolution_animation.py`:

```python
def _axis_limits(*arrays: FloatArray) -> tuple[float, float]:
    values = np.concatenate(arrays)
    minimum = float(np.min(values))
    maximum = float(np.max(values))
    margin = 0.1 * (maximum - minimum)
    if margin == 0.0:
        margin = 0.1
    return minimum - margin, maximum + margin


def create_animation(
    result: ConvolutionResult,
    config: AnimationConfig,
    output_path: Path,
) -> Path:
    if not writers.is_available("ffmpeg"):
        raise RuntimeError(
            "FFmpeg is not available. Install FFmpeg and add ffmpeg.exe to PATH."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame_indices = select_frame_indices(result.time.size, config.frame_stride)
    figure, (overlap_axis, output_axis) = plt.subplots(
        2,
        1,
        figsize=(config.figure_width, config.figure_height),
        constrained_layout=True,
    )

    input_line, = overlap_axis.plot(
        result.time,
        result.input_signal,
        linewidth=1.7,
        label=r"$x(\tau)$",
    )
    shifted_line, = overlap_axis.plot(
        result.time,
        np.zeros_like(result.time),
        linewidth=1.7,
        label=r"$h(t-\tau)$",
    )
    product_line, = overlap_axis.plot(
        result.time,
        np.zeros_like(result.time),
        linewidth=1.4,
        label=r"$x(\tau)h(t-\tau)$",
    )
    status_text = overlap_axis.text(
        0.02,
        0.95,
        "",
        transform=overlap_axis.transAxes,
        va="top",
    )
    overlap_axis.set_xlim(config.start_time, config.end_time)
    overlap_axis.set_ylim(
        *_axis_limits(result.input_signal, result.impulse_response, result.output)
    )
    overlap_axis.set_xlabel(r"$\tau$ (s)")
    overlap_axis.set_ylabel("Amplitude")
    overlap_axis.set_title(
        r"Integrando $x(\tau)h(t-\tau)$ para obter $y(t)$"
    )
    overlap_axis.grid(True, alpha=0.3)
    overlap_axis.legend(loc="upper right")

    output_axis.plot(
        result.time,
        result.output,
        color="0.75",
        linewidth=1.2,
        label="Resposta numerica completa",
    )
    output_axis.plot(
        result.time,
        result.analytical,
        "--",
        linewidth=1.3,
        label="Resposta analitica",
    )
    progress_line, = output_axis.plot(
        [],
        [],
        linewidth=2.0,
        label=r"$y(t)$ acumulada",
    )
    current_point, = output_axis.plot([], [], "o", markersize=6, label="Instante atual")
    output_axis.set_xlim(config.start_time, config.end_time)
    output_axis.set_ylim(*_axis_limits(result.output, result.analytical))
    output_axis.set_xlabel(r"$t$ (s)")
    output_axis.set_ylabel("Amplitude")
    output_axis.set_title(
        r"$y(t)=\int_{-\infty}^{\infty}x(\tau)h(t-\tau)\,d\tau$"
    )
    output_axis.grid(True, alpha=0.3)
    output_axis.legend(loc="lower right")

    product_fill = None

    def update(frame_index: int) -> tuple[object, ...]:
        nonlocal product_fill
        current_time = result.time[frame_index]
        shifted_response = impulse_function(
            current_time - result.time,
            config.damping_ratio,
            config.natural_frequency,
        )
        product = result.input_signal * shifted_response
        shifted_line.set_ydata(shifted_response)
        product_line.set_ydata(product)
        if product_fill is not None:
            product_fill.remove()
        product_fill = overlap_axis.fill_between(
            result.time,
            0.0,
            product,
            alpha=0.25,
        )
        progress_line.set_data(
            result.time[: frame_index + 1],
            result.output[: frame_index + 1],
        )
        current_point.set_data(
            [current_time],
            [result.output[frame_index]],
        )
        status_text.set_text(
            f"t = {current_time:.2f} s    y(t) = {result.output[frame_index]:.4f}"
        )
        return (
            input_line,
            shifted_line,
            product_line,
            progress_line,
            current_point,
            status_text,
            product_fill,
        )

    animation = FuncAnimation(
        figure,
        update,
        frames=frame_indices,
        interval=1000.0 / config.fps,
        blit=False,
        repeat=False,
    )
    writer = FFMpegWriter(
        fps=config.fps,
        codec="libx264",
        extra_args=["-pix_fmt", "yuv420p"],
    )
    animation.save(output_path, writer=writer, dpi=config.dpi)
    plt.close(figure)
    return output_path


def generate_outputs(
    config: AnimationConfig,
) -> tuple[Path, Path, ConvolutionResult]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    result = calculate_default_case(config)
    png_path = save_comparison_figure(
        result,
        config.output_dir / "comparacao_numerica_analitica.png",
    )
    mp4_path = create_animation(
        result,
        config,
        config.output_dir / "convolucao_animada.mp4",
    )
    return mp4_path, png_path, result


def main() -> None:
    mp4_path, png_path, result = generate_outputs(AnimationConfig())
    print(f"MP4: {mp4_path.resolve()}")
    print(f"Comparison: {png_path.resolve()}")
    print(f"Maximum absolute error: {result.maximum_absolute_error:.8f}")
    print(f"Root mean square error: {result.root_mean_square_error:.8f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all tests and confirm GREEN**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass, including creation of a short real H.264 MP4 when FFmpeg is available.

- [ ] **Step 5: Generate the full requested outputs**

Run:

```powershell
python convolution_animation.py
```

Expected: the command reports both output paths and finite error metrics, and creates the final MP4 and PNG. No Git commit is made.

---

### Task 5: Dependencies, Documentation, and Final Validation

**Files:**
- Create: `requirements.txt`
- Create: `README.md`
- Create: `PROJECT_CONTEXT.md`
- Verify: `outputs/convolucao_animada.mp4`
- Verify: `outputs/comparacao_numerica_analitica.png`

**Interfaces:**
- Consumes: all commands, files, equations, and measured outputs produced by Tasks 1-4.
- Produces: reproducible setup documentation and recorded validation evidence.

- [ ] **Step 1: Add dependency bounds**

Create `requirements.txt`:

```text
numpy>=2.0,<3.0
matplotlib>=3.9,<4.0
pytest>=8.0,<10.0
```

- [ ] **Step 2: Write the user README**

Create `README.md` containing these exact sections and populate measured values after the full run:

```markdown
# Animated convolution in Python

## Objective
## Mathematical model
## Project structure
## Requirements
## Installation on Windows
## Generate the MP4
## Outputs
## Numerical validation
## Customize the input signal
## Customize the impulse response
## Limitations
```

Document these Windows commands:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python convolution_animation.py
```

State explicitly that FFmpeg must be on `PATH`, the default MP4 is 25 fps, and code customizations are made in `input_function` and `impulse_function`.

- [ ] **Step 3: Write durable project context**

Create `PROJECT_CONTEXT.md` with:

```markdown
# Project context

## Engineering objective
## Active default case
## Numerical method
## Animation interpretation
## Generated artifacts
## Validation commands
## Validation results
## Assumptions and limitations
## Extension notes
```

Record the actual Python, NumPy, Matplotlib, pytest, FFmpeg, test, compilation, error-metric, and ffprobe results from the current environment. Every reported value must come from a command executed during validation.

- [ ] **Step 4: Run the complete verification suite**

Run:

```powershell
python -m pytest -q
python -m compileall convolution_animation.py tests
python convolution_animation.py
ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=codec_name,width,height,r_frame_rate,nb_read_frames,duration -of default=noprint_wrappers=1 outputs/convolucao_animada.mp4
```

Expected:

- every pytest test passes;
- compilation succeeds;
- the generator exits with code zero;
- ffprobe reports `codec_name=h264`, `width=1400`, `height=900`, `r_frame_rate=25/1`, and a positive duration/frame count.

- [ ] **Step 5: Inspect the generated visuals**

Extract three representative frames:

```powershell
New-Item -ItemType Directory -Force outputs\validation_frames | Out-Null
ffmpeg -y -ss 0.5 -i outputs\convolucao_animada.mp4 -frames:v 1 outputs\validation_frames\frame_start.png
ffmpeg -y -ss 3.0 -i outputs\convolucao_animada.mp4 -frames:v 1 outputs\validation_frames\frame_middle.png
ffmpeg -y -ss 5.5 -i outputs\convolucao_animada.mp4 -frames:v 1 outputs\validation_frames\frame_end.png
```

Visually confirm that axes, legends, the moving response, signed product fill, progressive output, current point, and analytical comparison are readable without clipping. Inspect `outputs/comparacao_numerica_analitica.png` for curve agreement.

- [ ] **Step 6: Update validation evidence and run a final clean check**

Replace the provisional validation text in `README.md` and `PROJECT_CONTEXT.md` with the measured values, then run:

```powershell
$redFlags = @(('T' + 'BD'), ('T' + 'ODO'), ('FIX' + 'ME'), ('place' + 'holder'), ('not yet ' + 'measured'))
Select-String -Path README.md,PROJECT_CONTEXT.md,docs\superpowers\*.md -Pattern $redFlags -CaseSensitive
python -m pytest -q
```

Expected: no red-flag matches and all tests pass. No Git commit or push is performed.
