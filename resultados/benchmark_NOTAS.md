# Benchmark: integração das implementações oficiais

## Estado da integração (18/11/2026)

O benchmark usa os arquivos oficiais presentes na branch
`joao/benchmark-resultados`, sem alterar código ou documentos dos colegas.
Os relatos de medições anteriores abaixo são históricos: os CSVs e PNGs
existentes não foram modificados nem representam execuções das versões oficiais.

| Nome em `--versoes` | Função chamada | Retorno usado | Gerações registradas |
| --- | --- | --- | --- |
| `sequencial` | `sequencial.simular` | Matriz final | Contadas em execução diagnóstica separada, após as medições do cenário |
| `paralela` | `paralelo.simular_com_detalhes` | `(matriz_final, geracoes_executadas)` | Informadas pela implementação |
| `distribuida` | `distribuido.simular_com_estatisticas` | `(matriz_final, geracoes_executadas)` | Informadas pela implementação |
| `sequencial_provisorio` | Laço com funções de `FakeNews.py` | `ResultadoExecucao` interno | Contadas pelo próprio laço |
| `sequencial_candidato` | `simular` do arquivo explícito | Matriz final | Desconhecidas, campo vazio |

As cinco versões continuam selecionáveis. O padrão da CLI permanece
`sequencial_provisorio`; as oficiais exigem seleção explícita. Provisório e
candidato **nunca** são baseline oficial. O nome de módulo `paralelo.py`
corresponde à opção `paralela`; `distribuido.py`, à opção `distribuida`.

### Executar as três versões e variar trabalhadores

Com quatro workers locais já iniciados, executar a partir da raiz:

```bash
~/Projetos/.venvs/fakenews-distribuidos/bin/python -B benchmark.py --rapido --versoes sequencial paralela distribuida --trabalhadores 1 2 4 --repeticoes 1 --saida resultados/benchmark_integracao_revisao.csv
~/Projetos/.venvs/fakenews-distribuidos/bin/python -B analisar_resultados.py resultados/benchmark_integracao_revisao.csv --saida resultados/analise_integracao_revisao
```

Esses comandos são exemplos para revisão, não uma bateria final já realizada.
Sem workers, testar apenas `--versoes sequencial paralela`. Um único valor,
como `--trabalhadores 4`, continua válido. Com uma lista de valores, cada
sequencial roda apenas com o primeiro valor solicitado, sempre com um trabalhador
efetivo; evita repetir o mesmo baseline e torná-lo ambíguo no analisador.
Paralela e distribuída rodam com todos os valores. A paralela limita a quantidade
às linhas; a distribuída rejeita antecipadamente valores maiores que o total de
linhas de qualquer cenário. Valores repetidos nas listas são recusados para
evitar registros duplicados.

### Iniciar e encerrar workers locais

Abrir quatro terminais na raiz e executar um comando em cada terminal:

```bash
~/Projetos/.venvs/fakenews-distribuidos/bin/python -B -u worker.py --host 127.0.0.1 --porta 5000
~/Projetos/.venvs/fakenews-distribuidos/bin/python -B -u worker.py --host 127.0.0.1 --porta 5001
~/Projetos/.venvs/fakenews-distribuidos/bin/python -B -u worker.py --host 127.0.0.1 --porta 5002
~/Projetos/.venvs/fakenews-distribuidos/bin/python -B -u worker.py --host 127.0.0.1 --porta 5003
```

Aguardar `Worker disponível` antes de iniciar o benchmark. Com um trabalhador,
o coordenador usa 5000; com dois, 5000–5001; com quatro, 5000–5003. Os processos
permanecem disponíveis entre chamadas e repetições; `encerrar` fecha apenas a
conexão da simulação. Ao terminar, usar Ctrl+C nos terminais dos próprios workers.
O benchmark não inicia nem encerra processos e não presume que estejam ativos.

Para evitar portas ocupadas, iniciar os próprios workers em outras portas e
informar, por exemplo, `FAKENEWS_WORKERS=127.0.0.1:15000,127.0.0.1:15001` antes do
comando com `--trabalhadores 2`. A variável é a configuração oficial do coordenador:
deve conter **exatamente** tantos endereços quanto trabalhadores solicitados.
Para variar `1 2 4` numa chamada, deixar `FAKENEWS_WORKERS` ausente ou vazia e usar
as portas padrão. Não enviar tarefas nem desligar serviços preexistentes para
liberar portas. Esta primeira integração aceita somente o host literal
`127.0.0.1`, registrando `hosts=1`; outros hosts são rejeitados para não registrar
ambiente distribuído incompleto como se fosse local. Experimentos entre máquinas
exigirão identificação do hardware e ambiente de cada host e da rede.

