from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
from numpy.typing import NDArray

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation, writers

from inputs import get_input_signal
from inputs.unit_step import input_function
from transfer_functions import get_transfer_function_definition
from transfer_functions.second_order_underdamped import impulse_function

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class AnimationConfig:
    start_time: float = -10.0
    end_time: float = 20.0
    dt: float = 1e-2
    damping_ratio: float = 0.2
    natural_frequency: float = 2.0
    input_name: str = "unit_step"
    transfer_function_name: str = "second_order_underdamped"
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


@dataclass(frozen=True)
class ConvolutionResult:
    time: FloatArray
    input_name: str
    transfer_function_name: str
    reference_frequency: float
    reference_frequency_source: str
    has_resonance: bool
    has_analytical_reference: bool
    input_signal: FloatArray
    impulse_response: FloatArray
    output: FloatArray
    analytical: FloatArray
    maximum_absolute_error: float
    root_mean_square_error: float


def build_time_axis(config: AnimationConfig) -> FloatArray:
    sample_count = int(round((config.end_time - config.start_time) / config.dt)) + 1
    return np.linspace(config.start_time, config.end_time, sample_count, dtype=float)


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
    transfer_definition = get_transfer_function_definition(config.transfer_function_name)
    frequency_reference = transfer_definition.reference_frequency(
        config.damping_ratio,
        config.natural_frequency,
    )
    input_signal = get_input_signal(
        config.input_name,
        time,
        config.dt,
        frequency_reference.value,
    )
    impulse_response = transfer_definition.impulse_function(
        time,
        config.damping_ratio,
        config.natural_frequency,
    )
    output = compute_convolution(time, input_signal, impulse_response, config.dt)
    has_analytical_reference = (
        config.input_name == "unit_step"
        and config.transfer_function_name == "second_order_underdamped"
    )
    if has_analytical_reference:
        analytical = analytical_step_response(
            time,
            config.damping_ratio,
            config.natural_frequency,
        )
        error = output - analytical
        maximum_absolute_error = float(np.max(np.abs(error)))
        root_mean_square_error = float(np.sqrt(np.mean(error**2)))
    else:
        analytical = np.full_like(time, np.nan, dtype=float)
        maximum_absolute_error = float("nan")
        root_mean_square_error = float("nan")
    return ConvolutionResult(
        time=time,
        input_name=config.input_name,
        transfer_function_name=config.transfer_function_name,
        reference_frequency=frequency_reference.value,
        reference_frequency_source=frequency_reference.source,
        has_resonance=frequency_reference.has_resonance,
        has_analytical_reference=has_analytical_reference,
        input_signal=input_signal,
        impulse_response=impulse_response,
        output=output,
        analytical=analytical,
        maximum_absolute_error=maximum_absolute_error,
        root_mean_square_error=root_mean_square_error,
    )


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
        label="Convolução numérica",
    )
    if result.has_analytical_reference:
        axis.plot(
            result.time,
            result.analytical,
            linewidth=1.5,
            label="Resposta analítica",
        )
    axis.set_xlabel(r"$t$ (s)")
    axis.set_ylabel("Amplitude")
    axis.set_title("Comparação entre convolução numérica e resposta analítica")
    axis.grid(True, alpha=0.3)
    axis.legend(loc="best")
    figure.savefig(output_path, dpi=150)
    plt.close(figure)
    return output_path


def _axis_limits(*arrays: FloatArray) -> tuple[float, float]:
    values = np.concatenate(arrays)
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return -1.0, 1.0
    minimum = float(np.min(finite_values))
    maximum = float(np.max(finite_values))
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
    transfer_definition = get_transfer_function_definition(config.transfer_function_name)
    frame_indices = select_frame_indices(result.time.size, config.frame_stride)
    figure, (overlap_axis, output_axis) = plt.subplots(
        2,
        1,
        figsize=(config.figure_width, config.figure_height),
        constrained_layout=True,
    )

    input_color = "#0072B2"
    shifted_color = "#D55E00"
    product_color = "#009E73"

    input_line, = overlap_axis.plot(
        result.time,
        result.input_signal,
        color=input_color,
        linewidth=1.7,
        label=r"$x(\tau)$",
    )
    shifted_line, = overlap_axis.plot(
        result.time,
        np.zeros_like(result.time),
        color=shifted_color,
        linewidth=1.7,
        label=r"$h(t-\tau)$",
    )
    product_line, = overlap_axis.plot(
        result.time,
        np.zeros_like(result.time),
        color=product_color,
        linewidth=1.4,
        label=r"$x(\tau)h(t-\tau)$",
    )
    status_text = overlap_axis.text(
        0.02,
        0.95,
        "",
        transform=overlap_axis.transAxes,
        verticalalignment="top",
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
        label="Resposta numérica completa",
    )
    if result.has_analytical_reference:
        output_axis.plot(
            result.time,
            result.analytical,
            color=shifted_color,
            linestyle="--",
            linewidth=1.3,
            label="Resposta analítica",
        )
    progress_line, = output_axis.plot(
        [],
        [],
        color=input_color,
        linewidth=2.0,
        label=r"$y(t)$ acumulada",
    )
    current_point, = output_axis.plot(
        [],
        [],
        "o",
        color=product_color,
        markersize=6,
        label="Instante atual",
    )
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
        shifted_response = transfer_definition.impulse_function(
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
            color=product_color,
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


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an animated MP4 of a convolution.",
    )
    parser.add_argument("--input-name", default="unit_step")
    parser.add_argument("--transfer-function-name", default="second_order_underdamped")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    config = AnimationConfig(
        input_name=arguments.input_name,
        transfer_function_name=arguments.transfer_function_name,
    )
    mp4_path, png_path, result = generate_outputs(config)
    print(f"MP4: {mp4_path.resolve()}")
    print(f"Comparison: {png_path.resolve()}")
    print(f"Input: {result.input_name}")
    print(f"Transfer function: {result.transfer_function_name}")
    print(f"Reference frequency: {result.reference_frequency:.8f} rad/s")
    print(f"Reference frequency source: {result.reference_frequency_source}")
    if result.has_analytical_reference:
        print(f"Maximum absolute error: {result.maximum_absolute_error:.8f}")
        print(f"Root mean square error: {result.root_mean_square_error:.8f}")
    else:
        print("Analytical reference: not available for this input/system combination")


if __name__ == "__main__":
    main()
