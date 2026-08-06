# Convolution Input Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a modular input library and transfer-function package while preserving the default convolution MP4 workflow.

**Architecture:** Use `inputs/` for one input module per signal and `transfer_functions/` for one transfer-function module per system. `convolution_animation.py` selects an input and transfer-function definition from registries based on `AnimationConfig`.

**Tech Stack:** Python 3.11+, NumPy, Matplotlib, pytest, FFmpeg/ffprobe.

## Global Constraints

- Keep the default case as unit step plus second-order underdamped transfer function.
- Keep code identifiers, filenames, and comments in English.
- Keep visible documentation in Portuguese.
- Do not use compound assignment operators in project code.
- Generate `outputs/convolucao_animada.mp4` and `outputs/comparacao_numerica_analitica.png`.
- Do not initialize Git or commit because this workspace is not a Git repository.

---

### Task 1: Tests for New Inputs and Resonance Reference

**Files:**
- Modify: `tests/test_convolution_animation.py`

**Interfaces:**
- `inputs.unit_impulse.input_function(time, dt, reference_frequency)`
- `inputs.unit_ramp.input_function(time, dt, reference_frequency)`
- `inputs.sine_0_7_resonance.input_function(time, dt, reference_frequency)`
- `transfer_functions.second_order_underdamped.resonance_frequency(...)`
- `transfer_functions.second_order_underdamped.reference_frequency(...)`

- [ ] Add failing tests for unit impulse area, ramp values, sinusoidal frequency scaling, resonance frequency, and fallback frequency.
- [ ] Run the focused tests and confirm they fail because the packages do not exist.

### Task 2: Input and Transfer-Function Packages

**Files:**
- Create: `inputs/__init__.py`
- Create: `inputs/registry.py`
- Create: `inputs/sine_common.py`
- Create: one module per input listed in the design.
- Create: `transfer_functions/__init__.py`
- Create: `transfer_functions/registry.py`
- Create: `transfer_functions/second_order_underdamped.py`
- Delete: `input_signal.py`
- Delete: `transfer_function.py`

**Interfaces:**
- `inputs.get_input_signal(name, time, dt, reference_frequency)`
- `inputs.available_input_names()`
- `transfer_functions.get_transfer_function_definition(name)`

- [ ] Implement the modules and registries.
- [ ] Run the focused tests and confirm they pass.

### Task 3: Orchestration Selection

**Files:**
- Modify: `convolution_animation.py`
- Modify: `tests/test_convolution_animation.py`

**Interfaces:**
- `AnimationConfig(input_name="unit_step", transfer_function_name="second_order_underdamped")`
- `calculate_default_case(config)`
- `main()` with optional command-line arguments.

- [ ] Add tests for selected ramp input and unknown input rejection.
- [ ] Update `convolution_animation.py` to use registries.
- [ ] Preserve default MP4 generation with no command-line arguments.
- [ ] Run the full test suite.

### Task 4: Documentation and Final Validation

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_CONTEXT.md`

**Interfaces:**
- Document how to edit each input module and transfer-function module.

- [ ] Update documentation with folder structure, available inputs, resonance criterion, fallback criterion, and commands.
- [ ] Run `python -m pytest -q`.
- [ ] Run `python -m compileall convolution_animation.py inputs transfer_functions tests`.
- [ ] Run `python convolution_animation.py`.
- [ ] Run `ffprobe` on the generated MP4.
