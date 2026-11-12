"""Primeiro benchmark: adaptador sequencial PROVISÓRIO do original.

Execução rápida (biblioteca padrão, sem dependências):
    python3 -B benchmark.py --rapido
    python3 -B benchmark.py --tamanhos 5x5 10x10 100x100 --geracoes 50 \
        --percentuais 0.05 --limiar 3 --semente 42 --repeticoes 3
    python3 -B benchmark.py --help

Cada combinação de tamanho, limite e percentual é um cenário. Sua grade é
gerada uma única vez; referência e repetições recebem cópias independentes.
O tempo inclui somente a chamada do executor: evolução, alocações internas,
contagem para parada e retorno. Exclui criação/cópia da entrada, referência,
validação, coleta do ambiente, impressão e CSV. Não há aquecimento separado.

O adaptador não substitui sequencial.py. O registro VERSOES reserva pontos de
integração: um futuro adaptador pode chamar simular(grade, geracoes, limiar,
trabalhadores) e embrulhar a matriz em ResultadoExecucao com gerações=None.
Esse tipo é interno ao benchmark; NÃO define simular_com_estatisticas, cuja
interface continua pendente. Nunca inferir gerações a partir da matriz final.
Antes de ativar versões futuras, validar contrato, estatísticas e política de
inicialização/encerramento de threads, processos e conexões com os colegas.

Os CSVs são dados preliminares do adaptador, não resultados das versões do
grupo. Não são calculados speedup nem eficiência nesta etapa. Implementação
com apoio de IA (Codex), a partir dos documentos locais e de FakeNews.py.
"""

import argparse
import csv
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
import os
import platform
import subprocess
import time
from typing import Callable, Optional

from FakeNews import (
    ESPALHADOR, IGNORANTE, INATIVO,
    contar_estados, criar_grade, proxima_geracao,
)


RAIZ = Path(__file__).resolve().parent
RESULTADOS = RAIZ / "resultados"


@dataclass
class ResultadoExecucao:
    """Resultado interno; None indica gerações ainda não instrumentadas."""

    grade: list
    geracoes_executadas: Optional[int]


def executar_sequencial_provisorio(grade, geracoes, limiar, trabalhadores):
    """Evolui com funções do professor, sem prints e sem alterar a entrada.

    PROVISÓRIO: trabalhadores é ignorado, como no contrato sequencial.
    A verificação de parada ocorre depois da atualização e da contagem.
    Com zero gerações, retorna a entrada intacta sem executar atualização.
    """
    executadas = 0
    for _ in range(geracoes):
        grade = proxima_geracao(grade, limiar)
        executadas += 1
        if contar_estados(grade)[ESPALHADOR] == 0:
            break
    return ResultadoExecucao(grade, executadas)


@dataclass(frozen=True)
class Versao:
    """Ponto de extensão para executores com o contrato interno acima."""

    executor: Optional[Callable]
    modulo: str


VERSOES = {
    "sequencial_provisorio": Versao(executar_sequencial_provisorio, "FakeNews.py"),
    "sequencial": Versao(None, "sequencial.py"),
    "paralela": Versao(None, "paralelo.py"),
    "distribuida": Versao(None, "distribuido.py"),
}


def executar_referencia(grade_inicial, geracoes, limiar):
    """Executa fora do cronômetro um laço independente com funções originais.

    Compartilha a regra de transição original, não o executor medido. Valida
    consistência e controle do laço; não é uma segunda implementação da regra.
    """
    grade = deepcopy(grade_inicial)
    executadas = 0
    while executadas < geracoes:
        grade = proxima_geracao(grade, limiar)
        executadas += 1
        estados = contar_estados(grade)
        if estados[ESPALHADOR] == 0:
            break
    return ResultadoExecucao(grade, executadas)


def medir_repeticao(executor, grade_inicial, geracoes, limiar, trabalhadores,
                    referencia):
    """Cronometra só o executor e verifica matriz, contagens, gerações e entrada."""
    entrada = deepcopy(grade_inicial)
    inicio = time.perf_counter()
    resultado = executor(entrada, geracoes, limiar, trabalhadores)
    tempo_s = time.perf_counter() - inicio

    if entrada != grade_inicial:
        raise RuntimeError("O executor modificou a entrada da repetição.")
    if resultado.grade != referencia.grade:
        raise RuntimeError("Matriz final diferente da referência.")
    contagens = contar_estados(resultado.grade)
    if contagens != contar_estados(referencia.grade):
        raise RuntimeError("Contagens finais diferentes da referência.")
    if (resultado.geracoes_executadas is not None
            and resultado.geracoes_executadas != referencia.geracoes_executadas):
        raise RuntimeError("Gerações executadas diferentes da referência.")
    return tempo_s, resultado, contagens


def coletar_ambiente():
    """Registra ambiente e commit fora da medição; desconhecidos ficam vazios.

    CPU/RAM física e detalhes de hardware devem ser complementados antes dos
    experimentos finais; a biblioteca padrão não os detecta portavelmente.
    """
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=RAIZ, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "desconhecido"
    return {
        "data_utc": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "python": platform.python_version(),
        "implementacao_python": platform.python_implementation(),
        "sistema": platform.platform(),
        "cpu": platform.processor(),
        "nucleos_logicos": os.cpu_count(),
        "nucleos_fisicos": None,
        "ram_bytes": None,
        "hosts": 1,
        "coordenadores": 0,
        "politica_tempo": "somente_executor_sem_copia_de_entrada",
        "codigo": "adaptador_provisorio_arvore_de_trabalho",
    }


