"""Benchmark das implementações oficiais e dos adaptadores preliminares.

Execução rápida (biblioteca padrão, sem dependências):
    python3 -B benchmark.py --rapido
    python3 -B benchmark.py --tamanhos 5x5 10x10 100x100 --geracoes 50 \
        --percentuais 0.05 --limiar 3 --semente 42 --repeticoes 3
    python3 -B benchmark.py --help
    python3 -B benchmark.py --rapido --versoes sequencial_candidato \
        --sequencial-arquivo /tmp/sequencial_colega.py
    python3 -B benchmark.py --rapido --versoes sequencial paralela distribuida \
        --trabalhadores 1 2 4

Cada combinação de tamanho, limite e percentual é um cenário. Sua grade é
gerada uma única vez; referência e repetições recebem cópias independentes.
O tempo inclui somente a chamada do executor: evolução, alocações internas,
contagem para parada e retorno. Exclui criação/cópia da entrada pelo benchmark,
carregamento do módulo e cálculo do SHA-256, referência, validação, coleta do
ambiente, impressão e CSV. Não há aquecimento separado.

Oficiais: sequencial.simular retorna matriz. Suas gerações são contadas em uma
execução diagnóstica determinística equivalente, após todas as medições do
cenário e fora dos cronômetros, sem instrumentar as chamadas cronometradas.
paralelo.simular_com_detalhes e distribuido.simular_com_estatisticas retornam
(matriz, gerações). Nunca inferir gerações a partir da matriz ou da referência.
Workers TCP devem estar iniciados antes da medição. A chamada distribuída
inclui conexão, comunicação, sincronização e encerramento das conexões;
exclui iniciar os processos workers. Threads são criadas/encerradas dentro da
chamada paralela. Essa política é comum às três chamadas oficiais.
Esta integração cobre somente um host, com workers em 127.0.0.1 (padrão:
portas 5000 em diante; FAKENEWS_WORKERS pode trocar as portas locais).
O benchmark não inicia nem desliga processos workers.

Provisório e candidato nunca são baseline oficial de speedup. O padrão da
CLI continua sendo sequencial_provisorio. Não se calculam speedup/eficiência
aqui. Implementação com apoio de IA (Codex), usando os documentos locais.
"""

import argparse
import csv
import hashlib
import importlib.util
import inspect
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
import os
import platform
import subprocess
import sys
import time
from typing import Callable, Optional

from FakeNews import (
    ESPALHADOR, IGNORANTE, INATIVO,
    contar_estados, criar_grade, proxima_geracao,
)


RAIZ = Path(__file__).resolve().parent
RESULTADOS = RAIZ / "resultados"
POLITICA_OFICIAL = "chamada_completa_v1_workers_tcp_preiniciados"


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
class ExecutorSequencialCandidato:
    """Adaptador chamável com o hash do conteúdo carregado fora do cronômetro."""

    simular: Callable
    sha256: str

    def __call__(self, grade_inicial, geracoes, limiar, trabalhadores):
        grade = self.simular(grade_inicial, geracoes, limiar, trabalhadores)
        return ResultadoExecucao(grade, geracoes_executadas=None)


def carregar_sequencial_candidato(caminho):
    """Calcula SHA-256 e carrega os mesmos bytes, sem reler fonte ou bytecode."""
    caminho = Path(caminho).resolve()
    if not caminho.is_file():
        raise ValueError(f"Arquivo sequencial candidato não encontrado: {caminho}")
    spec = importlib.util.spec_from_file_location("_sequencial_candidato", caminho)
    if spec is None or spec.loader is None:
        raise ValueError(f"Não foi possível carregar o módulo Python: {caminho}")
    modulo = importlib.util.module_from_spec(spec)
    try:
        conteudo = caminho.read_bytes()
        sha256 = hashlib.sha256(conteudo).hexdigest()
        exec(compile(conteudo, str(caminho), "exec"), modulo.__dict__)
    except Exception as erro:
        raise ValueError(f"Erro ao carregar {caminho}: {erro}") from erro
    simular = getattr(modulo, "simular", None)
    if not callable(simular):
        raise ValueError(f"{caminho}: função simular ausente ou não chamável.")
    try:
        inspect.signature(simular).bind([], 0, 3, 1)
    except (TypeError, ValueError) as erro:
        raise ValueError(
            f"{caminho}: simular deve aceitar os quatro parâmetros posicionais "
            "(grade_inicial, geracoes, limiar, trabalhadores)."
        ) from erro

    return ExecutorSequencialCandidato(simular, sha256)


