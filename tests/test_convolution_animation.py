from __future__ import annotations

from pathlib import Path

import convolution_animation
import matplotlib.animation as mpl_animation
import numpy as np
import pytest

from inputs import available_input_names, get_input_signal
from inputs.sine_0_7_resonance import input_function as sine_0_7_input_function
from inputs.unit_impulse import input_function as unit_impulse_input_function
from inputs.unit_ramp import input_function as unit_ramp_input_function
from transfer_functions import available_transfer_function_names
from transfer_functions.second_order_underdamped import (
    reference_frequency,
    resonance_frequency,
)

from convolution_animation import (
    AnimationConfig,
    BATCH_INPUT_NAMES,
    RESONANCE_SINE_INPUT_NAME,
    SINE_INPUT_NAMES,
    build_input_plot_representation,
    build_plot_scale,
    build_shared_sine_plot_scale,
    analytical_step_response,
    build_time_axis,
    calculate_default_case,
    calculate_bode_response,
    calculate_sine_sequence,
    compute_convolution,
    create_animation,
    generate_all_outputs,
    generate_outputs,
    generate_sine_sequence,
    parse_sine_multipliers,
    impulse_function,
    input_function,
    save_comparison_figure,
    select_frame_indices,
)


def test_build_time_axis_includes_exact_endpoints() -> None:
    config = AnimationConfig(start_time=-1.0, end_time=1.0, dt=0.25)

    time = build_time_axis(config)

    np.testing.assert_allclose(time, np.linspace(-1.0, 1.0, 9))


def test_unit_step_is_causal_and_includes_origin() -> None:
    time = np.array([-1.0, -0.01, 0.0, 0.01, 1.0])

    signal = input_function(time)

    np.testing.assert_array_equal(signal, np.array([0.0, 0.0, 1.0, 1.0, 1.0]))


def test_available_input_names_include_default_and_new_entries() -> None:
    expected_names = {
        "unit_step",
        "unit_impulse",
        "unit_ramp",
        "sine_0_7_resonance",
        "sine_0_8_resonance",
        "sine_0_9_resonance",
        "sine_1_0_resonance",
        "sine_1_1_resonance",
        "sine_1_2_resonance",
        "sine_1_3_resonance",
    }

    names = set(available_input_names())

    assert names == expected_names


def test_unit_impulse_input_has_unit_area() -> None:
    dt = 0.1
    time = np.array([-0.1, 0.0, 0.1])

    signal = unit_impulse_input_function(time, dt, reference_frequency=1.0)

    np.testing.assert_array_equal(signal, np.array([0.0, 10.0, 0.0]))
    assert np.sum(signal) * dt == pytest.approx(1.0)


def test_sine_sequence_preserves_frequency_order() -> None:
    sequence = calculate_sine_sequence(
        AnimationConfig(start_time=-1.0, end_time=2.0, dt=0.02),
        (0.7, 1.0, 1.3),
    )
    assert sequence.multipliers == (0.7, 1.0, 1.3)
    assert [case.multiplier for case in sequence.cases] == [0.7, 1.0, 1.3]
    assert [case.input_name for case in sequence.cases] == [
        "sine_0_7_resonance",
        "sine_1_0_resonance",
        "sine_1_3_resonance",
    ]


@pytest.mark.parametrize("multipliers", [(), (0.0,), (-1.0,), (float("nan"),)])
def test_sine_sequence_rejects_invalid_multipliers(
    multipliers: tuple[float, ...],
) -> None:
    with pytest.raises(ValueError):
        calculate_sine_sequence(AnimationConfig(), multipliers)


def test_sine_sequence_generates_overlay_outputs(tmp_path: Path) -> None:
    config = AnimationConfig(
        start_time=-0.5,
        end_time=1.0,
        dt=0.05,
        frame_stride=5,
        output_dir=tmp_path,
    )
    mp4_path, png_path, sequence = generate_sine_sequence(config, (0.8, 1.0))
    assert len(sequence.cases) == 2
    assert mp4_path.exists() and mp4_path.stat().st_size > 0
    assert mp4_path.name == "convolucao_senoides_com_convolucao.mp4"
    assert png_path.exists() and png_path.stat().st_size > 0


