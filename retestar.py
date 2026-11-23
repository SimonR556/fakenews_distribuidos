"""Refaz testes e a bateria comparativa em diretório novo, sem iniciar commits.

Uso: python -B -u retestar.py
Requer portas locais 5000–5007 disponíveis e Matplotlib para os PNGs opcionais.
Inicia e encerra somente os seus workers; não mistura resultados anteriores.
"""

from contextlib import ExitStack
from copy import copy
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import analisar_resultados
import benchmark
from worker import enviar_mensagem, receber_mensagem


RAIZ = Path(__file__).resolve().parent


def hashes_fontes():
    return {str(p.relative_to(RAIZ)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(RAIZ.glob("*.py"))}


def executar():
    instante = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    pasta = RAIZ / "resultados" / f"reteste_{instante}"
    pasta.mkdir(parents=True, exist_ok=False)
    print(f"Resultados: {pasta}", flush=True)
    fontes = hashes_fontes()
    ambiente = benchmark.coletar_ambiente()
    ambiente.update({
        "executavel": sys.executable,
        "gil_habilitado": getattr(sys, "_is_gil_enabled", lambda: None)(),
        "arvore_git": subprocess.check_output(
            ["git", "status", "--short"], cwd=RAIZ, text=True),
        "metodo": "Cenários sequenciais; ordem fixa sequencial/paralela/distribuída; sem aquecimento separado",
        "workers": "8 processos locais persistentes; logs em arquivos; portas 5000–5007",
        "inicio_processos_no_tempo": False,
        "hashes_fontes": fontes,
    })
    (pasta / "ambiente.json").write_text(
        json.dumps(ambiente, ensure_ascii=False, indent=2), encoding="utf-8")
    with (pasta / "testes.log").open("w", encoding="utf-8") as log:
        teste = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-v"],
                               cwd=RAIZ, stdout=log, stderr=subprocess.STDOUT,
                               timeout=120)
    if teste.returncode:
        raise RuntimeError(f"Testes falharam: {pasta / 'testes.log'}")
    print("Suíte de testes aprovada.", flush=True)

    # Verifica conflitos sem encerrar serviços preexistentes.
    with ExitStack() as reservas:
        for porta in range(5000, 5008):
            servidor = reservas.enter_context(socket.socket())
            servidor.bind(("127.0.0.1", porta))

    processos = []
    anterior = os.environ.pop("FAKENEWS_WORKERS", None)
    try:
        with ExitStack() as logs:
            for indice, porta in enumerate(range(5000, 5008)):
                log = logs.enter_context((pasta / f"worker_{indice}.log").open("w", encoding="utf-8"))
                processo = subprocess.Popen(
                    [sys.executable, "-B", "-u", "worker.py", "--porta", str(porta)],
                    cwd=RAIZ, stdout=log, stderr=subprocess.STDOUT,
                    creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
                )
                processos.append(processo)
                limite = time.monotonic() + 10
                while True:
                    if processo.poll() is not None:
                        raise RuntimeError(f"Worker {porta} encerrou; confira seu log.")
                    try:
                        with socket.create_connection(("127.0.0.1", porta), timeout=1) as conexao:
                            enviar_mensagem(conexao, {"tipo": "ping"})
                            if receber_mensagem(conexao).get("tipo") != "pong":
                                raise RuntimeError("Ping inválido.")
                        break
                    except OSError:
                        if time.monotonic() >= limite:
                            raise
                        time.sleep(0.05)

            argumentos = benchmark.ler_argumentos([
                "--versoes", "sequencial", "paralela", "distribuida",
                "--tamanhos", "100x100", "300x300", "500x500",
                "--percentuais", "0.05", "0.40", "--geracoes", "1", "2", "5",
                "--limiar", "3", "--semente", "42", "--repeticoes", "3",
                "--trabalhadores", "1", "2", "4", "8",
                "--saida", str(pasta / "medicoes.csv"),
            ])
            registros = []
            for indice, (tamanho, geracoes, percentual) in enumerate(product(
                    argumentos.tamanhos, argumentos.geracoes, argumentos.percentuais), 1):
                cenario = copy(argumentos)
                cenario.tamanhos = [tamanho]
                cenario.geracoes = [geracoes]
                cenario.percentuais = [percentual]
                registros.extend(benchmark.executar_benchmark(cenario))
                print(f"Cenário {indice}/18: {tamanho}, limite={geracoes}, "
                      f"fração={percentual}; {len(registros)} medições validadas.", flush=True)
                if hashes_fontes() != fontes:
                    raise RuntimeError("Fontes Python alteradas durante a coleta.")
            benchmark.exportar_csv(argumentos.saida, registros)
    finally:
        for processo in processos:
            if processo.poll() is None:
                processo.terminate()
        for processo in processos:
            try:
                processo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                processo.kill()
                processo.wait(timeout=5)
        if anterior is not None:
            os.environ["FAKENEWS_WORKERS"] = anterior

    print("Workers próprios encerrados; iniciando análise.", flush=True)
    retorno = analisar_resultados.main([
        str(pasta / "medicoes.csv"), "--saida", str(pasta / "analise"),
    ])
    if retorno:
        raise RuntimeError("Falha ao analisar a coleta; medições brutas preservadas.")
    print(f"Concluído: {pasta}", flush=True)
    return pasta


if __name__ == "__main__":
    executar()
