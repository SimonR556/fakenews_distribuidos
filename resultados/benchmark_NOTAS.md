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

`time.perf_counter()` mede somente a chamada ao adaptador, incluindo as alocações de próximas gerações e as contagens usadas para decidir a parada. Criação e cópia inicial pelo benchmark, leitura e SHA-256 do arquivo externo, carregamento do módulo, verificação da assinatura, referência, verificações, CSV e impressões ficam fora. Cópias internas feitas por `simular` e o empacotamento em `ResultadoExecucao` fazem parte do tempo do candidato. Não há aquecimento separado. A comparação usa igualdade completa das matrizes, contagens e preservação da entrada; gerações são comparadas somente quando informadas pelo executor, nunca substituídas pelas da referência. Os tempos não participam da validação. A referência compartilha a função original de transição: verifica consistência com o professor, sem constituir validação independente dessa regra.

`sequencial_provisorio` é um adaptador temporário, não a implementação futura de `sequencial.py`. Os nomes `sequencial`, `paralela` e `distribuida` estão reservados e indisponíveis. Arquivos futuros presentes não serão ativados automaticamente. Será necessário conectar adaptadores ao contrato `simular`, combinar estatísticas e definir custos de inicialização, comunicação e encerramento. `ResultadoExecucao` é exclusivo do benchmark; não estabelece o retorno da proposta `simular_com_estatisticas`. Gerações desconhecidas deverão ficar vazias, nunca inferidas da matriz final.

## Sequencial candidato externo (integração pendente)

O integrante 1 implementou `sequencial.py` na branch remota
`origin/joao/sequencial-testes`. Conforme o teste anterior informado pelo
integrante 4, uma cópia em `/tmp/sequencial_colega.py` reproduziu as contagens
finais do professor no cenário padrão: 9463 ignorantes, zero espalhadores e
537 inativos. Essa origem é informada pelo integrante: o carregador não consulta
a branch remota nem verifica a equivalência entre ela e o arquivo externo.

O executor opcional `sequencial_candidato` permite avaliar essa cópia sem
incorporar ou modificar o arquivo do colega nesta branch. **Ainda não foi
integrado à main e não pode ser usado como baseline oficial para speedup.**
Sua inclusão no benchmark permanece sujeita à revisão do integrante 4 e não
representa integração definitiva.

```bash
python3 -B benchmark.py --rapido --versoes sequencial_provisorio sequencial_candidato --sequencial-arquivo /tmp/sequencial_colega.py --saida resultados/benchmark_candidato_rapido.csv
python3 -B analisar_resultados.py resultados/benchmark_candidato_rapido.csv --saida resultados/analise_candidato_rapido
```

O caminho deve ser explícito e apontar para um arquivo Python existente;
`--sequencial-arquivo` exige selecionar `sequencial_candidato` em `--versoes`.
O padrão continua sendo apenas `sequencial_provisorio`. Não há busca automática,
cópia, merge ou alteração do arquivo externo. O carregamento usa
`importlib.util.spec_from_file_location` e `module_from_spec`, da biblioteca
padrão. O arquivo é lido uma única vez em bytes; `hashlib.sha256` identifica esse
conteúdo e `compile`/`exec` carrega exatamente esses mesmos bytes no módulo,
sem reler o arquivo nem usar bytecode em cache. Tudo ocorre antes das medições.
Assim, uma alteração posterior do arquivo no disco não troca o conteúdo já
carregado nem o hash registrado para ele. O bloco
`if __name__ == "__main__"` do colega não é executado. Como em uma importação
Python, o restante do código de nível superior do arquivo é executado.

Verificam-se a existência de `simular`, se ela é chamável e se sua assinatura
aceita os quatro argumentos posicionais do contrato. Cada repetição chama
`simular(grade_inicial, geracoes, limiar, trabalhadores)` e adapta somente a
matriz retornada para `ResultadoExecucao(grade, geracoes_executadas=None)`.
A matriz final, as contagens e a preservação da entrada continuam verificadas
contra a referência. A função não informa o número de atualizações: mesmo com
zero gerações solicitadas, o candidato registra `None` em memória e campo vazio
no CSV. Nenhum valor é inferido da matriz, do limite ou da referência.

O esquema de colunas do CSV foi preservado. Para o candidato, `codigo` contém
`sequencial_candidato_sha256:<64 dígitos hexadecimais>;arquivo_externo:<caminho absoluto>`;
para o provisório, o identificador anterior permanece. O hash identifica o
conteúdo do arquivo principal carregado; o caminho mantém sua origem. O hash
não cobre dependências importadas pelo arquivo. `commit` continua identificando
apenas o HEAD local, não a revisão do arquivo externo. CSVs antigos com apenas
o caminho continuam legíveis, sem acrescentar retroativamente hashes que não
foram coletados. Identificadores antigos e novos formam grupos separados.

### Validação do adaptador candidato

