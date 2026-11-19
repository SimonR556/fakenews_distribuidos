
import unittest
from copy import deepcopy

from FakeNews import criar_grade
from sequencial import simular as simular_sequencial
from paralelo import simular as simular_paralela


class TestesIntegracao(unittest.TestCase):

    def comparar_versoes(self, linhas, colunas, geracoes, percentual, limiar):
        grade = criar_grade(
            linhas=linhas,
            colunas=colunas,
            percentual_espalhadores=percentual,
            semente=42,
        )

        grade_original = deepcopy(grade)

        resultado_sequencial = simular_sequencial(
            grade_inicial=grade,
            geracoes=geracoes,
            limiar=limiar,
            trabalhadores=1,
        )

        resultado_paralelo = simular_paralela(
            grade_inicial=grade,
            geracoes=geracoes,
            limiar=limiar,
            trabalhadores=2,
        )

        self.assertEqual(resultado_sequencial, resultado_paralelo)
        self.assertEqual(grade, grade_original)

    def test_01_equivalencia_5x5(self):
        self.comparar_versoes(5, 5, 10, 0.20, 2)

    def test_02_equivalencia_10x10(self):
        self.comparar_versoes(10, 10, 20, 0.10, 3)

    def test_03_equivalencia_100x100(self):
        self.comparar_versoes(100, 100, 50, 0.05, 3)

    def test_04_zero_geracoes(self):
        self.comparar_versoes(5, 5, 0, 0.20, 2)


if __name__ == "__main__":
    unittest.main()
