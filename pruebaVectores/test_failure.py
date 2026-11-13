import unittest

from fisica.failure import evaluar_elemento
from fisica.materials import MATERIALES_EDUCATIVOS, Seccion


class TestCriteriosFalla(unittest.TestCase):
    def setUp(self):
        self.steel = MATERIALES_EDUCATIVOS["acero_s275"]
        self.section = Seccion.rectangulo("100x100 mm", 0.1, 0.1)

    def test_traccion_evalua_fluencia_y_resistencia_ultima(self):
        result = evaluar_elemento(self.steel, self.section, 2, 2_000_000)
        self.assertAlmostEqual(result["capacidades"]["fluencia_traccion_n"], 2_750_000)
        self.assertAlmostEqual(result["capacidades"]["rotura_traccion_n"], 4_300_000)
        self.assertEqual(result["criterio_critico"], "fluencia_traccion")
        self.assertEqual(result["estado"], "normal")

    def test_compresion_considera_euler_y_resistencia_material(self):
        result = evaluar_elemento(self.steel, self.section, 4, -1_100_000)
        self.assertIn("pandeo_euler", result["utilizaciones"])
        self.assertIn("aplastamiento_compresion", result["utilizaciones"])
        self.assertEqual(result["criterio_critico"], "pandeo_euler")
        self.assertEqual(result["estado"], "falla")

    def test_conexion_y_desplazamiento_solo_se_evalua_con_datos(self):
        material = MATERIALES_EDUCATIVOS["madera_c24"]
        result = evaluar_elemento(
            material, self.section, 2, 10_000,
            capacidad_conexion_n=20_000,
            desplazamiento_m=0.03,
            limite_desplazamiento_m=0.02,
        )
        self.assertEqual(result["criterio_critico"], "deformacion")
        self.assertEqual(result["estado"], "falla")
        self.assertNotIn("fluencia_traccion", result["utilizaciones"])


if __name__ == "__main__":
    unittest.main()
