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
zeta = 0.1
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

Com `zeta = 0.1` e `wn = 2 rad/s`, o projeto usa ressonancia real:

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

Na animacao, esse impulso nao e desenhado com amplitude `1/dt`, porque isso
achata visualmente a resposta ao impulso do sistema. Para fins didaticos, ele e
representado no painel superior por uma seta vertical em `x = 0`, saindo de
`y = 0` e apontando para cima em `y = 1`. O calculo numerico continua usando
o valor `1/dt` para preservar a area unitaria.

As entradas senoidais sao puras, nao causais e de amplitude unitaria:

```text
x(t) = sin(multiplier * omega_ref * t)
```

com `multiplier` em:

```text
[0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8]
```

Todos os casos senoidais usam a mesma escala vertical nos graficos. A escala
comum e calculada a partir do caso `sine_1_0_resonance`, que corresponde a
`1.0 * omega_ref`, ou seja, a frequencia de ressonancia do sistema padrao.
Isso facilita comparar visualmente as respostas em diferentes frequencias.

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

## Como gerar os MP4s

O comando principal gera todos os casos, nesta ordem:

```text
1. unit_impulse
2. unit_step
3. unit_ramp
4. sine_0_7_resonance
5. sine_0_8_resonance
6. sine_0_9_resonance
7. sine_1_0_resonance
8. sine_1_1_resonance
9. sine_1_2_resonance
10. sine_1_3_resonance
```

Para gerar todos:

```powershell
python convolution_animation.py
```

Cada caso e salvo em uma subpasta propria:

```text
outputs/01_unit_impulse/convolucao_animada.mp4
outputs/02_unit_step/convolucao_animada.mp4
outputs/03_unit_ramp/convolucao_animada.mp4
...
outputs/10_sine_1_3_resonance/convolucao_animada.mp4
```

Para gerar apenas uma entrada:

```powershell
python convolution_animation.py --input-name unit_ramp
python convolution_animation.py --input-name sine_1_0_resonance
```

Quando `--input-name` e usado, os arquivos gerados ficam diretamente em:

```text
outputs/convolucao_animada.mp4
outputs/comparacao_numerica_analitica.png
```

Para demonstrar a resposta em frequencia no dominio do tempo, use o modo
sequencial. Cada senoide e convoluida separadamente; a resposta atual e
revelada progressivamente e as respostas anteriores permanecem sobrepostas:

```powershell
python convolution_animation.py --sine-sequence
python convolution_animation.py --sine-sequence --sine-multipliers 0.8,1.0,1.2
```

Esse modo gera `outputs/convolucao_senoides_com_convolucao.mp4` e
`outputs/comparacao_senoides.png`. A legenda identifica o multiplicador de
`omega_ref` e a frequencia angular correspondente. A entrada nao e a soma das
senoides: o processamento individual facilita observar a variacao de ganho,
fase e proximidade da ressonancia. No painel superior sao mostrados a entrada,
 a resposta ao impulso deslocada, o produto e a area da convolucao; no painel
inferior, a resposta atual e as respostas das senoides anteriores.
O MP4 tambem inclui um terceiro painel com o diagrama de Bode completo. Cada
senoide acrescenta pontos scatter de magnitude e fase nas suas frequencias, e
as curvas teoricas permanecem visiveis para comparacao.

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
python convolution_animation.py --input-name unit_step
ffprobe -v error -select_streams v:0 -count_frames `
  -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames,duration `
  -of default=noprint_wrappers=1 outputs/convolucao_animada.mp4
```

Ultima validacao local registrada:

```text
testes = 45 passed
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
