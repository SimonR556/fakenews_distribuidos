
"""
melhorias.py

Integrante 5 - Melhorias opcionais da simulacao de Fake News.

Funcionalidades:
1. Influenciadores com maior poder de propagacao.
2. Individuos resistentes a desinformacao.
3. Estatisticas da propagacao por geracao.

As melhorias sao opcionais e nao modificam os modulos
sequencial.py, paralelo.py ou distribuido.py.
"""

from copy import deepcopy

from sequencial import contar_estados, simular


# ============================================================
# CONSTANTES
# ============================================================

IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2


# ============================================================
# FUNCOES AUXILIARES
# ============================================================

def obter_contagem(grade):
    """
    Retorna a quantidade de individuos em cada estado.

    contar_estados() retorna um dicionario cujas
    chaves sao 0, 1 e 2.
    """
    contagem = contar_estados(grade)

    return {
        "ignorantes": contagem[IGNORANTE],
        "espalhadores": contagem[ESPALHADOR],
        "inativos": contagem[INATIVO]
    }


def existem_espalhadores(grade):
    """
    Verifica se ainda existem espalhadores na matriz.
    """
    contagem = contar_estados(grade)
    return contagem[ESPALHADOR] > 0


def contar_influencia(
    grade,
    i,
    j,
    influenciadores,
    peso=3
):
    """
    Calcula a influencia recebida por uma celula.

    Espalhador comum: influencia 1.
    Influenciador espalhador: influencia configuravel.

    Utiliza vizinhanca de Moore, sem contorno periodico.
    """
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

                    if (ni, nj) in influenciadores:
                        total += peso
                    else:
                        total += 1

    return total


# ============================================================
# MELHORIA 1 - INFLUENCIADORES
# ============================================================

def proxima_geracao_influenciadores(
    grade,
    limiar,
    influenciadores,
    peso=3
):
    """
    Calcula uma geracao considerando influenciadores.

    A matriz original nao e modificada.
    """
    linhas = len(grade)
    colunas = len(grade[0])

    nova_grade = deepcopy(grade)

    for i in range(linhas):
        for j in range(colunas):

            estado = grade[i][j]

            if estado == IGNORANTE:

                influencia = contar_influencia(
                    grade,
                    i,
                    j,
                    influenciadores,
                    peso
                )

                if influencia >= limiar:
                    nova_grade[i][j] = ESPALHADOR

            elif estado == ESPALHADOR:
                nova_grade[i][j] = INATIVO

    return nova_grade


def simular_influenciadores(
    grade_inicial,
    geracoes,
    limiar,
    influenciadores,
    peso=3
):
    """
    Executa a simulacao com influenciadores.

    Retorna somente a matriz final.
    """
    grade = deepcopy(grade_inicial)

    for _ in range(geracoes):

        grade = proxima_geracao_influenciadores(
            grade,
            limiar,
            influenciadores,
            peso
        )

        if not existem_espalhadores(grade):
            break

    return grade


# ============================================================
# MELHORIA 2 - RESISTENCIA A DESINFORMACAO
# ============================================================

def proxima_geracao_resistencia(
    grade,
    limiar,
    resistentes,
    resistencia_extra=2,
    influenciadores=None,
    peso=3
):
    """
    Calcula uma geracao considerando resistencia
    e, opcionalmente, influenciadores.

    Individuos resistentes precisam atingir um
    limiar maior para se tornarem espalhadores.
    """
    if influenciadores is None:
        influenciadores = set()

    linhas = len(grade)
    colunas = len(grade[0])

    nova_grade = deepcopy(grade)

    for i in range(linhas):
        for j in range(colunas):

            estado = grade[i][j]

            if estado == IGNORANTE:

                influencia = contar_influencia(
                    grade,
                    i,
                    j,
                    influenciadores,
                    peso
                )

                limiar_individual = limiar

                if (i, j) in resistentes:
                    limiar_individual += resistencia_extra

                if influencia >= limiar_individual:
                    nova_grade[i][j] = ESPALHADOR

            elif estado == ESPALHADOR:
                nova_grade[i][j] = INATIVO

    return nova_grade


