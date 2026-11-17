# Implementação distribuída com sockets

## Arquivos e dependências

- `distribuido.py`: coordenador, divisão da matriz e teste de equivalência.
- `worker.py`: processo trabalhador e funções de comunicação.
- `FakeNews.py`: código original, usado para gerar a entrada e calcular a referência.

Requer Python 3. A implementação foi testada com Python 3.14.6 no Windows.
Utiliza somente bibliotecas padrão: socket, json, struct, argparse, os,
contextlib, copy e time.

## Executar em localhost

Abra quatro terminais na raiz do projeto e execute um comando em cada um:

```powershell
python worker.py --porta 5000
python worker.py --porta 5001
python worker.py --porta 5002
python worker.py --porta 5003
```

Em um quinto terminal, execute:

```powershell
python distribuido.py
```

O teste padrão utiliza matriz 100 × 100, até 50 gerações, percentual
inicial 0,05, semente 42, limiar 3 e quatro trabalhadores.

Resultado verificado:

- 490 espalhadores iniciais.
- 3 gerações executadas.
- 9463 ignorantes, 0 espalhadores e 537 inativos.
- Matriz final idêntica à referência original.
- Matriz inicial preservada.

Os workers permanecem ativos após a simulação. É possível executar
novamente o coordenador sem reiniciá-los. Para desligá-los, pressione
Ctrl+C em cada terminal.

## Interface para integração

```python
from distribuido import simular

grade_final = simular(
    grade_inicial,
    geracoes,
    limiar,
    trabalhadores
)
```

A função retorna somente a matriz final e não modifica a entrada.

Para obter também o número de gerações executadas:

```python
from distribuido import simular_com_estatisticas

grade_final, geracoes_executadas = simular_com_estatisticas(
    grade_inicial,
    geracoes,
    limiar,
    trabalhadores
)
```

Os workers precisam estar iniciados antes da chamada.
Cada worker atende uma conexão de simulação por vez.

Sem configuração adicional, são usadas as portas a partir de 5000 em
127.0.0.1. Por exemplo, dois trabalhadores usam 5000 e 5001.

## Execução em computadores diferentes

Todos os computadores devem possuir Python e uma cópia compatível do
código. O coordenador e os workers devem ter conectividade pela rede.

Em cada máquina trabalhadora, iniciar o worker com:

```powershell
python worker.py --host 0.0.0.0 --porta 5000
```

Permitir a porta TCP utilizada no firewall para o coordenador, em uma
rede confiável. Não é necessário expor o serviço à internet.

No terminal PowerShell do coordenador, configurar os endereços reais.
Exemplo para dois trabalhadores em máquinas distintas:

```powershell
$env:FAKENEWS_WORKERS = "192.168.0.10:5000,192.168.0.11:5000"
```

Nesse exemplo, chamar `simular` com `trabalhadores=2`.
O teste executado por `python distribuido.py` usa quatro trabalhadores;
para ele, fornecer quatro endereços.

Cada endereço deve identificar um processo worker. Processos na mesma
máquina precisam de portas distintas.

O endereço 0.0.0.0 é usado para escuta; o coordenador deve conectar ao
IP real da máquina.

Para remover a configuração e retornar aos endereços locais automáticos:

```powershell
Remove-Item Env:FAKENEWS_WORKERS -ErrorAction SilentlyContinue
```

A configuração de endereços foi testada em localhost. A execução entre
computadores diferentes ainda não foi validada.

## Divisão e sincronização

A matriz é dividida em faixas contíguas de linhas. As sobras são
distribuídas entre os primeiros trabalhadores.

Cada tarefa contém:

- As linhas que o worker deve calcular.
- Uma linha de fronteira acima, quando existir.
- Uma linha de fronteira abaixo, quando existir.
- Limiar, número da geração e índice inicial da faixa.

As fronteiras são usadas somente para leitura. O worker devolve apenas
as linhas de sua região.

O coordenador envia todas as tarefas antes de receber as respostas.
Ele valida a identificação e as dimensões dos resultados e monta a
próxima matriz na ordem das faixas.

