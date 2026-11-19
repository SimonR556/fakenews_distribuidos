
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from FakeNews import criar_grade
from sequencial import simular as simular_sequencial, contar_estados
from paralelo import simular as simular_paralela
from distribuido import simular as simular_distribuida

from melhorias import (
    simular_influenciadores,
    simular_resistencia,
    simular_com_estatisticas,
)


def ler_inteiro(mensagem, minimo=1, maximo=None):
    """Le um numero inteiro dentro dos limites permitidos."""
    while True:
        try:
            valor = int(input(mensagem))

            if valor < minimo:
                print(f"Digite um numero maior ou igual a {minimo}.")
                continue

            if maximo is not None and valor > maximo:
                print(f"Digite um numero menor ou igual a {maximo}.")
                continue

            return valor

        except ValueError:
            print("Entrada invalida. Digite um numero inteiro.")


def ler_percentual(mensagem):
    """Le um percentual entre 0 e 100."""
    while True:
        try:
            valor = float(input(mensagem).replace(",", "."))

            if 0 <= valor <= 100:
                return valor / 100

            print("Digite um percentual entre 0 e 100.")

        except ValueError:
            print("Entrada invalida. Digite um numero valido.")


def configurar_simulacao():
    """Solicita os parametros da simulacao."""
    print("\n=== CONFIGURACAO DA SIMULACAO ===")

    linhas = ler_inteiro("Quantidade de linhas: ")
    colunas = ler_inteiro("Quantidade de colunas: ")
    geracoes = ler_inteiro("Numero maximo de geracoes: ", minimo=0)

    percentual = ler_percentual(
        "Percentual inicial de espalhadores (0 a 100): "
    )

    limiar = ler_inteiro("Limiar (1 a 8): ", minimo=1, maximo=8)

    return {
        "linhas": linhas,
        "colunas": colunas,
        "geracoes": geracoes,
        "percentual": percentual,
        "limiar": limiar,
        "semente": 42,
    }


def mostrar_contagem(grade):
    """Exibe as quantidades e percentuais de cada estado."""
    contagem = contar_estados(grade)

    total = len(grade) * len(grade[0])

    print(f"Total de individuos: {total}")
    print(
        f"Ignorantes: {contagem[0]} "
        f"({contagem[0] / total * 100:.2f}%)"
    )
    print(
        f"Espalhadores: {contagem[1]} "
        f"({contagem[1] / total * 100:.2f}%)"
    )
    print(
        f"Inativos: {contagem[2]} "
        f"({contagem[2] / total * 100:.2f}%)"
    )


def executar_simulacao(tipo):
    """Executa a versao sequencial, paralela ou distribuida."""
    parametros = configurar_simulacao()

    trabalhadores = 1

    if tipo in ("paralela", "distribuida"):
        trabalhadores = ler_inteiro(
            "Quantidade de trabalhadores: ",
            minimo=1,
            maximo=parametros["linhas"],
        )

    grade_inicial = criar_grade(
        linhas=parametros["linhas"],
        colunas=parametros["colunas"],
        percentual_espalhadores=parametros["percentual"],
        semente=parametros["semente"],
    )

    print("\n=== ESTADO INICIAL ===")
    mostrar_contagem(grade_inicial)

    if tipo == "distribuida":
        print("\nATENCAO: os workers devem estar iniciados.")
        print("Por padrao, sao usadas as portas 5000 em diante.")
        print("Exemplo para dois workers:")
        print("  python3 worker.py --porta 5000")
        print("  python3 worker.py --porta 5001")

        input("\nPressione ENTER para iniciar a simulacao...")

    executores = {
        "sequencial": simular_sequencial,
        "paralela": simular_paralela,
        "distribuida": simular_distribuida,
    }

    executor = executores[tipo]

    print(f"\nExecutando versao {tipo}...")

    inicio = time.perf_counter()

    try:
        grade_final = executor(
            grade_inicial=grade_inicial,
            geracoes=parametros["geracoes"],
            limiar=parametros["limiar"],
            trabalhadores=trabalhadores,
        )

    except (OSError, ConnectionError, TimeoutError, RuntimeError) as erro:
        print(f"\nErro durante a simulacao: {erro}")

        if tipo == "distribuida":
            print("Confira se todos os workers estao ativos.")

        return

    tempo_total = time.perf_counter() - inicio

    print("\n=== RESULTADO FINAL ===")
    mostrar_contagem(grade_final)

    print(f"\nTempo de execucao: {tempo_total:.6f} segundos")


