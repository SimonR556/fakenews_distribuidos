# Primeira versão do benchmark

Executar a partir da raiz do projeto, sem instalar dependências:

```bash
python3 -B benchmark.py --rapido
python3 -B benchmark.py --tamanhos 5x5 10x10 100x100 --geracoes 0 50 --percentuais 0 0.05 --limiar 3 --semente 42 --repeticoes 3 --trabalhadores 4
python3 -B benchmark.py --help
```

`--rapido` fornece padrões de 5×5 e 10×10, limite de cinco gerações e duas repetições; parâmetros explícitos prevalecem. Sem opções, o padrão é 10×10, limite dez e três repetições. Percentuais são frações: `0.05` significa 5%. Dimensões devem ser positivas, gerações não negativas e limiar entre zero e oito. Esta validação pertence à CLI, sem definir o contrato de entradas inválidas dos colegas.

O nome padrão do CSV inclui data UTC. `--saida resultados/nome.csv` permite escolher um arquivo novo. A saída deve permanecer dentro de `resultados/`; arquivos existentes não são sobrescritos.

## Medição e consistência

Uma única grade é gerada por combinação de tamanho, limite de gerações e percentual, com a semente informada. Cada repetição recebe uma cópia profunda, criada antes do cronômetro. A referência roda fora do cronômetro, com outro laço que chama as funções originais. Não se executa a rotina principal de `FakeNews.py`.

`time.perf_counter()` mede somente a chamada ao adaptador, incluindo as alocações de próximas gerações e as contagens usadas para decidir a parada. Criação e cópia inicial, referência, verificações, CSV e impressões ficam fora. Não há aquecimento separado. A comparação usa igualdade completa das matrizes, contagens, gerações e preservação da entrada, nunca os tempos. A referência compartilha a função original de transição: verifica consistência com o professor, sem constituir validação independente dessa regra.

`sequencial_provisorio` é um adaptador temporário, não a implementação futura de `sequencial.py`. Os nomes `sequencial`, `paralela` e `distribuida` estão reservados e indisponíveis. Arquivos futuros presentes não serão ativados automaticamente. Será necessário conectar adaptadores ao contrato `simular`, combinar estatísticas e definir custos de inicialização, comunicação e encerramento. `ResultadoExecucao` é exclusivo do benchmark; não estabelece o retorno da proposta `simular_com_estatisticas`. Gerações desconhecidas deverão ficar vazias, nunca inferidas da matriz final.

## Campos do CSV

| Campos | Significado |
| --- | --- |
| `versao` | Executor medido, atualmente apenas `sequencial_provisorio` |
| `linhas`, `colunas` | Tamanho da matriz |
| `geracoes_maximas`, `geracoes_executadas` | Limite solicitado e atualizações efetivamente realizadas |
| `percentual_solicitado` | Fração inicial solicitada; sorteios com reposição podem produzir menos espalhadores distintos |
| `limiar`, `semente` | Configuração da regra e geração da entrada |
| `trabalhadores`, `trabalhadores_efetivos` | Quantidade solicitada e efetiva; o adaptador sempre usa um |
| `repeticao`, `tempo_s` | Índice a partir de um e duração em segundos |
| `ignorantes`, `espalhadores`, `inativos` | Contagens finais |
| `consistente`, `entrada_preservada` | Verificações aprovadas; falhas interrompem a execução sem exportar resultados |
| `data_utc`, `commit`, `codigo` | Data da coleta, HEAD e identificação de código provisório na árvore de trabalho |
| `python`, `implementacao_python`, `sistema`, `cpu` | Ambiente detectado pela biblioteca padrão |
| `nucleos_logicos`, `nucleos_fisicos`, `ram_bytes` | Núcleos lógicos detectados; físicos e RAM ficam vazios por falta de detecção portável |
| `hosts`, `coordenadores` | Um host local e nenhum coordenador nesta etapa |
| `politica_tempo` | Identificador da região medida descrita acima |

`commit` identifica o HEAD de base: esta entrega ainda não foi commitada. O CSV não afirma que o adaptador já pertence a esse commit. CPU pode ficar vazia conforme a plataforma; completar hardware e ambiente antes dos experimentos finais.