@dataclass(frozen=True)
class Versao:
    """Ponto de extensão para executores com o contrato interno acima."""

    executor: Optional[Callable]
    modulo: str


VERSOES = {
    "sequencial_provisorio": Versao(executar_sequencial_provisorio, "FakeNews.py"),
    "sequencial_candidato": Versao(None, "arquivo externo via --sequencial-arquivo"),
    "sequencial": Versao(None, "sequencial.py"),
    "paralela": Versao(None, "paralelo.py"),
    "distribuida": Versao(None, "distribuido.py"),
}


@dataclass(frozen=True)
class ExecutorOficial:
    """Adapta o retorno real, preservando a identidade dos bytes carregados."""

    simular: Callable
    com_geracoes: bool
    codigo: str
    obter_enderecos: Optional[Callable] = None

    def __call__(self, grade_inicial, geracoes, limiar, trabalhadores):
        retorno = self.simular(grade_inicial, geracoes, limiar, trabalhadores)
        if self.com_geracoes:
            grade, executadas = retorno
            return ResultadoExecucao(grade, executadas)
        return ResultadoExecucao(retorno, geracoes_executadas=None)


def carregar_modulo_oficial(arquivo):
    """Lê uma vez, identifica e executa os mesmos bytes fora do cronômetro."""
    caminho = RAIZ / arquivo
    spec = importlib.util.spec_from_file_location(f"_benchmark_{caminho.stem}", caminho)
    if spec is None or spec.loader is None:
        raise ValueError(f"Não foi possível carregar {caminho}.")
    modulo = importlib.util.module_from_spec(spec)
    conteudo = caminho.read_bytes()
    sha256 = hashlib.sha256(conteudo).hexdigest()
    exec(compile(conteudo, str(caminho), "exec"), modulo.__dict__)
    return modulo, sha256


def carregar_oficial(nome):
    """Usa as auxiliares existentes; não instrumenta o laço dos colegas."""
    arquivo = VERSOES[nome].modulo
    hash_worker = None
    if nome == "distribuida":
        # O coordenador importa as funções de worker. Carrega também essa
        # dependência dos bytes identificados, sem substituir arquivo algum.
        worker, hash_worker = carregar_modulo_oficial("worker.py")
        anterior = sys.modules.get("worker")
        sys.modules["worker"] = worker
        try:
            modulo, sha256 = carregar_modulo_oficial(arquivo)
        finally:
            if anterior is None:
                del sys.modules["worker"]
            else:
                sys.modules["worker"] = anterior
    else:
        modulo, sha256 = carregar_modulo_oficial(arquivo)
    funcao = {"sequencial": "simular", "paralela": "simular_com_detalhes",
              "distribuida": "simular_com_estatisticas"}[nome]
    simular = getattr(modulo, funcao, None)
    if not callable(simular):
        raise ValueError(f"{arquivo}: função {funcao} ausente ou não chamável.")
    inspect.signature(simular).bind([], 0, 3, 1)
    codigo = f"oficial:{arquivo}:{funcao};{arquivo}_sha256:{sha256}"
    if hash_worker is not None:
        codigo += f";worker.py_sha256:{hash_worker}"
    return ExecutorOficial(
        simular, nome != "sequencial", codigo,
        getattr(modulo, "obter_enderecos", None) if nome == "distribuida" else None,
    )


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
    executadas = resultado.geracoes_executadas
    if ((isinstance(executor, ExecutorOficial) and executor.com_geracoes
         and executadas is None)
            or (executadas is not None and (type(executadas) is not int or executadas < 0))):
        raise RuntimeError("Gerações informadas devem ser um inteiro não negativo.")
    if (not isinstance(resultado.grade, list)
            or any(not isinstance(linha, list) for linha in resultado.grade)
            or any(type(estado) is not int or estado not in (0, 1, 2)
                   for linha in resultado.grade for estado in linha)):
        raise RuntimeError("Matriz final deve ser uma lista de listas de estados inteiros.")
    if resultado.grade != referencia.grade:
        raise RuntimeError("Matriz final diferente da referência.")
    contagens = contar_estados(resultado.grade)
    if contagens != contar_estados(referencia.grade):
        raise RuntimeError("Contagens finais diferentes da referência.")
    if (resultado.geracoes_executadas is not None
            and resultado.geracoes_executadas != referencia.geracoes_executadas):
        raise RuntimeError("Gerações executadas diferentes da referência.")
    return tempo_s, resultado, contagens


