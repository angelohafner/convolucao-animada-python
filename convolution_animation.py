from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from pathlib import Path

import matplotlib
import numpy as np
from numpy.typing import NDArray

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation, writers

from inputs import get_input_signal
from inputs.sine_common import sine_input
from inputs.unit_step import input_function
from transfer_functions import get_transfer_function_definition
from transfer_functions.second_order_underdamped import impulse_function

FloatArray = NDArray[np.float64]

BATCH_INPUT_NAMES = (
    "unit_impulse",
    "unit_step",
    "unit_ramp",
    "sine_0_7_resonance",
    "sine_0_8_resonance",
    "sine_0_9_resonance",
    "sine_1_0_resonance",
    "sine_1_1_resonance",
    "sine_1_2_resonance",
    "sine_1_3_resonance",
)
SINE_INPUT_NAMES = (
    "sine_0_7_resonance",
    "sine_0_8_resonance",
    "sine_0_9_resonance",
    "sine_1_0_resonance",
    "sine_1_1_resonance",
    "sine_1_2_resonance",
    "sine_1_3_resonance",
)
RESONANCE_SINE_INPUT_NAME = "sine_1_0_resonance"
DEFAULT_SINE_MULTIPLIERS = (0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8)


@dataclass(frozen=True)
class AnimationConfig:
    start_time: float = -10.0
    end_time: float = 20.0
    dt: float = 1e-2
    damping_ratio: float = 0.1
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


@dataclass(frozen=True)
class InputPlotRepresentation:
    display_signal: FloatArray
    show_unit_impulse_arrow: bool
    arrow_x: float = 0.0
    arrow_y_start: float = 0.0
    arrow_y_end: float = 1.0


@dataclass(frozen=True)
class PlotScale:
    overlap_y_limits: tuple[float, float]
    output_y_limits: tuple[float, float]


@dataclass(frozen=True)
class GeneratedCase:
    input_name: str
    mp4_path: Path
    png_path: Path
    result: ConvolutionResult


@dataclass(frozen=True)
class SineCase:
    multiplier: float
    frequency: float
    input_name: str
    result: ConvolutionResult


@dataclass(frozen=True)
class SineSequenceResult:
    multipliers: tuple[float, ...]
    cases: tuple[SineCase, ...]


def calculate_bode_response(
    angular_frequencies: FloatArray,
    damping_ratio: float,
    natural_frequency: float,
) -> tuple[FloatArray, FloatArray]:
    if np.any(~np.isfinite(angular_frequencies)) or np.any(angular_frequencies <= 0.0):
        raise ValueError("angular_frequencies must be finite and positive")
    if natural_frequency <= 0.0:
        raise ValueError("natural_frequency must be positive")
    s = 1j * angular_frequencies
    transfer = natural_frequency**2 / (
        s**2 + 2.0 * damping_ratio * natural_frequency * s + natural_frequency**2
    )
    magnitude_db = 20.0 * np.log10(np.abs(transfer))
    phase_deg = np.unwrap(np.angle(transfer)) * 180.0 / np.pi
    return magnitude_db, phase_deg


def build_frequency_colors(multipliers: tuple[float, ...]) -> NDArray[np.float64]:
    if not multipliers:
        raise ValueError("multipliers must not be empty")
    normalized = np.asarray(multipliers, dtype=float)
    if np.any(~np.isfinite(normalized)):
        raise ValueError("multipliers must be finite")
    minimum = float(np.min(normalized))
    maximum = float(np.max(normalized))
    if maximum == minimum:
        positions = np.full(normalized.shape, 0.5, dtype=float)
    else:
        positions = (normalized - minimum) / (maximum - minimum)
    return plt.get_cmap("jet")(positions)


def build_time_axis(config: AnimationConfig) -> FloatArray:
    sample_count = int(round((config.end_time - config.start_time) / config.dt)) + 1
    return np.linspace(config.start_time, config.end_time, sample_count, dtype=float)