### Política comparável e identidade do código

As três versões oficiais usam a mesma política
`chamada_completa_v1_workers_tcp_preiniciados`: `time.perf_counter()` delimita a
chamada completa ao adaptador da função oficial. Inclui cópias e validações
internas da implementação, evolução, decisão de parada e retorno. Na paralela,
inclui criação, sincronização e encerramento dos pools/threads de cada geração.
Na distribuída, com processos workers previamente iniciados, inclui validação e
cópia internas, abertura das conexões, serialização, envio, cálculo, recepção,
sincronização, decisão global de parada, mensagens de encerramento, confirmações
e fechamento das conexões. Logs dos workers permanecem como no código oficial.
Não se mede nem se mistura a inicialização dos processos workers nesta política.
Uma futura política que inclua esse custo precisará de identificador próprio e
de medições separadas. A política mede o custo observado pelo chamador; os custos
de preparação internos de cada arquitetura fazem parte dessa comparação.

Criação da grade, cópia independente da entrada de cada repetição pelo benchmark,
carregamento/assinaturas/hashes, referência, validação completa da matriz,
contagens, diagnóstico sequencial, preservação da entrada, metadados, CSV e impressões do benchmark ficam
fora do intervalo. Não há aquecimento separado. Provisório e candidato mantêm a
política preliminar `somente_executor_sem_copia_de_entrada`, sem serem promovidos
a oficiais.

O esquema de colunas do CSV permanece igual. `codigo` registra função e SHA-256
dos bytes carregados do módulo oficial, mais hashes de `benchmark.py` e
`FakeNews.py`. O distribuído também identifica os bytes de `worker.py` carregados
como dependência do coordenador e os endereços configurados. Módulos oficiais são
lidos uma vez e executados desses mesmos bytes antes da medição, sem executar
seus exemplos `__main__`. Provisório e candidato também registram hashes do
benchmark e de `FakeNews.py`; o candidato conserva hash e caminho explícito.
`commit` identifica o HEAD local, enquanto os hashes identificam o conteúdo da
árvore de trabalho. Não alterar fontes durante a coleta. O protocolo atual não
atesta a identidade de processos workers preexistentes: iniciar os workers da
mesma cópia/revisão de `worker.py` é responsabilidade de quem conduz o experimento.

Para limite positivo, trabalhadores efetivos são um no sequencial,
`min(solicitados, linhas)` na paralela e o valor solicitado na distribuída.
Com zero gerações, paralela e distribuída registram zero trabalhadores efetivos,
pois não criam pools nem abrem conexões; o coordenador continua sendo um processo
local. A distribuída registra `coordenadores=1`, as demais zero. O analisador
aceita zero trabalhadores efetivos somente nessas duas versões com limite e
gerações executadas iguais a zero; não calcula eficiência para esses registros.

Falhas interrompem a coleta com código de saída 1 e mensagem que identifica
versão, cenário, trabalhadores, repetição, tipo e texto da exceção. Nenhum CSV
de medições é exportado quando há falha de execução ou validação, nem mesmo
com resultados parciais aprovados antes dela. Erros de argumentos retornam 2.
Falha na escrita pode deixar arquivo parcial e é informada separadamente.

### Condições para speedup e eficiência oficiais

Os dois impedimentos da primeira integração foram tratados na revisão abaixo,
sem alterar o sequencial ou flexibilizar as restrições do analisador. Continuam
necessários ambiente completo, gerações conhecidas e verificadas, cenário e
política compatíveis e um único baseline oficial. Fontes locais indisponíveis ou
inválidas continuam impedindo comparações; não se completam dados por suposição.

### Revisão: diagnóstico sequencial, hardware e gráficos contra p

O intervalo cronometrado continua chamando a própria `sequencial.simular`,
carregada dos bytes oficiais identificados no CSV, sem reimplementar seu laço e
sem instrumentação ativa. Após **todas** as repetições cronometradas de todas as
versões e quantidades de trabalhadores do cenário, o benchmark chama novamente
essa mesma função em uma cópia idêntica da grade inicial. Somente nessa execução
diagnóstica, substitui temporariamente `proxima_geracao` no `__globals__` de
`simular` por um contador que delega à função original. A restauração é obrigatória
em `finally`, inclusive se a simulação lançar uma exceção. O arquivo
`sequencial.py` e o corpo de `simular` permanecem intactos.

