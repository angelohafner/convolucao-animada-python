# Convolution Signal Modules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the default input signal and transfer-function impulse response out of `convolution_animation.py` without changing the generated convolution MP4.

**Architecture:** Keep `convolution_animation.py` as the orchestration module for configuration, convolution, plotting, animation, and CLI execution. Move editable signal definitions into `input_signal.py` and `transfer_function.py`, then re-export them through imports in `convolution_animation.py` for backward compatibility.

**Tech Stack:** Python 3.11+, NumPy, Matplotlib, pytest, FFmpeg/ffprobe.

## Global Constraints

- Keep all code identifiers, filenames, and code comments in English.
- Do not use compound assignment operators in project code.
- Do not change default numerical parameters or output filenames.
- Do not change the main animation layout.
- Keep documentation in Portuguese for the user-facing project files.
- Do not initialize Git or commit because `D:/convolucao` is not a Git repository.

---

### Task 1: Add Tests for Module Boundaries

**Files:**
- Modify: `tests/test_convolution_animation.py`

**Interfaces:**
- Produces test coverage for `input_signal.input_function`.
- Produces test coverage for `transfer_function.impulse_function`.
- Verifies `convolution_animation` still re-exports both functions.

- [ ] Add imports from `input_signal` and `transfer_function`.
- [ ] Add a test that the direct module imports match the backward-compatible imports from `convolution_animation`.
- [ ] Run the focused test and confirm it fails while the new modules do not exist.

### Task 2: Create Focused Signal Modules

**Files:**
- Create: `input_signal.py`
- Create: `transfer_function.py`
- Modify: `convolution_animation.py`

**Interfaces:**
- `input_signal.input_function(time: FloatArray) -> FloatArray`
- `transfer_function.impulse_function(time: FloatArray, damping_ratio: float = 0.2, natural_frequency: float = 2.0) -> FloatArray`

- [ ] Move the unit-step input implementation into `input_signal.py`.
- [ ] Move the underdamped second-order impulse response implementation into `transfer_function.py`.
- [ ] Import both functions in `convolution_animation.py`.
- [ ] Remove the original in-file function bodies from `convolution_animation.py`.
- [ ] Run the focused test and then the full pytest suite.

### Task 3: Update Documentation and Validate Artifacts

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_CONTEXT.md`

**Interfaces:**
- Documentation points users to the new files for editing signals.

- [ ] Update the project structure and customization sections in `README.md`.
- [ ] Update extension notes and architecture context in `PROJECT_CONTEXT.md`.
- [ ] Run `python -m compileall convolution_animation.py input_signal.py transfer_function.py tests`.
- [ ] Run `python convolution_animation.py`.
- [ ] Run `ffprobe` against `outputs/convolucao_animada.mp4`.
- [ ] Run final `python -m pytest -q`.
