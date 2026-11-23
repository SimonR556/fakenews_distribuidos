
# Propagação de Fake News em Sistemas Paralelos e Distribuídos

Trabalho acadêmico desenvolvido na Universidade Tecnológica Federal do Paraná (UTFPR), Campus Cornélio Procópio, para a disciplina de Sistemas Distribuídos.

O projeto tem como objetivo estudar a propagação de notícias falsas em uma população simulada, utilizando três abordagens de processamento:

- **Sequencial:** execução em um único fluxo de processamento.
- **Paralela:** utilização de múltiplas threads.
- **Distribuída:** utilização de processos trabalhadores que se comunicam por sockets TCP.

Além das implementações principais, o projeto inclui testes automatizados, ferramentas de benchmark e melhorias opcionais no modelo de propagação.

## 1. Objetivo do projeto

O trabalho parte de uma simulação sequencial fornecida pelo professor e propõe sua adaptação para ambientes paralelos e distribuídos.

Os principais objetivos são:

- Implementar a mesma lógica de propagação em três arquiteturas diferentes.
- Garantir que as implementações produzam resultados equivalentes.
- Comparar os tempos de execução.
- Analisar os custos de sincronização e comunicação.
- Identificar limitações e possíveis ganhos de desempenho.
- Implementar melhorias opcionais na simulação.

O projeto utiliza Python 3 e recursos da biblioteca padrão.

## 2. Funcionamento da simulação

A população é representada por uma matriz bidimensional.

Cada posição da matriz representa um indivíduo, que pode assumir um dos seguintes estados:

| Valor | Estado | Descrição |
| --- | --- | --- |
| 0 | Ignorante | Ainda não está propagando a notícia falsa |
| 1 | Espalhador | Acredita na notícia e está compartilhando |
| 2 | Inativo | Deixou de compartilhar a notícia |

### Regras de propagação

A simulação utiliza a vizinhança de Moore, considerando até oito vizinhos ao redor de cada indivíduo.

A cada geração:

1. Um indivíduo ignorante se torna espalhador quando possui uma quantidade de vizinhos espalhadores maior ou igual ao limiar configurado.
2. Um indivíduo espalhador se torna inativo.
3. Um indivíduo inativo permanece inativo.

As atualizações são síncronas: todas as células consultam o estado da geração anterior antes de produzir a próxima matriz.

A simulação termina quando:

- O número máximo de gerações é atingido; ou
- Não existem mais indivíduos espalhadores após uma geração.

## 3. Tecnologias utilizadas

- Python 3
- `threading` e mecanismos de sincronização
- `concurrent.futures`
- `socket`
- `json`
- `time`
- `random`
- `copy`
- `unittest`
- Biblioteca padrão do Python

Não é necessário instalar frameworks externos para executar as implementações principais.

## 4. Estrutura do projeto

Os principais arquivos são:

| Arquivo ou diretório | Finalidade |
| --- | --- |
| `FakeNews.py` | Código sequencial original fornecido pelo professor |
| `main.py` | Menu principal e integração das funcionalidades |
| `sequencial.py` | Implementação sequencial refatorada |
| `paralelo.py` | Implementação paralela com threads |
| `distribuido.py` | Coordenador da implementação distribuída |
| `worker.py` | Processo trabalhador da versão distribuída |
| `benchmark.py` | Medição e validação das implementações |
| `analisar_resultados.py` | Análise dos resultados do benchmark |
| `melhorias.py` | Funcionalidades opcionais da simulação |
| `testes.py` | Testes da implementação sequencial |
| `testes_melhorias.py` | Testes das melhorias opcionais |
| `resultados/` | Arquivos de benchmark e relatórios |
| `docs/` | Documentação técnica do projeto |
| `CONTRIBUTING.md` | Orientações de contribuição |

O arquivo `FakeNews.py` foi preservado como referência para o desenvolvimento das demais versões.

## 5. Como executar o projeto

### Pré-requisitos

É necessário ter instalado:

- Python 3
- Git

Para verificar a instalação:

```bash
python3 --version
git --version
```

### Clonar o repositório

```bash
git clone https://github.com/SimonR556/fakenews_distribuidos.git
cd fakenews_distribuidos
```

### Iniciar o programa

Execute:

```bash
python3 main.py
```

O programa apresentará o seguinte menu:

```text
========================================
       PROPAGACAO DE FAKE NEWS
========================================
1 - Executar simulacao sequencial
2 - Executar simulacao paralela
3 - Executar simulacao distribuida
4 - Executar benchmark rapido
5 - Demonstrar melhorias
0 - Sair
```

## 6. Execução sequencial

Selecione a opção `1` no menu.

O programa solicitará:

- Quantidade de linhas.
- Quantidade de colunas.
- Número máximo de gerações.
- Percentual inicial de espalhadores.
- Limiar de convencimento.

Exemplo de configuração:

