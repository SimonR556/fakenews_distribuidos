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
