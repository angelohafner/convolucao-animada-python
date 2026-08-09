# Design: Sequencial de senoides e respostas sobrepostas

## Objetivo

Evoluir a animacao de convolucao para apresentar varias senoides em uma unica execucao. Cada senoide sera processada individualmente e sua resposta sera adicionada ao grafico inferior, permitindo comparar no dominio do tempo como a amplitude e a fase variam com a frequencia.

## Escopo funcional

- Manter os casos existentes de impulso, degrau, rampa e senoide individual.
- Adicionar um modo de sequencia senoidal configuravel por uma lista de multiplicadores de `omega_ref`.
- Calcular uma entrada e uma resposta de convolucao para cada frequencia, sem somar as entradas entre si.
- Animar os casos em ordem, preservando as respostas anteriores no painel de saida.
- Destacar o caso atual e identificar cada frequencia na legenda e no painel de status.
- Gerar uma figura final com todas as respostas sobrepostas.
- Permitir selecionar o modo por linha de comando sem quebrar `--input-name`.

## Arquitetura

O dominio numerico sera separado da animacao. Uma nova estrutura de caso senoidal armazenara o multiplicador, a frequencia absoluta, o sinal de entrada, a resposta e os metadados de exibicao. Uma funcao de calculo de sequencia reutilizara `get_input_signal` e `compute_convolution`, garantindo que a convencao numerica atual permaneca unica.

O modo individual continuara usando `calculate_default_case`. O modo sequencial tera uma rotina propria para construir a lista de resultados e uma rotina de animacao que usa o indice do caso atual e o indice do frame para revelar a resposta corrente, mantendo as curvas anteriores visiveis.

## Interface e CLI

O fluxo existente continuara disponivel. Sera acrescentado um modo explicito para a sequencia senoidal, com valores padrao equivalentes aos casos existentes: `0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3`. A entrada textual sera validada: a lista nao pode ser vazia, deve conter frequencias positivas e nao deve conter valores nao finitos.

## Saidas

- Um MP4 dedicado ao modo sequencial.
- Uma PNG final com todas as respostas sobrepostas.
- Legenda com frequencia relativa e frequencia angular em rad/s.
- Documentacao dos comandos, da convencao de processamento e das limitacoes didaticas.

## Testes e validacao

Serao adicionados testes para validar a lista padrao, a conversao para frequencia absoluta, a preservacao da ordem, a igualdade entre cada resposta sequencial e o calculo individual correspondente, a rejeicao de entradas invalidas e a criacao da figura/animacao. A suite existente sera executada junto com compilacao Python e verificacao do MP4 com `ffprobe`.

## Decisoes e limites

- As senoides permanecem sinais puros de amplitude unitaria, conforme a implementacao atual.
- Cada resposta e calculada separadamente; nao havera superposicao fisica das entradas no sinal de convolucao.
- A resposta anterior permanece visivel para comparacao, enquanto a resposta atual pode ser destacada visualmente.
- Os arquivos modificados anteriormente no diretorio de trabalho serao preservados.
