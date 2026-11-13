import unittest

import pygame

from fisica.vehicle_visuals import PERFILES_VISUALES, dibujar_vehiculo_vectorial, geometria_visual, perfil_para_clave
from fisica.vehicles import VEHICULOS_EDUCATIVOS


class TestCatalogoVisualVehicular(unittest.TestCase):
    def test_modelos_tienen_fichas_fisicas_y_estilo(self):
        keys = (
            "sedan", "suv", "camioneta", "autobus_urbano", "autobus_interurbano",
            "camion_2_ejes", "camion_3_ejes", "camion_articulado_5_ejes",
        )
        for key in keys:
            spec = VEHICULOS_EDUCATIVOS[key]
            profile = perfil_para_clave(key)
            self.assertIn(profile, PERFILES_VISUALES.values())
            self.assertAlmostEqual(sum(spec.fracciones_peso_ejes), 1.0)
            self.assertAlmostEqual(
                sum(x*w for x, w in zip(spec.posiciones_ejes_m, spec.fracciones_peso_ejes)),
                spec.centro_masa_x_m,
                delta=0.08,
            )
            self.assertEqual(len(spec.posiciones_ejes_m), len(spec.ruedas_por_eje))

    def test_rellena_ruedas_en_ejes_fisicos_y_renderiza_todo_el_catalogo(self):
        for key, spec in VEHICULOS_EDUCATIVOS.items():
            profile = perfil_para_clave(key)
            geom = geometria_visual(spec, profile, 500, 440, 12)
            self.assertEqual(len(geom["ruedas_px"]), len(spec.posiciones_ejes_m))
            expected_xs = tuple(round(500 + offset * 12) for offset in spec.posiciones_ejes_m)
            self.assertEqual(geom["ejes_px"], expected_xs)
            canvas = pygame.Surface((1200, 750), pygame.SRCALPHA)
            drawn = dibujar_vehiculo_vectorial(
                canvas, pygame, spec, profile, 500, 440, 12,
                rotacion_rueda_rad=0.7,
                offsets_verticales_ejes_px=[0.0] * len(spec.posiciones_ejes_m),
            )
            self.assertEqual(drawn["ejes_px"], expected_xs)
            self.assertNotEqual(canvas.get_bounding_rect().size, (0, 0))


if __name__ == "__main__":
    unittest.main()
