# Ambiente experimental

## Especificações do ambiente

Este documento registra o ambiente local do integrante 4 para os testes do projeto `fakenews_distribuidos`. As especificações abaixo foram fornecidas pelo integrante como verificadas no Linux Mint; esta documentação não representa uma nova coleta automática nem altera os metadados dos CSVs existentes.

| Item | Especificação |
| --- | --- |
| Processador | Intel Core i5-12400F (12ª geração) |
| Núcleos físicos | 6 |
| Processadores lógicos | 12 |
| Threads por núcleo | 2 |
| Frequência máxima informada pelo `lscpu` | 4,4 GHz |
| Memória RAM utilizável informada pelo `free -h` | 15 GiB |
| Sistema operacional | Linux Mint 22.1 (Xia) |
| Arquitetura | x86_64 |
| Python | 3.12.3 |
| Implementação do Python | CPython |
| Git | 2.43.0 |
| Ambiente de execução | VS Code, terminal local |

Os 15 GiB representam a memória utilizável informada pelo sistema, não a quantidade de memória livre em cada execução. A frequência de 4,4 GHz é o máximo informado pelo `lscpu`, não uma frequência constante durante os testes. A frequência efetiva durante os experimentos não foi coletada.

## Núcleos físicos e processadores lógicos

Núcleos físicos são unidades de execução presentes no processador. Processadores lógicos são os contextos de execução que o sistema operacional pode escalonar. Neste ambiente, cada um dos seis núcleos físicos oferece dois contextos, totalizando 12 processadores lógicos.

Os dois contextos de um mesmo núcleo compartilham recursos de execução. Portanto, 12 processadores lógicos não correspondem a 12 núcleos físicos independentes nem garantem o dobro do desempenho de seis núcleos. O número de trabalhadores deve ser registrado em cada experimento, sem presumir aceleração proporcional.

## Paralelismo com threads no CPython

No CPython 3.12, o GIL (Global Interpreter Lock) permite que apenas uma thread por vez execute bytecode Python dentro de um mesmo processo. Assim, a futura versão com `threading` pode não acelerar o cálculo das gerações, que realiza operações intensivas em CPU em Python. A criação e a coordenação das threads também podem aumentar o tempo total.

A análise deve considerar os tempos medidos, inclusive quando houver perda de desempenho. A quantidade de threads não demonstra, por si só, execução simultânea do cálculo em vários núcleos.

## Execução distribuída e custos dos trabalhadores

Testes distribuídos executados somente em `localhost` usam a mesma máquina física e compartilham CPU, memória e recursos do sistema operacional. Eles permitem avaliar funcionamento e custos locais, mas não equivalem a experimentos entre máquinas físicas diferentes.

Processos e workers podem introduzir custos de inicialização, sincronização e comunicação, incluindo criação de processos, estabelecimento de conexões, serialização, transferência de dados, espera por resultados e encerramento. Esses custos devem ser considerados na interpretação das medições.

Ainda não foram documentados experimentos entre máquinas físicas diferentes neste registro. Não foram coletadas velocidade da rede, configuração de outros hosts ou especificações da GPU.

## Política de medição uniforme

As versões devem ser comparadas com uma política uniforme de cronometragem, explicitando quais etapas entram no tempo. Tempos totais que incluem inicialização e encerramento não devem ser misturados com tempos obtidos com trabalhadores previamente preparados. Se ambos forem medidos, devem ser identificados e analisados separadamente.

Na primeira versão de `benchmark.py`, `time.perf_counter()` mede somente a chamada ao executor sequencial provisório. O intervalo inclui a evolução das gerações, alocações internas, contagens para a parada e retorno. Geração e cópia da entrada, execução de referência, validações, coleta do ambiente, impressões e exportação CSV ficam fora da região medida. Não há aquecimento separado.

Antes de integrar as versões paralela e distribuída, a equipe deve definir como essa política tratará criação de threads/processos, conexões e encerramento. Este documento não afirma que essas versões já foram medidas. O detalhamento do benchmark atual está em [benchmark_NOTAS.md](benchmark_NOTAS.md).

## Condições do sistema e registro dos resultados

Processos em segundo plano, carga concorrente, disponibilidade de memória e condições térmicas ou de energia podem causar variações entre repetições. Cada conjunto de resultados deve registrar as condições observadas e possíveis interferências, sem atribuir uma causa específica sem evidência.

Registrar os parâmetros, a semente, o número de repetições, os trabalhadores, as gerações efetivamente executadas, o código utilizado e a política de tempo. Preservar as medições individuais para analisar sua dispersão. Quando disponíveis, acrescentar observações sobre aplicações abertas e carga do sistema durante a coleta.

Não foram coletados neste documento a frequência real durante as execuções, temperaturas, carga de processos em segundo plano ou condições de energia. A data e as condições de cada experimento devem acompanhar seus próprios resultados. Os metadados coletados automaticamente no CSV devem ser conferidos antes de associá-lo a este ambiente.
