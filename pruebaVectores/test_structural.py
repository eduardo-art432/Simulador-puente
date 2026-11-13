import unittest

from fisica.materials import MATERIALES_EDUCATIVOS, Seccion
from fisica.structural import DisenoBarra, analizar_estado_celosia, buscar_primera_falla
from fisica.vehicles import EstadoVehiculo, VEHICULOS_EDUCATIVOS


class TestIntegracionEstructural(unittest.TestCase):
    def setUp(self):
        steel = MATERIALES_EDUCATIVOS["acero_s275"]
        section = Seccion.circulo("barra 100mm", 0.1)
        self.designs = [DisenoBarra(f"B{i+1}", steel, section) for i in range(5)]
        self.nodes = [(0, 0), (2, 0), (4, 0), (2, 3)]
        self.bars = [(0, 1), (1, 2), (0, 3), (1, 3), (2, 3)]
        self.supports = {0: (True, True), 2: (False, True)}

    def test_reanaliza_posicion_y_devuelve_deformacion_demanda(self):
        result = analizar_estado_celosia(
            self.nodes, self.bars, self.designs, {}, self.supports,
            VEHICULOS_EDUCATIVOS["automovil"], EstadoVehiculo(2.7),
        )
        self.assertGreater(result["desplazamiento_nodal_maximo_m"], 0)
        self.assertEqual(len(result["elementos"]), 5)
        self.assertIn(result["estado"], {"normal", "advertencia", "falla"})
        total_vehicle_weight = -sum(
            force[1] for force in result["cargas_vehiculares"]["cargas_nodales_n"].values()
        )
        self.assertAlmostEqual(total_vehicle_weight, 1500 * 9.81)

    def test_busqueda_discreta_informa_primera_posicion_de_falla(self):
        seen = []

        def state_at(position):
            seen.append(position)
            return {"estado": "falla" if position >= 2 else "normal"}

        result = buscar_primera_falla([0, 1, 2, 3], state_at)
        self.assertEqual(result["posicion_eje_referencia_m"], 2.0)
        self.assertEqual(seen, [0, 1, 2])

    def test_modelo_elastico_recupera_geometria_al_salir_todos_los_ejes(self):
        vehicle = VEHICULOS_EDUCATIVOS["automovil"]
        loaded = analizar_estado_celosia(
            self.nodes, self.bars, self.designs, {}, self.supports,
            vehicle, EstadoVehiculo(2.7),
        )
        self.assertGreater(loaded["desplazamiento_nodal_maximo_m"], 0.0)

        # El eje trasero ya pasó el apoyo derecho: ningún eje carga el tablero.
        clear_position = max(node[0] for node in self.nodes) + abs(min(vehicle.posiciones_ejes_m)) + 0.01
        unloaded = analizar_estado_celosia(
            self.nodes, self.bars, self.designs, {}, self.supports,
            vehicle, EstadoVehiculo(clear_position),
        )
        self.assertAlmostEqual(unloaded["cargas_vehiculares"]["peso_en_puente_n"], 0.0)
        self.assertAlmostEqual(unloaded["desplazamiento_nodal_maximo_m"], 0.0)
        self.assertTrue(all(abs(force) < 1e-9 for force in unloaded["fuerzas_barras"]))


if __name__ == "__main__":
    unittest.main()
