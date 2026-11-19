# Relatório final — experimentos do integrante 4

Projeto acadêmico `fakenews_distribuidos`. Este relatório analisa exclusivamente
a bateria oficial identificada em 18/11/2026, às 21:16:56, no fuso
`America/Sao_Paulo` (19/11/2026, 00:16:56 UTC). A auditoria leu os resultados
existentes; não repetiu simulações nem alterou CSVs ou gráficos.

## 1. Objetivo

Comparar correção e desempenho das implementações oficiais sequencial, paralela
com threads e distribuída com processos e sockets TCP. Avaliar como os tempos,
o speedup e a eficiência variam com a quantidade de trabalhadores, mantendo
fixos cenário, entrada, ambiente e política de medição em cada comparação.

## 2. Ambiente experimental

| Item | Ambiente da coleta |
| --- | --- |
| Sistema | Linux Mint 22.1 (Xia), x86_64 |
| Kernel registrado no CSV | Linux 6.8.0-137-generic |
| Interpretador | CPython 3.12.3 |
| Processador | Intel Core i5-12400F, 12ª geração |
| Núcleos físicos / lógicos | 6 / 12 |
| RAM total reportada pelo sistema | 16.589.127.680 bytes |
| Hosts | Uma máquina física; comunicação em `127.0.0.1` |
| Ambiente virtual | `~/Projetos/.venvs/fakenews-distribuidos` |

O Linux Mint é identificado no [registro de ambiente](AMBIENTE_EXPERIMENTAL.md)
e em `/etc/os-release`; o campo `sistema` do CSV registra a plataforma Linux.
Modelo da CPU, topologia física e RAM foram coletados de `/proc/cpuinfo`,
`/sys/devices/system/cpu` e `os.sysconf`, respectivamente. A RAM indicada é total,
não memória livre durante cada amostra. Os 12 contextos lógicos compartilham os
seis núcleos físicos e não equivalem a 12 núcleos independentes.

O HEAD registrado é `95afeaae318cd36cdd99db926a635d59fed624bb`. Esse identificador
aponta para a revisão de base; o campo `codigo` também registra os hashes das
fontes efetivamente carregadas da árvore de trabalho, incluindo o benchmark e,
na distribuída, `worker.py`. A auditoria conferiu esses hashes contra os arquivos
da entrega. Portanto, o HEAD isolado não substitui a identidade das fontes.

## 3. Metodologia

| Parâmetro | Configuração |
| --- | --- |
| Versões oficiais na CLI | `sequencial`, `paralela`, `distribuida` |
| Matrizes | 100×100, 300×300 e 500×500 |
| Frações iniciais solicitadas | 0,05 e 0,40, equivalentes a 5% e 40% |
| Limite de gerações | 50 |
| Limiar / semente | 3 / 42 |
| Trabalhadores efetivos | Sequencial: 1; demais versões: 1, 2, 4 e 6 |
| Repetições por configuração | 3 |

Cada combinação de matriz e percentual constitui um dos seis cenários. São
nove configurações por cenário: uma sequencial, quatro paralelas e quatro
distribuídas. Assim, `6 × 9 × 3 = 162` medições, sendo 18 sequenciais, 72 paralelas
e 72 distribuídas. O sequencial tem somente uma configuração por cenário;
`sequencial_provisorio` e `sequencial_candidato` não participam desta bateria.

Para cada cenário, o benchmark cria uma única grade inicial fora do cronômetro.
Todas as versões e repetições recebem cópias profundas independentes dessa
grade. A geração usa sorteios com reposição: as frações são solicitadas, e não
uma garantia de igual quantidade de células distintas sorteadas.

A regra usa vizinhança de Moore sem contorno periódico e atualização simultânea.
O benchmark confronta a matriz final completa com uma referência baseada em
`FakeNews.py`, verifica contagens finais e preservação da entrada e interrompe a
coleta se detectar divergência. Essas verificações ocorrem fora da medição.
A referência compartilha a regra original do professor; não é uma segunda
implementação independente dessa regra.

