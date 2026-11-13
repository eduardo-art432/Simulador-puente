"""Criterios educativos de utilización y falla para barras de celosía.

Evalúa fuerzas axiales elásticas contra propiedades de material y sección.
No incluye factores normativos, imperfecciones, plasticidad ni diseño de uniones.
"""

from __future__ import annotations

import math

from .materials import Material, Seccion, propiedades_elemento


def evaluar_elemento(
    material: Material,
    seccion: Seccion,
    longitud_m: float,
    fuerza_axial_n: float,
    *,
    factor_longitud_efectiva: float = 1.0,
    capacidad_conexion_n: float | None = None,
    desplazamiento_m: float | None = None,
    limite_desplazamiento_m: float | None = None,
) -> dict[str, object]:
    """Calcula capacidades y utilización para una barra individual.

    ``fuerza_axial_n`` positiva significa tracción y negativa compresión.
    Los criterios sin dato requerido (conexión/desplazamiento) se omiten y
    aparecen en ``criterios_evaluados`` como no evaluados.
    """
    if not math.isfinite(fuerza_axial_n):
        raise ValueError("La fuerza axial debe ser finita.")
    properties = propiedades_elemento(
        material, seccion, longitud_m, factor_longitud_efectiva
    )
    force = abs(float(fuerza_axial_n))
    caps: dict[str, float] = {}
    utilizaciones: dict[str, float] = {}
    skipped: list[str] = []

    if fuerza_axial_n >= 0:
        if material.limite_fluencia_traccion_pa is not None:
            caps["fluencia_traccion_n"] = material.limite_fluencia_traccion_pa * seccion.area_m2
            utilizaciones["fluencia_traccion"] = force / caps["fluencia_traccion_n"]
        caps["rotura_traccion_n"] = material.resistencia_ultima_traccion_pa * seccion.area_m2
        utilizaciones["rotura_traccion"] = force / caps["rotura_traccion_n"]
        skipped.append("compresion")
    else:
        caps["aplastamiento_compresion_n"] = material.resistencia_compresion_pa * seccion.area_m2
        caps["pandeo_euler_n"] = float(properties["carga_critica_euler_n"])
        utilizaciones["aplastamiento_compresion"] = force / caps["aplastamiento_compresion_n"]
        utilizaciones["pandeo_euler"] = force / caps["pandeo_euler_n"]
        skipped.extend(("fluencia_traccion", "rotura_traccion"))

    if capacidad_conexion_n is None:
        skipped.append("conexion")
    else:
        if not math.isfinite(capacidad_conexion_n) or capacidad_conexion_n <= 0:
            raise ValueError("La capacidad de conexión debe ser finita y positiva.")
        caps["conexion_n"] = float(capacidad_conexion_n)
        utilizaciones["conexion"] = force / float(capacidad_conexion_n)

    if desplazamiento_m is None or limite_desplazamiento_m is None:
        skipped.append("deformacion")
    else:
        if not math.isfinite(desplazamiento_m):
            raise ValueError("El desplazamiento debe ser finito.")
        if not math.isfinite(limite_desplazamiento_m) or limite_desplazamiento_m <= 0:
            raise ValueError("El límite de desplazamiento debe ser finito y positivo.")
        caps["desplazamiento_limite_m"] = float(limite_desplazamiento_m)
        utilizaciones["deformacion"] = abs(float(desplazamiento_m)) / float(limite_desplazamiento_m)

    governing = max(utilizaciones, key=utilizaciones.get)
    max_utilization = utilizaciones[governing]
    return {
        "capacidades": caps,
        "utilizaciones": utilizaciones,
        "criterios_no_evaluados": tuple(skipped),
        "criterio_critico": governing,
        "utilizacion_maxima": max_utilization,
        "estado": "falla" if max_utilization >= 1.0 else "advertencia" if max_utilization >= 0.8 else "normal",
    }
