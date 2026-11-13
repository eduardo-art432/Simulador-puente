"""Modelo educativo de vehículos por ejes para cargas móviles 2D.

El peso de cada eje se transmite verticalmente a la línea de nodos del tablero.
La fuerza inercial horizontal se calcula aparte y no se suma al peso.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class EspecificacionVehiculo:
    nombre: str
    masa_kg: float
    posiciones_ejes_m: tuple[float, ...]
    fracciones_peso_ejes: tuple[float, ...]
    ruedas_por_eje: tuple[int, ...]
    longitud_m: float = 12.0
    altura_m: float = 3.6
    ancho_m: float = 2.5
    centro_masa_x_m: float = -6.0
    centro_masa_y_m: float = 1.2
    radio_rueda_m: float = 0.48

    def __post_init__(self) -> None:
        count = len(self.posiciones_ejes_m)
        if not self.nombre.strip() or count == 0:
            raise ValueError("El vehículo requiere nombre y al menos un eje.")
        if len(self.fracciones_peso_ejes) != count or len(self.ruedas_por_eje) != count:
            raise ValueError("Cada eje debe tener fracción de peso y cantidad de ruedas.")
        if not math.isfinite(self.masa_kg) or self.masa_kg <= 0:
            raise ValueError("La masa debe ser finita y positiva.")
        if any(not math.isfinite(x) for x in self.posiciones_ejes_m):
            raise ValueError("Las posiciones de ejes deben ser finitas.")
        if any(x < 0 for x in self.fracciones_peso_ejes) or not math.isclose(
            sum(self.fracciones_peso_ejes), 1.0, rel_tol=1e-9, abs_tol=1e-9
        ):
            raise ValueError("Las fracciones de peso deben ser no negativas y sumar 1.")
        if any(not isinstance(n, int) or n < 1 for n in self.ruedas_por_eje):
            raise ValueError("Cada eje debe tener una o más ruedas.")
        for field in ("longitud_m", "altura_m", "ancho_m", "radio_rueda_m"):
            value = getattr(self, field)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{field} debe ser finito y positivo.")
        if not math.isfinite(self.centro_masa_x_m) or not math.isfinite(self.centro_masa_y_m):
            raise ValueError("El centro de masa debe ser finito.")
        if self.centro_masa_y_m < 0 or self.radio_rueda_m * 2 >= self.altura_m:
            raise ValueError("La altura del centro de masa/radio de rueda no es coherente.")
        if any(abs(offset) > self.longitud_m for offset in self.posiciones_ejes_m):
            raise ValueError("Los ejes deben quedar dentro de la longitud del vehículo.")
        cm_from_axle_loads = sum(
            position * fraction
            for position, fraction in zip(self.posiciones_ejes_m, self.fracciones_peso_ejes)
        )
        if not math.isclose(cm_from_axle_loads, self.centro_masa_x_m, abs_tol=0.08):
            raise ValueError("El centro de masa longitudinal debe concordar con el reparto estático por ejes.")


@dataclass(frozen=True)
class EstadoVehiculo:
    """Estado cinemático. Velocidad y aceleración se expresan en m/s y m/s²."""

    posicion_eje_referencia_m: float
    velocidad_m_s: float = 0.0
    aceleracion_m_s2: float = 0.0

    def __post_init__(self) -> None:
        if not all(math.isfinite(v) for v in (
            self.posicion_eje_referencia_m, self.velocidad_m_s, self.aceleracion_m_s2
        )):
            raise ValueError("El estado del vehículo debe contener valores finitos.")


# Valores de referencia aproximados; las cargas de eje suman el peso total.
# La posición de referencia es el eje delantero (x=0); los offsets negativos
# apuntan hacia la parte trasera del vehículo.
VEHICULOS_EDUCATIVOS: dict[str, EspecificacionVehiculo] = {
    "sedan": EspecificacionVehiculo("Sedán", 1500, (0.0, -2.7), (0.55, 0.45), (2, 2), 4.6, 1.48, 1.82, -1.215, 0.68, 0.32),
    "suv": EspecificacionVehiculo("SUV", 2200, (0.0, -2.85), (0.54, 0.46), (2, 2), 4.85, 1.82, 1.95, -1.311, 0.82, 0.36),
    "camioneta": EspecificacionVehiculo("Camioneta", 2400, (0.0, -3.2), (0.52, 0.48), (2, 2), 5.45, 1.82, 2.02, -1.536, 0.84, 0.36),
    "autobus_urbano": EspecificacionVehiculo("Autobús urbano", 12000, (0.0, -4.0, -8.0), (0.35, 0.35, 0.30), (2, 2, 2), 12.0, 3.25, 2.55, -3.8, 1.35, 0.48),
    "autobus_interurbano": EspecificacionVehiculo("Autobús interurbano", 15000, (0.0, -5.5, -11.0), (0.25, 0.40, 0.35), (2, 2, 2), 13.5, 3.75, 2.55, -6.05, 1.55, 0.50),
    "camion_2_ejes": EspecificacionVehiculo("Camión · 2 ejes", 18000, (0.0, -5.0), (0.42, 0.58), (2, 4), 9.0, 3.8, 2.55, -2.9, 1.75, 0.52),
    "camion_3_ejes": EspecificacionVehiculo("Camión · 3 ejes", 18000, (0.0, -3.8, -7.0), (0.28, 0.36, 0.36), (2, 4, 4), 11.0, 3.9, 2.55, -3.888, 1.72, 0.52),
    "camion_articulado_5_ejes": EspecificacionVehiculo("Camión articulado · 5 ejes", 36000, (0.0, -3.5, -7.0, -9.0, -11.5), (0.16, 0.17, 0.22, 0.225, 0.225), (2, 4, 4, 4, 4), 16.5, 4.0, 2.55, -6.7475, 1.75, 0.52),
    # Alias antiguos conservados para llamadas existentes.
    "automovil": EspecificacionVehiculo("Automóvil", 1500, (0.0, -2.7), (0.55, 0.45), (2, 2), 4.6, 1.48, 1.82, -1.215, 0.68, 0.32),
    "autobus": EspecificacionVehiculo("Autobús", 12000, (0.0, -4.0, -8.0), (0.35, 0.35, 0.30), (2, 2, 2), 12.0, 3.25, 2.55, -3.8, 1.35, 0.48),
    "camion": EspecificacionVehiculo("Camión", 18000, (0.0, -3.8, -7.0), (0.28, 0.36, 0.36), (2, 4, 4), 11.0, 3.9, 2.55, -3.872, 1.72, 0.52),
    "camion_5_ejes": EspecificacionVehiculo("Camión · 5 ejes", 26000, (0.0, -3.5, -7.0, -9.0, -11.0), (0.18, 0.19, 0.21, 0.21, 0.21), (2, 4, 4, 4, 4), 15.0, 4.0, 2.55, -6.335, 1.75, 0.52),
}


def distribuir_cargas_ejes(
    vehiculo: EspecificacionVehiculo,
    estado: EstadoVehiculo,
    posiciones_nodos_m: Sequence[float],
    gravedad_m_s2: float = 9.81,
) -> dict[str, object]:
    """Distribuye pesos de ejes a nodos vecinos mediante interpolación lineal.

    Los ejes que están fuera del tramo modelado no cargan sus nodos. Devuelve
    cargas ``Fy`` negativas (hacia abajo), cargas por eje/rueda y ``m*a`` como
    resultado separado para que el llamador decida cómo modelar dinámica.
    """
    if len(posiciones_nodos_m) < 2:
        raise ValueError("Se requieren al menos dos nodos de tablero.")
    xs = tuple(float(x) for x in posiciones_nodos_m)
    if any(not math.isfinite(x) for x in xs) or any(b <= a for a, b in zip(xs, xs[1:])):
        raise ValueError("Las posiciones de nodos deben ser finitas y crecientes.")
    if not math.isfinite(gravedad_m_s2) or gravedad_m_s2 <= 0:
        raise ValueError("La gravedad debe ser finita y positiva.")

    nodal = {index: [0.0, 0.0] for index in range(len(xs))}
    axle_details = []
    total_on_bridge = 0.0
    for index, (offset, fraction, wheel_count) in enumerate(zip(
        vehiculo.posiciones_ejes_m, vehiculo.fracciones_peso_ejes, vehiculo.ruedas_por_eje
    )):
        x = estado.posicion_eje_referencia_m + offset
        axle_weight = vehiculo.masa_kg * gravedad_m_s2 * fraction
        wheel_weight = axle_weight / wheel_count
        if x < xs[0] or x > xs[-1]:
            axle_details.append({"eje": index + 1, "x_m": x, "peso_n": axle_weight,
                                 "peso_por_rueda_n": wheel_weight, "en_puente": False})
            continue
        right = next((i for i, node_x in enumerate(xs) if node_x >= x), len(xs) - 1)
        if math.isclose(xs[right], x, abs_tol=1e-12) or right == 0:
            nodal[right][1] -= axle_weight
        else:
            left = right - 1
            ratio = (x - xs[left]) / (xs[right] - xs[left])
            nodal[left][1] -= axle_weight * (1 - ratio)
            nodal[right][1] -= axle_weight * ratio
        total_on_bridge += axle_weight
        axle_details.append({"eje": index + 1, "x_m": x, "peso_n": axle_weight,
                             "peso_por_rueda_n": wheel_weight, "en_puente": True})

    return {
        "cargas_nodales_n": {i: (force[0], force[1]) for i, force in nodal.items() if force != [0.0, 0.0]},
        "cargas_por_eje": tuple(axle_details),
        "peso_en_puente_n": total_on_bridge,
        "peso_total_n": vehiculo.masa_kg * gravedad_m_s2,
        "fuerza_inercial_horizontal_n": vehiculo.masa_kg * estado.aceleracion_m_s2,
    }
