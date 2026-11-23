# Reteste completo das versões corrigidas

Coleta de 19/11/2026, iniciada às 20:27:38 no fuso America/Sao_Paulo (23:27:38 UTC). Todas as três versões foram medidas nesta mesma máquina. Este conjunto substitui as conclusões sobre desempenho da revisão corrigida; os arquivos anteriores continuam preservados como histórico e não foram combinados com estes dados.

## Resultado da validação

- **40 testes automatizados aprovados**, incluindo regressões e sockets TCP reais. Registro completo: [testes.log](testes.log).
- **486 medições válidas**, com matriz final completa igual à referência, entrada preservada e gerações executadas conferidas durante cada medição (para o sequencial, diagnóstico após as amostras do cenário).
- **162 grupos estatísticos**, com três repetições por configuração.
- **144 comparações de speedup e eficiência** e **90 gráficos PNG** (54 de tempo, 18 de speedup e 18 de eficiência).
- Auditoria posterior: conferência de repetições 1/2/3, médias, medianas, mínimos, máximos, desvios amostrais, speedup e eficiência, com tolerância relativa 1e-12; hashes das fontes executadas conferidos; todos os PNGs decodificados sem erros. Dois gráficos de speedup representativos também foram inspecionados visualmente.

## Ambiente

| Item | Valor |
| --- | --- |
| CPU | AMD Ryzen 7 5700X 8-Core Processor |
| Núcleos físicos / processadores lógicos | 8 / 16 |
| RAM física total visível ao Windows | 34.240.208.896 bytes (aproximadamente 31,89 GiB) |
| Sistema | Windows-11-10.0.26300-SP0, x64 |
| Linguagem / interpretador | Python / CPython 3.14.6, GIL habilitado |
| Hosts | 1 computador; comunicação em 127.0.0.1 |
| Workers TCP | 8 processos próprios, previamente iniciados nas portas 5000–5007 |
| Ambiente de execução | venv-benchmark, na pasta irmã do projeto |
| Gráficos | Matplotlib 3.11.2; dependências em requirements-graficos.txt |

O coletor Windows usa GetLogicalProcessorInformationEx para núcleos e GlobalMemoryStatusEx para a RAM total visível, além do registro para identificar a CPU. Não foi deduzida a quantidade de núcleos físicos a partir dos processadores lógicos. Os programas de simulação usam somente a biblioteca padrão; Matplotlib e suas dependências atuam após a coleta, na geração de gráficos.

O commit de base é `2066c953ae25edd34e55e38e4839de754569cd8a`. As correções ainda não foram commitadas: **o commit sozinho não identifica o código executado**. [ambiente.json](ambiente.json) contém os hashes de todos os arquivos Python e o estado do Git na coleta; [fontes_executadas.zip](fontes_executadas.zip) preserva exatamente essas fontes. Cada medição identifica ainda as fontes relevantes no campo `codigo`.

## Configuração e método

| Parâmetro | Configuração |
| --- | --- |
| Matrizes | 100×100, 300×300, 500×500 |
| Limites de gerações | 1, 2, 5 |
| Frações iniciais solicitadas | 0,05 e 0,40 |
| Limiar / semente | 3 / 42 |
| Trabalhadores | Sequencial: 1; paralela e distribuída: 1, 2, 4, 8 |
| Repetições por configuração | 3 |

São 3 tamanhos × 3 limites × 2 percentuais = 18 cenários. Cada cenário tem nove configurações (uma sequencial, quatro paralelas, quatro distribuídas) e três repetições: **18 × 9 × 3 = 486** medições. A grade de cada cenário é criada uma vez, com sorteios com reposição, e as execuções recebem cópias independentes. Os mesmos parâmetros são usados nas três versões.

`time.perf_counter()` mede somente a chamada completa do executor. Entram evolução, cópias internas, contagem da parada, criação/encerramento das threads e, no distribuído, abertura/fechamento das conexões, serialização, comunicação e sincronização. Ficam fora criação da entrada pelo benchmark, referência, diagnóstico sequencial, validação, coleta de metadados, logs de progresso, CSVs e gráficos. A inicialização dos processos TCP fica fora; seus logs ficam ativos e são direcionados a arquivos. Os workers permanecem vivos entre chamadas e são encerrados ao final pela automação.

A execução foi sequencial por cenário, na ordem fixa sequencial → paralela → distribuída; p crescente, sem aquecimento separado. Não foi imposta afinidade de CPU nem isolada a máquina de aplicativos do usuário. Esses fatores e as três repetições limitam inferências sobre pequenas diferenças de tempo. A eficiência divide o speedup pelos workers efetivos; o processo coordenador é registrado separadamente e não entra nesse denominador.

## Gerações realmente executadas

| Limite | Fração 5% | Fração 40% |
| --- | --- | --- |
| 1 | 1 | 1 |
| 2 | 2 | 2 |
| 5 | 3 | 5 |

