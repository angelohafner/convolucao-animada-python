# Convolution Signal Modules Design

## Context

The current Python project generates a didactic MP4 animation of convolution.
The main module `convolution_animation.py` still owns the numerical workflow,
plotting, animation, and the default signal definitions.

The user approved evolving the structure so the editable engineering model
definitions live outside the animation orchestration file.

## Approved Design

Create two focused modules at the project root:

- `input_signal.py`: owns `input_function(time)`, the default unit-step input.
- `transfer_function.py`: owns `impulse_function(time, damping_ratio, natural_frequency)`
  and documents the default transfer function
  `H(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)`.

`convolution_animation.py` will import those functions and keep the same public
exports so existing code can still import `input_function` and
`impulse_function` from `convolution_animation`.

## Behavior

The numerical result, animation layout, filenames, default parameters, and
generated outputs must remain unchanged.

## Testing

Tests should verify the new modules directly and verify backward-compatible
imports from `convolution_animation`.

The full project verification remains:

```powershell
python -m pytest -q
python -m compileall convolution_animation.py input_signal.py transfer_function.py tests
python convolution_animation.py
ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_read_frames,duration -of default=noprint_wrappers=1 outputs/convolucao_animada.mp4
```

## Documentation

Update `README.md` and `PROJECT_CONTEXT.md` so future users know where to edit:

- input signal: `input_signal.py`
- transfer function / impulse response: `transfer_function.py`
- default transfer-function parameters: `AnimationConfig` in
  `convolution_animation.py`