## Teste inicial realizado

```bash
python3 -B benchmark.py --rapido --saida resultados/benchmark_inicial_rapido.csv
```

Foram registradas quatro medições, duas por tamanho, todas consistentes. Ambos os cenários encerraram em uma geração. Os tempos são amostras preliminares muito curtas, não conclusões de desempenho. Nenhuma versão paralela ou distribuída foi executada e não há speedup calculado.

Também foram verificados em memória zero gerações, ausência inicial de espalhadores, limiar zero, propagação nos cantos e parada. A configuração de `docs/TESTE_PADRAO.md` reproduziu três gerações e contagens finais 9463/0/537, preservando a entrada.

Implementação e documentação produzidas com apoio de IA (Codex), usando os documentos locais e `FakeNews.py`. Nenhuma dependência instalada.

## Análise dos CSVs

O script `analisar_resultados.py` lê um ou mais CSVs com `csv.DictReader` e usa
somente a biblioteca padrão para validar e calcular estatísticas. Não executa
simulações. Executar a partir da raiz:

```bash
python3 -B analisar_resultados.py resultados/benchmark_inicial_rapido.csv resultados/benchmark_tamanhos_teste.csv --saida resultados/analise_inicial
python3 -B analisar_resultados.py --help
```

A pasta de saída deve ser uma **subpasta nova** de `resultados/`. Se ela já
existir, a execução é recusada: escolha outro nome. Os CSVs de entrada são
abertos somente para leitura. A validação ocorre antes de criar a saída;
falhas posteriores de escrita podem deixar uma pasta parcial, que é preservada.
Não há opção de sobrescrita nem instalação automática de dependências.

O `resumo.csv` conserva os identificadores do cenário e contém `amostras`,
`media_s`, `mediana_s`, `minimo_s`, `maximo_s` e
`desvio_padrao_amostral_s`. Todas as durações estão em segundos. O desvio é
amostral (`statistics.stdev`, divisor n−1); com uma única medição fica vazio,
pois não pode ser estimado. Não são removidos valores extremos.

São obrigatórias as colunas emitidas pelo benchmark atual. Colunas adicionais
são aceitas e entram na identidade do grupo; arquivos com conjuntos de colunas
diferentes devem ser analisados separadamente. Números são normalizados, os
tempos devem ser positivos e finitos, e as verificações `consistente` e
`entrada_preservada` devem ser `True`. Também se verificam intervalos, soma das
contagens, limites de gerações, parada antecipada e trabalhadores efetivos.
Repetições da mesma coleta/cenário com contagens ou gerações divergentes são
recusadas, assim como medições duplicadas, CSVs vazios e cabeçalhos inválidos.
A análise confia nas verificações registradas pelo benchmark: o CSV não contém
as matrizes para repetir a comparação célula por célula.

O agrupamento usa todos os campos exceto data da coleta, índice da repetição,
tempo e indicadores de validação. Assim, versão, dimensões, gerações máximas
e executadas, percentual, limiar, semente, trabalhadores solicitados e efetivos,
política de tempo, commit, código, ambiente, hosts, coordenadores e contagens
finais permanecem separados. Datas diferentes podem contribuir para o mesmo
grupo quando os demais identificadores coincidem. Campos de ambiente ausentes
são preservados como desconhecidos: estatísticas descritivas não comprovam que
o hardware foi o mesmo entre coletas.

Para speedup, o baseline deve ser exatamente `sequencial` com um trabalhador
efetivo, e o outro grupo deve ser `paralela` ou `distribuida`. Usam-se as médias:
`S(p) = media_sequencial_s / media_s` e `E(p) = S(p) / trabalhadores_efetivos`.
A eficiência é uma razão (multiplicar por 100 para percentual). Trabalhadores
solicitados/efetivos e coordenadores não fazem parte da chave de comparação
entre versões; todos os demais identificadores devem coincidir, inclusive
hosts, contagens, gerações executadas, commit, código e política de tempo.
Gerações desconhecidas impedem a comparação. Baseline ambíguo também é recusado.

