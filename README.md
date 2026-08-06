# Convolucao animada em Python

Projeto Python para gerar um MP4 didatico de convolucao. A animacao mostra
`x(tau)`, o deslocamento de `h(t - tau)`, o produto `x(tau) * h(t - tau)` e a
construcao progressiva de `y(t)`.

Repositorio publico:

```text
https://github.com/angelohafner/convolucao-animada-python
```

## Objetivo

O caso padrao continua sendo um degrau unitario aplicado a um sistema de segunda
ordem subamortecido. O projeto agora tambem possui uma biblioteca modular de
entradas, com um arquivo por sinal, e uma biblioteca de funcoes de transferencia,
com um arquivo por sistema.

## Modelo matematico padrao

Entrada padrao:

```text
x(t) = u(t)
```

Funcao de transferencia padrao:

```text
H(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
```

Resposta ao impulso usada na convolucao:

```text
h(t) = wn / sqrt(1 - zeta^2)
       * exp(-zeta * wn * t)
       * sin(wd * t)
       * u(t)

wd = wn * sqrt(1 - zeta^2)
zeta = 0.2
wn = 2 rad/s
```

A convolucao continua e aproximada numericamente por:

```text
y(t) = integral x(tau) * h(t - tau) d(tau)
y_num = convolve(x, h) * dt
```

## Frequencia de referencia

Para o sistema de segunda ordem padrao, a frequencia de ressonancia existe
quando:

```text
zeta < 1 / sqrt(2)
```

Nesse caso:

```text
omega_ref = omega_r = wn * sqrt(1 - 2*zeta^2)
```

Com `zeta = 0.2` e `wn = 2 rad/s`, o projeto usa ressonancia real:

```text
omega_ref = 1.91833261 rad/s
```

Se um sistema futuro nao tiver frequencia de ressonancia, o criterio alternativo
documentado e:

```text
omega_ref = wn
```

## Estrutura do projeto

```text
D:/convolucao/
├── convolution_animation.py
├── .gitignore
├── inputs/
│   ├── unit_step.py
│   ├── unit_impulse.py
│   ├── unit_ramp.py
│   ├── sine_0_7_resonance.py
│   ├── sine_0_8_resonance.py
│   ├── sine_0_9_resonance.py
│   ├── sine_1_0_resonance.py
│   ├── sine_1_1_resonance.py
│   ├── sine_1_2_resonance.py
│   ├── sine_1_3_resonance.py
│   ├── sine_common.py
│   └── registry.py
├── transfer_functions/
│   ├── second_order_underdamped.py
│   └── registry.py
├── tests/
│   └── test_convolution_animation.py
├── outputs/
├── README.md
├── PROJECT_CONTEXT.md
└── requirements.txt
```

## Entradas disponiveis

Use estes nomes em `AnimationConfig(input_name=...)` ou no argumento
`--input-name`:

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

O impulso unitario e numerico. O criterio usado e:

```text
x[indice mais proximo de t = 0] = 1 / dt
sum(x) * dt = 1
```

As entradas senoidais sao puras, nao causais e de amplitude unitaria:

```text
x(t) = sin(multiplier * omega_ref * t)
```

com `multiplier` em:

```text
[0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
```

## Funcoes de transferencia disponiveis

Use estes nomes em `AnimationConfig(transfer_function_name=...)` ou no argumento
`--transfer-function-name`:

```text
second_order_underdamped
```

O arquivo do sistema padrao e:

```text
transfer_functions/second_order_underdamped.py
```

## Como gerar o MP4

Caso padrao:

```powershell
python convolution_animation.py
```

Escolhendo outra entrada:

```powershell
python convolution_animation.py --input-name unit_ramp
python convolution_animation.py --input-name sine_1_0_resonance
```

Os arquivos gerados ficam em:

```text
outputs/convolucao_animada.mp4
outputs/comparacao_numerica_analitica.png
```

## GitHub

O projeto esta publicado como repositorio publico em:

```text
https://github.com/angelohafner/convolucao-animada-python
```

O branch principal e `main`.

## Como adicionar uma nova entrada

1. Crie um novo arquivo em `inputs/`, por exemplo `inputs/my_signal.py`.
2. Implemente:

```python
def input_function(time: FloatArray, dt: float, reference_frequency: float) -> FloatArray:
    ...
```

3. Registre a entrada em `inputs/registry.py`.
4. Adicione ou ajuste testes em `tests/test_convolution_animation.py`.

## Como adicionar uma nova funcao de transferencia

1. Crie um novo arquivo em `transfer_functions/`.
2. Implemente a resposta ao impulso.
3. Implemente o criterio de frequencia de referencia.
4. Registre o sistema em `transfer_functions/registry.py`.
5. Documente se existe ressonancia real ou se sera usado o fallback.

## Validacao

Comandos principais:

```powershell
python -m pytest -q
python -m compileall convolution_animation.py inputs transfer_functions tests
python convolution_animation.py
ffprobe -v error -select_streams v:0 -count_frames `
  -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames,duration `
  -of default=noprint_wrappers=1 outputs/convolucao_animada.mp4
```

Ultima validacao local registrada:

```text
testes = 39 passed
erro absoluto maximo = 0.00752794
RMSE = 0.00143955
codec = h264
resolucao = 1400 x 900
fps = 25/1
quadros = 152
duracao = 6.080000 s
```

## Limitacoes

- A resposta analitica implementada vale somente para o caso padrao:
  `unit_step` com `second_order_underdamped`.
- Para outras entradas, o MP4 e a convolucao numerica sao gerados normalmente,
  mas a curva analitica nao e exibida.
- A aproximacao do impulso depende de `dt`.
- O FFmpeg precisa estar instalado e disponivel no `PATH`.