### Gerações efetivamente executadas

O limite de 50 não foi atingido: todos os tamanhos executaram **três gerações
com 5% e cinco com 40%**, encerrando com zero espalhadores. Em cada cenário,
versões, trabalhadores e repetições concordaram nas gerações e contagens finais.

A função cronometrada do sequencial é a própria `sequencial.simular`, sem
instrumentação. Sua contagem vem de uma **execução diagnóstica determinística
equivalente**, realizada depois de todas as medições do cenário. Nela, conta-se
diretamente cada chamada à `proxima_geracao` original por uma substituição
temporária no namespace de `simular`, restaurada em `finally`. A matriz é
confrontada com a execução cronometrada, e a contagem com a referência. O campo
não é inferido da matriz, do limite ou da referência e não representa uma
instrumentação individual de cada amostra cronometrada.

A paralela informa gerações por `simular_com_detalhes`; a distribuída, por
`simular_com_estatisticas`. Comparações entre versões usam sempre o mesmo
cenário e número efetivo de gerações. Diferenças entre 5% e 40% envolvem também
número de atualizações e composição dos estados; seus tempos não isolam apenas
o efeito do percentual inicial.

## 4. Política de cronometragem

A política registrada é `chamada_completa_v1_workers_tcp_preiniciados`.
`time.perf_counter()` mede a chamada completa ao adaptador da função oficial,
incluindo cópias e validações internas da implementação, evolução, decisão de
parada e retorno.

Na paralela, a medição inclui criação dos pools/threads a cada geração,
sincronização e encerramento. Na distribuída, seis processos workers locais
foram iniciados antes das medições nas portas 5000–5005 e ficaram disponíveis
entre chamadas. Cada configuração usa apenas os primeiros p workers. Entram no
tempo distribuído abertura de conexões, serialização, transmissão das faixas e
fronteiras, processamento, recepção, sincronização, decisão global de parada,
mensagens e confirmações de encerramento e fechamento das conexões. Os logs
previstos na implementação permanecem ativos.

Ficam fora do cronômetro: iniciar e desligar os processos workers, criar a grade,
copiar a entrada pelo benchmark, carregar módulos e calcular hashes, executar a
referência e o diagnóstico sequencial, validar resultados, coletar metadados,
imprimir o resumo e gravar o CSV. Não houve aquecimento separado. A ordem de
versões e repetições foi fixa, conforme o benchmark.

Essa comparação mede o custo das chamadas nas condições documentadas. Ela não
estima o tempo total de uma aplicação distribuída que precise iniciar todos os
processos a cada simulação. Os seis processos próprios foram encerrados após a
coleta; processos preexistentes não foram encerrados.

## 5. Auditoria dos resultados e dos gráficos

**Auditoria aprovada**, sem inconsistência material identificada.

| Item conferido | Resultado |
| --- | --- |
| Medições brutas válidas | 162 |
| Grupos descritivos | 54, cada um com três amostras |
| Baselines oficiais | 6 sequenciais, um por cenário |
| Comparações oficiais | 48: 24 paralelas e 24 distribuídas |
| Duplicatas, repetições ausentes ou valores inválidos | Nenhum identificado |
| Cenários e trabalhadores | Todas as configurações solicitadas, repetições 1, 2 e 3 |
| Indicadores de consistência e entrada preservada | `True` nas 162 linhas |
| Metadados e política de tempo | Completos e compatíveis nas comparações |
| Gráficos oficiais | 30: 18 de tempo, 6 de speedup e 6 de eficiência |

Todas as linhas dos três CSVs foram lidas. Médias, medianas, mínimos, máximos e
desvios amostrais foram recalculados dos tempos brutos, assim como speedup e
eficiência. Valores numéricos foram confrontados com tolerância relativa de
`1e-12` e absoluta de `1e-15`, para acomodar representação em ponto flutuante.
As identidades dos baselines e os campos comuns de cenário, gerações,
contagens, ambiente e política também foram conferidos em cada comparação.
Somente a coleta oficial foi usada; os resultados históricos ficaram separados.

