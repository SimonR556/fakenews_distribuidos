# Teste padrão de equivalência

## Configuração

| Parâmetro | Valor |
| --- | --- |
| Linhas × colunas | 100 × 100 |
| Gerações máximas | 50 |
| Percentual inicial solicitado | 0,05 |
| Limiar | 3 |
| Semente | 42 |
| Threads / processos trabalhadores | 4 / 4 |
| Melhorias | Desativadas |

## Procedimento

1. Importar `criar_grade` de `FakeNews.py` e gerar **uma única** grade com os parâmetros acima.
2. Fazer uma cópia independente para cada versão, incluindo as linhas internas (`deepcopy`, por exemplo).
3. Executar as três implementações com os mesmos parâmetros. O sequencial ignora trabalhadores.
4. Medir com `time.perf_counter()`, sem criação da grade nem impressões na região cronometrada; documentar a política de inicialização dos trabalhadores.
5. Comparar as matrizes célula por célula, além das contagens e gerações realmente executadas.
6. Verificar que cada entrada permaneceu intacta. Encerrar após uma geração sem espalhadores, como no original.

A igualdade das contagens sozinha não comprova a igualdade das matrizes. O registro das gerações das novas versões depende da interface complementar pendente em [CONTRATO.md](CONTRATO.md).

## Referência verificada no original

O arquivo original foi executado em Python 3.14.6, com os parâmetros padrão de seu bloco principal, correspondentes a este teste:

| Etapa | Ignorantes | Espalhadores | Inativos |
| --- | ---: | ---: | ---: |
| Inicial | 9510 | 490 | 0 |
| Geração 1 | 9464 | 46 | 490 |
| Geração 2 | 9463 | 1 | 536 |
| Geração 3 | 9463 | 0 | 537 |

São **três gerações efetivas**. As 500 tentativas de posicionamento produzem 490 espalhadores distintos, pois há sorteios repetidos. Estes valores são uma referência de correção, não resultados das implementações do grupo. O tempo do original inclui impressão e não foi adotado como resultado comparativo.

## Registro a preencher após a implementação

| Versão | Tempo (s) | Gerações | Ignorantes | Espalhadores | Inativos |
| --- | --- | --- | --- | --- | --- |
| Sequencial refatorada | Pendente | Pendente | Pendente | Pendente | Pendente |
| Paralela | Pendente | Pendente | Pendente | Pendente | Pendente |
| Distribuída | Pendente | Pendente | Pendente | Pendente | Pendente |

- Matrizes finais idênticas: pendente.
- Entradas preservadas: pendente.
- Ambiente e commit: preencher na execução.
- Observações: preencher na execução.

Também testar 5 × 5, 10 × 10, cantos e bordas, contágio entre faixas, divisão de linhas com resto, zero gerações e ausência inicial de espalhadores. O teste padrão verifica correção; os benchmarks devem variar cenários e repetir execuções. Como a propagação termina cedo neste cenário, aumentar apenas o limite de 50 para 100 não aumenta necessariamente o trabalho realizado.
