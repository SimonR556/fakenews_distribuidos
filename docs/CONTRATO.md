# Contrato de integração

## Regras acordadas

`simular(grade_inicial, geracoes, limiar, trabalhadores)` recebe uma lista de listas com estados inteiros 0, 1 e 2 e retorna somente a grade final. A entrada não pode ser modificada, inclusive suas listas internas. O sequencial ignora `trabalhadores`.

Usar vizinhança de Moore sem contorno periódico. Ignorantes com pelo menos `limiar` vizinhos espalhadores tornam-se espalhadores; espalhadores tornam-se inativos; inativos permanecem inativos. A atualização é simultânea: leituras da geração atual e escritas na próxima.

O original verifica a ausência de espalhadores **após** atualizar e contar a geração. Portanto, com limite positivo, uma grade inicialmente sem espalhadores ainda passa por uma atualização. Com zero gerações, nenhuma atualização é feita. Manter essa ordem para preservar também a contagem de gerações. Não antecipar a parada antes do laço apenas em uma versão.

`criar_grade` usa sorteios com reposição: uma mesma posição pode ser sorteada várias vezes. Não substituir por amostragem de posições únicas em apenas uma versão.

## Pendências para combinar antes da integração

Estas são propostas, não alterações já aprovadas do contrato:

1. **Estatísticas:** acrescentar uma função auxiliar `simular_com_estatisticas(...)` que retorne matriz e gerações executadas, mantendo `simular(...)` com retorno somente da matriz. Definir um formato único antes de conectar o benchmark. Não usar contagem inferida da matriz final.
2. **Entradas inválidas:** definir tratamento de matriz vazia ou irregular, estados inválidos, gerações negativas, limiar fora da faixa escolhida e trabalhadores não positivos. Testar também mais trabalhadores do que linhas e divisão com resto.
3. **Configuração distribuída:** definir como fornecer hosts/portas sem quebrar os quatro parâmetros comuns, e como iniciar/encerrar workers em localhost.
4. **Cronometragem:** definir a inclusão dos custos de inicialização, conexão e encerramento. Se houver tempo total e tempo com workers já prontos, identificá-los separadamente.

## Arquitetura sugerida para a parte distribuída

Esta seção orienta a implementação futura; não descreve código já disponível.

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

**Proposta de protocolo:** TCP com cabeçalho de quatro bytes sem sinal em ordem de rede (`struct.pack("!I", tamanho)`) e corpo JSON em UTF-8. O tamanho deve ser o número de bytes codificados, não o número de caracteres. Usar envio completo e leitura em laço tanto do cabeçalho quanto do corpo: um `recv` não equivale necessariamente a uma mensagem inteira. Documentar limite de tamanho, desconexões e timeouts.

O formato definitivo deve documentar versão do protocolo, tipo de mensagem, geração, início da faixa, quantidade de linhas, limiar, dados e fronteiras; a resposta identifica a mesma tarefa e inclui apenas as linhas calculadas. Prever encerramento e erro explícitos.

Começar em `127.0.0.1`. Para múltiplas máquinas, documentar endereço de escuta, IP acessível, porta TCP, ordem de inicialização e conectividade de rede. Usar uma rede confiável; este protocolo acadêmico ainda não define autenticação ou criptografia. Manter processos vivos entre gerações é uma possível otimização a medir.