A próxima geração só começa após receber todos os resultados da geração
atual. A ausência de espalhadores é verificada após essa atualização,
como no original.

## Protocolo de comunicação

A comunicação utiliza TCP. Cada mensagem tem:

1. Cabeçalho de 4 bytes: inteiro sem sinal em ordem de rede (`!I`).
2. Corpo JSON codificado em UTF-8.

O cabeçalho informa o tamanho do corpo em bytes.
O recebimento ocorre em laço, pois uma chamada a `recv` pode retornar
apenas parte da mensagem. O envio utiliza `sendall`.

O receptor aceita corpos de até 64 MiB. As operações nas conexões
possuem timeout de 60 segundos.

| Tipo | Finalidade |
| --- | --- |
| `ping` / `pong` | Verificação de comunicação |
| `calcular` | Envia geração, início, linhas, fronteiras e limiar |
| `resultado` | Devolve geração, início e linhas calculadas |
| `encerrar` / `encerrado` | Finaliza a conexão da simulação |
| `erro` | Informa tipo de mensagem desconhecido |

A mensagem `encerrar` não desliga o processo worker: ele volta a
aguardar outra conexão.

## Validações e limitações

O coordenador exige:

- Matriz não vazia, retangular e formada por listas de listas.
- Estados inteiros 0, 1 ou 2.
- Gerações e limiar inteiros não negativos.
- Quantidade inteira de trabalhadores entre 1 e o número de linhas.
- Quantidade de endereços configurados igual à de trabalhadores.

Com zero gerações, retorna uma cópia independente sem abrir conexões.

Em caso de falha, não há recuperação automática da simulação.
O coordenador fecha suas conexões; o worker trata erros previstos e
volta a aguardar uma nova conexão.

O protocolo não implementa autenticação ou criptografia e pressupõe
workers confiáveis.

A cada geração são enviados os blocos completos com suas fronteiras.
Isso simplifica a implementação, mas adiciona custos de serialização,
comunicação e memória. O coordenador também concentra a distribuição
e reunião dos resultados.

## Testes realizados

| Cenário | Resultado |
| --- | --- |
| Região com fronteiras acima e abaixo | Igual à região correspondente do original |
| 5 × 5, percentual 0,40, quatro workers | Equivalência; 2 gerações |
| 10 × 10, percentual 0,40, quatro workers | Equivalência; 4 gerações |
| 100 × 100, percentual 0,05, quatro workers | Equivalência; 3 gerações |
| 100 × 100 com 1, 2, 3 e 4 workers | Mesma matriz e gerações; entrada preservada |
| Execuções consecutivas | Workers reutilizados corretamente |
| Configuração de endereços por variável de ambiente | Validada em localhost |
| Zero gerações | Cópia independente da entrada |
| Estado inválido 9 | Rejeitado com ValueError |

Os testes de equivalência usaram semente 42, limiar 3 e até 50 gerações.

## Medição de desempenho

O tempo mostrado pelo teste inclui validação da entrada, cópia da matriz,
conexões, comunicação, cálculo, sincronização e encerramento das conexões.

Não inclui a inicialização manual dos processos trabalhadores,
a geração da matriz inicial, o cálculo da referência ou as impressões
finais do coordenador.

Os workers imprimem mensagens de conexão e encerramento. Para os
experimentos finais, avaliar a desativação desses logs e documentar
a política de medição.

Os tempos observados nos testes são verificações iniciais, não um
benchmark conclusivo. Não comparar diretamente com o tempo impresso
pelo original, que inclui saída no terminal.

## Referências e apoio

- Código `FakeNews.py` fornecido pelo professor.
- Documentação Python — Socket Programming HOWTO:
  https://docs.python.org/3/howto/sockets.html
- ChatGPT: apoio na elaboração e explicação do código, diagnóstico
  de erros e preparação dos testes. A execução dos testes e rascunho do código foi realizada
  pelo integrante responsável.