Os 30 arquivos PNG foram decodificados e comparados pixel a pixel com figuras
reconstruídas **somente em memória** pelo analisador a partir dos CSVs auditados.
Todos coincidiram. Nenhum PNG foi gravado novamente e nenhuma simulação foi
executada nesta auditoria. Os CSVs não armazenam as matrizes: a igualdade célula
por célula foi verificada durante a coleta pelo benchmark, enquanto esta
auditoria confere os registros, as fontes identificadas e sua consistência.

Para identificar o conjunto bruto auditado, seu SHA-256 é:

```text
327ea954b6e441812d8b9cd8331b4e9e9142b0df56e64c0bfc438c918447dd94
```

## 6. Resultados principais

Para cada cenário, usando médias de três repetições em segundos:

```text
S(p) = T_seq / T_p
E(p) = S(p) / p
```

O baseline é o sequencial oficial do mesmo cenário. `S > 1` indica redução do
tempo médio; `S < 1`, aumento. A eficiência é uma razão, apresentada abaixo como
percentual. Seu denominador conta os trabalhadores; na distribuída, o
coordenador é um processo adicional e não entra em p.

A tabela fixa p=6 nas versões concorrentes para mostrar todos os seis cenários
com a mesma quantidade máxima solicitada. Os CSVs preservam também p=1,2,4 e a
dispersão das amostras. Os arredondamentos abaixo não foram usados nos cálculos.

| Matriz | Inicial | T_seq (s) | T_par,6 (s) | S_par,6 | E_par,6 | T_dist,6 (s) | S_dist,6 | E_dist,6 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100×100 | 5% | 0,021323 | 0,024286 | 0,878 | 14,63% | 0,008575 | 2,487 | 41,44% |
| 100×100 | 40% | 0,020984 | 0,024051 | 0,872 | 14,54% | 0,008822 | 2,379 | 39,64% |
| 300×300 | 5% | 0,199718 | 0,209771 | 0,952 | 15,87% | 0,071706 | 2,785 | 46,42% |
| 300×300 | 40% | 0,184143 | 0,192155 | 0,958 | 15,97% | 0,066524 | 2,768 | 46,13% |
| 500×500 | 5% | 0,599348 | 0,610675 | 0,981 | 16,36% | 0,196174 | 3,055 | 50,92% |
| 500×500 | 40% | 0,530294 | 0,545571 | 0,972 | 16,20% | 0,226895 | 2,337 | 38,95% |

Para examinar escalabilidade sem juntar cenários, os speedups distribuídos são:

| Matriz | Inicial | S(1) | S(2) | S(4) | S(6) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 100×100 | 5% | 0,913 | 1,592 | 2,587 | 2,487 |
| 100×100 | 40% | 0,971 | 1,567 | 2,183 | 2,379 |
| 300×300 | 5% | 0,897 | 1,706 | 2,696 | 2,785 |
| 300×300 | 40% | 0,952 | 1,712 | 2,490 | 2,768 |
| 500×500 | 5% | 0,936 | 1,871 | 2,725 | 3,055 |
| 500×500 | 40% | 0,938 | 1,757 | 2,071 | 2,337 |

## 7. Discussão

### Threads e GIL

Considerando todas as configurações paralelas, o speedup observado variou de
0,872 a 1,010. Com seis threads, ficou abaixo de um nos seis cenários. Assim,
esta implementação não apresentou aceleração substancial ao aumentar threads
para o cálculo das gerações.

