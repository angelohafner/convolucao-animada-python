# Contexto do projeto

## Objetivo de engenharia

Converter e evoluir um exemplo MATLAB de convolucao para Python, gerando um MP4
didatico e mantendo a estrutura facil de estender.

Repositorio publico:

```text
https://github.com/angelohafner/convolucao-animada-python
```

## Caso padrao ativo

- O comando `python convolution_animation.py` gera todos os casos em lote.
- A ordem do lote e: impulso, degrau, rampa e todas as senoides.
- Para validar o caso padrao isolado, use `--input-name unit_step`.
- Entrada do caso padrao isolado: `unit_step`, com `x(t) = u(t)`.
- Sistema: `second_order_underdamped`.
- Razao de amortecimento: `zeta = 0.1`.
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

## Escala comum para casos senoidais

Todos os casos com entrada senoidal compartilham os mesmos limites verticais nos
graficos. Os limites sao calculados a partir do caso `sine_1_0_resonance`, que
representa a entrada em `1.0 * omega_ref`.

Essa regra vale para o painel superior da animacao, para o painel inferior da
animacao e para a figura PNG de comparacao. O objetivo e permitir comparacao
visual direta entre as frequencias `0.7` a `1.3` vezes a frequencia de
referencia.

## Criterio de impulso numerico

O impulso unitario e aproximado no indice mais proximo de `t = 0`:

```text
x[k0] = 1 / dt
sum(x) * dt = 1
```

Esse criterio preserva a area unitaria na aproximacao retangular usada pela
convolucao numerica.

## Representacao visual do impulso

O impulso numerico nao e desenhado com amplitude `1/dt` no painel superior da
animacao. Essa amplitude e muito alta e comprime visualmente `h(t - tau)`.

Para manter a interpretacao didatica, o impulso e desenhado como uma seta
vertical em `x = 0`, saindo de `y = 0` e com cabeca em `y = 1`. Essa escolha e
apenas grafica; o calculo da convolucao continua usando o vetor numerico com
area unitaria.

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

Para os parametros atuais, `zeta = 0.1 < 1/sqrt(2)`, portanto o criterio usado
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

## Sequencia de senoides

O modo `--sine-sequence` calcula uma senoide por vez e sobrepoe as respostas no
painel inferior. A lista padrao e `0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3` vezes
`omega_ref`, podendo ser substituida com `--sine-multipliers`. As senoides nao
sao somadas entre si; essa escolha permite ao aluno associar cada resposta a
uma frequencia especifica. Os arquivos gerados sao
`outputs/convolucao_senoides_com_convolucao.mp4` e
`outputs/comparacao_senoides.png`. No painel superior, a animacao mostra
`x(tau)`, `h(t-tau)`, o produto e a area integrada; no painel inferior, a
resposta atual e as respostas anteriores permanecem visiveis.

## Artefatos gerados

- `outputs/01_unit_impulse/convolucao_animada.mp4`.
- `outputs/02_unit_step/convolucao_animada.mp4`.
- `outputs/03_unit_ramp/convolucao_animada.mp4`.
- `outputs/04_sine_0_7_resonance/convolucao_animada.mp4`.
- `outputs/05_sine_0_8_resonance/convolucao_animada.mp4`.
- `outputs/06_sine_0_9_resonance/convolucao_animada.mp4`.
- `outputs/07_sine_1_0_resonance/convolucao_animada.mp4`.
- `outputs/08_sine_1_1_resonance/convolucao_animada.mp4`.
- `outputs/09_sine_1_2_resonance/convolucao_animada.mp4`.
- `outputs/10_sine_1_3_resonance/convolucao_animada.mp4`.
- Cada subpasta tambem recebe `comparacao_numerica_analitica.png`.
- `outputs/convolucao_animada.mp4` e `outputs/comparacao_numerica_analitica.png`
  continuam sendo usados quando `--input-name` gera um caso isolado.
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
python convolution_animation.py --input-name unit_step
ffprobe -v error -select_streams v:0 -count_frames `
  -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames,duration `
  -of default=noprint_wrappers=1 outputs/convolucao_animada.mp4
```

## Resultados de validacao

- Testes automatizados: `45 passed`.
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
- Sem `--input-name`, `python convolution_animation.py` gera todos os casos na
  ordem solicitada: impulso, degrau, rampa e senoides.
- Para trocar o sistema ativo, use
  `AnimationConfig(transfer_function_name="...")` ou
  `python convolution_animation.py --transfer-function-name ...`.
- Ao criar uma nova entrada, use um arquivo proprio em `inputs/` e registre em
  `inputs/registry.py`.
- Ao criar uma nova funcao de transferencia, use um arquivo proprio em
  `transfer_functions/` e registre em `transfer_functions/registry.py`.
- Ao adicionar um sistema sem frequencia de ressonancia, documente o fallback
  `omega_ref = wn`.
