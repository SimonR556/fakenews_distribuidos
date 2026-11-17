"""Implementação paralela da propagação de fake news usando threads.

A estratégia adotada é dividir a matriz por linhas entre várias threads.
Cada thread processa apenas um conjunto de linhas da geração atual e grava
apenas as linhas correspondentes na próxima geração. A matriz atual permanece
imutável durante o cálculo de uma geração, preservando a semântica da versão
sequencial (sem atualização em tempo real).

Sincronização:
- Todas as threads leem a mesma matriz de entrada (`grade`).
- Cada thread escreve em um subconjunto disjunto de linhas da `nova_grade`.
- Uma barreira sincroniza o fim da geração: todas as threads devem concluir
  antes que a próxima geração seja iniciada.
"""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier

IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2


def contar_vizinhos_espalhadores(grade, i, j):
    """Conta quantos vizinhos de Moore são espalhadores."""
    linhas = len(grade)
    colunas = len(grade[0])
    total = 0

    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue

            ni = i + di
            nj = j + dj

            if 0 <= ni < linhas and 0 <= nj < colunas:
                if grade[ni][nj] == ESPALHADOR:
                    total += 1

    return total


def _distribuir_linhas(total_linhas, numero_threads):
    """Divide as linhas em faixas contíguas para as threads."""
    if numero_threads <= 0:
        raise ValueError("O número de threads deve ser maior que zero.")

    numero_threads = min(numero_threads, total_linhas)

    faixas = []
    inicio = 0
    base = total_linhas // numero_threads
    resto = total_linhas % numero_threads

    for indice in range(numero_threads):
        tamanho = base + (1 if indice < resto else 0)
        fim = inicio + tamanho
        faixas.append((inicio, fim))
        inicio = fim

    return faixas


def _processar_linhas(grade, proxima_grade, inicio, fim, limiar, barreira):
    """Calcula uma fatia de linhas da próxima geração.

    Cada thread acessa somente a matriz de entrada atual (`grade`) e grava uma
    faixa de linhas exclusiva na `proxima_grade`. Como não há sobreposição de
    linhas, não precisamos de lock na escrita.
    """
    linhas = len(grade)
    colunas = len(grade[0])

    for i in range(inicio, fim):
        for j in range(colunas):
            estado = grade[i][j]

            if estado == IGNORANTE:
                vizinhos = contar_vizinhos_espalhadores(grade, i, j)
                if vizinhos >= limiar:
                    proxima_grade[i][j] = ESPALHADOR
                else:
                    proxima_grade[i][j] = IGNORANTE

            elif estado == ESPALHADOR:
                proxima_grade[i][j] = INATIVO

            elif estado == INATIVO:
                proxima_grade[i][j] = INATIVO

    # Sincroniza o fim do processamento da geração antes de avançar.
    barreira.wait()


def proxima_geracao(grade, limiar=2, trabalhadores=4):
    """Calcula a próxima geração usando threads.

    Todas as threads leem a geração atual; nenhuma altera a matriz atual. O
    resultado é escrito em uma cópia da grade, garantindo atualização em lote.
    """
    if not grade:
        return []

    linhas = len(grade)
    colunas = len(grade[0])
    proxima_grade = deepcopy(grade)

    faixas = _distribuir_linhas(linhas, trabalhadores)
    barreira = Barrier(len(faixas))

    with ThreadPoolExecutor(max_workers=len(faixas)) as executor:
        tarefas = [
            executor.submit(
                _processar_linhas,
                grade,
                proxima_grade,
                inicio,
                fim,
                limiar,
                barreira,
            )
            for inicio, fim in faixas
        ]

        for tarefa in tarefas:
            tarefa.result()

    return proxima_grade


def contar_estados(grade):
    """Conta a quantidade de células em cada estado."""
    contagem = {
        IGNORANTE: 0,
        ESPALHADOR: 0,
        INATIVO: 0,
    }

    for linha in grade:
        for estado in linha:
            contagem[estado] += 1

    return contagem


def simular(grade_inicial, geracoes, limiar=2, trabalhadores=4):
    """Executa a simulação paralela com sincronização por geração.

    A interface foi mantida compatível com a versão sequencial: retorna apenas
    a grade final. Caso seja necessário acompanhar o número de gerações
    efetivamente executadas, use a função `simular_com_detalhes`.
    """
    grade = deepcopy(grade_inicial)

    for _ in range(geracoes):
        grade = proxima_geracao(grade, limiar, trabalhadores)

        contagem = contar_estados(grade)
        if contagem[ESPALHADOR] == 0:
            break

    return grade


def simular_com_detalhes(grade_inicial, geracoes, limiar=2, trabalhadores=4):
    """Executa a simulação e retorna `(grade_final, geracoes_executadas)`.

    Esta variante é útil para testes de correção e benchmark, porque informa a
    quantidade real de gerações calculadas.
    """
    grade = deepcopy(grade_inicial)
    geracoes_executadas = 0

    for _ in range(geracoes):
        grade = proxima_geracao(grade, limiar, trabalhadores)
        geracoes_executadas += 1

        contagem = contar_estados(grade)
        if contagem[ESPALHADOR] == 0:
            break

    return grade, geracoes_executadas


if __name__ == "__main__":
    from FakeNews import criar_grade

    grade_inicial = criar_grade(
        linhas=100,
        colunas=100,
        percentual_espalhadores=0.05,
        semente=42,
    )

    resultado, geracoes = simular_com_detalhes(
        grade_inicial=grade_inicial,
        geracoes=50,
        limiar=3,
        trabalhadores=4,
    )

    contagem = contar_estados(resultado)
    print("=== SIMULAÇÃO PARALELA ===")
    print(f"Threads: 4")
    print(f"Gerações executadas: {geracoes}")
    print(f"Ignorantes: {contagem[IGNORANTE]}")
    print(f"Espalhadores: {contagem[ESPALHADOR]}")
    print(f"Inativos: {contagem[INATIVO]}")