def test_parse_sine_multipliers_accepts_comma_separated_values() -> None:
    assert parse_sine_multipliers("0.8, 1.0,1.2") == (0.8, 1.0, 1.2)


def test_parse_sine_multipliers_rejects_malformed_values() -> None:
    with pytest.raises(ValueError):
        parse_sine_multipliers("0.8,abc")


def test_bode_response_matches_second_order_transfer_function() -> None:
    frequency = np.array([2.0])
    magnitude_db, phase_deg = calculate_bode_response(
        frequency,
        damping_ratio=0.1,
        natural_frequency=2.0,
    )
    assert magnitude_db[0] == pytest.approx(20.0 * np.log10(1.0 / 0.2), abs=1e-6)
    assert phase_deg[0] == pytest.approx(-90.0, abs=1e-6)


def test_unit_ramp_is_causal() -> None:
    time = np.array([-1.0, 0.0, 0.5, 2.0])

    signal = unit_ramp_input_function(time, dt=0.1, reference_frequency=1.0)

    np.testing.assert_allclose(signal, np.array([0.0, 0.0, 0.5, 2.0]))


@pytest.mark.parametrize(
    ("input_name", "multiplier"),
    [
        ("sine_0_7_resonance", 0.7),
        ("sine_0_8_resonance", 0.8),
        ("sine_0_9_resonance", 0.9),
        ("sine_1_0_resonance", 1.0),
        ("sine_1_1_resonance", 1.1),
        ("sine_1_2_resonance", 1.2),
        ("sine_1_3_resonance", 1.3),
    ],
)
def test_sine_inputs_use_reference_frequency(
    input_name: str,
    multiplier: float,
) -> None:
    reference = 10.0
    time = np.array([0.0, np.pi / (2.0 * multiplier * reference)])

    signal = get_input_signal(input_name, time, dt=0.01, reference_frequency=reference)

    np.testing.assert_allclose(signal, np.array([0.0, 1.0]), atol=1e-12)
    assert np.max(np.abs(signal)) <= 1.0 + 1e-12


def test_named_sine_module_matches_registry() -> None:
    time = np.array([0.0, 0.5, 1.0])

    direct = sine_0_7_input_function(time, dt=0.01, reference_frequency=2.0)
    selected = get_input_signal(
        "sine_0_7_resonance",
        time,
        dt=0.01,
        reference_frequency=2.0,
    )

    np.testing.assert_allclose(direct, selected)


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


def test_available_transfer_function_names_include_default_system() -> None:
    assert available_transfer_function_names() == ("second_order_underdamped",)


def test_second_order_resonance_frequency_matches_formula() -> None:
    result = resonance_frequency(damping_ratio=0.2, natural_frequency=2.0)

    assert result == pytest.approx(2.0 * np.sqrt(1.0 - 2.0 * 0.2**2))


def test_second_order_reference_frequency_uses_resonance_when_it_exists() -> None:
    result = reference_frequency(damping_ratio=0.2, natural_frequency=2.0)

    assert result.value == pytest.approx(2.0 * np.sqrt(1.0 - 2.0 * 0.2**2))
    assert result.has_resonance is True
    assert result.source == "resonance_frequency"


def test_second_order_reference_frequency_falls_back_to_natural_frequency() -> None:
    result = reference_frequency(damping_ratio=0.8, natural_frequency=2.0)

    assert result.value == pytest.approx(2.0)
    assert result.has_resonance is False
    assert result.source == "natural_frequency_fallback"


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("dt", 0.0),
        ("natural_frequency", 0.0),
        ("damping_ratio", -0.1),
        ("damping_ratio", 1.0),
        ("frame_stride", 0),
        ("fps", 0),
        ("end_time", -10.0),
        ("dpi", 0),
    ],
)
def test_invalid_configuration_is_rejected(field_name: str, value: float) -> None:
    values = {field_name: value}

    with pytest.raises(ValueError):
        AnimationConfig(**values)


