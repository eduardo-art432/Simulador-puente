import unittest

from fisica.visualization import (
    color_por_utilizacion,
    proyectar_ejes_px,
    proyectar_nodos_deformados,
    proyectar_serie_temporal,
    proyectar_vector_fuerza_px,
)
from fisica.vehicles import VEHICULOS_EDUCATIVOS


class TestProyeccionVisual(unittest.TestCase):
    def test_deformacion_real_y_amplificada_solo_proyectan_el_mismo_resultado(self):
        nodes = [(0.0, 0.0), (1.0, 0.0)]
        displacement = [(0.0, 0.0), (0.001, -0.002)]
        real = proyectar_nodos_deformados(nodes, displacement, (10, 20), 1000,
                                           amplificada=False, factor_amplificacion=250)
        amplified = proyectar_nodos_deformados(nodes, displacement, (10, 20), 1000,
                                                amplificada=True, factor_amplificacion=250)
        self.assertEqual(real[1], (1011, 22))
        self.assertEqual(amplified[1], (1260, 520))

    def test_ejes_dibujados_corresponden_a_offsets_del_modelo(self):
        for key, expected in (("camion_2_ejes", 2), ("camion_3_ejes", 3), ("camion_5_ejes", 5)):
            spec = VEHICULOS_EDUCATIVOS[key]
            self.assertEqual(len(spec.posiciones_ejes_m), expected)
            self.assertEqual(len(spec.ruedas_por_eje), expected)
            screen = proyectar_ejes_px(500, spec.posiciones_ejes_m, 12)
            self.assertEqual(len(screen), expected)
            self.assertEqual(screen[0], 500)

    def test_categoria_de_color_usa_fuerza_y_utilizacion(self):
        self.assertEqual(color_por_utilizacion(1000, 0.1), "baja_traccion")
        self.assertEqual(color_por_utilizacion(-1000, 0.4), "compresion")
        self.assertEqual(color_por_utilizacion(1000, 0.9), "cerca_capacidad")
        self.assertEqual(color_por_utilizacion(-1000, 1.1), "falla")

    def test_grafica_temporal_respeta_intervalos_reales_y_reacciones_con_signo(self):
        samples = [(2.0, 1.0), (3.0, 0.0), (7.0, -1.0)]
        points = proyectar_serie_temporal(samples, 0, 1, (10, 20, 110, 80), (-1.0, 1.0))
        self.assertEqual(points, ((10, 20), (30, 50), (110, 80)))

    def test_grafica_temporal_rechaza_tiempos_desordenados(self):
        with self.assertRaises(ValueError):
            proyectar_serie_temporal([(2.0, 1.0), (1.0, 2.0)], 0, 1, (0, 0, 10, 10), (0, 2))

    def test_puente_y_grafica_comparten_eje_vertical_positivo_hacia_arriba(self):
        nodes = [(0.0, 0.0), (1.0, 0.0)]
        displacement = [(0.0, 0.0), (0.0, -0.002)]
        bridge = proyectar_nodos_deformados(
            nodes, displacement, (10, 100), 1000,
            amplificada=False, factor_amplificacion=1,
        )
        graph = proyectar_nodos_deformados(
            nodes, displacement, (10, 50), (100, 10000),
            amplificada=False, factor_amplificacion=1,
        )
        self.assertEqual(bridge, ((10, 100), (1010, 102)))
        self.assertEqual(graph, ((10, 50), (110, 70)))

    def test_vector_reaccion_respeta_signo_de_x_y(self):
        self.assertEqual(proyectar_vector_fuerza_px((10, 20), (3, -4), 2), (16, 28))


if __name__ == "__main__":
    unittest.main()