def diagnosticar_sequencial(executor, grade_inicial, geracoes, limiar,
                           trabalhadores, cronometrado, referencia):
    """Conta chamadas reais em outra execução de simular, nunca cronometrada.

    Usar somente após todas as medições do cenário. A função oficial e sua
    proxima_geracao não são reimplementadas; a substituição só conta chamadas.
    A contagem é diagnóstica, não uma instrumentação das amostras de tempo.
    """
    simular = executor.simular
    namespace = simular.__globals__
    original = namespace["proxima_geracao"]
    entrada = deepcopy(grade_inicial)
    executadas = 0

    def contar_chamada(*args, **kwargs):
        nonlocal executadas
        executadas += 1
        return original(*args, **kwargs)

    try:
        namespace["proxima_geracao"] = contar_chamada
        grade = simular(entrada, geracoes, limiar, trabalhadores)
    finally:
        namespace["proxima_geracao"] = original

    if entrada != grade_inicial:
        raise RuntimeError("Diagnóstico sequencial modificou a entrada.")
    if grade != cronometrado.grade or grade != referencia.grade:
        raise RuntimeError("Matriz do diagnóstico sequencial diverge da medição ou referência.")
    if contar_estados(grade) != contar_estados(cronometrado.grade):
        raise RuntimeError("Contagens do diagnóstico sequencial divergem da medição.")
    if executadas != referencia.geracoes_executadas:
        raise RuntimeError("Gerações contadas no diagnóstico sequencial divergem da referência.")
    return executadas


def coletar_hardware_linux():
    """Lê modelo, topologia completa e RAM física; falhas ficam desconhecidas.

    Não deduz núcleos físicos de threads por núcleo. RAM é o total físico
    reportado pelo sistema, não memória livre nem limite de um processo.
    """
    hardware = {"cpu": "", "nucleos_fisicos": None, "ram_bytes": None}
    try:
        blocos = Path("/proc/cpuinfo").read_text(encoding="utf-8").strip().split("\n\n")
        processadores = [dict(linha.split(":", 1) for linha in bloco.splitlines()
                              if ":" in linha) for bloco in blocos]
        processadores = [{k.strip(): v.strip() for k, v in p.items()} for p in processadores]
        modelos = [p.get("model name", "") for p in processadores]
        if modelos and all(modelos):
            hardware["cpu"] = " | ".join(sorted(set(modelos)))
    except (OSError, UnicodeError, ValueError):
        pass

    try:
        raiz_cpu = Path("/sys/devices/system/cpu")
        online = (raiz_cpu / "online").read_text(encoding="ascii").strip()
        cpus = set()
        for faixa in online.split(","):
            limites = [int(valor) for valor in faixa.split("-")]
            if len(limites) not in (1, 2) or limites[0] < 0 or limites[-1] < limites[0]:
                raise ValueError("Lista de CPUs online inválida.")
            cpus.update(range(limites[0], limites[-1] + 1))
        if not cpus or len(cpus) != os.cpu_count():
            raise ValueError("Topologia incompleta ou divergente da quantidade de CPUs lógicas.")
        nucleos = set()
        for cpu in cpus:
            topologia = raiz_cpu / f"cpu{cpu}" / "topology"
            pacote = int((topologia / "physical_package_id").read_text(encoding="ascii"))
            nucleo = int((topologia / "core_id").read_text(encoding="ascii"))
            if pacote < 0 or nucleo < 0:
                raise ValueError("Identificação de núcleo físico desconhecida.")
            nucleos.add((pacote, nucleo))
        if (1 <= len(nucleos) <= len(cpus)
                and (raiz_cpu / "online").read_text(encoding="ascii").strip() == online):
            hardware["nucleos_fisicos"] = len(nucleos)
    except (OSError, UnicodeError, ValueError):
        pass

    try:
        paginas = os.sysconf("SC_PHYS_PAGES")
        tamanho = os.sysconf("SC_PAGE_SIZE")
        if type(paginas) is int and type(tamanho) is int and paginas > 0 and tamanho > 0:
            hardware["ram_bytes"] = paginas * tamanho
    except (OSError, ValueError, AttributeError):
        pass
    return hardware