def simular_resistencia(
    grade_inicial,
    geracoes,
    limiar,
    resistentes,
    resistencia_extra=2,
    influenciadores=None,
    peso=3
):
    """
    Executa a simulacao com individuos resistentes
    e influenciadores opcionais.

    Retorna somente a matriz final.
    """
    grade = deepcopy(grade_inicial)

    for _ in range(geracoes):

        grade = proxima_geracao_resistencia(
            grade=grade,
            limiar=limiar,
            resistentes=resistentes,
            resistencia_extra=resistencia_extra,
            influenciadores=influenciadores,
            peso=peso
        )

        if not existem_espalhadores(grade):
            break

    return grade


# ============================================================
# MELHORIA 3 - ESTATISTICAS DE PROPAGACAO
# ============================================================

def simular_com_estatisticas(
    grade_inicial,
    geracoes,
    limiar,
    resistentes=None,
    resistencia_extra=2,
    influenciadores=None,
    peso=3
):
    """
    Executa a simulacao registrando as estatisticas
    de cada geracao.

    Retorna:
        grade_final: matriz resultante.
        historico: lista de registros por geracao.

    A geracao 0 representa o estado inicial.
    """
    if resistentes is None:
        resistentes = set()

    if influenciadores is None:
        influenciadores = set()

    grade = deepcopy(grade_inicial)
    historico = []

    def registrar(numero_geracao):

        contagem = obter_contagem(grade)

        historico.append({
            "geracao": numero_geracao,
            "ignorantes": contagem["ignorantes"],
            "espalhadores": contagem["espalhadores"],
            "inativos": contagem["inativos"]
        })

    # Registra a matriz inicial
    registrar(0)

    for numero in range(1, geracoes + 1):

        grade = proxima_geracao_resistencia(
            grade=grade,
            limiar=limiar,
            resistentes=resistentes,
            resistencia_extra=resistencia_extra,
            influenciadores=influenciadores,
            peso=peso
        )

        registrar(numero)

        if not existem_espalhadores(grade):
            break

    return grade, historico


# ============================================================
# DEMONSTRACAO DAS MELHORIAS
# ============================================================

if __name__ == "__main__":

    grade_inicial = [
        [0, 1, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]

    influenciadores = {(0, 1)}
    resistentes = {(1, 1)}

    print("=== GRADE INICIAL ===")

    for linha in grade_inicial:
        print(linha)

    # --------------------------------------------------------
    # MODELO ORIGINAL
    # --------------------------------------------------------

    print("\n=== MODELO ORIGINAL ===")

    resultado_original = simular(
        grade_inicial,
        geracoes=1,
        limiar=3,
        trabalhadores=1
    )

    for linha in resultado_original:
        print(linha)

    # --------------------------------------------------------
    # MELHORIA 1 - INFLUENCIADORES
    # --------------------------------------------------------

    print("\n=== MELHORIA 1: INFLUENCIADORES ===")

    resultado_influenciadores = simular_influenciadores(
        grade_inicial=grade_inicial,
        geracoes=1,
        limiar=3,
        influenciadores=influenciadores,
        peso=3
    )

    for linha in resultado_influenciadores:
        print(linha)

    # --------------------------------------------------------
    # MELHORIA 2 - RESISTENCIA
    # --------------------------------------------------------

    print("\n=== MELHORIA 2: RESISTENCIA ===")

    resultado_resistencia = simular_resistencia(
        grade_inicial=grade_inicial,
        geracoes=1,
        limiar=3,
        resistentes=resistentes,
        resistencia_extra=2,
        influenciadores=influenciadores,
        peso=3
    )

    for linha in resultado_resistencia:
        print(linha)

    # --------------------------------------------------------
    # MELHORIA 3 - ESTATISTICAS
    # --------------------------------------------------------

    print("\n=== MELHORIA 3: ESTATISTICAS ===")

    grade_final, historico = simular_com_estatisticas(
        grade_inicial=grade_inicial,
        geracoes=5,
        limiar=3,
        resistentes=resistentes,
        resistencia_extra=2,
        influenciadores=influenciadores,
        peso=3
    )

    for registro in historico:
        print(
            f"Geracao {registro['geracao']}: "
            f"Ignorantes={registro['ignorantes']}, "
            f"Espalhadores={registro['espalhadores']}, "
            f"Inativos={registro['inativos']}"
        )

    print("\n=== GRADE FINAL ===")

    for linha in grade_final:
        print(linha)

    print("\nDemonstracao concluida!")
