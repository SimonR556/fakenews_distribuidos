
"""
Testes automatizados das melhorias opcionais.

Executar:
    python3 -m unittest -v testes_melhorias
"""

import unittest
from copy import deepcopy

from melhorias import (
    contar_influencia,
    proxima_geracao_influenciadores,
    simular_influenciadores,
    proxima_geracao_resistencia,
    simular_resistencia,
    simular_com_estatisticas,
)

from sequencial import simular


class TestesMelhorias(unittest.TestCase):

    def setUp(self):
        self.grade = [
            [0, 1, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]
        self.influenciadores = {(0, 1)}
        self.resistentes = {(1, 1)}

    def test_01_influenciador_tem_peso_maior(self):
        influencia = contar_influencia(
            self.grade, 1, 1, self.influenciadores, 3
        )
        self.assertEqual(influencia, 3)

    def test_02_espalhador_comum_tem_peso_um(self):
        influencia = contar_influencia(
            self.grade, 1, 1, set(), 3
        )
        self.assertEqual(influencia, 1)

    def test_03_influenciador_convence_vizinhos(self):
        resultado = proxima_geracao_influenciadores(
            self.grade, 3, self.influenciadores
        )
        self.assertEqual(resultado[1][1], 1)
        self.assertEqual(resultado[0][1], 2)

    def test_04_resistente_nao_e_convencido(self):
        resultado = proxima_geracao_resistencia(
            self.grade,
            3,
            self.resistentes,
            influenciadores=self.influenciadores
        )
        self.assertEqual(resultado[1][1], 0)
        self.assertEqual(resultado[1][0], 1)

    def test_05_matriz_original_preservada(self):
        original = deepcopy(self.grade)

        simular_resistencia(
            self.grade,
            5,
            3,
            self.resistentes,
            influenciadores=self.influenciadores
        )

        self.assertEqual(self.grade, original)

    def test_06_zero_geracoes(self):
        resultado = simular_influenciadores(
            self.grade, 0, 3, self.influenciadores
        )
        self.assertEqual(resultado, self.grade)

    def test_07_sem_melhorias_equivale_ao_original(self):
        original = simular(self.grade, 5, 3, 1)

        melhorado = simular_resistencia(
            self.grade,
            5,
            3,
            resistentes=set(),
            influenciadores=set()
        )

        self.assertEqual(melhorado, original)

    def test_08_estatisticas_iniciais(self):
        _, historico = simular_com_estatisticas(
            self.grade,
            5,
            3,
            resistentes=self.resistentes,
            influenciadores=self.influenciadores
        )

        self.assertEqual(historico[0]["ignorantes"], 8)
        self.assertEqual(historico[0]["espalhadores"], 1)
        self.assertEqual(historico[0]["inativos"], 0)

    def test_09_estatisticas_finais(self):
        grade_final, historico = simular_com_estatisticas(
            self.grade,
            5,
            3,
            resistentes=self.resistentes,
            influenciadores=self.influenciadores
        )

        self.assertEqual(historico[-1]["espalhadores"], 0)
        self.assertEqual(grade_final[1][1], 0)
        self.assertEqual(len(historico), 3)

    def test_10_total_populacao_constante(self):
        _, historico = simular_com_estatisticas(
            self.grade,
            5,
            3,
            resistentes=self.resistentes,
            influenciadores=self.influenciadores
        )

        for registro in historico:
            total = (
                registro["ignorantes"]
                + registro["espalhadores"]
                + registro["inativos"]
            )
            self.assertEqual(total, 9)

    def test_11_bordas_sem_contorno_periodico(self):
        grade = [
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]

        influencia = contar_influencia(
            grade, 2, 2, {(0, 0)}, 3
        )

        self.assertEqual(influencia, 0)

    def test_12_inativos_permanecem_inativos(self):
        grade = [
            [2, 1],
            [0, 0]
        ]

        resultado = proxima_geracao_resistencia(
            grade, 2, set()
        )

        self.assertEqual(resultado[0][0], 2)

    def test_13_parada_antecipada(self):
        _, historico = simular_com_estatisticas(
            self.grade,
            50,
            3,
            resistentes=self.resistentes,
            influenciadores=self.influenciadores
        )

        self.assertEqual(historico[-1]["geracao"], 2)

    def test_14_estatisticas_zero_geracoes(self):
        resultado, historico = simular_com_estatisticas(
            self.grade, 0, 3
        )

        self.assertEqual(resultado, self.grade)
        self.assertEqual(len(historico), 1)
        self.assertEqual(historico[0]["geracao"], 0)


if __name__ == "__main__":
    unittest.main()
