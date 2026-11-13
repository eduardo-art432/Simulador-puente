import math
import unittest

from fisica.materials import MATERIALES_EDUCATIVOS, Material, Seccion, propiedades_elemento


class TestMateriales(unittest.TestCase):
    def test_catalogo_y_diferencia_de_modelo_de_fluencia(self):
        self.assertEqual(set(MATERIALES_EDUCATIVOS), {"acero_s275", "hormigon_c30", "madera_c24"})
        self.assertEqual(MATERIALES_EDUCATIVOS["acero_s275"].limite_fluencia_traccion_pa, 275e6)
        self.assertIsNone(MATERIALES_EDUCATIVOS["hormigon_c30"].limite_fluencia_traccion_pa)

    def test_seccion_rectangular_y_propiedades_derivadas(self):
        section = Seccion.rectangulo("50x100 mm", 0.05, 0.10)
        self.assertAlmostEqual(section.area_m2, 0.005)
        self.assertAlmostEqual(section.inercia_minima_m4, 0.10 * 0.05**3 / 12)
        material = MATERIALES_EDUCATIVOS["acero_s275"]
        values = propiedades_elemento(material, section, 2.0)
        self.assertAlmostEqual(values["masa_kg"], 7850 * 0.005 * 2)
        self.assertAlmostEqual(values["rigidez_axial_n_m"], 200e9 * 0.005 / 2, delta=1e-5)
        self.assertAlmostEqual(
            values["carga_critica_euler_n"],
            math.pi**2 * 200e9 * section.inercia_minima_m4 / 4,
        )

    def test_rechaza_propiedades_no_fisicas(self):
        with self.assertRaises(ValueError):
            Seccion("inválida", 0, 1e-6)
        with self.assertRaises(ValueError):
            propiedades_elemento(MATERIALES_EDUCATIVOS["acero_s275"], Seccion.circulo("d", 0.1), 0)


if __name__ == "__main__":
    unittest.main()
