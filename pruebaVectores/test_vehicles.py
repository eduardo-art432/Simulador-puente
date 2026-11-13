import unittest

from fisica.vehicles import EstadoVehiculo, VEHICULOS_EDUCATIVOS, distribuir_cargas_ejes


class TestModeloVehicular(unittest.TestCase):
    def test_auto_reparte_peso_y_separa_fuerza_inercial(self):
        car = VEHICULOS_EDUCATIVOS["automovil"]
        state = EstadoVehiculo(5.0, velocidad_m_s=10.0, aceleracion_m_s2=2.0)
        result = distribuir_cargas_ejes(car, state, [0, 5, 10, 15])
        nodal_weight = -sum(force[1] for force in result["cargas_nodales_n"].values())
        self.assertAlmostEqual(nodal_weight, result["peso_en_puente_n"])
        self.assertAlmostEqual(result["peso_en_puente_n"], car.masa_kg * 9.81)
        self.assertAlmostEqual(result["fuerza_inercial_horizontal_n"], car.masa_kg * 2)
        self.assertNotIn("fuerza_inercial_horizontal_n", result["cargas_nodales_n"])
        self.assertAlmostEqual(result["cargas_por_eje"][0]["peso_por_rueda_n"] * 2,
                               result["cargas_por_eje"][0]["peso_n"])

    def test_ejes_fuera_del_tramo_no_aplican_carga(self):
        bus = VEHICULOS_EDUCATIVOS["autobus"]
        result = distribuir_cargas_ejes(bus, EstadoVehiculo(1.0), [0, 5, 10, 15])
        self.assertLess(result["peso_en_puente_n"], result["peso_total_n"])
        self.assertTrue(any(not axle["en_puente"] for axle in result["cargas_por_eje"]))

    def test_carga_se_conserva_en_interpolacion(self):
        suv = VEHICULOS_EDUCATIVOS["suv"]
        result = distribuir_cargas_ejes(suv, EstadoVehiculo(3.5), [0, 1, 2, 3, 4])
        self.assertAlmostEqual(
            -sum(value[1] for value in result["cargas_nodales_n"].values()),
            suv.masa_kg * 9.81,
        )

    def test_catalogo_visual_anade_los_tipos_sin_perder_alias_de_cargas(self):
        self.assertNotIn("motocicleta", VEHICULOS_EDUCATIVOS)
        self.assertEqual(len(VEHICULOS_EDUCATIVOS["suv"].posiciones_ejes_m), 2)
        self.assertEqual(len(VEHICULOS_EDUCATIVOS["autobus_interurbano"].posiciones_ejes_m), 3)
        self.assertEqual(len(VEHICULOS_EDUCATIVOS["camion_articulado_5_ejes"].posiciones_ejes_m), 5)
        self.assertEqual(VEHICULOS_EDUCATIVOS["automovil"].masa_kg, 1500)


if __name__ == "__main__":
    unittest.main()