O teste pequeno com `/tmp/sequencial_colega.py` executou os dois adaptadores
em 5×5 e 10×10, limite cinco, percentual 0,05, limiar três, semente 42 e duas
repetições por versão/tamanho. As oito medições passaram na comparação da matriz,
contagens e preservação da entrada. O provisório informou uma geração em ambos
os tamanhos; o candidato manteve gerações desconhecidas.

| Matriz | Contagens finais (ignorantes/espalhadores/inativos), iguais nas duas versões | Tempos do candidato (s), repetições 1 e 2 |
| --- | --- | --- |
| 5×5 | 24/0/1 | 0.000032358; 0.000029793 |
| 10×10 | 95/0/5 | 0.000091361; 0.000091845 |

São medições curtas de verificação, sem conclusão de desempenho ou speedup.
Um controle adicional em 100×100, limite 50 e quatro trabalhadores solicitados
reproduziu 9463/0/537 com o candidato, mantendo gerações desconhecidas.
Também passaram os casos de zero gerações, ausência inicial de espalhadores,
limiar zero, matriz 1×1 e mais trabalhadores do que linhas.

O analisador leu os oito registros novos (quatro grupos) e os 19 registros dos
dois CSVs antigos (cinco grupos), inclusive uma leitura conjunta de 27 registros.
O resumo novo preservou os campos de gerações vazios do candidato e não produziu
comparações oficiais. O fluxo completo de análise gerou o CSV e informou que
`matplotlib` está ausente, sem instalar dependências.

Foram verificadas as rejeições de caminho ausente/diretório, falta de caminho
explícito, `simular` ausente ou não chamável, assinatura incompatível e módulo
com sintaxe inválida. Executores que alteram a entrada ou retornam matriz
incorreta continuam recusados. Dados sintéticos somente em memória confirmaram
que o candidato nunca vira baseline, mesmo com gerações e hardware preenchidos,
e que gerações desconhecidas impedem comparações entre versões oficiais.

As saídas de validação ficaram em uma pasta temporária sob `/tmp`, redirecionando
somente as raízes de saída na sessão de teste; a CLI entregue continua exigindo
`resultados/`. Nenhum CSV ou módulo foi adicionado ao repositório. O conteúdo do
arquivo externo foi conferido antes/depois e permaneceu igual.

## Campos do CSV

| Campos | Significado |
| --- | --- |
| `versao` | Executor medido: `sequencial_provisorio` ou, explicitamente, `sequencial_candidato` |
| `linhas`, `colunas` | Tamanho da matriz |
| `geracoes_maximas`, `geracoes_executadas` | Limite solicitado e atualizações informadas pelo executor; executadas ficam vazias no candidato |
| `percentual_solicitado` | Fração inicial solicitada; sorteios com reposição podem produzir menos espalhadores distintos |
| `limiar`, `semente` | Configuração da regra e geração da entrada |
| `trabalhadores`, `trabalhadores_efetivos` | Quantidade solicitada e efetiva; o adaptador sempre usa um |
| `repeticao`, `tempo_s` | Índice a partir de um e duração em segundos |
| `ignorantes`, `espalhadores`, `inativos` | Contagens finais |
| `consistente`, `entrada_preservada` | Verificações aprovadas; falhas interrompem a execução sem exportar resultados |
| `data_utc`, `commit`, `codigo` | Data da coleta, HEAD local e identificação do adaptador provisório ou SHA-256 e caminho externo candidato |
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
A eficiência é uma razão (multiplicar por 100 para percentual).

O agrupamento estatístico continua incluindo `versao`, `codigo` e `commit`:
revisões diferentes não têm seus tempos misturados em uma média. Já a chave de
comparação exclui esses três identificadores individuais, além de trabalhadores
solicitados/efetivos e coordenadores. Os demais campos continuam exigidos iguais:
dimensões da matriz, limites e gerações executadas, percentual, limiar, semente,
contagens finais, Python/implementação, sistema, CPU, núcleos, RAM, hosts e política
de tempo. Colunas adicionais também participam da compatibilidade, por cautela.
O CSV não contém as matrizes; a análise depende da geração de entradas conforme
o contrato e da validação completa registrada pelo benchmark.

Havia um problema real: a chave anterior retirava `versao`, mas conservava
`codigo` e `commit`. Assim, implementações oficiais com identificadores próprios
não podiam ser comparadas mesmo no mesmo cenário e ambiente. Esses identificadores
agora servem à rastreabilidade, sem exigir que os códigos das versões sejam iguais.
`comparacoes.csv` preserva `versao`, `codigo` e `commit` da versão comparada e
acrescenta `versao_sequencial`, `codigo_sequencial` e `commit_sequencial` do baseline.
Os gráficos de comparação também mantêm separadas as identidades dos baselines.

