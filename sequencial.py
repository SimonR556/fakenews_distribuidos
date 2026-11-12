from copy import deepcopy

IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2


def contar_vizinhos_espalhadores(grade, i, j):
    """
    Conta os vizinhos espalhadores de uma célula
    utilizando a vizinhança de Moore (até 8 vizinhos).
    """
    linhas = len(grade)
    colunas = len(grade[0])
    total = 0

    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):

            # Ignora a própria célula.
            if di == 0 and dj == 0:
                continue

            ni = i + di
            nj = j + dj

            # Verifica se o vizinho está dentro da matriz.
            if 0 <= ni < linhas and 0 <= nj < colunas:
                if grade[ni][nj] == ESPALHADOR:
                    total += 1

    return total


def proxima_geracao(grade, limiar=2):
    """
    Calcula uma geração completa.

    Todas as leituras são realizadas na matriz atual,
    enquanto as alterações são feitas em uma cópia.
    """
    linhas = len(grade)
    colunas = len(grade[0])

    nova_grade = deepcopy(grade)

    for i in range(linhas):
        for j in range(colunas):

            estado = grade[i][j]

            if estado == IGNORANTE:
                vizinhos = contar_vizinhos_espalhadores(
                    grade, i, j
                )

                if vizinhos >= limiar:
                    nova_grade[i][j] = ESPALHADOR

            elif estado == ESPALHADOR:
                nova_grade[i][j] = INATIVO

            elif estado == INATIVO:
                nova_grade[i][j] = INATIVO

    return nova_grade


def contar_estados(grade):
    """
    Conta a quantidade de indivíduos em cada estado.
    """
    contagem = {
        IGNORANTE: 0,
        ESPALHADOR: 0,
        INATIVO: 0
    }

    for linha in grade:
        for estado in linha:
            contagem[estado] += 1

    return contagem


def simular(grade_inicial, geracoes, limiar=2, trabalhadores=1):
    """
    Executa a simulação sequencial.

    Parâmetros:
        grade_inicial: matriz inicial da população.
        geracoes: número máximo de gerações.
        limiar: mínimo de vizinhos para convencimento.
        trabalhadores: mantido para compatibilidade.

    Retorno:
        Matriz final após a simulação.

    A matriz inicial não é modificada.
    """
    # Cria uma cópia independente da matriz recebida.
    grade = deepcopy(grade_inicial)

    # A versão sequencial não utiliza trabalhadores.
    # O parâmetro existe para manter a interface comum.
    for _ in range(geracoes):

        # Calcula a próxima geração.
        grade = proxima_geracao(grade, limiar)

        # Verifica se ainda existem espalhadores.
        contagem = contar_estados(grade)

        if contagem[ESPALHADOR] == 0:
            break

    return grade


if __name__ == "__main__":
    # Exemplo de execução independente.
    from FakeNews import criar_grade

    grade_inicial = criar_grade(
        linhas=100,
        colunas=100,
        percentual_espalhadores=0.05,
        semente=42
    )

    resultado = simular(
        grade_inicial=grade_inicial,
        geracoes=50,
        limiar=3,
        trabalhadores=1
    )

    print("=== SIMULAÇÃO SEQUENCIAL ===")
    print("Matriz: 100 x 100")
    print("Gerações máximas: 50")
    print("Limiar: 3")
    print()

    contagem = contar_estados(resultado)

    print(f"Ignorantes: {contagem[IGNORANTE]}")
    print(f"Espalhadores: {contagem[ESPALHADOR]}")
    print(f"Inativos: {contagem[INATIVO]}")
