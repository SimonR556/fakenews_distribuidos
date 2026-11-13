"""Analisa CSVs do benchmark sem executar simulações ou alterar dados brutos."""

import argparse
import csv
from datetime import datetime
import math
from pathlib import Path
import statistics
import sys
from collections import defaultdict


RESULTADOS = Path(__file__).resolve().parent / "resultados"
CAMPOS = """data_utc commit python implementacao_python sistema cpu nucleos_logicos
nucleos_fisicos ram_bytes hosts coordenadores politica_tempo codigo versao linhas
colunas geracoes_maximas geracoes_executadas percentual_solicitado limiar semente
trabalhadores trabalhadores_efetivos repeticao tempo_s ignorantes espalhadores
inativos consistente entrada_preservada""".split()
INTEIROS = """nucleos_logicos nucleos_fisicos ram_bytes hosts coordenadores linhas
colunas geracoes_maximas geracoes_executadas limiar semente trabalhadores
trabalhadores_efetivos repeticao ignorantes espalhadores inativos""".split()
OPCIONAIS = {"nucleos_logicos", "nucleos_fisicos", "ram_bytes", "geracoes_executadas"}
IGNORAR_GRUPO = {"data_utc", "repeticao", "tempo_s", "consistente", "entrada_preservada"}
# O número de trabalhadores e o papel de coordenador pertencem à versão.
IGNORAR_COMPARACAO = {"versao", "trabalhadores", "trabalhadores_efetivos", "coordenadores"}
ESTATISTICAS = ["amostras", "media_s", "mediana_s", "minimo_s", "maximo_s",
                "desvio_padrao_amostral_s"]


def validar(registro):
    """Normaliza números e rejeita medições inválidas, sem tentar corrigi-las."""
    for campo in INTEIROS:
        valor = registro[campo]
        registro[campo] = None if valor == "" and campo in OPCIONAIS else int(valor)
    for campo in ("tempo_s", "percentual_solicitado"):
        registro[campo] = float(registro[campo])
        if not math.isfinite(registro[campo]):
            raise ValueError(f"{campo} deve ser finito")
    for campo in ("consistente", "entrada_preservada"):
        if registro[campo] != "True":
            raise ValueError(f"{campo} deve ser True")
    for campo in ("commit", "python", "implementacao_python", "sistema",
                  "politica_tempo", "codigo"):
        if not registro[campo]:
            raise ValueError(f"{campo} vazio")
    if registro["versao"] not in {"sequencial_provisorio", "sequencial", "paralela", "distribuida"}:
        raise ValueError("versão desconhecida")
    datetime.fromisoformat(registro["data_utc"])
    for campo in INTEIROS:
        valor = registro[campo]
        if valor is not None and campo != "semente" and valor < 0:
            raise ValueError(f"{campo} negativo")
    for campo in ("linhas", "colunas", "hosts", "trabalhadores",
                  "trabalhadores_efetivos", "repeticao", "nucleos_logicos",
                  "nucleos_fisicos", "ram_bytes"):
        if registro[campo] is not None and registro[campo] < 1:
            raise ValueError(f"{campo} deve ser positivo")
    if registro["tempo_s"] <= 0:
        raise ValueError("tempo_s deve ser positivo")
    if not 0 <= registro["percentual_solicitado"] <= 1 or not 0 <= registro["limiar"] <= 8:
        raise ValueError("percentual ou limiar fora do intervalo aceito pelo benchmark")
    if registro["trabalhadores_efetivos"] > registro["trabalhadores"]:
        raise ValueError("trabalhadores efetivos excedem os solicitados")
    if registro["versao"].startswith("sequencial") and registro["trabalhadores_efetivos"] != 1:
        raise ValueError("versão sequencial deve usar um trabalhador efetivo")
    executadas = registro["geracoes_executadas"]
    limite = registro["geracoes_maximas"]
    if executadas is not None:
        if not 0 <= executadas <= limite or (limite > 0 and executadas == 0):
            raise ValueError("gerações executadas incompatíveis com o limite")
        if executadas < limite and registro["espalhadores"] != 0:
            raise ValueError("parada antecipada com espalhadores ativos")
    if sum(registro[c] for c in ("ignorantes", "espalhadores", "inativos")) != registro["linhas"] * registro["colunas"]:
        raise ValueError("contagens finais não somam o tamanho da matriz")
    return registro