def coletar_hardware_windows():
    """Consulta registro e APIs nativas; não estima núcleos a partir de threads.

    GetLogicalProcessorInformationEx(RelationProcessorCore) fornece um registro
    por núcleo ativo. GlobalMemoryStatusEx informa a RAM física total visível.
    Falhas deixam somente o campo correspondente desconhecido.
    """
    import ctypes
    from ctypes import wintypes
    import winreg

    hardware = {"cpu": platform.processor(), "nucleos_fisicos": None, "ram_bytes": None}
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as chave:
            hardware["cpu"] = winreg.QueryValueEx(chave, "ProcessorNameString")[0].strip()
    except OSError:
        pass

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    try:
        consultar = kernel.GetLogicalProcessorInformationEx
        consultar.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
        consultar.restype = wintypes.BOOL
        tamanho = wintypes.DWORD()
        if not consultar(0, None, ctypes.byref(tamanho)) and ctypes.get_last_error() != 122:
            raise ctypes.WinError(ctypes.get_last_error())
        if not 0 < tamanho.value <= 16 * 1024 * 1024:
            raise ValueError("Tamanho da topologia inválido.")
        dados = ctypes.create_string_buffer(tamanho.value)
        if not consultar(0, dados, ctypes.byref(tamanho)):
            raise ctypes.WinError(ctypes.get_last_error())
        posicao = nucleos = 0
        while posicao < tamanho.value:
            if posicao + 8 > tamanho.value:
                raise ValueError("Cabeçalho de topologia incompleto.")
            relacao = wintypes.DWORD.from_buffer(dados, posicao).value
            comprimento = wintypes.DWORD.from_buffer(dados, posicao + 4).value
            if comprimento < 8 or posicao + comprimento > tamanho.value:
                raise ValueError("Registro de topologia inválido.")
            nucleos += int(relacao == 0)
            posicao += comprimento
        if 1 <= nucleos <= (os.cpu_count() or 0):
            hardware["nucleos_fisicos"] = nucleos
    except (OSError, ValueError, AttributeError):
        pass

    class EstadoMemoria(ctypes.Structure):
        _fields_ = [("tamanho", wintypes.DWORD), ("carga", wintypes.DWORD)] + [
            (nome, ctypes.c_ulonglong) for nome in (
                "total_fisica", "livre_fisica", "total_paginacao", "livre_paginacao",
                "total_virtual", "livre_virtual", "livre_estendida",
            )
        ]

    try:
        memoria = EstadoMemoria()
        memoria.tamanho = ctypes.sizeof(memoria)
        consultar_memoria = kernel.GlobalMemoryStatusEx
        consultar_memoria.argtypes = [ctypes.POINTER(EstadoMemoria)]
        consultar_memoria.restype = wintypes.BOOL
        if consultar_memoria(ctypes.byref(memoria)) and memoria.total_fisica > 0:
            hardware["ram_bytes"] = memoria.total_fisica
    except (OSError, AttributeError):
        pass
    return hardware