Por cautela, comparações exigem CPU, núcleos físicos/lógicos e RAM preenchidos,
commit conhecido e identificação de código sem `provisorio`. O identificador
`codigo` deve representar a mesma revisão/conjunto experimental para as versões
comparadas. Esta regra pode recusar experimentos equivalentes com metadados
diferentes; é preferível registrar corretamente o ambiente e a política no
benchmark antes de medir, sem editar os dados brutos. Igualdade textual desses
campos ainda depende de um registro fiel do experimento, inclusive configuração
de cada host/rede em execuções distribuídas (colunas adicionais). O script não
consegue verificar hardware, estado da árvore de trabalho, política ou correção
da simulação apenas pelos tempos.

Quando houver comparações válidas, serão gerados `comparacoes.csv` e os PNGs
`speedup_NNN.png` e `eficiencia_NNN.png`. Sem comparação válida, esses arquivos
não são criados. `sequencial_provisorio` nunca participa como baseline oficial.

Os gráficos de tempo são `media_s_NNN.png`. `matplotlib` é usado exclusivamente
para visualização com backend `Agg`, sem paralelizar a simulação. Se a biblioteca
não estiver disponível, uma mensagem informa a limitação e os CSVs continuam
sendo gerados. Cada gráfico corresponde a um grupo que varia apenas as dimensões
e as contagens finais; os demais identificadores, inclusive gerações executadas,
ficam fixos. O eixo lista as dimensões em ordem crescente de área. A numeração
segue a primeira ocorrência de cada grupo no resumo. Grupos com um único tamanho
produzem um ponto. Quando todas as medições são provisórias, os títulos exibem
`PRELIMINAR`; a coluna `versao` do resumo também identifica essa condição.

### Análise dos arquivos iniciais

A execução indicada acima produziu `resultados/analise_inicial/resumo.csv`, com
19 medições em cinco grupos. Os dois tamanhos pequenos têm limite de cinco
atualizações e executaram uma; os demais têm limite 50 e executaram três.
Todos usam semente 42, percentual 0,05, limiar 3 e um trabalhador efetivo.

| Matriz | n | Média (s) | Mediana (s) | Mínimo (s) | Máximo (s) | Desvio amostral (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5×5 | 2 | 0.000024528003 | 0.000024528003 | 0.000023181005 | 0.000025875001 | 0.000001904943 |
| 10×10 | 2 | 0.000077891000 | 0.000077891000 | 0.000076328004 | 0.000079453996 | 0.000002210410 |
| 100×100 | 5 | 0.022528616599 | 0.020075102999 | 0.018472659001 | 0.033083185001 | 0.005980690860 |
| 300×300 | 5 | 0.192714203801 | 0.193472936997 | 0.182925695000 | 0.199828553006 | 0.006181697687 |
| 500×500 | 5 | 0.559536649600 | 0.556870280998 | 0.542018738997 | 0.587529732999 | 0.017061960937 |

São **resultados preliminares**, exclusivamente do adaptador
`sequencial_provisorio`. Não existe medição do sequencial oficial, paralelo ou
distribuído nesses CSVs. Portanto, não há speedup ou eficiência calculável.
O hardware também está incompleto (núcleos físicos/RAM ausentes). Tempos de
matrizes com números de gerações diferentes não isolam o efeito do tamanho.
As amostras são pequenas, especialmente os tempos muito curtos de 5×5 e 10×10.

Neste ambiente, `matplotlib` não está instalado: nenhum PNG foi gerado e nenhuma
dependência foi instalada. Com a biblioteca disponível, repetir o comando usando
outra pasta de saída gerará os gráficos de tempo preliminares.

A validação de desenvolvimento incluiu leitura dos CSVs reais, grupos e tamanho
das amostras, desvio indefinido para n=1, rejeição de valores inválidos, duplicatas,
esquemas incompletos, arquivos vazios e proteção da saída. Fórmulas e rejeição de
comparações incompatíveis foram verificadas com dados sintéticos somente em
memória, sem incluí-los nos resultados experimentais. Implementação da análise
com apoio de IA (Codex).