O diagnóstico não é medido e ocorre depois das amostras, sem acrescentar um
aquecimento sequencial anterior a elas. O benchmark verifica preservação da
entrada, igualdade da matriz e das contagens com a execução cronometrada, e
igualdade da matriz e da contagem de chamadas com a referência independente de
`FakeNews.py`. Todas as repetições cronometradas já foram confrontadas com essa
mesma referência. Qualquer divergência interrompe a coleta, sem exportar CSV.

`geracoes_executadas` do sequencial passa a conter a quantidade de chamadas
**diretamente observada numa execução diagnóstica determinística equivalente**.
Não é uma contagem instrumentada em cada chamada cronometrada. A referência
serve somente para validar; não preenche o campo. Mesmo com limite zero, o zero
registrado vem do contador diagnóstico. `codigo` inclui
`geracoes:diagnostico_deterministico_apos_medicoes` para explicitar a procedência.
O candidato externo permanece com gerações desconhecidas; os CSVs antigos não
recebem preenchimento retroativo. Uma futura auxiliar oficial poderia informar
gerações diretamente, mas não é necessária para o diagnóstico solicitado.

No Linux, os metadados são coletados antes dos cronômetros, só com biblioteca
padrão: modelo da CPU em `/proc/cpuinfo`; núcleos físicos como pares distintos de
`physical_package_id` e `core_id` em `/sys/devices/system/cpu/cpuN/topology` para
**todas** as CPUs online; RAM total como
`os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')`. A topologia só é aceita
se a lista online estiver estável, completa e concordar com `os.cpu_count()`, e
se os identificadores forem não negativos. Núcleos físicos devem estar entre um
e a quantidade lógica; os dois fatores da RAM devem ser inteiros positivos.
Não se deduzem núcleos físicos dividindo threads nem se usam números dos documentos
como substitutos da coleta. RAM significa memória física total reportada pelo
sistema, não memória livre ou limite de um processo. Em outros sistemas, ou se
uma fonte falhar, os campos não detectados continuam desconhecidos.

O esquema de colunas é preservado. Os gráficos `media_s_NNN.png` continuam
mostrando tempo contra dimensões. Quando há comparações oficiais válidas,
`speedup_NNN.png` e `eficiencia_NNN.png` passam a usar trabalhadores efetivos
**p no eixo horizontal**, com legendas **Paralela** e **Distribuída**.
Usam `S(p)=T_seq/T_p` e `E(p)=S(p)/p`, calculados a partir das médias medidas.
Cada figura fixa dimensões, limites, gerações executadas, percentual, limiar,
semente, contagens, ambiente, hosts, política, colunas adicionais e identidade do
baseline. Cada revisão de código/commit da versão comparada fica em uma série
distinta. Apenas o sufixo de endereços workers em `codigo` pode variar com p sem
ser tratado como revisão de fonte; os hashes são preservados. Configurações
distintas com o mesmo p aparecem como pontos, sem agregação ou ligação por linha.
Não se juntam cenários diferentes para formar uma curva. Sem baseline oficial
validado, não se geram gráficos de comparação.

### Validação da revisão com dados medidos (18/11/2026)

Passaram os 13 testes de `testes.py` e os seis grupos de validação temporários
em `/tmp/test_fakenews_revisao.py`, usando o interpretador do ambiente virtual
existente. Não houve instalação de dependências. Os testes verificaram que a
função cronometrada continua vindo de `sequencial.py`, sem substituição ativa de
`proxima_geracao` em nenhum intervalo, e que o diagnóstico roda somente após
todas as medições do cenário. Também passaram restauração em `finally` com
exceção injetada, rejeição de matriz/contagem diagnósticas divergentes, interrupção
sem CSV, zero gerações, parada sem espalhadores iniciais, limiar zero, entrada
preservada, candidato ainda desconhecido e fontes de hardware indisponíveis.

A coleta pequena real usou as três versões, matrizes 5×5 e 10×10, fração 0,40,
semente 42, limiar 3, limite cinco, duas repetições e 1, 2 e 4 trabalhadores.
Foram iniciados quatro subprocessos próprios em 127.0.0.1, portas livres
5000–5003, confirmada a prontidão de cada filho pelo seu log e executada a CLI.
Os quatro workers foram encerrados e aguardados em `finally`. Nenhum processo
preexistente foi encerrado. As matrizes e contagens passaram na referência e as
entradas foram preservadas; 5×5 executou duas gerações e 10×10, quatro.