def test_convolution_of_unit_samples_scales_by_dt() -> None:
    time = np.array([0.0, 0.5, 1.0])
    input_signal = np.array([1.0, 1.0, 1.0])
    impulse_response = np.array([1.0, 0.0, 0.0])

    result = compute_convolution(time, input_signal, impulse_response, dt=0.5)

    np.testing.assert_allclose(result, np.array([0.5, 0.5, 0.5]))


def test_convolution_rejects_arrays_with_different_lengths() -> None:
    time = np.array([0.0, 0.5, 1.0])
    input_signal = np.ones(3)
    impulse_response = np.ones(2)

    with pytest.raises(ValueError, match="same length"):
        compute_convolution(time, input_signal, impulse_response, dt=0.5)


def test_analytical_step_response_is_zero_before_origin() -> None:
    time = np.array([-1.0, -0.1, 0.0, 0.1])

    response = analytical_step_response(time, 0.2, 2.0)

    np.testing.assert_array_equal(response[:3], np.zeros(3))
    assert response[3] > 0.0


def test_default_numerical_response_matches_analytical_response() -> None:
    result = calculate_default_case(AnimationConfig())
    causal = result.time >= 0.0

    maximum_error = np.max(np.abs(result.output[causal] - result.analytical[causal]))

    assert result.input_name == "unit_step"
    assert result.transfer_function_name == "second_order_underdamped"
    assert result.has_analytical_reference is True
    assert result.has_resonance is True
    assert result.reference_frequency_source == "resonance_frequency"
    assert maximum_error < 0.011
    np.testing.assert_allclose(result.output[result.time < 0.0], 0.0, atol=1e-12)


def test_calculation_uses_selected_ramp_input() -> None:
    config = AnimationConfig(
        start_time=-1.0,
        end_time=1.0,
        dt=0.5,
        input_name="unit_ramp",
    )

    result = calculate_default_case(config)

    np.testing.assert_allclose(result.input_signal, np.array([0.0, 0.0, 0.0, 0.5, 1.0]))
    assert result.input_name == "unit_ramp"
    assert result.has_analytical_reference is False
    assert np.isnan(result.maximum_absolute_error)


def test_unknown_input_name_is_rejected_during_calculation() -> None:
    config = AnimationConfig(input_name="missing_input")

    with pytest.raises(ValueError, match="Unknown input_name"):
        calculate_default_case(config)


def test_unit_impulse_is_drawn_as_unit_height_arrow() -> None:
    result = calculate_default_case(
        AnimationConfig(start_time=-0.1, end_time=0.1, dt=0.1, input_name="unit_impulse")
    )

    representation = build_input_plot_representation(result)

    np.testing.assert_array_equal(
        representation.display_signal,
        np.zeros_like(result.input_signal),
    )
    assert representation.show_unit_impulse_arrow is True
    assert representation.arrow_x == pytest.approx(0.0)
    assert representation.arrow_y_start == pytest.approx(0.0)
    assert representation.arrow_y_end == pytest.approx(1.0)


def test_non_impulse_input_uses_actual_signal_for_plot() -> None:
    result = calculate_default_case(
        AnimationConfig(start_time=-0.1, end_time=0.1, dt=0.1, input_name="unit_step")
    )

    representation = build_input_plot_representation(result)

    np.testing.assert_array_equal(representation.display_signal, result.input_signal)
    assert representation.show_unit_impulse_arrow is False