```text
Quantidade de linhas: 5
Quantidade de colunas: 5
Numero maximo de geracoes: 10
Percentual inicial de espalhadores: 20
Limiar: 2
```

A execução apresentará as quantidades e os percentuais de indivíduos em cada estado, além do tempo total da simulação.

A versão sequencial também pode ser executada diretamente:

```bash
python3 sequencial.py
```

## 7. Execução paralela

Selecione a opção `2` no menu.

A implementação paralela divide o processamento da matriz entre múltiplas threads, mantendo a sincronização entre as gerações.

Além dos parâmetros da simulação, será solicitada a quantidade de trabalhadores.

Exemplo:

```text
Quantidade de linhas: 5
Quantidade de colunas: 5
Numero maximo de geracoes: 10
Percentual inicial de espalhadores: 20
Limiar: 2
Quantidade de trabalhadores: 2
```

O número de trabalhadores não pode ultrapassar a quantidade de linhas da matriz.

A utilização de threads permite estudar a divisão de tarefas e os custos de sincronização.

Entretanto, em implementações tradicionais do CPython com GIL habilitado, threads não garantem aceleração em tarefas intensivas em CPU.

## 8. Execução distribuída

Selecione a opção `3` no menu.

A implementação distribuída utiliza um coordenador e processos trabalhadores que se comunicam por sockets TCP.

Antes de executar a simulação, é necessário iniciar os trabalhadores.

### Iniciar dois trabalhadores

Abra um terminal e execute:

```bash
cd ~/fakenews_distribuidos
python3 worker.py --porta 5000
```

Em outro terminal:

```bash
cd ~/fakenews_distribuidos
python3 worker.py --porta 5001
```

Mantenha os dois terminais abertos.

Em um terceiro terminal, execute:

```bash
python3 main.py
```

Selecione a opção `3` e informe `2` trabalhadores.

Por padrão, a implementação utiliza o endereço `127.0.0.1`, com portas a partir de `5000`.

A variável de ambiente `FAKENEWS_WORKERS` permite configurar outros endereços de trabalhadores, conforme a implementação.

### Funcionamento

O coordenador distribui partes da matriz para os trabalhadores.

Os trabalhadores calculam suas regiões e devolvem os resultados ao coordenador, que organiza a próxima geração.

A comunicação e a sincronização introduzem custos adicionais que devem ser considerados na análise de desempenho.

A integração e o benchmark foram validados localmente com dois trabalhadores no mesmo computador. Isso não equivale a uma validação em múltiplos computadores físicos.

## 9. Benchmark e comparação de desempenho

O projeto possui um benchmark para medir e verificar as implementações.

No menu principal, selecione a opção `4`.

A configuração rápida integrada utiliza:

| Parâmetro | Configuração |
| --- | --- |
| Versões | Sequencial, paralela e distribuída |
| Matrizes | 5x5 e 10x10 |
| Repetições | 2 |
| Trabalhadores | 2 |
| Gerações máximas | 5 |
| Semente | 42 |

Os trabalhadores distribuídos devem estar iniciados antes da execução.

O benchmark verifica a equivalência das matrizes finais, das contagens e das entradas utilizadas.

### Executar pelo terminal

Também é possível executar diretamente:

```bash
python3 -B benchmark.py \
  --rapido \
  --versoes sequencial paralela distribuida \
  --trabalhadores 2
```

O benchmark gera arquivos CSV na pasta `resultados/`.

A opção integrada ao menu utiliza nomes exclusivos para os arquivos, evitando sobrescrever resultados anteriores.

### Política de medição

O tempo medido considera a chamada completa de cada implementação.

A preparação da matriz inicial, o carregamento dos módulos e a validação dos resultados não fazem parte do tempo cronometrado.

Na versão paralela, o tempo inclui a criação e a finalização das threads.

Na versão distribuída, inclui a comunicação e a sincronização, mas não o tempo necessário para iniciar os processos trabalhadores.

### Speedup e eficiência

O speedup pode ser calculado por:

```text
Speedup = Tempo sequencial / Tempo paralelo ou distribuido
```

A eficiência pode ser calculada por:

```text
Eficiencia = Speedup / Numero de trabalhadores
```

Essas métricas devem ser interpretadas considerando o ambiente, a quantidade de trabalhadores e a política de medição.

## 10. Resultados da integração

Durante a validação local, as três versões foram executadas com os seguintes parâmetros:

| Parâmetro | Valor |
| --- | --- |
| Matriz | 5x5 |
| Gerações máximas | 10 |
| Percentual inicial | 20% |
| Limiar | 2 |
| Trabalhadores paralelos | 2 |
| Trabalhadores distribuídos | 2 |
| Semente | 42 |

As três implementações apresentaram as mesmas contagens finais:

| Estado | Quantidade |
| --- | --- |
| Ignorantes | 7 |
| Espalhadores | 0 |
| Inativos | 18 |