O ambiente coletado diretamente foi CPU `12th Gen Intel(R) Core(TM) i5-12400F`,
12 CPUs lógicas, seis núcleos físicos e 16.589.127.680 bytes de RAM total. A
contagem física foi conferida também pelos pares de pacote/núcleo de
`/proc/cpuinfo`, independentemente da leitura de `/sys` usada no benchmark.

Foram exportadas **28 medições reais**, resumidas em **14 grupos**, gerando
**12 comparações oficiais**: seis paralelas e seis distribuídas, com baseline
sequencial oficial e fórmula conferida em cada linha. A análise produziu
14 PNGs de tempo, **dois de speedup e dois de eficiência contra p**. Os testes
inspecionaram os dados dos eixos: em cada gráfico de comparação, séries Paralela
e Distribuída com p=1,2,4 e valores iguais aos de `comparacoes.csv`. As figuras
também foram inspecionadas visualmente. Nenhum tempo sintético foi usado como
prova experimental; todos os tempos dessas comparações vieram da coleta real.
São amostras pequenas para verificar o fluxo, sem conclusão final de desempenho.

Artefatos temporários desta revisão:

```text
/tmp/fakenews_revisao_ajn6y56q/test_06_tcp_comparacoes_medidas_e_graficos/coleta_real.csv
/tmp/fakenews_revisao_ajn6y56q/test_06_tcp_comparacoes_medidas_e_graficos/analise_real/comparacoes.csv
/tmp/fakenews_revisao_ajn6y56q/test_06_tcp_comparacoes_medidas_e_graficos/analise_real/
```

As raízes de saída dos módulos foram redirecionadas para `/tmp` apenas no teste;
a CLI entregue continua exigindo saídas novas em `resultados/`. Os três CSVs
históricos continuam legíveis (27 registros), inclusive junto de CSV novo.
Diferenças de cenário, gerações, ambiente e política, baseline provisório ou
candidato e baseline ambíguo continuaram recusados, usando cópias dos dados
medidos somente para testes de rejeição. Os 27 arquivos protegidos, incluindo
fontes dos colegas, documentos, CSVs e gráficos históricos, tiveram seus hashes
conferidos e permaneceram intactos. Não foi executada a bateria final.

### Validação da primeira integração (antes desta revisão)

- `~/Projetos/.venvs/fakenews-distribuidos/bin/python -B testes.py`: 13 testes
  aprovados. O comando inicial `python -B testes.py` encontrou
  `/bin/bash: python: command not found`; a execução foi concluída pelo ambiente
  virtual solicitado, sem instalar dependências.
- Sequencial/paralela: matrizes 5×5, 10×10 e 100×100, com 1, 2 e 4 threads,
  comparadas célula por célula com a referência e entre si. Foram usadas também
  densidades 0,40 nas matrizes pequenas e 0,05 em 100×100, limite 50, limiar 3,
  semente 42, além dos cenários rápidos. Contagens e entradas preservadas.
- Distribuída: mesmos tamanhos e equivalência com 1, 2 e 4 workers temporários
  próprios. Foram testadas portas livres alternativas via `FAKENEWS_WORKERS` e
  as portas padrão 5000–5003; a CLI com as três versões e `--trabalhadores 1 2 4`
  passou e produziu 14 registros de verificação em `/tmp`. Workers foram
  reutilizados e todos os subprocessos próprios foram encerrados ao final;
  nenhum processo preexistente foi encerrado.
- Zero gerações, ausência inicial de espalhadores, limiar zero, todos espalhadores,
  matrizes pequenas/retangulares, divisão com resto e mais threads que linhas
  passaram. Mais workers distribuídos que linhas são recusados pela CLI.
  Zero gerações não abriu conexões TCP. Gerações conhecidas foram conferidas
  com a referência; as desconhecidas permaneceram vazias.
- Foi verificado que cópia e contagens de validação ficam fora do cronômetro,
  e que não há leitura/hash de fonte durante a coleta. Hashes coincidiram com
  as fontes identificadas. Retorno incorreto, entrada alterada, gerações erradas,
  argumentos inválidos e hosts externos foram recusados.
- Os três CSVs brutos antigos foram lidos: 27 registros, sem comparação oficial.
  Também passaram leitura conjunta com CSV novo, análise e geração de PNGs pelo
  ambiente virtual com Matplotlib. Provisório/candidato continuaram impedidos de
  ser baseline. Testes sintéticos somente em memória confirmaram fórmulas,
  baseline ambíguo e rejeição de diferenças de cenário, gerações, ambiente e
  política; nenhum resultado fictício foi acrescentado aos dados experimentais.