def test_batch_input_names_follow_requested_order() -> None:
    assert BATCH_INPUT_NAMES == (
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


def test_generate_all_outputs_uses_ordered_case_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed_configs: list[AnimationConfig] = []
    observed_plot_scales: list[object] = []

    def fake_generate_outputs(
        config: AnimationConfig,
        plot_scale: object | None = None,
    ) -> tuple[Path, Path, object]:
        observed_configs.append(config)
        observed_plot_scales.append(plot_scale)
        return (
            config.output_dir / "convolucao_animada.mp4",
            config.output_dir / "comparacao_numerica_analitica.png",
            object(),
        )

    monkeypatch.setattr(convolution_animation, "generate_outputs", fake_generate_outputs)

    outputs = generate_all_outputs(AnimationConfig(output_dir=tmp_path))

    assert [config.input_name for config in observed_configs] == list(BATCH_INPUT_NAMES)
    assert [config.output_dir.name for config in observed_configs] == [
        "01_unit_impulse",
        "02_unit_step",
        "03_unit_ramp",
        "04_sine_0_7_resonance",
        "05_sine_0_8_resonance",
        "06_sine_0_9_resonance",
        "07_sine_1_0_resonance",
        "08_sine_1_1_resonance",
        "09_sine_1_2_resonance",
        "10_sine_1_3_resonance",
    ]
    assert [output.input_name for output in outputs] == list(BATCH_INPUT_NAMES)


def test_shared_sine_plot_scale_matches_resonance_sine_case() -> None:
    config = AnimationConfig(start_time=-1.0, end_time=1.0, dt=0.1)
    resonance_config = AnimationConfig(
        start_time=-1.0,
        end_time=1.0,
        dt=0.1,
        input_name=RESONANCE_SINE_INPUT_NAME,
    )
    resonance_result = calculate_default_case(resonance_config)

    shared_scale = build_shared_sine_plot_scale(config)
    resonance_scale = build_plot_scale(resonance_result)

    assert shared_scale == resonance_scale


def test_generate_all_outputs_applies_resonance_scale_to_every_sine_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed_configs: list[AnimationConfig] = []
    observed_plot_scales: list[object] = []

    def fake_generate_outputs(
        config: AnimationConfig,
        plot_scale: object | None = None,
    ) -> tuple[Path, Path, object]:
        observed_configs.append(config)
        observed_plot_scales.append(plot_scale)
        return (
            config.output_dir / "convolucao_animada.mp4",
            config.output_dir / "comparacao_numerica_analitica.png",
            object(),
        )

    monkeypatch.setattr(convolution_animation, "generate_outputs", fake_generate_outputs)

    generate_all_outputs(AnimationConfig(output_dir=tmp_path))
    non_null_sine_scales = [
        scale
        for config, scale in zip(observed_configs, observed_plot_scales)
        if config.input_name in SINE_INPUT_NAMES
    ]
    non_sine_scales = [
        scale
        for config, scale in zip(observed_configs, observed_plot_scales)
        if config.input_name not in SINE_INPUT_NAMES
    ]

    assert len(non_null_sine_scales) == len(SINE_INPUT_NAMES)
    assert len({id(scale) for scale in non_null_sine_scales}) == 1
    assert all(scale is None for scale in non_sine_scales)


def test_frame_indices_include_first_and_last_sample() -> None:
    indices = select_frame_indices(sample_count=101, stride=20)

    np.testing.assert_array_equal(indices, np.array([0, 19, 39, 59, 79, 99, 100]))
    assert np.all(np.diff(indices) > 0)


@pytest.mark.parametrize(
    ("sample_count", "stride"),
    [(0, 20), (101, 0)],
)
def test_frame_selection_rejects_invalid_arguments(
    sample_count: int,
    stride: int,
) -> None:
    with pytest.raises(ValueError):
        select_frame_indices(sample_count, stride)


def test_comparison_figure_is_written(tmp_path: Path) -> None:
    result = calculate_default_case(
        AnimationConfig(start_time=-1.0, end_time=2.0, dt=0.02)
    )
    output_path = tmp_path / "comparison.png"

    returned_path = save_comparison_figure(result, output_path)

    assert returned_path == output_path
    assert output_path.is_file()
    assert output_path.stat().st_size > 1_000


def test_animation_reports_unavailable_ffmpeg(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = AnimationConfig(start_time=-0.1, end_time=0.1, dt=0.1)
    result = calculate_default_case(config)
    monkeypatch.setattr(
        convolution_animation.writers,
        "is_available",
        lambda writer_name: False,
    )

    with pytest.raises(RuntimeError, match="FFmpeg"):
        create_animation(result, config, tmp_path / "animation.mp4")


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