O benchmark rápido da integração realizou 12 medições. A bateria oficial posterior contém **162 medições**, com matrizes 100×100, 300×300 e 500×500, percentuais 5% e 40%, três repetições e 1, 2, 4 e 6 trabalhadores nas versões paralela e distribuída. Consulte [o relatório oficial](resultados/RELATORIO_FINAL.md).

Nos cenários pequenos testados, a implementação sequencial apresentou os menores tempos de execução.

Esse resultado é compatível com os custos adicionais de sincronização entre threads e comunicação entre processos.

Os cenários rápidos executaram apenas uma geração. A bateria oficial executou três ou cinco gerações, mas manteve o limite máximo em 50. A coleta complementar foi executada no Windows com o código corrigido: **486 medições**, limites 1, 2 e 5, trabalhadores 1, 2, 4 e 8, três repetições. Foram produzidos 162 grupos, 144 comparações e 90 gráficos. Consulte [o relatório do reteste](resultados/reteste_20261119T232737979530Z/RELATORIO.md). Os baselines são da própria coleta; os resultados anteriores no Linux permanecem separados.

## 11. Testes automatizados

O projeto utiliza o módulo `unittest` da biblioteca padrão do Python.

Para executar os testes:

```bash
python3 -m unittest discover -v
```

Na revisão local, foram aprovados **40 testes automatizados** em Python 3.14.6 no Windows.

Os testes abrangem o sequencial, a integração com threads, as melhorias, as regressões do menu e da sincronização e a comunicação TCP real com workers locais. `testes_distribuido.py` inicia workers próprios em portas temporárias e encerra somente esses processos ao final; não exige iniciar servidores manualmente.

A equivalência entre as implementações também foi verificada pelo benchmark oficial nos cenários executados.

Para uma validação mais abrangente, recomenda-se testar diferentes dimensões, limiares, percentuais, quantidades de trabalhadores e regiões de fronteira.

## 12. Melhorias opcionais

O arquivo `melhorias.py` implementa três funcionalidades adicionais.

Essas melhorias não modificam o comportamento padrão das três implementações oficiais.

### Influenciadores

Alguns indivíduos espalhadores possuem maior capacidade de influenciar seus vizinhos.

Um espalhador comum contribui com peso `1`, enquanto um influenciador pode contribuir com um peso maior, como `3`.

### Resistência à desinformação

Determinados indivíduos precisam receber uma influência maior para se tornarem espalhadores.

Essa funcionalidade permite representar indivíduos mais resistentes à propagação de notícias falsas.

### Estatísticas por geração

A simulação pode registrar a quantidade de ignorantes, espalhadores e inativos em cada geração.

Isso permite acompanhar a evolução da propagação.

### Executar a demonstração

No menu principal, selecione a opção `5`.

Também é possível executar:

```bash
python3 melhorias.py
```

As melhorias possuem testes específicos no arquivo `testes_melhorias.py`.

## 13. Organização e desenvolvimento em equipe

O desenvolvimento foi dividido entre integrantes responsáveis pelas implementações, testes, benchmark, documentação e melhorias.

O trabalho utilizou branches individuais e integração por meio do Git e do GitHub.

O fluxo de colaboração inclui:

1. Desenvolvimento em branches separadas.
2. Commits das alterações.
3. Execução dos testes.
4. Abertura de Pull Requests.
5. Revisão e integração na branch principal.

As orientações completas estão disponíveis em `CONTRIBUTING.md`.

## 14. Limitações do projeto

As principais limitações observadas ou consideradas são:

- O GIL do CPython pode limitar o desempenho da versão com threads em tarefas intensivas em CPU.
- A comunicação por sockets introduz custos adicionais na implementação distribuída.
- Matrizes pequenas podem favorecer a execução sequencial.
- O desempenho depende do hardware e do ambiente de execução.
- A validação distribuída local não substitui testes em múltiplos computadores.
- O benchmark rápido não representa necessariamente cargas de trabalho maiores.
- As melhorias opcionais não fazem parte das comparações oficiais entre as três versões.

## 15. Documentação complementar

O repositório contém documentos adicionais sobre:

- Contrato das implementações.
- Cenários de testes.
- Funcionamento da versão distribuída.
- Referências técnicas.
- Resultados experimentais e análises.

Consulte os diretórios `docs/` e `resultados/` para mais informações.

## 16. Considerações finais

O projeto demonstra como uma mesma simulação pode ser implementada utilizando processamento sequencial, threads e comunicação distribuída por sockets.

As três abordagens permitem observar diferenças de arquitetura, sincronização, comunicação e desempenho.

A integração das implementações, a validação dos resultados e a realização dos benchmarks oferecem uma base prática para compreender conceitos de Sistemas Paralelos e Distribuídos.

Os resultados também mostram que utilizar mais trabalhadores não significa necessariamente executar mais rapidamente, especialmente quando o custo de coordenação supera o trabalho computacional realizado.