def chave(registro, campos):
    return tuple(registro[c] for c in campos)


def ler_csvs(caminhos):
    registros, vistos, cabecalho = [], set(), None
    resultados_esperados = {}
    for caminho in caminhos:
        with caminho.open(newline="", encoding="utf-8-sig") as arquivo:
            leitor = csv.DictReader(arquivo)
            campos = leitor.fieldnames or []
            if len(campos) != len(set(campos)) or not set(CAMPOS) <= set(campos):
                raise ValueError(f"{caminho}: cabeçalho inválido; obrigatórios: {', '.join(CAMPOS)}")
            if cabecalho is not None and set(campos) != set(cabecalho):
                raise ValueError("CSVs com esquemas diferentes; analise-os separadamente")
            cabecalho = campos
            quantidade = 0
            for linha, bruto in enumerate(leitor, 2):
                try:
                    if None in bruto or any(v is None for v in bruto.values()):
                        raise ValueError("quantidade de campos diferente do cabeçalho")
                    registro = validar({c: v.strip() for c, v in bruto.items()})
                    identidade = chave(registro, [c for c in campos if c not in
                                                {"tempo_s", "geracoes_executadas", "ignorantes",
                                                 "espalhadores", "inativos", "consistente",
                                                 "entrada_preservada"}])
                    if identidade in vistos:
                        raise ValueError("medição duplicada (mesma coleta, cenário e repetição)")
                    vistos.add(identidade)
                    campos_resultado = {"geracoes_executadas", "ignorantes", "espalhadores", "inativos"}
                    cenario_coleta = chave(registro, [c for c in campos if c not in
                                                     campos_resultado | {"tempo_s", "repeticao",
                                                                         "consistente", "entrada_preservada"}])
                    resultado = chave(registro, sorted(campos_resultado))
                    if cenario_coleta in resultados_esperados and resultados_esperados[cenario_coleta] != resultado:
                        raise ValueError("repetições da mesma coleta têm gerações ou contagens divergentes")
                    resultados_esperados[cenario_coleta] = resultado
                    registros.append(registro)
                    quantidade += 1
                except ValueError as erro:
                    raise ValueError(f"{caminho}:{linha}: {erro}") from erro
            if not quantidade:
                raise ValueError(f"{caminho}: nenhuma medição")
    return registros, [c for c in cabecalho if c not in IGNORAR_GRUPO]


def resumir(registros, campos):
    grupos = defaultdict(list)
    for registro in registros:
        grupos[chave(registro, campos)].append(registro["tempo_s"])
    resumos = []
    for valores, tempos in grupos.items():
        resumos.append(dict(zip(campos, valores), amostras=len(tempos),
                            media_s=statistics.mean(tempos), mediana_s=statistics.median(tempos),
                            minimo_s=min(tempos), maximo_s=max(tempos),
                            desvio_padrao_amostral_s=statistics.stdev(tempos) if len(tempos) > 1 else ""))
    return resumos


def comparar(resumos, campos):
    """Exige metadados coincidentes, gerações conhecidas e baseline inequívoco."""
    comuns = [c for c in campos if c not in IGNORAR_COMPARACAO]
    baselines = defaultdict(list)
    for resumo in resumos:
        if resumo["versao"] == "sequencial":
            baselines[chave(resumo, comuns)].append(resumo)
    comparacoes = []
    for resumo in resumos:
        if resumo["versao"] not in {"paralela", "distribuida"}:
            continue
        candidatos = baselines[chave(resumo, comuns)]
        # Igualdade de campos vazios não comprova igualdade de hardware.
        ambiente = ("cpu", "nucleos_logicos", "nucleos_fisicos", "ram_bytes")
        if (len(candidatos) != 1 or resumo["geracoes_executadas"] is None
                or any(resumo[c] in (None, "", "desconhecido") for c in ambiente)
                or "provisorio" in resumo["codigo"].lower()
                or resumo["commit"] == "desconhecido"):
            continue
        baseline = candidatos[0]
        speedup = baseline["media_s"] / resumo["media_s"]
        comparacoes.append({**resumo, "media_sequencial_s": baseline["media_s"],
                            "amostras_sequencial": baseline["amostras"],
                            "speedup": speedup,
                            "eficiencia": speedup / resumo["trabalhadores_efetivos"]})
    return comparacoes


