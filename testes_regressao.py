"""Regressões do menu e da sincronização por geração."""

import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import main


class TestesRegressao(unittest.TestCase):
    def test_configuracao_distribuida_invalida_volta_ao_menu(self):
        parametros = dict(linhas=2, colunas=2, geracoes=1,
                          percentual=0.2, limiar=2, semente=42)
        saida = io.StringIO()
        with (patch.dict(os.environ, {"FAKENEWS_WORKERS": "localhost:5000,localhost:5001"}),
              patch("main.configurar_simulacao", return_value=parametros),
              patch("main.ler_inteiro", return_value=1),
              patch("builtins.input", return_value=""),
              contextlib.redirect_stdout(saida)):
            main.executar_simulacao("distribuida")
        self.assertIn("quantidade de endereços", saida.getvalue())
        self.assertNotIn("RESULTADO FINAL", saida.getvalue())

    def test_erro_em_thread_nao_bloqueia_demais_threads(self):
        # Processo separado: se houver regressão, timeout encerra o teste
        # sem deixar threads presas no processo do unittest.
        codigo = '''
from unittest.mock import patch
import paralelo
original = paralelo._processar_linhas
def falhar(grade, proxima, inicio, fim, limiar, *extras):
    if inicio == 0:
        raise RuntimeError("falha de teste")
    return original(grade, proxima, inicio, fim, limiar, *extras)
with patch.object(paralelo, "_processar_linhas", side_effect=falhar):
    try:
        paralelo.simular([[2, 2], [0, 0]], 1, 2, 2)
    except RuntimeError as erro:
        assert str(erro) == "falha de teste"
    else:
        raise AssertionError("A falha da thread não foi propagada")
'''
        resultado = subprocess.run(
            [sys.executable, "-B", "-c", codigo],
            cwd=Path(__file__).resolve().parent,
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)

    def test_grade_irregular_rejeitada_antes_das_threads(self):
        import paralelo
        with patch.object(paralelo, "ThreadPoolExecutor") as executor:
            with self.assertRaises(ValueError):
                paralelo.simular([[2, 2], [0]], 1, 2, 2)
            executor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
