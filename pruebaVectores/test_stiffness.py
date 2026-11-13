"""Validación del motor de rigidez con soluciones analíticas simples."""

import math
import unittest

from fisica.stiffness import resolver_celosia_rigidez


class TestRigidezCelosia(unittest.TestCase):
    def test_barra_axial_una_dimension(self):
        area, modulus, length, load = 0.01, 200e9, 2.0, 10_000.0
        result = resolver_celosia_rigidez(
            [(0, 0), (length, 0)],
            [(0, 1, area, modulus)],
            {1: (load, 0)},
            {0: (True, True), 1: (False, True)},
        )
        self.assertAlmostEqual(result["desplazamientos"][1][0], load * length / (area * modulus), places=12)
        self.assertAlmostEqual(result["fuerzas_barras"][0], load, places=7)
        self.assertAlmostEqual(result["reacciones"][0][0], -load, places=7)

    def test_celosia_triangular_equilibrio_y_fuerzas(self):
        area, modulus, load = 0.01, 200e9, 10_000.0
        result = resolver_celosia_rigidez(
            [(0, 0), (4, 0), (2, 3)],
            [(0, 1, area, modulus), (0, 2, area, modulus), (1, 2, area, modulus)],
            {2: (0, -load)},
            {0: (True, True), 1: (False, True)},
        )
        expected_diagonal = -load * math.sqrt(13) / 6
        self.assertAlmostEqual(result["fuerzas_barras"][0], load / 3, places=6)
        self.assertAlmostEqual(result["fuerzas_barras"][1], expected_diagonal, places=6)
        self.assertAlmostEqual(result["fuerzas_barras"][2], expected_diagonal, places=6)
        self.assertAlmostEqual(result["reacciones"][0][1], load / 2, places=6)
        self.assertAlmostEqual(result["reacciones"][1][1], load / 2, places=6)
        total_vertical = sum(vector[1] for vector in result["reacciones"].values()) - load
        self.assertAlmostEqual(total_vertical, 0.0, places=7)
        for ux, uy in result["desplazamientos"][:2]:
            self.assertAlmostEqual(uy, 0.0, places=12)

    def test_detecta_estructura_inestable(self):
        with self.assertRaisesRegex(ValueError, "inestable"):
            resolver_celosia_rigidez(
                [(0, 0), (1, 0)], [(0, 1, 0.01, 200e9)], {1: (0, -100)},
                {0: (True, True)},
            )


if __name__ == "__main__":
    unittest.main()
