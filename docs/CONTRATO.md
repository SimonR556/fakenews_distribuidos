# Contrato de integração

## Regras acordadas

`simular(grade_inicial, geracoes, limiar, trabalhadores)` recebe uma lista de listas com estados inteiros 0, 1 e 2 e retorna somente a grade final. A entrada não pode ser modificada, inclusive suas listas internas. O sequencial ignora `trabalhadores`.

Usar vizinhança de Moore sem contorno periódico. Ignorantes com pelo menos `limiar` vizinhos espalhadores tornam-se espalhadores; espalhadores tornam-se inativos; inativos permanecem inativos. A atualização é simultânea: leituras da geração atual e escritas na próxima.

O original verifica a ausência de espalhadores **após** atualizar e contar a geração. Portanto, com limite positivo, uma grade inicialmente sem espalhadores ainda passa por uma atualização. Com zero gerações, nenhuma atualização é feita. Manter essa ordem para preservar também a contagem de gerações. Não antecipar a parada antes do laço apenas em uma versão.

`criar_grade` usa sorteios com reposição: uma mesma posição pode ser sorteada várias vezes. Não substituir por amostragem de posições únicas em apenas uma versão.

## Interfaces e configuração integradas

As funções públicas `simular` preservam o contrato de quatro parâmetros.

- **Gerações:** `paralelo.simular_com_detalhes` e `distribuido.simular_com_estatisticas` retornam `(grade_final, geracoes_executadas)`. O benchmark conta gerações do sequencial em execução diagnóstica separada, fora do cronômetro. `melhorias.simular_com_estatisticas` retorna histórico, não uma contagem inteira.
- **Entradas inválidas:** o distribuído valida matriz, estados e parâmetros. O paralelo rejeita linhas vazias ou irregulares antes de iniciar threads; aceita grade vazia e limita threads ao número de linhas. A validação completa ainda não é uniforme entre versões. O menu gera matrizes válidas e limita trabalhadores ao número de linhas.
- **Configuração distribuída:** `FAKENEWS_WORKERS` define endereços `host:porta`, em quantidade igual aos trabalhadores. Sem a variável, usam-se portas locais a partir de 5000. Consulte [DISTRIBUIDO.md](DISTRIBUIDO.md).
- **Cronometragem:** mede-se a chamada completa. Threads são criadas e encerradas dentro dela; processos TCP ficam previamente iniciados. Conexões, transmissão e encerramento das conexões entram no tempo distribuído. Comparar somente dados com a mesma política registrada.

## Arquitetura da parte distribuída

Os itens abaixo descrevem a arquitetura implementada.

- `distribuido.py`: coordenador divide a matriz em faixas contíguas de linhas, envia tarefas, reúne respostas e decide a parada global.
- `worker.py`: processo separado calcula apenas suas linhas, lendo também uma linha de fronteira acima e outra abaixo, quando existirem.
- As fronteiras são cópias da geração atual e não entram nas linhas devolvidas. A faixa do topo não possui vizinho acima; a do fundo não possui vizinho abaixo.
- Enviar tarefas a todos os trabalhadores antes de aguardar o conjunto de resultados, permitindo cálculos concorrentes.
- Identificar geração e faixa nas mensagens; reconstruir a grade pela posição das linhas, nunca pela ordem de chegada.
- Só iniciar a próxima geração após receber e validar todas as faixas da geração atual.

Para 100 linhas e quatro trabalhadores, usando índices a partir de zero:

| Trabalhador | Linhas calculadas | Linhas adicionais de leitura |
| --- | --- | --- |
| 0 | 0–24 | 25 |
| 1 | 25–49 | 24 e 50 |
| 2 | 50–74 | 49 e 75 |
| 3 | 75–99 | 74 |

**Protocolo implementado:** TCP com cabeçalho de quatro bytes sem sinal em ordem de rede (`struct.pack("!I", tamanho)`) e corpo JSON em UTF-8. O tamanho deve ser o número de bytes codificados, não o número de caracteres. Usar envio completo e leitura em laço tanto do cabeçalho quanto do corpo: um `recv` não equivale necessariamente a uma mensagem inteira. Documentar limite de tamanho, desconexões e timeouts.

As mensagens incluem tipo, geração, início da faixa, linhas, limiar e fronteiras; a resposta identifica a tarefa e contém apenas as linhas calculadas. Há mensagens de encerramento e confirmação. Ainda não existe um campo explícito de versão do protocolo; veja tipos e limitações em DISTRIBUIDO.md.

Começar em `127.0.0.1`. Para múltiplas máquinas, documentar endereço de escuta, IP acessível, porta TCP, ordem de inicialização e conectividade de rede. Usar uma rede confiável; este protocolo acadêmico ainda não define autenticação ou criptografia. Manter processos vivos entre gerações é uma possível otimização a medir.
