import unittest
from copy import deepcopy

from FakeNews import criar_grade
from FakeNews import proxima_geracao as proxima_original

from sequencial import (
    simular,
    proxima_geracao,
    contar_estados,
    contar_vizinhos_espalhadores,
)


class TestesSequencial(unittest.TestCase):

    def test_01_contagem_vizinhos(self):
        """Conta corretamente os vizinhos espalhadores."""
        grade = [
            [1, 0, 1],
            [0, 0, 0],
            [1, 0, 1]
        ]

        self.assertEqual(
            contar_vizinhos_espalhadores(grade, 1, 1),
            4
        )

    def test_02_espalhador_vira_inativo(self):
        """Espalhadores deixam de compartilhar apos uma geracao."""
        grade = [
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0]
        ]

        esperado = [
            [0, 0, 0],
            [0, 2, 0],
            [0, 0, 0]
        ]

        self.assertEqual(simular(grade, 1, 2, 1), esperado)

    def test_03_ignorante_vira_espalhador(self):
        """Ignorante com vizinhos suficientes vira espalhador."""
        grade = [
            [1, 1, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]

        resultado = proxima_geracao(grade, 2)

        self.assertEqual(resultado[1][1], 1)

    def test_04_inativo_permanece_inativo(self):
        """Uma pessoa inativa nao muda de estado."""
        grade = [
            [2, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]

        resultado = proxima_geracao(grade, 2)

        self.assertEqual(resultado[0][0], 2)

    def test_05_sem_espalhadores(self):
        """Uma matriz sem espalhadores permanece igual."""
        grade = [
            [0, 0, 0],
            [0, 2, 0],
            [0, 0, 0]
        ]

        self.assertEqual(simular(grade, 10, 2, 1), grade)

    def test_06_todos_espalhadores(self):
        """Todos os espalhadores tornam-se inativos."""
        grade = [
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]
        ]

        esperado = [
            [2, 2, 2],
            [2, 2, 2],
            [2, 2, 2]
        ]

        self.assertEqual(simular(grade, 1, 2, 1), esperado)

    def test_07_zero_geracoes(self):
        """Zero geracoes nao altera o resultado."""
        grade = [
            [1, 0],
            [0, 1]
        ]

        self.assertEqual(simular(grade, 0, 2, 1), grade)

    def test_08_preserva_matriz_original(self):
        """A funcao nao pode modificar a entrada."""
        grade = [
            [1, 1, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]

        copia = deepcopy(grade)

        simular(grade, 5, 2, 1)

        self.assertEqual(grade, copia)

    def test_09_equivalencia_5x5(self):
        """Compara a proxima geracao com o codigo original."""
        grade = criar_grade(5, 5, 0.30, 42)

        esperado = proxima_original(grade, 2)
        resultado = proxima_geracao(grade, 2)

        self.assertEqual(resultado, esperado)

    def test_10_equivalencia_10x10(self):
        """Compara varias geracoes com o codigo original."""
        grade = criar_grade(10, 10, 0.20, 42)

        esperado = deepcopy(grade)

        for _ in range(5):
            esperado = proxima_original(esperado, 2)

        resultado = simular(grade, 5, 2, 1)

        self.assertEqual(resultado, esperado)

    def test_11_cenario_padrao_100x100(self):
        """Valida o resultado documentado pelo grupo."""
        grade = criar_grade(100, 100, 0.05, 42)

        resultado = simular(
            grade_inicial=grade,
            geracoes=50,
            limiar=3,
            trabalhadores=1
        )

        contagem = contar_estados(resultado)

        self.assertEqual(contagem[0], 9463)
        self.assertEqual(contagem[1], 0)
        self.assertEqual(contagem[2], 537)

    def test_12_limiar_elevado(self):
        """Sem vizinhos suficientes, nao ha novos espalhadores."""
        grade = [
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]

        resultado = proxima_geracao(grade, 8)

        self.assertEqual(resultado[1][1], 0)
        self.assertEqual(resultado[0][0], 2)

    def test_13_bordas_da_matriz(self):
        """Verifica se os cantos nao acessam posicoes invalidas."""
        grade = [
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, 0]
        ]

        self.assertEqual(
            contar_vizinhos_espalhadores(grade, 0, 0),
            2
        )

        resultado = proxima_geracao(grade, 2)

        self.assertEqual(resultado[0][0], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