Gerações desconhecidas impedem a comparação, mesmo quando desconhecidas dos dois
lados. Se houver mais de um grupo sequencial compatível, inclusive revisões de
código diferentes, o baseline é ambíguo e a comparação é recusada: não se escolhe
o mais rápido nem se agregam revisões. Nesse caso, analisar separadamente os
arquivos do experimento que identificam o baseline pretendido.
O analisador aceita os CSVs anteriores e `sequencial_candidato` no mesmo esquema;
campos de gerações vazios continuam como `None` internamente e vazios em
`resumo.csv`, sem preenchimento ou estimativa. Gráficos mostram `desconhecidas`.

Por cautela, comparações exigem CPU, núcleos físicos/lógicos e RAM preenchidos.
Ambos os lados precisam de commit conhecido e código sem as marcas `provisorio`
ou `candidato`; seus commits podem ser diferentes. Isso não substitui a restrição
ao nome exato `sequencial` para o baseline. É necessário registrar corretamente
o ambiente e a política no benchmark antes de medir, sem editar os dados brutos.
Igualdade textual desses campos depende de um registro fiel do experimento,
inclusive configuração de cada host/rede em execuções distribuídas (colunas
adicionais). O script não consegue verificar hardware, estado da árvore de
trabalho, política ou correção da simulação apenas pelos tempos.

Quando houver comparações válidas, serão gerados `comparacoes.csv` e os PNGs
`speedup_NNN.png` e `eficiencia_NNN.png`. Sem comparação válida, esses arquivos
não são criados. `sequencial_provisorio` e `sequencial_candidato` nunca participam
como baseline oficial; somente o nome exato `sequencial` é elegível.

Os gráficos de tempo são `media_s_NNN.png`. `matplotlib` é usado exclusivamente
para visualização com backend `Agg`, sem paralelizar a simulação. Se a biblioteca
não estiver disponível, uma mensagem informa a limitação e os CSVs continuam
sendo gerados. Cada gráfico corresponde a um grupo que varia apenas as dimensões
e as contagens finais; os demais identificadores, inclusive gerações executadas,
ficam fixos. O eixo lista as dimensões em ordem crescente de área. A numeração
segue a primeira ocorrência de cada grupo no resumo. Grupos com um único tamanho
produzem um ponto. Quando todas as medições são provisórias ou candidatas, os
títulos exibem `PRELIMINAR`; a coluna `versao` do resumo identifica cada executor.

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

### Validação da chave de comparação e do SHA-256

A revisão foi testada com dados identificados como `TESTE_SINTETICO`, separados
dos resultados reais. Para ambos os nomes oficiais `paralela` e `distribuida`,
um baseline `sequencial` com código e commit próprios foi aceito quando todos os
metadados de compatibilidade coincidiam. As fórmulas foram verificadas somente
como teste: tempos artificiais de quatro e dois segundos resultam em speedup
dois e eficiência 0,5 para quatro trabalhadores. Esses valores não representam
desempenho medido do projeto.

Foram recusadas individualmente 16 diferenças em cenário, contagens, Python,
sistema, CPU, núcleos, RAM, hosts e política de tempo. Também foram verificadas
as recusas de gerações desconhecidas em um ou nos dois lados, hardware incompleto,
provisório/candidato como baseline, código temporário ou commit desconhecido em
qualquer lado, baseline sem um trabalhador efetivo e múltiplas revisões sequenciais
compatíveis. Colunas adicionais de ambiente incompatíveis continuam bloqueando
comparações. Revisões diferentes continuaram separadas no resumo; a exportação
da comparação preservou as identidades dos dois lados.

Fixtures Python em `/tmp` verificaram que conteúdos diferentes no mesmo caminho
produzem hashes diferentes, que o mesmo conteúdo em outro caminho mantém o hash
e que um executor já carregado continua usando seus bytes originais após mudar
a fixture no disco. Nenhum arquivo do colega foi usado como fixture nem alterado.

Os dois CSVs reais antigos continuaram produzindo 19 registros em cinco grupos.
O teste real pequeno com `/tmp/sequencial_colega.py` produziu oito medições dos
dois adaptadores, com as mesmas contagens 24/0/1 (5×5) e 95/0/5 (10×10), entradas
preservadas e gerações do candidato vazias. O SHA-256 registrado coincidiu com
o cálculo independente do conteúdo. O teste impediu novas leituras e chamadas
a `hashlib.sha256` durante `executar_benchmark`, confirmando que esses trabalhos
ocorrem no carregamento anterior à medição. A leitura conjunta dos CSVs antigos
e do novo produziu 27 registros. O CSV candidato anterior, sem hash, também foi
lido junto ao novo. Nenhum hash foi fabricado para registros antigos.

Os artefatos ficaram apenas em `/tmp`, com a exportação sintética identificada
em uma subpasta `TESTES_SINTETICOS`; nenhum resultado fictício foi acrescentado
ao repositório. A análise real preservou gerações desconhecidas e não gerou
speedup ou eficiência. `matplotlib` continuou ausente, sem instalação de
dependências e sem validação de renderização dos PNGs nesta revisão.
