# Multi-Sine Time Response Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a sequential multi-sine simulation that overlays each individual system response in time-domain plots while preserving existing single-input cases.

**Architecture:** Keep signal generation and convolution numerical logic in the existing modules. Add typed sequence results and a dedicated sequential animation path in `convolution_animation.py`, reusing the current transfer-function registry and plotting conventions. Expose the feature through an explicit CLI mode and document it.

**Tech Stack:** Python 3.13, NumPy, Matplotlib, FFmpeg, pytest.

## Global Constraints

- Preserve existing impulse, step, ramp, and single-sine behavior.
- Process each sine separately; do not sum sine inputs into one convolution input.
- Use the current `dt`, transfer function, reference-frequency, and common-scale conventions.
- Keep code identifiers and comments in English; user-facing explanatory text may remain Portuguese.
- Preserve unrelated existing worktree changes and generated artifacts.

---

### Task 1: Define the sequential calculation model

**Files:**
- Modify: `convolution_animation.py`
- Test: `tests/test_convolution_animation.py`

**Interfaces:**
- Produce `SineSequenceConfig` with a tuple of positive finite frequency multipliers.
- Produce `SineSequenceResult` containing ordered `ConvolutionResult` objects and their multipliers.
- Produce `calculate_sine_sequence(config: AnimationConfig, multipliers: tuple[float, ...]) -> SineSequenceResult`.

- [ ] **Step 1: Write failing tests**

Add tests that require a default sequence to preserve order and calculate each result independently:

```python
def test_sine_sequence_preserves_frequency_order() -> None:
    sequence = calculate_sine_sequence(
        AnimationConfig(start_time=-1.0, end_time=2.0, dt=0.02),
        (0.7, 1.0, 1.3),
    )
    assert sequence.multipliers == (0.7, 1.0, 1.3)
    assert [item.input_name for item in sequence.cases] == [
        "sine_0_7_resonance",
        "sine_1_0_resonance",
        "sine_1_3_resonance",
    ]
```

Also test that empty, zero, negative, and non-finite multipliers raise `ValueError`.

- [ ] **Step 2: Run the focused tests and verify the expected failure**

Run:

```powershell
python -m pytest -q tests/test_convolution_animation.py -k "sine_sequence or frequency_multiplier"
```

Expected: FAIL because the sequence types and calculation function do not yet exist.

- [ ] **Step 3: Implement the minimal calculation model**

Add immutable dataclasses and validation. Map each multiplier to the existing registered sine input when it matches a supported multiplier; otherwise generate the sine directly with `sine_common` semantics while retaining an explicit display label. Reuse `calculate_default_case` for registered inputs and the existing `compute_convolution` path for arbitrary positive multipliers.

- [ ] **Step 4: Run focused and existing tests**

Run:

```powershell
python -m pytest -q tests/test_convolution_animation.py -k "sine_sequence or frequency_multiplier"
python -m pytest -q
```

Expected: new tests and the existing suite pass.

- [ ] **Step 5: Commit the calculation model**

```powershell
git add convolution_animation.py tests/test_convolution_animation.py
git commit -m "feat(convolution): add multi-sine sequence calculation"
```

### Task 2: Add sequential overlay plotting and animation

**Files:**
- Modify: `convolution_animation.py`
- Test: `tests/test_convolution_animation.py`

**Interfaces:**
- Produce a sequential output directory containing `convolucao_senoides.mp4` and `comparacao_senoides.png`.
- Expose `generate_sine_sequence(config, multipliers, output_dir)` for programmatic use.

- [ ] **Step 1: Write failing tests**

Add tests that generate a small sequence with a short time window and assert that the comparison PNG and MP4 exist, have nonzero size, and contain one plotted result per multiplier through the returned metadata.

- [ ] **Step 2: Run the focused tests and verify failure**

```powershell
python -m pytest -q tests/test_convolution_animation.py -k "sine_sequence_output or overlay"
```

Expected: FAIL because the sequential generator and output paths do not exist.

- [ ] **Step 3: Implement the minimal overlay animation**

Create a sequential animation loop that reveals one current response at a time, keeps completed response curves visible, uses deterministic colors, and labels each curve with both multiplier and angular frequency. Reuse the existing frame selection, axis limits, FFmpeg writer, and figure lifecycle. The final comparison PNG must show all complete output curves simultaneously.

- [ ] **Step 4: Run focused tests and inspect the generated figure**

```powershell
python -m pytest -q tests/test_convolution_animation.py -k "sine_sequence_output or overlay"
```

Open the generated PNG and confirm that the curves are distinguishable, the legend identifies frequencies, and the axes retain units.

- [ ] **Step 5: Commit the animation feature**

```powershell
git add convolution_animation.py tests/test_convolution_animation.py
git commit -m "feat(animation): overlay sequential sine responses"
```

### Task 3: Expose the workflow through the CLI

**Files:**
- Modify: `convolution_animation.py`
- Test: `tests/test_convolution_animation.py`

**Interfaces:**
- Add an explicit CLI mode such as `--sine-sequence`.
- Add `--sine-multipliers` accepting a comma-separated list, defaulting to `0.7,0.8,0.9,1.0,1.1,1.2,1.3`.

- [ ] **Step 1: Write failing CLI tests**

Test parsing of the default list, a custom list, and rejection of malformed or non-positive values.

- [ ] **Step 2: Run tests and verify failure**

```powershell
python -m pytest -q tests/test_convolution_animation.py -k "cli_sine_sequence"
```

Expected: FAIL because the arguments are not registered.

- [ ] **Step 3: Implement CLI dispatch**

Add parser arguments, parse and validate the multiplier list, and dispatch to the sequence generator only when `--sine-sequence` is selected. Keep `--input-name` behavior unchanged when that mode is not selected.

- [ ] **Step 4: Run CLI tests and a real short command**

```powershell
python -m pytest -q tests/test_convolution_animation.py -k "cli_sine_sequence"
python convolution_animation.py --sine-sequence --sine-multipliers 0.8,1.0,1.2 --start-time -1 --end-time 2 --dt 0.02 --frame-stride 10 --output-dir outputs/sequence_validation
```

Expected: command completes and creates the documented MP4 and PNG.

- [ ] **Step 5: Commit the CLI changes**

```powershell
git add convolution_animation.py tests/test_convolution_animation.py
git commit -m "feat(cli): expose multi-sine sequence mode"
```

### Task 4: Update durable documentation and validate artifacts

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_CONTEXT.md`
- Test: `tests/test_convolution_animation.py` if validation metadata needs coverage

- [ ] **Step 1: Document commands and interpretation**

Explain that responses are calculated independently and overlaid, list the default multipliers, show the CLI command, describe colors/legend/current-case behavior, and state that the feature demonstrates time-domain evidence of frequency response rather than simultaneous excitation.

- [ ] **Step 2: Run the complete validation suite**

```powershell
python -m pytest -q
python -m compileall convolution_animation.py inputs transfer_functions tests
ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames,duration -of default=noprint_wrappers=1 outputs/sequence_validation/convolucao_senoides.mp4
```

Expected: all tests pass, compilation succeeds, and `ffprobe` reports a valid H.264 MP4 with nonzero duration and frame count.

- [ ] **Step 3: Review the worktree and final generated files**

```powershell
git status --short
Get-ChildItem outputs/sequence_validation
```

Confirm that only intended source/documentation changes and the explicitly generated validation artifacts are present.

- [ ] **Step 4: Commit documentation**

```powershell
git add README.md PROJECT_CONTEXT.md
git commit -m "docs(convolution): document multi-sine workflow"
```