No CPython 3.12, o GIL permite que somente uma thread de um processo execute
código Python por vez, ressalvadas operações que liberam esse bloqueio. Essa
característica limita o paralelismo de cálculo intensivo em Python, como os
laços desta simulação. [Documentação oficial de threading no Python 3.12](https://docs.python.org/3.12/library/threading.html).

A [implementação paralela](../paralelo.py) ainda cria pools por geração e usa
barreiras. GIL e custos de criação, sincronização e gerenciamento são explicações
compatíveis com os tempos observados. Esta é uma interpretação, não uma medição
isolada desses custos: não foram coletados perfis de CPU ou tempos por etapa.
Ganhos de aproximadamente 1% próximos da unidade, em algumas configurações,
não demonstram significância estatística com este desenho experimental.

### Processos, sockets e overhead

Workers em processos distintos permitem distribuir o cálculo sem depender do
mesmo GIL para todos eles. O uso de subprocessos para contornar essa limitação
é descrito na [documentação oficial sobre paralelismo com processos](https://docs.python.org/3.12/library/multiprocessing.html#introduction).
Na implementação avaliada, os processos comunicam-se por sockets TCP em
localhost e o coordenador reúne as regiões antes de avançar a geração.

Com um worker, todos os speedups distribuídos ficaram abaixo de um, entre 0,897
e 0,971. Com dois, quatro e seis, ficaram acima de um nos cenários medidos.
Isso é compatível com um custo adicional de comunicação e coordenação que
passa a ser compensado pela divisão do cálculo. O total cronometrado não
permite atribuir valores separados a serialização JSON, transmissão, espera,
cópias e processamento; não se afirma que apenas um deles explique o resultado.

### Escalabilidade e eficiência

Com seis workers, os speedups distribuídos variaram de 2,337 a 3,055 e as
eficiências, de 38,95% a 50,92%. A maior aceleração observada ocorreu em 500×500
com 5%: tempo médio de 0,599348 s no sequencial e 0,196174 s na distribuída.
Esse resultado permanece abaixo de uma aceleração linear de seis vezes.

O aumento de trabalhadores não melhorou todas as médias: em 100×100 com 5%,
quatro workers obtiveram 0,008243 s e seis, 0,008575 s. Essa diferença é uma
observação descritiva da coleta, não uma prova de superioridade estatística
de quatro workers. Para os demais cenários, seis tiveram menor tempo médio
distribuído que quatro, mas os incrementos de speedup foram inferiores aos
incrementos de p.

O coordenador, a troca de faixas e fronteiras, a sincronização e o uso da mesma
CPU e memória são limites plausíveis à escalabilidade. Nenhum deles foi isolado
experimentalmente. Não se estimou uma fração serial nem se extrapolou a curva
para mais trabalhadores ou outras máquinas.

## 8. Limitações

- Há somente três repetições por configuração e uma semente. O resumo conserva
  o desvio amostral, mas não foram realizados testes de hipótese ou intervalos
  de confiança para sustentar diferenças pequenas.
- Todos os processos executaram em uma única máquina. Localhost compartilha
  CPU, memória e sistema operacional; não houve validação entre computadores
  físicos, nem medição de latência ou largura de banda de uma rede externa.
- Os resultados dependem das versões avaliadas e da política de workers
  previamente iniciados. Não incluem o custo de iniciar os processos workers
  e não constituem uma comparação de inicialização completa das arquiteturas.
- A execução não foi aleatorizada, não teve aquecimento separado e não registrou
  frequência efetiva da CPU, temperatura ou carga concorrente por amostra.
- O limite solicitado foi 50, mas as simulações mediram somente três ou cinco
  gerações. Não se podem tratar esses tempos como execuções de 50 atualizações.
- As gerações do sequencial vêm do diagnóstico equivalente, não de contadores
  ativos em cada chamada cronometrada. A auditoria atual não repetiu a comparação
  das matrizes porque elas não estão armazenadas nos CSVs.

## 9. Conclusão

Nas condições observadas, a versão com threads manteve desempenho próximo ou
inferior ao sequencial e não escalou de forma relevante. A distribuída com
processos locais reduziu o tempo médio a partir de dois workers em todos os
cenários avaliados, alcançando speedup máximo de 3,055 com seis workers.

Os resultados apoiam o uso de processos para esta carga em Python, sob a
política e o ambiente estudados, mas evidenciam custos e escalabilidade
sublinear. Não demonstram aceleração proporcional ao número de trabalhadores
nem desempenho equivalente em uma rede entre máquinas. Mais repetições,
outras sementes e experimentos entre computadores seriam necessários para
ampliar essas conclusões.

## 10. Arquivos e gráficos de referência

Os números completos e a dispersão das amostras estão nos arquivos existentes:

- [Medições oficiais: benchmark_oficial.csv](benchmark_oficial.csv).
- [Estatísticas: resumo.csv](analise_oficial/resumo.csv).
- [Speedup e eficiência: comparacoes.csv](analise_oficial/comparacoes.csv).
- [Benchmark utilizado](../benchmark.py), [analisador](../analisar_resultados.py),
  [notas de integração e histórico](benchmark_NOTAS.md) e
  [registro de ambiente](AMBIENTE_EXPERIMENTAL.md).

Cada par abaixo fixa o cenário e mostra p=1,2,4,6 nas séries Paralela e
Distribuída. Os nomes foram conferidos contra os dados e as figuras existentes.

| Matriz | Inicial | Speedup | Eficiência |
| --- | ---: | --- | --- |
| 100×100 | 5% | [speedup_001.png](analise_oficial/speedup_001.png) | [eficiencia_001.png](analise_oficial/eficiencia_001.png) |
| 100×100 | 40% | [speedup_002.png](analise_oficial/speedup_002.png) | [eficiencia_002.png](analise_oficial/eficiencia_002.png) |
| 300×300 | 5% | [speedup_003.png](analise_oficial/speedup_003.png) | [eficiencia_003.png](analise_oficial/eficiencia_003.png) |
| 300×300 | 40% | [speedup_004.png](analise_oficial/speedup_004.png) | [eficiencia_004.png](analise_oficial/eficiencia_004.png) |
| 500×500 | 5% | [speedup_005.png](analise_oficial/speedup_005.png) | [eficiencia_005.png](analise_oficial/eficiencia_005.png) |
| 500×500 | 40% | [speedup_006.png](analise_oficial/speedup_006.png) | [eficiencia_006.png](analise_oficial/eficiencia_006.png) |

Gráficos representativos de tempo para os três tamanhos, fixando 5% e três
gerações: [sequencial, p=1](analise_oficial/media_s_001.png),
[paralela, p=6](analise_oficial/media_s_005.png) e
[distribuída, p=6](analise_oficial/media_s_009.png). Os nove gráficos de tempo
`media_s_001.png` a `media_s_009.png` correspondem a 5%; os nove seguintes,
`media_s_010.png` a `media_s_018.png`, a 40%, sempre mantendo fixos os demais
identificadores de cada curva.

## 11. Reprodução sem o script temporário da coleta

Os comandos abaixo reproduzem os cenários usando diretamente os programas do
repositório. O script temporário usado para orquestrar a coleta original não
é necessário. Esta seção é uma instrução para uma execução futura; nenhum desses
comandos de simulação foi executado na elaboração deste relatório.

### Preparar o ambiente e conferir a CLI

No terminal do coordenador, a partir da instalação existente:

```bash
cd ~/Projetos/fakenews_distribuidos
source ~/Projetos/.venvs/fakenews-distribuidos/bin/activate
python --version
python -B benchmark.py --help
python -B analisar_resultados.py --help
unset FAKENEWS_WORKERS
```

Usar o mesmo ambiente virtual nos terminais dos workers. O interpretador deve
ser Python 3.12.3; Matplotlib já está presente nesse ambiente. Não há etapa de
instalação. `FAKENEWS_WORKERS` ausente seleciona 127.0.0.1 e as portas padrão,
permitindo variar p na mesma chamada.

Antes de iniciar qualquer worker, conferir as seis portas no coordenador:

```bash
python -B - <<'PY'
from contextlib import ExitStack
import socket

with ExitStack() as recursos:
    for porta in range(5000, 5006):
        servidor = recursos.enter_context(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        )
        servidor.bind(("127.0.0.1", porta))
print("Portas 5000 a 5005 disponíveis.")
PY
```

Se houver erro, interromper o procedimento e identificar o conflito. Não
encerrar processos preexistentes para liberar portas. A checagem libera as
reservas ao terminar; ainda é necessário confirmar a inicialização de cada
worker a seguir.

### Iniciar seis workers

Abrir seis terminais na raiz do projeto, ativar o ambiente virtual em cada um
como acima e executar **uma linha em cada terminal**, respectivamente:

```bash
python -B -u worker.py --host 127.0.0.1 --porta 5000
python -B -u worker.py --host 127.0.0.1 --porta 5001
python -B -u worker.py --host 127.0.0.1 --porta 5002
python -B -u worker.py --host 127.0.0.1 --porta 5003
python -B -u worker.py --host 127.0.0.1 --porta 5004
python -B -u worker.py --host 127.0.0.1 --porta 5005
```

Aguardar `Worker disponível em 127.0.0.1:PORTA` em todos os terminais antes de
medir. Os workers permanecem em primeiro plano e são reutilizados entre chamadas.
Na coleta original, sua saída foi direcionada a logs temporários; neste roteiro
ela fica visível nos terminais. O destino dos logs e a carga do sistema podem
afetar tempos, embora os cenários e a região cronometrada sejam os mesmos.

### Reexecutar a bateria preservando a entrega

A CLI original usou `--saida resultados/benchmark_oficial.csv`, seguida do
analisador com `--saida resultados/analise_oficial`. Como esses destinos já
existem, as ferramentas recusam reutilizá-los. Para uma nova rodada com a mesma
configuração, escolher destinos novos e manter as variáveis no mesmo terminal:

```bash
rodada=$(date -u +%Y%m%dT%H%M%S)
csv_reexecucao="resultados/benchmark_oficial_reexecucao_${rodada}.csv"
analise_reexecucao="resultados/analise_oficial_reexecucao_${rodada}"

python -B benchmark.py \
  --versoes sequencial paralela distribuida \
  --tamanhos 100x100 300x300 500x500 \
  --percentuais 0.05 0.40 \
  --geracoes 50 --limiar 3 --semente 42 \
  --repeticoes 3 --trabalhadores 1 2 4 6 \
  --saida "$csv_reexecucao" &&
python -B analisar_resultados.py "$csv_reexecucao" \
  --saida "$analise_reexecucao"
```

Se a coleta falhar, interromper e examinar o erro; não analisar um arquivo
parcial. A sequência usa `&&` para executar o analisador somente após sucesso
do benchmark. Ela produz uma nova coleta de 162 medições, cujo tempo pode variar;
não se espera igualdade exata dos tempos entre rodadas.

Para reproduzir **somente a análise dos dados oficiais existentes**, sem nova
simulação e sem workers, usar uma pasta nova:

```bash
python -B analisar_resultados.py resultados/benchmark_oficial.csv \
  --saida "resultados/analise_oficial_reproduzida_$(date -u +%Y%m%dT%H%M%S)"
```

Esse comando gera resumo, comparações e PNGs a partir de um único CSV, sem
misturar medições históricas. Se o destino já existir, escolher outro nome.

### Encerrar os workers

Ao terminar a coleta, ou em caso de erro, pressionar **Ctrl+C em cada um dos seis
terminais dos próprios workers**. Isso envia SIGINT, tratado pelo worker como
`KeyboardInterrupt`, e encerra esses processos. A mensagem TCP `encerrar` termina
apenas a conexão da simulação e não desliga o servidor worker. Não usar comandos
que encerrem todos os processos Python ou serviços preexistentes.

Apoio de IA: Codex na auditoria e redação. Todos os resultados numéricos deste
relatório derivam dos CSVs oficiais preservados.
