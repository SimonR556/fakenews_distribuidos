"""Integração TCP real; inicia e encerra somente os workers destes testes."""

from copy import deepcopy
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from FakeNews import criar_grade
from benchmark import executar_referencia
from distribuido import simular_com_estatisticas
from worker import enviar_mensagem, receber_mensagem


class TestesDistribuido(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processos = []
        cls.portas = []
        cls.addClassCleanup(cls.encerrar_workers)
        for _ in range(4):
            with socket.socket() as reserva:
                reserva.bind(("127.0.0.1", 0))
                porta = reserva.getsockname()[1]
            processo = subprocess.Popen(
                [sys.executable, "-B", "worker.py", "--porta", str(porta)],
                cwd=Path(__file__).resolve().parent,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
            )
            cls.processos.append(processo)
            cls.portas.append(porta)
            limite = time.monotonic() + 10
            while True:
                if processo.poll() is not None:
                    raise RuntimeError("Worker de teste encerrou durante a inicialização.")
                try:
                    with socket.create_connection(("127.0.0.1", porta), timeout=1) as conexao:
                        enviar_mensagem(conexao, {"tipo": "ping"})
                        if receber_mensagem(conexao).get("tipo") != "pong":
                            raise RuntimeError("Worker não respondeu ao ping.")
                    break
                except OSError:
                    if time.monotonic() >= limite:
                        raise
                    time.sleep(0.05)

    @classmethod
    def encerrar_workers(cls):
        for processo in cls.processos:
            if processo.poll() is None:
                processo.terminate()
        for processo in cls.processos:
            try:
                processo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                processo.kill()
                processo.wait(timeout=5)

    def comparar(self, grade, geracoes, limiar, trabalhadores):
        original = deepcopy(grade)
        referencia = executar_referencia(grade, geracoes, limiar)
        enderecos = ",".join(f"127.0.0.1:{p}" for p in self.portas[:trabalhadores])
        with patch.dict(os.environ, {"FAKENEWS_WORKERS": enderecos}):
            resultado, executadas = simular_com_estatisticas(
                grade, geracoes, limiar, trabalhadores,
            )
        self.assertEqual(resultado, referencia.grade)
        self.assertEqual(executadas, referencia.geracoes_executadas)
        self.assertEqual(grade, original)
        self.assertIsNot(resultado, grade)
        for recebida, entrada in zip(resultado, grade):
            self.assertIsNot(recebida, entrada)

    def test_tamanhos_e_divisao_com_sobra(self):
        for tamanho in (5, 10, 100):
            for trabalhadores in (1, 2, 4):
                with self.subTest(tamanho=tamanho, trabalhadores=trabalhadores):
                    self.comparar(criar_grade(tamanho, tamanho, 0.4, 42),
                                  8, 3, trabalhadores)

    def test_cenario_padrao_100x100(self):
        self.comparar(criar_grade(100, 100, 0.05, 42), 50, 3, 4)

    def test_contagio_nas_fronteiras(self):
        grade = [[0] * 5 for _ in range(7)]
        grade[1][2] = grade[2][2] = grade[4][2] = grade[5][2] = 1
        for geracoes in (1, 2, 5):
            with self.subTest(geracoes=geracoes):
                self.comparar(grade, geracoes, 2, 4)

    def test_zero_geracoes_nao_abre_conexoes(self):
        with patch("distribuido.socket.create_connection") as conectar:
            self.comparar([[1, 0], [0, 2]], 0, 2, 2)
            conectar.assert_not_called()

    def test_sem_espalhadores_e_limiar_zero(self):
        for limiar in (0, 3):
            with self.subTest(limiar=limiar):
                self.comparar([[0] * 4 for _ in range(5)], 5, limiar, 4)

    def test_workers_reutilizados_entre_simulacoes(self):
        for _ in range(2):
            self.comparar(criar_grade(5, 5, 0.4, 42), 5, 2, 2)


if __name__ == "__main__":
    unittest.main()