O teste de sockets foi inicialmente bloqueado pelo sandbox com
`PermissionError: [Errno 1] Operation not permitted`; a execução autorizada com
acesso TCP local passou. O teste intencional sem workers ativos retornou:

```text
Erro: Falha em distribuida, 5x5, limite=5, percentual=0.05, trabalhadores=1, repetição=1: ConnectionRefusedError: [Errno 111] Connection refused. Coleta interrompida; nenhum CSV de medições exportado.
```

Esse caso retornou 1 e não criou CSV. Nenhuma implementação apresentou falha de
equivalência nos testes concluídos. As saídas ficaram somente em diretórios
temporários, incluindo `/tmp/fakenews_integracao_9gl4y_31` (validações sem TCP e
gráficos) e `/tmp/fakenews_integracao_8pcncw_o` (TCP e CLI com portas padrão).
Nos testes, apenas as constantes de destino dos módulos importados foram
redirecionadas para `/tmp`; a CLI entregue continua exigindo saída nova dentro de
`resultados/`. Não foi executada a bateria final de experimentos nem produzido
speedup/eficiência medidos.

## Uso preliminar preservado

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

`time.perf_counter()` mede somente a chamada ao adaptador, incluindo as alocações de próximas gerações e as contagens usadas para decidir a parada. Criação e cópia inicial pelo benchmark, leitura e SHA-256 do arquivo externo, carregamento do módulo, verificação da assinatura, referência, diagnóstico sequencial, verificações, CSV e impressões ficam fora. Cópias internas feitas por `simular` e o empacotamento em `ResultadoExecucao` fazem parte do tempo do candidato. Não há aquecimento separado. A comparação usa igualdade completa das matrizes, contagens e preservação da entrada; gerações são comparadas quando informadas pelo executor ou contadas diretamente no diagnóstico, nunca substituídas pelas da referência. Os tempos não participam da validação. A referência compartilha a função original de transição: verifica consistência com o professor, sem constituir validação independente dessa regra.

`sequencial_provisorio` continua sendo um adaptador temporário, distinto de
`sequencial.py`. As três versões oficiais estão disponíveis conforme a seção
de integração acima. `ResultadoExecucao` é exclusivo do benchmark e adapta os
retornos reais, sem estabelecer uma nova interface para os módulos dos colegas.
Gerações desconhecidas ficam vazias, nunca inferidas da matriz final.

## Sequencial candidato externo e histórico da integração anterior

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
| `versao` | `sequencial`, `paralela`, `distribuida`, `sequencial_provisorio` ou `sequencial_candidato` |
| `linhas`, `colunas` | Tamanho da matriz |
| `geracoes_maximas`, `geracoes_executadas` | Limite e atualizações informadas pelo executor ou contadas no diagnóstico sequencial validado; vazias no candidato e nos registros antigos que não as coletaram |
| `percentual_solicitado` | Fração inicial solicitada; sorteios com reposição podem produzir menos espalhadores distintos |
| `limiar`, `semente` | Configuração da regra e geração da entrada |
| `trabalhadores`, `trabalhadores_efetivos` | Quantidade solicitada e efetiva, conforme versão, linhas e limite zero descritos acima |
| `repeticao`, `tempo_s` | Índice a partir de um e duração em segundos |
| `ignorantes`, `espalhadores`, `inativos` | Contagens finais |
| `consistente`, `entrada_preservada` | Verificações aprovadas; falhas interrompem a execução sem exportar resultados |
| `data_utc`, `commit`, `codigo` | Data da coleta, HEAD local e identidade das fontes/função conforme integração acima; identificadores antigos são preservados |
| `python`, `implementacao_python`, `sistema`, `cpu` | Ambiente detectado pela biblioteca padrão |
| `nucleos_logicos`, `nucleos_fisicos`, `ram_bytes` | Valores detectados localmente; físicos e RAM no Linux conforme fontes e validações acima; desconhecidos ficam vazios |
| `hosts`, `coordenadores` | Um host local; um coordenador na distribuída, zero nas demais |
| `politica_tempo` | Identificador da região medida descrita acima |

`commit` identifica o HEAD de base: esta entrega ainda não foi commitada. O CSV não afirma que o adaptador já pertence a esse commit; os hashes registram suas fontes. Hardware indisponível permanece desconhecido e impede comparações oficiais.

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

Os gráficos de tempo são `media_s_NNN.png`. A descrição de facetas por tamanho
a seguir se aplica aos gráficos de tempo; speedup e eficiência variam somente
p, com cenário e baseline fixos, conforme a revisão acima.
`matplotlib` é usado exclusivamente
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