def analytical_step_response(
    time: FloatArray,
    damping_ratio: float = 0.1,
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


def calculate_sine_sequence(
    config: AnimationConfig,
    multipliers: tuple[float, ...],
) -> SineSequenceResult:
    if not multipliers:
        raise ValueError("multipliers must not be empty")
    if any(not np.isfinite(value) or value <= 0.0 for value in multipliers):
        raise ValueError("multipliers must be finite and positive")

    time = build_time_axis(config)
    transfer_definition = get_transfer_function_definition(config.transfer_function_name)
    frequency_reference = transfer_definition.reference_frequency(
        config.damping_ratio,
        config.natural_frequency,
    )
    impulse_response = transfer_definition.impulse_function(
        time,
        config.damping_ratio,
        config.natural_frequency,
    )
    cases: list[SineCase] = []
    for multiplier in multipliers:
        input_signal = sine_input(time, multiplier, frequency_reference.value)
        output = compute_convolution(time, input_signal, impulse_response, config.dt)
        input_name = f"sine_{multiplier:.1f}_resonance".replace(".", "_")
        result = ConvolutionResult(
            time=time,
            input_name=input_name,
            transfer_function_name=config.transfer_function_name,
            reference_frequency=frequency_reference.value,
            reference_frequency_source=frequency_reference.source,
            has_resonance=frequency_reference.has_resonance,
            has_analytical_reference=False,
            input_signal=input_signal,
            impulse_response=impulse_response,
            output=output,
            analytical=np.full_like(time, np.nan, dtype=float),
            maximum_absolute_error=float("nan"),
            root_mean_square_error=float("nan"),
        )
        cases.append(
            SineCase(
                multiplier=multiplier,
                frequency=multiplier * frequency_reference.value,
                input_name=input_name,
                result=result,
            )
        )
    return SineSequenceResult(tuple(multipliers), tuple(cases))


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


def build_input_plot_representation(result: ConvolutionResult) -> InputPlotRepresentation:
    if result.input_name == "unit_impulse":
        return InputPlotRepresentation(
            display_signal=np.zeros_like(result.input_signal, dtype=float),
            show_unit_impulse_arrow=True,
        )
    return InputPlotRepresentation(
        display_signal=result.input_signal,
        show_unit_impulse_arrow=False,
    )


def build_plot_scale(result: ConvolutionResult) -> PlotScale:
    input_representation = build_input_plot_representation(result)
    input_limit_signal = input_representation.display_signal
    if input_representation.show_unit_impulse_arrow:
        input_limit_signal = np.concatenate(
            (
                input_limit_signal,
                np.array(
                    [
                        input_representation.arrow_y_start,
                        input_representation.arrow_y_end,
                    ],
                    dtype=float,
                ),
            )
        )
    return PlotScale(
        overlap_y_limits=_axis_limits(
            input_limit_signal,
            result.impulse_response,
            result.output,
        ),
        output_y_limits=_axis_limits(result.output, result.analytical),
    )


def build_shared_sine_plot_scale(config: AnimationConfig) -> PlotScale:
    resonance_config = replace(config, input_name=RESONANCE_SINE_INPUT_NAME)
    resonance_result = calculate_default_case(resonance_config)
    return build_plot_scale(resonance_result)


def save_comparison_figure(
    result: ConvolutionResult,
    output_path: Path,
    plot_scale: PlotScale | None = None,
) -> Path:
    active_plot_scale = plot_scale
    if active_plot_scale is None:
        active_plot_scale = build_plot_scale(result)
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
    axis.set_ylim(*active_plot_scale.output_y_limits)
    axis.grid(True, alpha=0.3)
    axis.legend(loc="best")
    figure.savefig(output_path, dpi=150)
    plt.close(figure)
    return output_path


def save_sine_sequence_figure(
    sequence: SineSequenceResult,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(14.0, 5.0), constrained_layout=True)
    colors = build_frequency_colors(sequence.multipliers)
    outputs = [case.result.output for case in sequence.cases]
    axis.set_xlim(sequence.cases[0].result.time[0], sequence.cases[0].result.time[-1])
    axis.set_ylim(*_axis_limits(*outputs))
    for color, case in zip(colors, sequence.cases):
        axis.plot(
            case.result.time,
            case.result.output,
            color=color,
            linewidth=1.7,
            label=f"{case.multiplier:.2f} omega_ref ({case.frequency:.3f} rad/s)",
        )
    axis.set_xlabel(r"$t$ (s)")
    axis.set_ylabel("Amplitude")
    axis.set_title("Respostas no dominio do tempo para varias frequencias")
    axis.grid(True, alpha=0.3)
    axis.legend(loc="upper right")
    figure.savefig(output_path, dpi=150)
    plt.close(figure)
    return output_path


def create_sine_sequence_animation(
    sequence: SineSequenceResult,
    config: AnimationConfig,
    output_path: Path,
) -> Path:
    if not writers.is_available("ffmpeg"):
        raise RuntimeError("FFmpeg is not available. Install FFmpeg and add ffmpeg.exe to PATH.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    time = sequence.cases[0].result.time
    frame_indices = select_frame_indices(time.size, config.frame_stride)
    colors = build_frequency_colors(sequence.multipliers)
    figure, (input_axis, output_axis, bode_axis) = plt.subplots(
        3, 1, figsize=(config.figure_width, config.figure_height + 2.0), constrained_layout=True
    )
    input_line, = input_axis.plot([], [], color=colors[0], linewidth=1.7, label=r"$x(\tau)$")
    shifted_line, = input_axis.plot([], [], color="#D55E00", linewidth=1.5, label=r"$h(t-\tau)$")
    product_line, = input_axis.plot([], [], color="#009E73", linewidth=1.2, label=r"$x(\tau)h(t-\tau)$")
    output_lines = [
        output_axis.plot([], [], color=color, linewidth=2.0, label=f"{case.multiplier:.2f} omega_ref")[0]
        for color, case in zip(colors, sequence.cases)
    ]
    input_axis.set_xlim(time[0], time[-1])
    input_axis.set_ylim(*_axis_limits(*(case.result.input_signal for case in sequence.cases)))
    input_axis.set_xlabel(r"$t$ (s)")
    input_axis.set_ylabel("Amplitude")
    input_axis.set_title("Construção da convolução da senoide atual")
    input_axis.grid(True, alpha=0.3)
    input_axis.legend(loc="upper right")
    output_axis.set_xlim(time[0], time[-1])
    output_axis.set_ylim(*_axis_limits(*(case.result.output for case in sequence.cases)))
    output_axis.set_xlabel(r"$t$ (s)")
    output_axis.set_ylabel("Amplitude")
    output_axis.set_title("Respostas sobrepostas no dominio do tempo")
    output_axis.grid(True, alpha=0.3)
    output_axis.legend(loc="upper right")
    reference_frequency = sequence.cases[0].result.reference_frequency
    bode_frequencies = np.logspace(
        np.log10(max(reference_frequency * 0.1, 0.01)),
        np.log10(reference_frequency * 3.0),
        300,
    )
    bode_magnitude, bode_phase = calculate_bode_response(
        bode_frequencies,
        config.damping_ratio,
        config.natural_frequency,
    )
    bode_axis_phase = bode_axis.twinx()
    magnitude_line, = bode_axis.semilogx(bode_frequencies, bode_magnitude, color="gray", linewidth=1.5, label="Magnitude teorica")
    phase_line, = bode_axis_phase.semilogx(bode_frequencies, bode_phase, color="gray", linestyle="--", linewidth=1.3, label="Fase teorica")
    bode_axis.set_xlabel(r"$\omega$ (rad/s)")
    bode_axis.set_ylabel("Magnitude (dB)")
    bode_axis_phase.set_ylabel("Fase (graus)")
    bode_axis.set_title("Diagrama de Bode e pontos das senoides")
    bode_axis.grid(True, which="both", alpha=0.3)
    bode_axis.set_xlim(bode_frequencies[0], bode_frequencies[-1])
    bode_magnitude_points = bode_axis.scatter([], [], s=96, label="Pontos simulados", zorder=4)
    bode_phase_points = bode_axis_phase.scatter([], [], s=96, zorder=4)
    bode_axis.legend(
        handles=[magnitude_line, phase_line, bode_magnitude_points],
        loc="upper right",
    )
    status_text = output_axis.text(0.02, 0.95, "", transform=output_axis.transAxes, verticalalignment="top")
    upper_status = input_axis.text(0.02, 0.95, "", transform=input_axis.transAxes, verticalalignment="top")
    product_fill = None
    frames_per_case = len(frame_indices)

    def update(frame: int) -> tuple[object, ...]:
        case_index = min(frame // frames_per_case, len(sequence.cases) - 1)
        time_index = frame_indices[frame % frames_per_case]
        case = sequence.cases[case_index]
        nonlocal product_fill
        input_line.set_color(colors[case_index])
        input_line.set_data(time, case.result.input_signal)
        shifted_response = case.result.impulse_response
        transfer_definition = get_transfer_function_definition(config.transfer_function_name)
        shifted_response = transfer_definition.impulse_function(
            time[time_index] - time,
            config.damping_ratio,
            config.natural_frequency,
        )
        product = case.result.input_signal * shifted_response
        shifted_line.set_data(time, shifted_response)
        product_line.set_data(time, product)
        if product_fill is not None:
            product_fill.remove()
        product_fill = input_axis.fill_between(time, 0.0, product, color="#009E73", alpha=0.25)
        for index, line in enumerate(output_lines):
            if index < case_index:
                line.set_data(time, sequence.cases[index].result.output)
            elif index == case_index:
                line.set_data(time[: time_index + 1], case.result.output[: time_index + 1])
            else:
                line.set_data([], [])
        status_text.set_text(
            f"Senoide {case_index + 1}/{len(sequence.cases)}: "
            f"{case.multiplier:.2f} omega_ref | t = {time[time_index]:.2f} s"
        )
        upper_status.set_text(
            f"t = {time[time_index]:.2f} s | área = {case.result.output[time_index]:.4f}"
        )
        completed_cases = sequence.cases[: case_index + 1]
        point_frequencies = np.array([item.frequency for item in completed_cases])
        point_magnitudes, point_phases = calculate_bode_response(
            point_frequencies,
            config.damping_ratio,
            config.natural_frequency,
        )
        bode_magnitude_points.set_offsets(np.column_stack((point_frequencies, point_magnitudes)))
        bode_phase_points.set_offsets(np.column_stack((point_frequencies, point_phases)))
        bode_magnitude_points.set_facecolors(colors[: case_index + 1])
        bode_phase_points.set_facecolors(colors[: case_index + 1])
        return (
            input_line,
            shifted_line,
            product_line,
            *output_lines,
            status_text,
            upper_status,
            product_fill,
            bode_magnitude_points,
            bode_phase_points,
        )

    animation = FuncAnimation(
        figure,
        update,
        frames=range(len(sequence.cases) * frames_per_case),
        interval=1000.0 / config.fps,
        blit=False,
        repeat=False,
    )
    writer = FFMpegWriter(fps=config.fps, codec="libx264", extra_args=["-pix_fmt", "yuv420p"])
    animation.save(output_path, writer=writer, dpi=config.dpi)
    plt.close(figure)
    return output_path


def generate_sine_sequence(
    config: AnimationConfig,
    multipliers: tuple[float, ...],
) -> tuple[Path, Path, SineSequenceResult]:
    sequence = calculate_sine_sequence(config, multipliers)
    png_path = save_sine_sequence_figure(
        sequence,
        config.output_dir / "comparacao_senoides.png",
    )
    mp4_path = create_sine_sequence_animation(
        sequence,
        config,
        config.output_dir / "convolucao_senoides_com_convolucao.mp4",
    )
    return mp4_path, png_path, sequence


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
    plot_scale: PlotScale | None = None,
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
    input_representation = build_input_plot_representation(result)
    active_plot_scale = plot_scale
    if active_plot_scale is None:
        active_plot_scale = build_plot_scale(result)

    input_line, = overlap_axis.plot(
        result.time,
        input_representation.display_signal,
        color=input_color,
        linewidth=1.7,
        label=r"$x(\tau)$",
    )
    if input_representation.show_unit_impulse_arrow:
        overlap_axis.annotate(
            "",
            xy=(input_representation.arrow_x, input_representation.arrow_y_end),
            xytext=(input_representation.arrow_x, input_representation.arrow_y_start),
            arrowprops={
                "arrowstyle": "-|>",
                "color": input_color,
                "linewidth": 2.0,
                "mutation_scale": 18.0,
            },
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
    overlap_axis.set_ylim(*active_plot_scale.overlap_y_limits)
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
    output_axis.set_ylim(*active_plot_scale.output_y_limits)
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
    plot_scale: PlotScale | None = None,
) -> tuple[Path, Path, ConvolutionResult]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    result = calculate_default_case(config)
    png_path = save_comparison_figure(
        result,
        config.output_dir / "comparacao_numerica_analitica.png",
        plot_scale,
    )
    mp4_path = create_animation(
        result,
        config,
        config.output_dir / "convolucao_animada.mp4",
        plot_scale,
    )
    return mp4_path, png_path, result


def build_case_output_directory(
    base_output_dir: Path,
    case_number: int,
    input_name: str,
) -> Path:
    return base_output_dir / f"{case_number:02d}_{input_name}"


def generate_all_outputs(config: AnimationConfig) -> list[GeneratedCase]:
    generated_cases: list[GeneratedCase] = []
    shared_sine_plot_scale = build_shared_sine_plot_scale(config)
    for zero_based_index, input_name in enumerate(BATCH_INPUT_NAMES):
        case_number = zero_based_index + 1
        case_config = replace(
            config,
            input_name=input_name,
            output_dir=build_case_output_directory(
                config.output_dir,
                case_number,
                input_name,
            ),
        )
        plot_scale = None
        if input_name in SINE_INPUT_NAMES:
            plot_scale = shared_sine_plot_scale
        mp4_path, png_path, result = generate_outputs(case_config, plot_scale)
        generated_cases.append(
            GeneratedCase(
                input_name=input_name,
                mp4_path=mp4_path,
                png_path=png_path,
                result=result,
            )
        )
    return generated_cases


def parse_sine_multipliers(value: str) -> tuple[float, ...]:
    try:
        multipliers = tuple(float(item.strip()) for item in value.split(","))
    except ValueError as error:
        raise ValueError("sine multipliers must be comma-separated numbers") from error
    if not multipliers or any(not np.isfinite(item) or item <= 0.0 for item in multipliers):
        raise ValueError("sine multipliers must be finite and positive")
    return multipliers


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an animated MP4 of a convolution.",
    )
    parser.add_argument(
        "--input-name",
        default=None,
        help="Generate only one input case. If omitted, all cases are generated.",
    )
    parser.add_argument("--transfer-function-name", default="second_order_underdamped")
    parser.add_argument("--sine-sequence", action="store_true")
    parser.add_argument(
        "--sine-multipliers",
        default=",".join(f"{value:g}" for value in DEFAULT_SINE_MULTIPLIERS),
    )
    parser.add_argument("--start-time", type=float, default=-10.0)
    parser.add_argument("--end-time", type=float, default=20.0)
    parser.add_argument("--dt", type=float, default=1e-2)
    parser.add_argument("--frame-stride", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    return parser.parse_args()


def print_case_summary(generated_case: GeneratedCase) -> None:
    result = generated_case.result
    print(f"Input: {result.input_name}")
    print(f"MP4: {generated_case.mp4_path.resolve()}")
    print(f"Comparison: {generated_case.png_path.resolve()}")
    print(f"Transfer function: {result.transfer_function_name}")
    print(f"Reference frequency: {result.reference_frequency:.8f} rad/s")
    print(f"Reference frequency source: {result.reference_frequency_source}")
    if result.has_analytical_reference:
        print(f"Maximum absolute error: {result.maximum_absolute_error:.8f}")
        print(f"Root mean square error: {result.root_mean_square_error:.8f}")
    else:
        print("Analytical reference: not available for this input/system combination")


def main() -> None:
    arguments = parse_arguments()
    config = AnimationConfig(
        transfer_function_name=arguments.transfer_function_name,
        start_time=arguments.start_time,
        end_time=arguments.end_time,
        dt=arguments.dt,
        frame_stride=arguments.frame_stride,
        output_dir=arguments.output_dir,
    )
    if arguments.sine_sequence:
        mp4_path, png_path, sequence = generate_sine_sequence(
            config,
            parse_sine_multipliers(arguments.sine_multipliers),
        )
        print(f"MP4: {mp4_path.resolve()}")
        print(f"Comparison: {png_path.resolve()}")
        print(f"Sine multipliers: {sequence.multipliers}")
    elif arguments.input_name is None:
        generated_cases = generate_all_outputs(config)
        for generated_case in generated_cases:
            print_case_summary(generated_case)
            print("")
    else:
        single_config = replace(config, input_name=arguments.input_name)
        mp4_path, png_path, result = generate_outputs(single_config)
        print_case_summary(
            GeneratedCase(
                input_name=result.input_name,
                mp4_path=mp4_path,
                png_path=png_path,
                result=result,
            )
        )


if __name__ == "__main__":
    main()