def coletar_ambiente():
    """Registra ambiente e commit fora da medição; desconhecidos ficam vazios."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=RAIZ, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "desconhecido"
    if platform.system() == "Linux":
        hardware = coletar_hardware_linux()
    elif platform.system() == "Windows":
        hardware = coletar_hardware_windows()
    else:
        hardware = {"cpu": platform.processor(), "nucleos_fisicos": None, "ram_bytes": None}
    return {
        "data_utc": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "python": platform.python_version(),
        "implementacao_python": platform.python_implementation(),
        "sistema": platform.platform(),
        "cpu": hardware["cpu"],
        "nucleos_logicos": os.cpu_count(),
        "nucleos_fisicos": hardware["nucleos_fisicos"],
        "ram_bytes": hardware["ram_bytes"],
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
        sequencial_cronometrado = None
        registros_sequenciais = []
        for nome in args.versoes:
            executor = args.executores[nome]
            # Sequenciais ignoram p; uma única configuração evita baselines
            # redundantes/ambíguos quando se varia o paralelismo na mesma coleta.
            quantidades = (args.trabalhadores[:1] if nome.startswith("sequencial")
                           else args.trabalhadores)
            for trabalhadores in quantidades:
                # Com limite zero, nenhum pool/conexão worker é utilizado.
                efetivos = (1 if nome.startswith("sequencial") else
                            0 if geracoes == 0 else min(trabalhadores, linhas))
                for repeticao in range(1, args.repeticoes + 1):
                    try:
                        tempo_s, resultado, contagens = medir_repeticao(
                            executor, grade, geracoes, args.limiar,
                            trabalhadores, referencia,
                        )
                    except Exception as erro:
                        raise RuntimeError(
                            f"Falha em {nome}, {linhas}x{colunas}, limite={geracoes}, "
                            f"percentual={percentual}, trabalhadores={trabalhadores}, "
                            f"repetição={repeticao}: {type(erro).__name__}: {erro}"
                        ) from erro
                    registros.append({
                        **ambiente,
                        "codigo": (args.codigos[nome] + ";enderecos_workers:" + ",".join(
                            f"{host}:{porta}" for host, porta in args.enderecos_workers[trabalhadores]
                        ) if nome == "distribuida" else args.codigos[nome]),
                        "politica_tempo": (POLITICA_OFICIAL if isinstance(executor, ExecutorOficial)
                                           else ambiente["politica_tempo"]),
                        "coordenadores": int(nome == "distribuida"),
                        "versao": nome,
                        "linhas": linhas,
                        "colunas": colunas,
                        "geracoes_maximas": geracoes,
                        "geracoes_executadas": resultado.geracoes_executadas,
                        "percentual_solicitado": percentual,
                        "limiar": args.limiar,
                        "semente": args.semente,
                        "trabalhadores": trabalhadores,
                        "trabalhadores_efetivos": efetivos,
                        "repeticao": repeticao,
                        "tempo_s": tempo_s,
                        "ignorantes": contagens[IGNORANTE],
                        "espalhadores": contagens[ESPALHADOR],
                        "inativos": contagens[INATIVO],
                        "consistente": True,
                        "entrada_preservada": True,
                    })
                    if nome == "sequencial":
                        # Todas as amostras já foram comparadas integralmente à
                        # mesma referência; guarda a última também para confronto
                        # direto com o diagnóstico, sem reter matrizes de todas elas.
                        sequencial_cronometrado = resultado
                        registros_sequenciais.append(registros[-1])
        if registros_sequenciais:
            try:
                executadas = diagnosticar_sequencial(
                    args.executores["sequencial"], grade, geracoes, args.limiar,
                    args.trabalhadores[0], sequencial_cronometrado, referencia,
                )
            except Exception as erro:
                raise RuntimeError(
                    f"Falha no diagnóstico sequencial, {linhas}x{colunas}, limite={geracoes}, "
                    f"percentual={percentual}: {type(erro).__name__}: {erro}"
                ) from erro
            for registro in registros_sequenciais:
                registro["geracoes_executadas"] = executadas
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
    parser.add_argument("--trabalhadores", type=int, nargs="+", default=[1],
                        help="Um ou vários valores, ex.: 1 2 4. Sequenciais usam 1; "
                             "paralela limita às linhas; distribuída exige valor <= linhas.")
    parser.add_argument("--repeticoes", type=int)
    parser.add_argument("--versoes", nargs="+", choices=VERSOES,
                        default=["sequencial_provisorio"])
    parser.add_argument("--sequencial-arquivo", type=Path,
                        help="Arquivo Python externo para --versoes sequencial_candidato; "
                             "ainda não é baseline oficial para speedup.")
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
    if args.repeticoes < 1 or any(t < 1 for t in args.trabalhadores):
        parser.error("Repetições e trabalhadores devem ser positivos.")
    for valores, opcao in ((args.versoes, "versoes"), (args.trabalhadores, "trabalhadores"),
                           (args.tamanhos, "tamanhos"), (args.geracoes, "geracoes"),
                           (args.percentuais, "percentuais")):
        if len(set(valores)) != len(valores):
            parser.error(f"--{opcao} não aceita valores repetidos.")
    if ("distribuida" in args.versoes
            and max(args.trabalhadores) > min(l for l, _ in args.tamanhos)):
        parser.error("Distribuída exige trabalhadores <= linhas em todos os tamanhos.")
    candidato = "sequencial_candidato" in args.versoes
    if candidato and args.sequencial_arquivo is None:
        parser.error("sequencial_candidato exige --sequencial-arquivo CAMINHO.")
    if args.sequencial_arquivo is not None:
        if not candidato:
            parser.error("--sequencial-arquivo exige --versoes sequencial_candidato.")
        args.sequencial_arquivo = args.sequencial_arquivo.resolve()
        if not args.sequencial_arquivo.is_file():
            parser.error(f"Arquivo sequencial candidato não encontrado: {args.sequencial_arquivo}")
    if args.saida is None:
        data = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        args.saida = RESULTADOS / f"benchmark_{data}.csv"
    args.saida = args.saida.resolve()
    if not args.saida.is_relative_to(RESULTADOS.resolve()):
        parser.error("O CSV deve ficar dentro de resultados/.")
    if args.saida.exists():
        parser.error("O arquivo de saída já existe; escolha outro nome.")
    args.executores = {nome: VERSOES[nome].executor for nome in args.versoes}
    try:
        # Toda leitura de fonte, carga, assinatura e hash precede as medições.
        identidade_comum = ";".join(
            f"{arquivo}_sha256:{hashlib.sha256((RAIZ / arquivo).read_bytes()).hexdigest()}"
            for arquivo in ("benchmark.py", "FakeNews.py")
        )
        args.codigos = {}
        for nome in args.versoes:
            if nome in {"sequencial", "paralela", "distribuida"}:
                executor = carregar_oficial(nome)
                args.executores[nome] = executor
                args.codigos[nome] = f"{executor.codigo};{identidade_comum}"
                if nome == "sequencial":
                    args.codigos[nome] += ";geracoes:diagnostico_deterministico_apos_medicoes"
            elif nome == "sequencial_provisorio":
                args.codigos[nome] = f"sequencial_provisorio;{identidade_comum}"
        if candidato:
            args.executores["sequencial_candidato"] = carregar_sequencial_candidato(
                args.sequencial_arquivo,
            )
            executor = args.executores["sequencial_candidato"]
            args.codigos["sequencial_candidato"] = (
                f"sequencial_candidato_sha256:{executor.sha256};"
                f"arquivo_externo:{args.sequencial_arquivo};{identidade_comum}"
            )
        args.enderecos_workers = {}
        if "distribuida" in args.versoes:
            executor = args.executores["distribuida"]
            for trabalhadores in args.trabalhadores:
                enderecos = executor.obter_enderecos(trabalhadores)
                if any(host != "127.0.0.1" for host, _ in enderecos):
                    raise ValueError("Esta integração mede apenas workers em 127.0.0.1; "
                                     "experimentos entre hosts exigem metadados adicionais.")
                args.enderecos_workers[trabalhadores] = enderecos
    except Exception as erro:
        parser.error(f"{type(erro).__name__}: {erro}")
    return args


def main(argv=None):
    """Executa a CLI e imprime resumo somente fora da região medida."""
    args = ler_argumentos(argv)
    if "sequencial_candidato" in args.versoes:
        print(f"sequencial_candidato: {args.sequencial_arquivo}; integração à main pendente; "
              "não pode ser baseline oficial para speedup.")
        print(f"SHA-256 do candidato: {args.executores['sequencial_candidato'].sha256}")
        print("Gerações executadas do candidato: desconhecidas (campo vazio no CSV).")
    if "sequencial" in args.versoes:
        print("sequencial.simular: tempo sem instrumentação; gerações de execução diagnóstica "
              "determinística após as medições de cada cenário.")
    if any(nome in args.versoes for nome in ("sequencial", "paralela", "distribuida")):
        print(f"Política oficial: {POLITICA_OFICIAL}; chamada completa; "
              "workers TCP previamente iniciados.")
    if "distribuida" in args.versoes:
        for trabalhadores in args.trabalhadores:
            print(f"Workers configurados para p={trabalhadores}: "
                  f"{args.enderecos_workers[trabalhadores]}")
    try:
        registros = executar_benchmark(args)
    except Exception as erro:
        print(f"Erro: {erro}. Coleta interrompida; nenhum CSV de medições exportado.",
              file=sys.stderr)
        return 1
    try:
        exportar_csv(args.saida, registros)
    except (OSError, csv.Error) as erro:
        print(f"Erro ao exportar CSV: {erro}. Verifique se há arquivo parcial em {args.saida}.",
              file=sys.stderr)
        return 1
    print(f"CSV: {args.saida}")
    print(f"{len(registros)} medições; matrizes, contagens e entradas verificadas; "
          "gerações informadas pelos executores ou pelo diagnóstico sequencial validado.")
    for registro in registros:
        geracoes = registro['geracoes_executadas']
        print(f"{registro['versao']} {registro['linhas']}x{registro['colunas']} "
              f"repetição={registro['repeticao']} "
              f"trabalhadores={registro['trabalhadores']} "
              f"efetivos={registro['trabalhadores_efetivos']} "
              f"gerações={geracoes if geracoes is not None else 'desconhecidas'} "
              f"tempo_s={registro['tempo_s']:.9f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