Essa tabela foi observada nos três tamanhos e nas três versões. No limite 5 com 5%, a propagação termina na terceira geração. Assim, o experimento varia efetivamente o trabalho, sem interpretar o limite como quantidade garantida de atualizações.

## Tempos representativos e análise

A tabela fixa o limite em 5 e compara o sequencial com as versões de oito trabalhadores. Os valores são médias em segundos; todos os outros p e limites estão nos CSVs.

| Matriz | Fração | Gerações reais | Sequencial (s) | Threads p=8 (s) | TCP p=8 (s) | Speedup TCP | Eficiência TCP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 100×100 | 5% | 3 | 0.047940 | 0.053444 | 0.017327 | 2.767 | 34.58% |
| 100×100 | 40% | 5 | 0.044638 | 0.047281 | 0.024658 | 1.810 | 22.63% |
| 300×300 | 5% | 3 | 0.433172 | 0.446942 | 0.108243 | 4.002 | 50.02% |
| 300×300 | 40% | 5 | 0.338705 | 0.348670 | 0.098735 | 3.430 | 42.88% |
| 500×500 | 5% | 3 | 1.218981 | 1.276914 | 0.267701 | 4.554 | 56.92% |
| 500×500 | 40% | 5 | 0.933290 | 0.959684 | 0.254392 | 3.669 | 45.86% |

Fórmulas: `S(p) = média sequencial / média da versão com p workers`; `E(p) = S(p) / p`.

No cenário 500×500, 5% e limite 5 (três gerações reais), o sequencial levou em média 1,218981 s e o distribuído com oito workers 0,267701 s: speedup 4,5535 e eficiência 56,92%. Com 40% e cinco gerações reais, as médias foram 0,933290 s e 0,254392 s, respectivamente. O número de gerações sozinho não explica o tempo: a distribuição dos estados altera quantas células exigem contagem de vizinhos.

Nas 72 comparações da versão com threads, o speedup ficou entre 0,876 e 1,031. Isso não demonstra aceleração sustentada; os pequenos ganhos isolados são compatíveis com variabilidade de medição. O GIL habilitado é uma limitação técnica para esses laços Python intensivos em CPU. A criação de um pool por geração, cópias e sincronização também têm custo.

Nas 72 comparações TCP, o speedup ficou entre 0,728 e 4,554, com 54 médias acima de 1. A versão distribuída utiliza processos independentes, que podem executar em núcleos diferentes. O ganho observado em cenários maiores é compatível com a divisão do cálculo entre processos. O experimento não mede separadamente cada componente de custo: a atribuição a comunicação, serialização e coordenação é uma interpretação da arquitetura, não uma decomposição cronometrada.

O ganho não é linear com p e a eficiência não chega a 100%. O coordenador continua serializando/distribuindo tarefas e reunindo resultados; há transmissão de faixas completas e fronteiras em todas as gerações, além de trabalho sequencial de preparação e parada. Em cargas pequenas esses custos pesam mais. Este experimento usa TCP local e não permite concluir o desempenho entre computadores físicos ou sob latência de rede externa.

## Dados, gráficos e reprodução

- [Medições brutas](medicoes.csv)
- [Estatísticas por configuração](analise/resumo.csv)
- [Speedup e eficiência](analise/comparacoes.csv)
- [Speedup: 500×500, 5%, limite 5](analise/speedup_017.png)
- [Eficiência: mesmo cenário](analise/eficiencia_017.png)
- [Speedup: 500×500, 40%, limite 5](analise/speedup_018.png)
- Todos os outros gráficos estão em `analise/` e identificam cenário, gerações efetivas e política no título.

Para repetir a coleta na raiz do projeto com o ambiente de gráficos preparado:

```powershell
..\venv-benchmark\Scripts\python.exe -B -u retestar.py
```

`retestar.py` executa os testes, verifica as portas, inicia seus workers, mede todos os cenários e gera análise em diretório novo com data UTC. Ele não encerra processos preexistentes. Para outro computador, preparar um ambiente virtual com Python compatível e instalar Matplotlib; `requirements-graficos.txt` registra as versões usadas nesta coleta. Comparar as três versões dentro da nova coleta, sem misturar baselines de sistemas distintos.

Para apresentação, escolher cenários fixos e mostrar tempos, speedup e eficiência, explicando GIL, custo de comunicação e número real de gerações. Não selecionar apenas o maior speedup como se representasse todos os cenários. Este relatório cobre o código básico; as melhorias opcionais devem ser demonstradas e fundamentadas separadamente.

Referências: documentação Python de concurrent.futures e sockets; documentação Microsoft das APIs de hardware, listadas em `docs/REFERENCIAS.md`. Codex/ChatGPT apoiou o coletor Windows, a automação, a execução e a análise; a equipe deve revisar e compreender os resultados. Não houve commit, push ou PR.
