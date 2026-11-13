"""Integración del motor de rigidez con vehículos y criterios de falla."""

from __future__ import annotations

import math
from dataclasses import dataclass
from collections.abc import Mapping, Sequence

from .failure import evaluar_elemento
from .materials import Material, Seccion
from .stiffness import resolver_celosia_rigidez
from .vehicles import EstadoVehiculo, EspecificacionVehiculo, distribuir_cargas_ejes


@dataclass(frozen=True)
class DisenoBarra:
    nombre: str
    material: Material
    seccion: Seccion
    factor_longitud_efectiva: float = 1.0
    capacidad_conexion_n: float | None = None
    limite_alargamiento_m: float | None = None


def analizar_estado_celosia(
    nodos: Sequence[Sequence[float]],
    conectividad: Sequence[Sequence[int]],
    disenos: Sequence[DisenoBarra],
    cargas_permanentes: Mapping[int, Sequence[float]],
    apoyos: Mapping[int, Sequence[bool]],
    vehiculo: EspecificacionVehiculo,
    estado_vehiculo: EstadoVehiculo,
) -> dict[str, object]:
    """Resuelve un estado instantáneo y evalúa cada barra según sus datos.

    Las cargas permanentes y vehiculares se suman como fuerzas nodales. El
    término ``m*a`` se devuelve aparte desde el modelo vehicular y no se agrega
    como carga hasta que exista un modelo dinámico explícito.
    """
    if len(conectividad) != len(disenos):
        raise ValueError("Cada barra debe tener exactamente un diseño material/sección.")
    lowest_y = min(float(node[1]) for node in nodos)
    deck_node_indices = sorted(
        (i for i, node in enumerate(nodos) if math.isclose(float(node[1]), lowest_y, abs_tol=1e-9)),
        key=lambda i: float(nodos[i][0]),
    )
    positions = [float(nodos[i][0]) for i in deck_node_indices]
    vehicle_result = distribuir_cargas_ejes(vehiculo, estado_vehiculo, positions)
    vehicle_loads = {
        deck_node_indices[local_index]: vector
        for local_index, vector in vehicle_result["cargas_nodales_n"].items()
    }
    combined: dict[int, list[float]] = {}
    for source in (cargas_permanentes, vehicle_loads):
        for node, vector in source.items():
            if not isinstance(node, int) or not 0 <= node < len(nodos) or len(vector) != 2:
                raise ValueError(f"Carga nodal inválida en {node!r}.")
            current = combined.setdefault(node, [0.0, 0.0])
            current[0] += float(vector[0])
            current[1] += float(vector[1])

    stiffness_bars = []
    lengths = []
    for index, (nodes_pair, design) in enumerate(zip(conectividad, disenos)):
        if len(nodes_pair) != 2:
            raise ValueError(f"Conectividad inválida para barra {index + 1}.")
        i, j = nodes_pair
        if not (0 <= i < len(nodos) and 0 <= j < len(nodos)):
            raise ValueError(f"Conectividad fuera de rango en barra {index + 1}.")
        length = math.dist(nodos[i], nodos[j])
        lengths.append(length)
        stiffness_bars.append((i, j, design.seccion.area_m2, design.material.modulo_elasticidad_pa))

    structural = resolver_celosia_rigidez(nodos, stiffness_bars, combined, apoyos)
    member_results = []
    for index, (force, strain, design, length) in enumerate(zip(
        structural["fuerzas_barras"], structural["deformaciones"], disenos, lengths
    )):
        result = evaluar_elemento(
            design.material,
            design.seccion,
            length,
            force,
            factor_longitud_efectiva=design.factor_longitud_efectiva,
            capacidad_conexion_n=design.capacidad_conexion_n,
            desplazamiento_m=strain * length if design.limite_alargamiento_m is not None else None,
            limite_desplazamiento_m=design.limite_alargamiento_m,
        )
        member_results.append({"indice": index, "nombre": design.nombre, **result})

    first_failed = next((member for member in member_results if member["estado"] == "falla"), None)
    max_member = max(member_results, key=lambda member: member["utilizacion_maxima"])
    state = "falla" if first_failed else "advertencia" if any(
        member["estado"] == "advertencia" for member in member_results
    ) else "normal"
    max_displacement = max(
        (math.hypot(*vector) for vector in structural["desplazamientos"]), default=0.0
    )
    max_vertical_displacement = max(
        (abs(vector[1]) for vector in structural["desplazamientos"]), default=0.0
    )
    return {
        **structural,
        "estado_barras": tuple(
            "Tensión" if force > 1e-8 else "Compresión" if force < -1e-8 else "Sin carga"
            for force in structural["fuerzas_barras"]
        ),
        "cargas_nodales_combinadas_n": {node: tuple(vector) for node, vector in combined.items()},
        "cargas_vehiculares": vehicle_result,
        "elementos": tuple(member_results),
        "elemento_mas_solicitado": max_member,
        "primer_elemento_fallado": first_failed,
        "utilizacion_maxima": max_member["utilizacion_maxima"],
        "desplazamiento_nodal_maximo_m": max_displacement,
        "desplazamiento_vertical_maximo_m": max_vertical_displacement,
        "estado": state,
    }


def buscar_primera_falla(
    posiciones_eje_referencia_m: Sequence[float],
    analizar_posicion,
) -> dict[str, object] | None:
    """Recorre posiciones discretas y devuelve el primer estado que falla.

    Es una búsqueda cuasiestática por muestras. No representa propagación de
    rotura ni garantiza detectar el máximo entre posiciones muestreadas.
    """
    for position in posiciones_eje_referencia_m:
        result = analizar_posicion(float(position))
        if result["estado"] == "falla":
            return {"posicion_eje_referencia_m": float(position), "resultado": result}
    return None
