import argparse
import json
import socket
import struct


def receber_exatamente(conexao, quantidade):
    dados = bytearray()

    while len(dados) < quantidade:
        parte = conexao.recv(quantidade - len(dados))

        if not parte:
            raise ConnectionError("a conexão foi encerrada durante a leitura.")

        dados.extend(parte)

    return bytes(dados)


def enviar_mensagem(conexao, mensagem):
    corpo = json.dumps(mensagem).encode("utf-8")
    cabecalho = struct.pack("!I", len(corpo))
    conexao.sendall(cabecalho + corpo)


def receber_mensagem(conexao):
    cabecalho = receber_exatamente(conexao, 4)
    tamanho = struct.unpack("!I", cabecalho)[0]

    if tamanho == 0 or tamanho > 64 * 1024 * 1024:
        raise ValueError("tamanho de mensagem inválido (limite: 64 MiB).")

    corpo = receber_exatamente(conexao, tamanho)
    return json.loads(corpo.decode("utf-8"))


def executar_worker(host, porta):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind((host, porta))
        servidor.listen(1)

        print(f"Worker disponível em {host}:{porta}")

        try:
            while True:
                print("Aguardando uma nova simulação...")
                conexao, endereco = servidor.accept()

                with conexao:
                    conexao.settimeout(60)
                    print(f"Coordenador conectado: {endereco}")

                    try:
                        while True:
                            mensagem = receber_mensagem(conexao)
                            tipo = mensagem.get("tipo")

                            if tipo == "ping":
                                enviar_mensagem(
                                    conexao,
                                    {
                                        "tipo": "pong",
                                        "mensagem": "Worker pronto!"
                                    }
                                )

                            elif tipo == "calcular":
                                resultado = calcular_regiao(
                                    mensagem["linhas"],
                                    mensagem["fronteira_acima"],
                                    mensagem["fronteira_abaixo"],
                                    mensagem["limiar"]
                                )

                                enviar_mensagem(
                                    conexao,
                                    {
                                        "tipo": "resultado",
                                        "geracao": mensagem["geracao"],
                                        "inicio": mensagem["inicio"],
                                        "linhas": resultado
                                    }
                                )

                            elif tipo == "encerrar":
                                enviar_mensagem(
                                    conexao,
                                    {"tipo": "encerrado"}
                                )
                                break

                            else:
                                enviar_mensagem(
                                    conexao,
                                    {
                                        "tipo": "erro",
                                        "mensagem": "Tipo desconhecido."
                                    }
                                )

                    except (OSError, ValueError, KeyError, TypeError, IndexError) as erro:
                        print(f"Simulação interrompida: {erro}")

                print("Conexão da simulação encerrada.")

        except KeyboardInterrupt:
            print("\nWorker desligado pelo usuário.")


def calcular_regiao(linhas, fronteira_acima, fronteira_abaixo, limiar):
    leitura = []

    if fronteira_acima is not None:
        leitura.append(fronteira_acima)

    inicio = len(leitura)
    leitura.extend(linhas)

    if fronteira_abaixo is not None:
        leitura.append(fronteira_abaixo)

    nova_regiao = [linha[:] for linha in linhas]
    colunas = len(linhas[0])

    for i in range(len(linhas)):
        linha_leitura = inicio + i

        for j in range(colunas):
            estado = linhas[i][j]

            if estado == 1:
                nova_regiao[i][j] = 2

            elif estado == 0:
                espalhadores = 0

                for di in (-1, 0, 1):
                    for dj in (-1, 0, 1):
                        if di == 0 and dj == 0:
                            continue

                        ni = linha_leitura + di
                        nj = j + dj

                        if 0 <= ni < len(leitura) and 0 <= nj < colunas:
                            if leitura[ni][nj] == 1:
                                espalhadores += 1

                if espalhadores >= limiar:
                    nova_regiao[i][j] = 1

    return nova_regiao

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="worker da simulação.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--porta", type=int, default=5000)
    argumentos = parser.parse_args()

    executar_worker(argumentos.host, argumentos.porta)