def executar_benchmark():
    """Executa o benchmark rapido das tres versoes oficiais."""
    print("\n=== BENCHMARK DAS TRES VERSOES ===")
    print("Versoes: sequencial, paralela e distribuida")
    print("Matrizes: 5x5 e 10x10")
    print("Trabalhadores: 2")
    print("Repeticoes: 2")
    print("\nATENCAO: dois workers devem estar ativos.")
    print("Portas padrao: 5000 e 5001.")
    print("O benchmark nao inicia os workers automaticamente.")

    confirmar = input("\nExecutar benchmark? (s/n): ").strip().lower()

    if confirmar != "s":
        print("\nBenchmark cancelado.")
        return

    pasta_projeto = Path(__file__).resolve().parent
    pasta_resultados = pasta_projeto / "resultados"
    pasta_resultados.mkdir(exist_ok=True)

    instante = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    arquivo_saida = pasta_resultados / (
        f"benchmark_integracao_{instante}.csv"
    )

    comando = [
        sys.executable,
        "-B",
        str(pasta_projeto / "benchmark.py"),
        "--rapido",
        "--versoes",
        "sequencial",
        "paralela",
        "distribuida",
        "--trabalhadores",
        "2",
        "--saida",
        str(arquivo_saida),
    ]

    print("\nExecutando benchmark oficial...\n")

    try:
        subprocess.run(
            comando,
            check=True,
            cwd=pasta_projeto,
        )

        print("\n=== BENCHMARK CONCLUIDO ===")
        print(f"Arquivo CSV: {arquivo_saida}")

    except subprocess.CalledProcessError as erro:
        print(f"\nBenchmark terminou com erro: {erro}")

    except OSError as erro:
        print(f"\nNao foi possivel executar o benchmark: {erro}")


def imprimir_grade(grade):
    """Exibe uma matriz no terminal."""
    for linha in grade:
        print(linha)


def executar_melhorias():
    """Demonstra influenciadores, resistencia e estatisticas."""
    print("\n=== DEMONSTRACAO DAS MELHORIAS ===")

    grade_inicial = [
        [0, 1, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]

    influenciadores = {(0, 1)}
    resistentes = {(1, 1)}

    print("\nGrade inicial:")
    imprimir_grade(grade_inicial)

    resultado_original = simular_sequencial(
        grade_inicial=grade_inicial,
        geracoes=1,
        limiar=3,
        trabalhadores=1,
    )

    print("\nModelo original:")
    imprimir_grade(resultado_original)

    resultado_influenciadores = simular_influenciadores(
        grade_inicial=grade_inicial,
        geracoes=1,
        limiar=3,
        influenciadores=influenciadores,
        peso=3,
    )

    print("\nCom influenciadores:")
    imprimir_grade(resultado_influenciadores)

    resultado_resistencia = simular_resistencia(
        grade_inicial=grade_inicial,
        geracoes=1,
        limiar=3,
        resistentes=resistentes,
        resistencia_extra=2,
        influenciadores=influenciadores,
        peso=3,
    )

    print("\nCom resistencia:")
    imprimir_grade(resultado_resistencia)

    _, historico = simular_com_estatisticas(
        grade_inicial=grade_inicial,
        geracoes=5,
        limiar=3,
        resistentes=resistentes,
        resistencia_extra=2,
        influenciadores=influenciadores,
        peso=3,
    )

    print("\nEstatisticas por geracao:")

    for registro in historico:
        print(
            f"Geracao {registro['geracao']}: "
            f"Ignorantes={registro['ignorantes']}, "
            f"Espalhadores={registro['espalhadores']}, "
            f"Inativos={registro['inativos']}"
        )


def mostrar_menu():
    """Exibe o menu principal."""
    print("\n========================================")
    print("       PROPAGACAO DE FAKE NEWS")
    print("========================================")
    print("1 - Executar simulacao sequencial")
    print("2 - Executar simulacao paralela")
    print("3 - Executar simulacao distribuida")
    print("4 - Executar benchmark rapido")
    print("5 - Demonstrar melhorias")
    print("0 - Sair")


def main():
    """Controla a navegacao do programa."""
    while True:
        mostrar_menu()

        try:
            opcao = input("\nEscolha uma opcao: ").strip()

            if opcao == "1":
                executar_simulacao("sequencial")

            elif opcao == "2":
                executar_simulacao("paralela")

            elif opcao == "3":
                executar_simulacao("distribuida")

            elif opcao == "4":
                executar_benchmark()

            elif opcao == "5":
                executar_melhorias()

            elif opcao == "0":
                print("\nEncerrando programa...")
                break

            else:
                print("\nOpcao invalida. Tente novamente.")

        except (KeyboardInterrupt, EOFError):
            print("\nPrograma encerrado pelo usuario.")
            break


if __name__ == "__main__":
    main()
