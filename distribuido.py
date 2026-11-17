import socket
import os
from contextlib import ExitStack
from copy import deepcopy
from time import perf_counter

from FakeNews import criar_grade, proxima_geracao, contar_estados
from worker import enviar_mensagem, receber_mensagem


def dividir_linhas(total_linhas, trabalhadores):
    """Retorna intervalos [inicio, fim), distribuindo também as sobras."""
    quantidade, sobra = divmod(total_linhas, trabalhadores)
    faixas = []
    inicio = 0

    for indice in range(trabalhadores):
        tamanho = quantidade + (1 if indice < sobra else 0)
        fim = inicio + tamanho
        faixas.append((inicio, fim))
        inicio = fim

    return faixas


def simular_com_estatisticas(grade_inicial, geracoes, limiar, trabalhadores):
    """Retorna a matriz final e a quantidade de gerações executadas."""
    if not isinstance(grade_inicial, list) or not grade_inicial:
        raise ValueError("A grade deve ser uma lista não vazia.")

    if any(
        not isinstance(linha, list) or not linha
        for linha in grade_inicial
    ):
        raise ValueError("Cada linha deve ser uma lista não vazia.")

    colunas = len(grade_inicial[0])

    if any(len(linha) != colunas for linha in grade_inicial):
        raise ValueError("Todas as linhas devem ter o mesmo tamanho.")

    if any(
        type(estado) is not int or estado not in (0, 1, 2)
        for linha in grade_inicial
        for estado in linha
    ):
        raise ValueError("Os estados devem ser inteiros: 0, 1 ou 2.")

    if type(geracoes) is not int or geracoes < 0:
        raise ValueError("Gerações deve ser um inteiro não negativo.")

    if type(limiar) is not int or limiar < 0:
        raise ValueError("O limiar deve ser um inteiro não negativo.")

    if (
        type(trabalhadores) is not int
        or not 1 <= trabalhadores <= len(grade_inicial)
    ):
        raise ValueError(
            "Trabalhadores deve ser um inteiro entre 1 e o total de linhas."
        )

    atual = deepcopy(grade_inicial)
    executadas = 0

    if geracoes == 0:
        return atual, executadas

    faixas = dividir_linhas(len(atual), trabalhadores)

    # Fecha todas as conexões ao sair, inclusive se ocorrer uma exceção.
    with ExitStack() as recursos:
        conexoes = []

        for endereco in obter_enderecos(trabalhadores):
            conexao = recursos.enter_context(
                socket.create_connection(endereco, timeout=60)
            )
            conexoes.append(conexao)

        for geracao in range(1, geracoes + 1):
            # Primeiro envia as tarefas para TODOS os workers.
            for conexao, (inicio, fim) in zip(conexoes, faixas):
                enviar_mensagem(
                    conexao,
                    {
                        "tipo": "calcular",
                        "geracao": geracao,
                        "inicio": inicio,
                        "linhas": atual[inicio:fim],
                        "fronteira_acima": (
                            atual[inicio - 1] if inicio > 0 else None
                        ),
                        "fronteira_abaixo": (
                            atual[fim] if fim < len(atual) else None
                        ),
                        "limiar": limiar
                    }
                )

            proxima = [None] * len(atual)

            # Depois recebe e encaixa cada resultado na posição correta.
            for conexao, (inicio, fim) in zip(conexoes, faixas):
                resposta = receber_mensagem(conexao)

                if (
                    resposta.get("tipo") != "resultado"
                    or resposta.get("geracao") != geracao
                    or resposta.get("inicio") != inicio
                ):
                    raise RuntimeError("Resposta incompatível com a tarefa.")

                linhas = resposta["linhas"]

                if (
                    len(linhas) != fim - inicio
                    or any(len(linha) != colunas for linha in linhas)
                ):
                    raise RuntimeError("Região recebida com tamanho incorreto.")

                proxima[inicio:fim] = linhas

            # Só troca a geração após receber todas as regiões.
            atual = proxima
            executadas = geracao

            if not any(1 in linha for linha in atual):
                break

        for conexao in conexoes:
            enviar_mensagem(conexao, {"tipo": "encerrar"})

        for conexao in conexoes:
            resposta = receber_mensagem(conexao)

            if resposta.get("tipo") != "encerrado":
                raise RuntimeError("Worker não confirmou o encerramento.")

    return atual, executadas


def simular(grade_inicial, geracoes, limiar, trabalhadores):
    """Interface combinada pelo time: retorna somente a matriz final."""
    grade_final, _ = simular_com_estatisticas(
        grade_inicial, geracoes, limiar, trabalhadores
    )
    return grade_final


def testar_distribuido():
    inicial = criar_grade(
        linhas=100,
        colunas=100,
        percentual_espalhadores=0.05,
        semente=42
    )
    original = deepcopy(inicial)

    # Referência calculada usando a função original do professor.
    esperado = deepcopy(inicial)
    geracoes_referencia = 0

    for geracao in range(1, 51):
        esperado = proxima_geracao(esperado, 3)
        geracoes_referencia = geracao

        if contar_estados(esperado)[1] == 0:
            break

    inicio = perf_counter()

    resultado, geracoes_executadas = simular_com_estatisticas(
        grade_inicial=inicial,
        geracoes=50,
        limiar=3,
        trabalhadores=4
    )

    tempo = perf_counter() - inicio

    assert resultado == esperado, "Matriz diferente da referência!"
    assert inicial == original, "A matriz inicial foi alterada!"
    assert geracoes_executadas == geracoes_referencia, (
        "Quantidade de gerações diferente da referência!"
    )

    contagem = contar_estados(resultado)

    print("Matriz distribuída idêntica à referência: OK")
    print("Matriz inicial preservada: OK")
    print(f"Gerações executadas: {geracoes_executadas}")
    print(f"Ignorantes: {contagem[0]}")
    print(f"Espalhadores: {contagem[1]}")
    print(f"Inativos: {contagem[2]}")
    print(f"Tempo da execução distribuída: {tempo:.4f} s")

def obter_enderecos(trabalhadores):
    """Lê os endereços configurados ou utiliza workers locais."""
    configuracao = os.environ.get("FAKENEWS_WORKERS", "").strip()

    if not configuracao:
        return [
            ("127.0.0.1", 5000 + indice)
            for indice in range(trabalhadores)
        ]

    enderecos = []

    for item in configuracao.split(","):
        host, separador, porta_texto = item.strip().rpartition(":")

        if not separador or not host.strip():
            raise ValueError(
                "Use FAKENEWS_WORKERS no formato host:porta,host:porta."
            )

        porta = int(porta_texto)

        if not 1 <= porta <= 65535:
            raise ValueError("A porta deve estar entre 1 e 65535.")

        enderecos.append((host.strip(), porta))

    if len(enderecos) != trabalhadores:
        raise ValueError(
            "A quantidade de endereços deve corresponder aos trabalhadores."
        )

    if len(set(enderecos)) != len(enderecos):
        raise ValueError("Não repita o mesmo endereço de worker.")

    return enderecos

if __name__ == "__main__":
    testar_distribuido()