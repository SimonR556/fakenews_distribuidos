import time

from FakeNews import criar_grade
from sequencial import simular, contar_estados


def ler_inteiro(mensagem, minimo=1):
    """Solicita um numero inteiro valido ao usuario."""
    while True:
        try:
            valor = int(input(mensagem))

            if valor < minimo:
                print(f"Digite um numero maior ou igual a {minimo}.")
                continue

            return valor

        except ValueError:
            print("Entrada invalida. Digite um numero inteiro.")


def ler_percentual(mensagem):
    """Solicita um percentual entre 0 e 100."""
    while True:
        try:
            valor = float(input(mensagem).replace(",", "."))

            if 0 <= valor <= 100:
                return valor / 100

            print("Digite um percentual entre 0 e 100.")

        except ValueError:
            print("Entrada invalida. Digite um numero valido.")


def configurar_simulacao():
    """Recebe os parametros da simulacao."""
    print("\n=== CONFIGURACAO DA SIMULACAO ===")

    linhas = ler_inteiro("Quantidade de linhas: ")
    colunas = ler_inteiro("Quantidade de colunas: ")
    geracoes = ler_inteiro("Numero maximo de geracoes: ", 0)

    percentual = ler_percentual(
        "Percentual inicial de espalhadores (0 a 100): "
    )

    limiar = ler_inteiro(
        "Limiar de convencimento (1 a 8): "
    )

    while limiar > 8:
        print("O limiar nao pode ultrapassar 8.")
        limiar = ler_inteiro(
            "Limiar de convencimento (1 a 8): "
        )

    return {
        "linhas": linhas,
        "colunas": colunas,
        "geracoes": geracoes,
        "percentual": percentual,
        "limiar": limiar,
        "semente": 42
    }


def executar_sequencial():
    """Executa a versao sequencial da simulacao."""
    parametros = configurar_simulacao()

    grade_inicial = criar_grade(
        linhas=parametros["linhas"],
        colunas=parametros["colunas"],
        percentual_espalhadores=parametros["percentual"],
        semente=parametros["semente"]
    )

    contagem_inicial = contar_estados(grade_inicial)

    print("\n=== ESTADO INICIAL ===")
    print(f"Ignorantes: {contagem_inicial[0]}")
    print(f"Espalhadores: {contagem_inicial[1]}")
    print(f"Inativos: {contagem_inicial[2]}")

    print("\nExecutando simulacao sequencial...")

    # O tempo medido nao inclui a criacao da matriz.
    inicio = time.perf_counter()

    grade_final = simular(
        grade_inicial=grade_inicial,
        geracoes=parametros["geracoes"],
        limiar=parametros["limiar"],
        trabalhadores=1
    )

    fim = time.perf_counter()

    tempo_total = fim - inicio
    contagem_final = contar_estados(grade_final)

    total = parametros["linhas"] * parametros["colunas"]

    print("\n=== RESULTADO FINAL ===")
    print(f"Total de individuos: {total}")
    print(f"Ignorantes: {contagem_final[0]}")
    print(f"Espalhadores: {contagem_final[1]}")
    print(f"Inativos: {contagem_final[2]}")

    print(f"\nTempo de execucao: {tempo_total:.6f} segundos")

    print("\nPercentuais finais:")
    print(f"Ignorantes: {contagem_final[0] / total * 100:.2f}%")
    print(f"Espalhadores: {contagem_final[1] / total * 100:.2f}%")
    print(f"Inativos: {contagem_final[2] / total * 100:.2f}%")


def mostrar_menu():
    """Exibe o menu principal."""
    print("\n========================================")
    print("       PROPAGACAO DE FAKE NEWS")
    print("========================================")
    print("1 - Executar simulacao sequencial")
    print("2 - Executar simulacao paralela")
    print("3 - Executar simulacao distribuida")
    print("4 - Comparar resultados (benchmark)")
    print("0 - Sair")


def main():
    """Controla a navegacao do programa."""
    while True:
        mostrar_menu()

        opcao = input("\nEscolha uma opcao: ").strip()

        if opcao == "1":
            executar_sequencial()

        elif opcao == "2":
            print("\nVersao paralela ainda nao integrada.")

        elif opcao == "3":
            print("\nVersao distribuida ainda nao integrada.")

        elif opcao == "4":
            print("\nBenchmark ainda nao integrado.")

        elif opcao == "0":
            print("\nEncerrando programa...")
            break

        else:
            print("\nOpcao invalida. Tente novamente.")


if __name__ == "__main__":
    main()
