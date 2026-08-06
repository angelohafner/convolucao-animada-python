# Contexto do projeto

## Objetivo de engenharia

Converter e evoluir um exemplo MATLAB de convolucao para Python, gerando um MP4
didatico e mantendo a estrutura facil de estender.

Repositorio publico:

```text
https://github.com/angelohafner/convolucao-animada-python
```

## Caso padrao ativo

- Entrada: `unit_step`, com `x(t) = u(t)`.
- Sistema: `second_order_underdamped`.
- Razao de amortecimento: `zeta = 0.2`.
- Frequencia natural: `wn = 2 rad/s`.
- Frequencia amortecida: `wd = wn * sqrt(1 - zeta^2)`.
- Frequencia de referencia usada pelas senoides: `omega_ref = 1.91833261 rad/s`.
- Origem da frequencia de referencia: ressonancia real do sistema.
- Janela temporal: `-10 s` a `20 s`.
- Passo numerico: `dt = 0.01 s`.

## Organizacao do codigo

- `convolution_animation.py`: configuracao, calculo da convolucao, comparacao
  analitica, figura estatica, animacao MP4 e interface de linha de comando.
- `.gitignore`: exclui caches Python, `.pytest_cache` e ambientes virtuais.
- `inputs/`: biblioteca de entradas, com um arquivo por sinal.
- `transfer_functions/`: biblioteca de sistemas, com um arquivo por funcao de
  transferencia/resposta ao impulso.
- `tests/test_convolution_animation.py`: testes de sinais, ressonancia, selecao,
  calculo numerico, figura e MP4.

## Entradas implementadas

- `unit_step`: degrau unitario.
- `unit_impulse`: impulso numerico de area unitaria.
- `unit_ramp`: rampa unitaria causal.
- `sine_0_7_resonance`: seno puro com `0.7 * omega_ref`.
- `sine_0_8_resonance`: seno puro com `0.8 * omega_ref`.
- `sine_0_9_resonance`: seno puro com `0.9 * omega_ref`.
- `sine_1_0_resonance`: seno puro com `1.0 * omega_ref`.
- `sine_1_1_resonance`: seno puro com `1.1 * omega_ref`.
- `sine_1_2_resonance`: seno puro com `1.2 * omega_ref`.
- `sine_1_3_resonance`: seno puro com `1.3 * omega_ref`.

## Criterio de impulso numerico

O impulso unitario e aproximado no indice mais proximo de `t = 0`:

```text
x[k0] = 1 / dt
sum(x) * dt = 1
```

Esse criterio preserva a area unitaria na aproximacao retangular usada pela
convolucao numerica.

## Criterio de ressonancia

Para o sistema padrao:

```text
H(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
```

A frequencia de ressonancia existe quando:

```text
zeta < 1 / sqrt(2)
```

Quando existe:

```text
omega_ref = omega_r = wn * sqrt(1 - 2*zeta^2)
```

Quando nao existe:

```text
omega_ref = wn
```

Para os parametros atuais, `zeta = 0.2 < 1/sqrt(2)`, portanto o criterio usado
foi a frequencia de ressonancia real, nao o fallback.

## Metodo numerico

`numpy.convolve` calcula a convolucao completa. O resultado e multiplicado por
`dt` para aproximar a integral e interpolado de volta para o eixo temporal
original com valor zero fora do suporte calculado.

## Interpretacao da animacao

O painel superior mantem `x(tau)` fixo, desloca `h(t - tau)` e preenche a area
assinada do produto `x(tau) * h(t - tau)`. O painel inferior revela `y(t)` ate o
instante atual.

Quando a entrada ativa e `unit_step` e o sistema ativo e
`second_order_underdamped`, a resposta analitica ao degrau tambem e exibida.
Para outras entradas, a resposta analitica nao e exibida.

## Artefatos gerados

- `outputs/convolucao_animada.mp4`.
- `outputs/comparacao_numerica_analitica.png`.
- `outputs/validation_frames/frame_start.png`.
- `outputs/validation_frames/frame_middle.png`.
- `outputs/validation_frames/frame_end.png`.

## Ambiente validado

- Windows com PowerShell.
- Python 3.13.5.
- NumPy 2.4.2.
- Matplotlib 3.10.8.
- pytest 9.0.2.
- FFmpeg 8.0.1.
- ffprobe 8.0.1.

## Comandos de validacao

```powershell
python -m pytest -q
python -m compileall convolution_animation.py inputs transfer_functions tests
python convolution_animation.py
ffprobe -v error -select_streams v:0 -count_frames `
  -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames,duration `
  -of default=noprint_wrappers=1 outputs/convolucao_animada.mp4
```

## Resultados de validacao

- Testes automatizados: `39 passed`.
- Erro absoluto maximo do caso padrao: `0.00752794`.
- Raiz do erro quadratico medio do caso padrao: `0.00143955`.
- Codec: `h264`.
- Formato de pixel: `yuv420p`.
- Dimensoes: `1400 x 900`.
- Taxa de quadros: `25/1` fps.
- Duracao: `6.080000 s`.
- Quadros lidos por ffprobe: `152`.

## Publicacao no GitHub

- Repositorio: `https://github.com/angelohafner/convolucao-animada-python`.
- Visibilidade solicitada: publico.
- Branch principal: `main`.
- Remote local: `origin`.

## Notas para extensao

- Para trocar a entrada ativa, use `AnimationConfig(input_name="...")` ou
  `python convolution_animation.py --input-name ...`.
- Para trocar o sistema ativo, use
  `AnimationConfig(transfer_function_name="...")` ou
  `python convolution_animation.py --transfer-function-name ...`.
- Ao criar uma nova entrada, use um arquivo proprio em `inputs/` e registre em
  `inputs/registry.py`.
- Ao criar uma nova funcao de transferencia, use um arquivo proprio em
  `transfer_functions/` e registre em `transfer_functions/registry.py`.
- Ao adicionar um sistema sem frequencia de ressonancia, documente o fallback
  `omega_ref = wn`.
