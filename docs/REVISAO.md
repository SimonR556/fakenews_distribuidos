# Revisão de integração — 19/11/2026

## Correções

- `main.py`: trata `ValueError` ao executar simulações e orienta conferir `FAKENEWS_WORKERS`. Uma quantidade incompatível de endereços não encerra mais o menu com traceback.
- `paralelo.py`: remove a barreira interna. O coordenador continua aguardando todos os `Future.result()` e o encerramento do executor antes de devolver a geração. Cada thread lê a mesma grade e escreve somente sua faixa; a divisão explícita do cálculo permanece.
- A versão paralela rejeita linhas vazias ou irregulares antes de criar o executor. A remoção da barreira também permite propagar falhas de cálculo sem prender outras threads nela.

## Testes

```bash
python -B -m unittest discover -v
```

Validação local: 40 testes aprovados em Python 3.14.6 no Windows. Os novos testes cobrem erro de configuração no menu, falha injetada em uma thread, rejeição de matriz irregular e workers TCP reais em portas temporárias. São verificados fronteiras, divisão com sobra, 5×5, 10×10, 100×100, zero gerações sem conexão, limiar zero, ausência inicial de espalhadores e reutilização de workers.

Os testes encerram somente os processos que iniciam. O teste de falha em thread usa subprocesso com timeout para que uma regressão não bloqueie toda a suíte.

## Coleta realizada e reprodução alternativa

A coleta foi **executada em 19/11/2026 no Windows**, com Ryzen 7 5700X, 8 núcleos físicos e CPython 3.14.6. Os 40 testes e as 486 medições passaram nas validações. Foram usados 1, 2, 4 e **8** trabalhadores; os baselines sequenciais são desta mesma coleta. Veja [o relatório completo](../resultados/reteste_20261119T232737979530Z/RELATORIO.md). O script `python -B -u retestar.py` automatiza testes, workers, coleta e análise em pasta nova (Matplotlib é necessário para os PNGs).

O roteiro manual abaixo permanece como **alternativa de reprodução no Linux**, com 1, 2, 4 e **6** trabalhadores. Essa alternativa não é a coleta Windows realizada. Usar o mesmo hardware para as três versões em qualquer nova coleta. Os resultados antigos são históricos: a fonte de `paralelo.py` mudou, portanto seus tempos não representam a nova implementação. Reexecutar as três versões juntas e não misturar baselines de ambientes ou fontes diferentes.

1. Executar a suíte de testes.
2. Iniciar seis workers, um comando em cada terminal na raiz do projeto:

```bash
python -B -u worker.py --porta 5000
python -B -u worker.py --porta 5001
python -B -u worker.py --porta 5002
python -B -u worker.py --porta 5003
python -B -u worker.py --porta 5004
python -B -u worker.py --porta 5005
```

3. Em outro terminal Bash, na raiz do projeto, executar:

```bash
unset FAKENEWS_WORKERS
rodada=$(date -u +%Y%m%dT%H%M%S)
csv="resultados/benchmark_geracoes_${rodada}.csv"
analise="resultados/analise_geracoes_${rodada}"

python -B benchmark.py \
  --versoes sequencial paralela distribuida \
  --tamanhos 100x100 300x300 500x500 \
  --percentuais 0.05 0.40 \
  --geracoes 1 2 5 \
  --limiar 3 --semente 42 \
  --repeticoes 3 --trabalhadores 1 2 4 6 \
  --saida "$csv" && \
python -B analisar_resultados.py "$csv" --saida "$analise"
```

São 18 cenários, nove configurações por cenário e três repetições: **486 medições**. A análise deve produzir 162 grupos descritivos e 144 comparações, se o ambiente estiver completo e compatível. Os destinos são novos; o programa recusa sobrescrever arquivos existentes. Para PNGs, é necessário Matplotlib, como no ambiente oficial anterior.

Os limites 1, 2 e 5 permitem observar diferentes quantidades de trabalho nos cenários atuais. O campo `geracoes_executadas` informa a parada real; limite 5 não garante cinco gerações em todos os cenários. Aumentar somente 50 para 100 não resolveria essa variação quando a simulação termina antes.

4. Conferir equivalência e gerações, atualizar a análise dos novos dados e encerrar os próprios workers com Ctrl+C. Não copiar tempos ou conclusões de desempenho da bateria anterior para a nova.

No Windows, usar `python`, remover a variável com `Remove-Item Env:FAKENEWS_WORKERS -ErrorAction SilentlyContinue` e adaptar a continuação de linhas para PowerShell. O coletor foi ampliado para Windows: núcleos físicos são consultados pela API GetLogicalProcessorInformationEx, RAM por GlobalMemoryStatusEx e nome da CPU pelo registro. Campos indisponíveis continuam desconhecidos; a análise não inventa metadados para permitir comparações.

## Fundamentação e entrega

As referências de apoio à revisão e a relação com as decisões estão em REFERENCIAS.md. A equipe deve ler e compreender as fontes antes de apresentá-las; pesos e resistência extra são parâmetros didáticos, sem calibração empírica. Ainda é necessário identificar o docente e a data do código fornecido.

Após a coleta, atualizar o relatório e preparar o PDF e o código compactado. Os slides devem incluir contribuições individuais e o registro de apoio de IA. A revisão não cria commits, PRs nem altera dados experimentais históricos.

## Apoio de IA

Codex/ChatGPT apoiou a revisão, as correções do menu e sincronização, a implementação dos testes de regressão e TCP, a atualização documental e a seleção de referências. Os testes e a coleta Windows foram executados; o roteiro manual Linux é uma alternativa para outra rodada. A equipe é responsável pela revisão humana, compreensão e validação no ambiente final.