def salvar_csv(caminho, registros, campos):
    with caminho.open("x", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(registros)
    print(f"Gerado: {caminho}")


def graficos(resumos, comparacoes, campos, saida, preliminar):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib não está instalado: CSVs gerados; gráficos PNG indisponíveis. Nenhuma instalação solicitada.")
        return
    especificacoes = [(resumos, "media_s", "Tempo médio (s)")]
    if comparacoes:
        especificacoes += [(comparacoes, "speedup", "Speedup S(p)"),
                          (comparacoes, "eficiencia", "Eficiência E(p)")]
    for registros, metrica, rotulo in especificacoes:
        # Varia somente o tamanho; não conecta cenários ou gerações diferentes.
        facetas = [c for c in campos if c not in {"linhas", "colunas", "ignorantes", "espalhadores", "inativos"}]
        grupos = defaultdict(list)
        for registro in registros:
            grupos[chave(registro, facetas)].append(registro)
        for indice, grupo in enumerate(grupos.values(), 1):
            grupo.sort(key=lambda r: (r["linhas"] * r["colunas"], r["linhas"], r["colunas"]))
            fig, ax = plt.subplots(figsize=(8, 5))
            x = list(range(len(grupo)))
            ax.plot(x, [r[metrica] for r in grupo], marker="o")
            ax.set_xticks(x, [f"{r['linhas']}×{r['colunas']}" for r in grupo])
            ax.set_xlabel("Tamanho da matriz (linhas × colunas)")
            ax.set_ylabel(rotulo)
            exemplo = grupo[0]
            ax.set_title(("PRELIMINAR — " if preliminar else "") + exemplo["versao"] +
                         f" | p={exemplo['trabalhadores_efetivos']} | limite={exemplo['geracoes_maximas']}"
                         f" | executadas={exemplo['geracoes_executadas']}")
            ax.grid(alpha=0.3)
            fig.tight_layout()
            caminho = saida / f"{metrica}_{indice:03d}.png"
            # A pasta é criada exclusivamente para esta análise; ainda assim, usa x.
            with caminho.open("xb") as arquivo:
                fig.savefig(arquivo, format="png")
            plt.close(fig)
            print(f"Gerado: {caminho}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csvs", nargs="+", type=Path, help="Um ou vários CSVs do benchmark")
    parser.add_argument("--saida", required=True, type=Path, help="Pasta nova dentro de resultados/")
    args = parser.parse_args(argv)
    saida = args.saida.resolve()
    if not saida.is_relative_to(RESULTADOS.resolve()) or saida == RESULTADOS.resolve():
        parser.error("--saida deve ser uma subpasta nova dentro de resultados/")
    if saida.exists():
        parser.error("pasta de saída já existe; escolha outra para preservar os arquivos")
    try:
        caminhos = [c.resolve() for c in args.csvs]
        if len(set(caminhos)) != len(caminhos):
            raise ValueError("CSV de entrada repetido")
        registros, campos = ler_csvs(caminhos)
        resumos = resumir(registros, campos)
        comparacoes = comparar(resumos, campos)
        preliminar = all(r["versao"] == "sequencial_provisorio" for r in registros)
        saida.mkdir(parents=True, exist_ok=False)
        salvar_csv(saida / "resumo.csv", resumos, campos + ESTATISTICAS)
        print(f"{len(registros)} medições; {len(resumos)} grupos descritivos.")
        if preliminar:
            print("RESULTADOS PRELIMINARES: somente sequencial_provisorio; sem baseline oficial ou medições paralelas/distribuídas.")
        if comparacoes:
            salvar_csv(saida / "comparacoes.csv", comparacoes,
                       campos + ESTATISTICAS + ["media_sequencial_s", "amostras_sequencial", "speedup", "eficiencia"])
        else:
            print("Speedup e eficiência não calculados: nenhuma comparação oficial com cenário, ambiente completo e política de tempo compatíveis.")
        graficos(resumos, comparacoes, campos, saida, preliminar)
    except (OSError, ValueError, csv.Error, OverflowError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
