import unittest

from fisica.materials import MATERIALES_EDUCATIVOS, Seccion
from fisica.structural import DisenoBarra, analizar_estado_celosia
from fisica.vehicles import EstadoVehiculo, VEHICULOS_EDUCATIVOS


class TestDimensionamientoVehiculos(unittest.TestCase):
    def test_bus_y_camion_cruzan_bajo_limite_de_utilizacion(self):
        screen_nodes = [
            (370, 430), (490, 430), (610, 430), (730, 430),
            (850, 430), (970, 430), (1090, 430),
            (430, 330), (550, 330), (670, 330), (790, 330), (910, 330), (1030, 330),
        ]
        nodes = [((x - 370) / 12, (430 - y) / 12) for x, y in screen_nodes]
        bars = [
            (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
            (7, 8), (8, 9), (9, 10), (10, 11), (11, 12),
            (0, 7), (7, 1), (1, 8), (8, 2), (2, 9), (9, 3),
            (3, 10), (10, 4), (4, 11), (11, 5), (5, 12), (12, 6),
        ]
        steel = MATERIALES_EDUCATIVOS["acero_s275"]
        section = Seccion.circulo("Referencia Ø150 mm", 0.15)
        designs = [DisenoBarra(f"Barra {i + 1}", steel, section) for i in range(len(bars))]
        # Mantiene la carga vertical inicial de 10 kN ubicada en x=30 m.
        permanent_loads = {3: (0.0, -10_000.0)}

        for vehicle_key in ("autobus", "camion"):
            vehicle = VEHICULOS_EDUCATIVOS[vehicle_key]
            min_offset = min(vehicle.posiciones_ejes_m)
            max_offset = max(vehicle.posiciones_ejes_m)
            first = max(0.0, -max_offset)
            last = 60.0 - min_offset
            max_utilization = 0.0
            position = first
            while position <= last + 1e-9:
                result = analizar_estado_celosia(
                    nodes, bars, designs, permanent_loads,
                    {0: (True, True), 6: (False, True)}, vehicle,
                    EstadoVehiculo(position),
                )
                max_utilization = max(max_utilization, result["utilizacion_maxima"])
                position += 0.5
            self.assertLess(max_utilization, 0.8, vehicle.nombre)


if __name__ == "__main__":
    unittest.main()
