# Propagação de Fake News em Sistemas Paralelos e Distribuídos

Trabalho acadêmico da UTFPR — Campus Cornélio Procópio. O projeto transforma uma simulação sequencial em versões paralela e distribuída e compara correção, desempenho e custos de sincronização e comunicação.

> **Estado atual:** organização inicial e código original do professor disponíveis. As implementações do grupo, os benchmarks e as melhorias ainda serão desenvolvidos. Não há resultados comparativos nesta etapa.

## Modelo da simulação

A população é uma matriz de listas de listas do Python, com os estados:

| Valor | Estado | Transição na próxima geração |
| --- | --- | --- |
| `0` | Ignorante | Torna-se espalhador se tiver pelo menos `limiar` vizinhos espalhadores |
| `1` | Espalhador | Torna-se inativo |
| `2` | Inativo | Permanece inativo |

A vizinhança de Moore considera até oito vizinhos, sem incluir a própria célula e sem conectar bordas opostas. Todas as células leem a geração anterior e escrevem na próxima. O cálculo termina ao atingir o limite de gerações ou quando não restam espalhadores, com a verificação de parada após cada geração, como no original.

## Começar pelo código original

Pré-requisitos: Git e Python 3. O código original usa apenas a biblioteca padrão (`random`, `time` e `copy`). Execução inicial verificada com Python 3.14.6; a versão comum da equipe ainda deve ser combinada.

```bash
git clone https://github.com/SimonR556/fakenews_distribuidos.git
cd fakenews_distribuidos
python --version
python FakeNews.py
```

No Windows, `py` pode substituir `python`, se esse for o comando disponível. Em alguns ambientes Linux, use `python3`. Não há dependências externas para executar o original.

`FakeNews.py` é uma cópia preservada do material do professor. As alterações devem ser feitas nos módulos do grupo. O tempo impresso pelo original inclui saída no terminal e não deve ser usado diretamente como baseline do benchmark sem padronizar a medição.

## Organização e responsabilidades

Os arquivos marcados como planejados ainda não foram criados. Cada integrante pode começar a partir do original, sem esperar os demais.

| Arquivo ou pasta | Responsável | Finalidade / situação |
| --- | --- | --- |
| `FakeNews.py` | Referência do professor | Código sequencial original preservado |
| `sequencial.py`, `testes.py` | Integrante 1 | Refatoração, configuração e validação — planejados |
| `paralelo.py` | Integrante 2 | Divisão de linhas com `threading` — planejado |
| `distribuido.py`, `worker.py` | Integrante 3 — Thiago | Coordenador e trabalhadores com `socket` — planejados |
| `benchmark.py`, `resultados/` | Integrante 4 | Medições, tabelas e gráficos — implementação planejada |
| `melhorias.py` | Integrante 5 | Extensões opcionais — planejado |
| `docs/` | Equipe | Contrato, testes, referências e decisões técnicas |
| `CONTRIBUTING.md` | Equipe | Branches, commits e Pull Requests |
| `.github/pull_request_template.md` | Equipe | Checklist de revisão |

Não alterar arquivos de outro responsável sem combinar previamente. Documentar bibliotecas adicionais e sua finalidade. Não usar NumPy vetorizado, Pandas, Numba, Cython, GPU/CUDA ou frameworks para paralelizar automaticamente o cálculo das gerações.

## Contrato comum

Cada implementação principal deverá oferecer:

```python
def simular(grade_inicial, geracoes, limiar, trabalhadores):
    # Retorna somente a matriz final, sem modificar grade_inicial.
    ...
```

Este trecho documenta a interface; não é uma implementação. A versão sequencial ignora `trabalhadores`. A versão paralela usa threads e a distribuída usa processos separados que trocam mensagens por sockets. Todas devem produzir a mesma matriz final para entradas idênticas.

Consulte [o contrato e as decisões de integração](docs/CONTRATO.md), incluindo a pendência sobre como registrar gerações executadas sem alterar o retorno de `simular`.

## Desenvolvimento em equipe

Usar branches no padrão `nome/arquivo-arquivo`, em minúsculas, sem acentos, espaços ou extensão `.py`. Exemplo da parte distribuída: `thiago/distribuido-worker`. Para documentação: `thiago/readme-organizacao`.

Ao concluir uma entrega, abrir um Pull Request para `main`, descrever as mudanças e os testes e solicitar revisão a outro integrante. O [guia de contribuição](CONTRIBUTING.md) apresenta os comandos. Revisão é uma convenção da equipe; esta documentação não configura proteção automática da branch.

## Validação e desempenho

O [teste padrão](docs/TESTE_PADRAO.md) usa uma única grade 100 × 100, até 50 gerações, percentual inicial 0,05, limiar 3, semente 42 e quatro trabalhadores. Comparar as matrizes célula por célula, as contagens e o número de gerações. Também testar grades 5 × 5, 10 × 10 e regiões de fronteira.

O benchmark deverá variar tamanho, gerações máximas, percentual inicial e quantidade de trabalhadores; repetir medições e registrar o número de gerações realmente executadas. Criar a grade antes do cronômetro e não imprimir dentro da região medida.

- **Speedup:** `S(p) = T_sequencial / T_p`.
- **Eficiência:** `E(p) = S(p) / p`; multiplicar por 100 para percentual.
- `p` representa os trabalhadores de cálculo. Registrar separadamente o coordenador, a quantidade de hosts e os núcleos disponíveis.
- Registrar CPU, núcleos físicos/lógicos, RAM, SO, Python, ambiente e, em múltiplos hosts, rede e configuração de cada máquina.
- Explicitar se o tempo inclui criação de threads/processos, conexão, comunicação e encerramento; não misturar políticas entre resultados.

Em CPython com GIL habilitado, threads não executam simultaneamente o bytecode Python de tarefas intensivas em CPU. A versão com `threading` continua sendo a escolha da equipe, mas aceleração não é garantida. Esse limite e o custo dos sockets devem entrar na análise, mesmo quando houver perda de desempenho. Veja as [referências técnicas](docs/REFERENCIAS.md).

## Melhorias e entrega

As melhorias ficam em `melhorias.py`, opcionais e desativadas por padrão. Cada uma precisa de justificativa, documentação e testes. Mudanças na dinâmica só podem entrar nas comparações depois de integradas a todas as versões comparadas. Possibilidades: probabilidades de convencimento, influenciadores, bots, resistência e estatísticas adicionais. A pontuação de cada melhoria depende da avaliação do professor.

A entrega final inclui código compactado com instruções e apresentação em PDF, com modelo, divisão do processamento, sincronização, resultados, speedup, eficiência, gargalos, melhorias, limitações, referências e contribuição individual. A apresentação dura 15–20 minutos; todos participam e devem compreender as decisões e demonstrar as versões paralela e distribuída.

## Próximas etapas

- [ ] Confirmar nomes dos integrantes e versão comum do Python.
- [ ] Combinar a interface complementar para estatísticas e a política de medição.
- [ ] Desenvolver cada módulo em sua branch.
- [ ] Validar equivalência com o original e integrar por Pull Requests.
- [ ] Executar benchmarks reais e integrar melhorias selecionadas.
- [ ] Preparar referências, slides e demonstração.

O uso de fontes externas e IA deve ser registrado. Consulte [referências e registro de apoio](docs/REFERENCIAS.md).