def executar_benchmark(args):
    """Gera uma grade por cenário e coleta somente execuções disponíveis."""
    ambiente = coletar_ambiente()
    registros = []
    for (linhas, colunas), geracoes, percentual in product(
            args.tamanhos, args.geracoes, args.percentuais):
        grade = criar_grade(linhas, colunas, percentual, args.semente)
        referencia = executar_referencia(grade, geracoes, args.limiar)
        for nome in args.versoes:
            executor = VERSOES[nome].executor
            for repeticao in range(1, args.repeticoes + 1):
                tempo_s, resultado, contagens = medir_repeticao(
                    executor, grade, geracoes, args.limiar,
                    args.trabalhadores, referencia,
                )
                registros.append({
                    **ambiente,
                    "versao": nome,
                    "linhas": linhas,
                    "colunas": colunas,
                    "geracoes_maximas": geracoes,
                    "geracoes_executadas": resultado.geracoes_executadas,
                    "percentual_solicitado": percentual,
                    "limiar": args.limiar,
                    "semente": args.semente,
                    "trabalhadores": args.trabalhadores,
                    "trabalhadores_efetivos": 1,
                    "repeticao": repeticao,
                    "tempo_s": tempo_s,
                    "ignorantes": contagens[IGNORANTE],
                    "espalhadores": contagens[ESPALHADOR],
                    "inativos": contagens[INATIVO],
                    "consistente": True,
                    "entrada_preservada": True,
                })
    return registros


def exportar_csv(caminho, registros):
    """Grava CSV UTF-8 novo, sem sobrescrever experimentos anteriores."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("x", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(registros[0]))
        escritor.writeheader()
        escritor.writerows(registros)


def tamanho(texto):
    """Converte a notação LINHASxCOLUNAS em dimensões positivas."""
    try:
        linhas, colunas = map(int, texto.lower().split("x"))
        if linhas > 0 and colunas > 0:
            return linhas, colunas
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("Use dimensões positivas, por exemplo 10x10.")


def ler_argumentos(argv=None):
    """Configura cenários pequenos e rejeita parâmetros inválidos ou pendentes."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rapido", action="store_true",
                        help="Padrões: 5x5 e 10x10, limite 5, duas repetições.")
    parser.add_argument("--tamanhos", type=tamanho, nargs="+")
    parser.add_argument("--geracoes", type=int, nargs="+")
    parser.add_argument("--percentuais", type=float, nargs="+", default=[0.05],
                        help="Frações entre 0 e 1; 0.05 significa 5%%.")
    parser.add_argument("--limiar", type=int, default=3)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--trabalhadores", type=int, default=1,
                        help="Solicitados; o adaptador sequencial usa sempre 1.")
    parser.add_argument("--repeticoes", type=int)
    parser.add_argument("--versoes", nargs="+", choices=VERSOES,
                        default=["sequencial_provisorio"])
    parser.add_argument("--saida", type=Path,
                        help="CSV novo dentro de resultados/; padrão com data UTC.")
    args = parser.parse_args(argv)
    if args.tamanhos is None:
        args.tamanhos = [(5, 5), (10, 10)] if args.rapido else [(10, 10)]
    if args.geracoes is None:
        args.geracoes = [5 if args.rapido else 10]
    if args.repeticoes is None:
        args.repeticoes = 2 if args.rapido else 3
    if any(g < 0 for g in args.geracoes):
        parser.error("Gerações devem ser não negativas.")
    if any(not 0 <= p <= 1 for p in args.percentuais):
        parser.error("Percentuais devem estar entre 0 e 1.")
    if not 0 <= args.limiar <= 8:
        parser.error("Este benchmark aceita limiar entre 0 e 8.")
    if args.repeticoes < 1 or args.trabalhadores < 1:
        parser.error("Repetições e trabalhadores devem ser positivos.")
    for nome in args.versoes:
        if VERSOES[nome].executor is None:
            parser.error(f"Versão {nome} pendente: ainda não integrada ao benchmark.")
    if args.saida is None:
        data = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        args.saida = RESULTADOS / f"benchmark_{data}.csv"
    args.saida = args.saida.resolve()
    if not args.saida.is_relative_to(RESULTADOS.resolve()):
        parser.error("O CSV deve ficar dentro de resultados/.")
    if args.saida.exists():
        parser.error("O arquivo de saída já existe; escolha outro nome.")
    return args


def main(argv=None):
    """Executa a CLI e imprime resumo somente fora da região medida."""
    args = ler_argumentos(argv)
    for nome, versao in VERSOES.items():
        if versao.executor is None:
            situacao = ("arquivo ausente" if not (RAIZ / versao.modulo).is_file()
                        else "arquivo presente; integração pendente")
            print(f"{nome}: não executada ({situacao}).")
    registros = executar_benchmark(args)
    exportar_csv(args.saida, registros)
    print(f"CSV: {args.saida}")
    print(f"{len(registros)} medições; matrizes, contagens, gerações e entradas verificadas.")
    for registro in registros:
        print(f"{registro['versao']} {registro['linhas']}x{registro['colunas']} "
              f"repetição={registro['repeticao']} "
              f"gerações={registro['geracoes_executadas']} "
              f"tempo_s={registro['tempo_s']:.9f}")


if __name__ == "__main__":
    main()
