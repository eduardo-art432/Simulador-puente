"""Análisis lineal elástico de celosías planas por rigidez directa.

Unidades coherentes: coordenadas en m, área en m², módulo E en Pa y cargas
en N. Las barras solo trabajan axialmente y los desplazamientos son pequeños.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np


def _finite(value: float, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{label} debe ser numérico.") from error
    if not math.isfinite(result):
        raise ValueError(f"{label} debe ser finito.")
    return result


def resolver_celosia_rigidez(
    nodos: Sequence[Sequence[float]],
    barras: Sequence[Sequence[float]],
    cargas: Mapping[int, Sequence[float]],
    apoyos: Mapping[int, Sequence[bool]],
) -> dict[str, object]:
    """Resuelve una celosía 2D lineal mediante ``[K]{u}={F}``.

    Cada barra es ``(nodo_i, nodo_j, área_m2, E_Pa)``. Cada apoyo asigna
    ``(restringe_x, restringe_y)``. Las fuerzas axiales son positivas en
    tracción. Devuelve desplazamientos por nodo, deformaciones, tensiones,
    fuerzas axiales, reacciones y la matriz global ensamblada.
    """
    if len(nodos) < 2:
        raise ValueError("La celosía debe contener al menos dos nodos.")
    puntos: list[tuple[float, float]] = []
    for index, node in enumerate(nodos):
        if len(node) != 2:
            raise ValueError(f"El nodo {index} debe tener coordenadas (x, y).")
        puntos.append((_finite(node[0], f"x del nodo {index}"), _finite(node[1], f"y del nodo {index}")))

    count_nodes = len(puntos)
    dofs = 2 * count_nodes
    stiffness = np.zeros((dofs, dofs), dtype=float)
    validated: list[tuple[int, int, float, float, float, float, float]] = []
    if not barras:
        raise ValueError("La celosía debe contener barras.")
    for index, bar in enumerate(barras):
        if len(bar) != 4:
            raise ValueError(f"La barra {index} debe ser (i, j, área, E).")
        i_raw, j_raw, area_raw, modulus_raw = bar
        if not isinstance(i_raw, int) or not isinstance(j_raw, int):
            raise TypeError(f"Los nodos de la barra {index} deben ser índices enteros.")
        i, j = i_raw, j_raw
        if i == j or not (0 <= i < count_nodes and 0 <= j < count_nodes):
            raise ValueError(f"La barra {index} tiene conectividad inválida.")
        area = _finite(area_raw, f"Área de la barra {index}")
        modulus = _finite(modulus_raw, f"E de la barra {index}")
        if area <= 0 or modulus <= 0:
            raise ValueError(f"Área y E de la barra {index} deben ser positivos.")
        dx, dy = puntos[j][0] - puntos[i][0], puntos[j][1] - puntos[i][1]
        length = math.hypot(dx, dy)
        if length == 0:
            raise ValueError(f"La barra {index} tiene longitud cero.")
        cx, cy = dx / length, dy / length
        local = (area * modulus / length) * np.array(
            [[cx * cx, cx * cy, -cx * cx, -cx * cy],
             [cx * cy, cy * cy, -cx * cy, -cy * cy],
             [-cx * cx, -cx * cy, cx * cx, cx * cy],
             [-cx * cy, -cy * cy, cx * cy, cy * cy]], dtype=float
        )
        indices = (2 * i, 2 * i + 1, 2 * j, 2 * j + 1)
        stiffness[np.ix_(indices, indices)] += local
        validated.append((i, j, area, modulus, length, cx, cy))

    force = np.zeros(dofs, dtype=float)
    for node, vector in cargas.items():
        if not isinstance(node, int) or not 0 <= node < count_nodes or len(vector) != 2:
            raise ValueError(f"Carga nodal inválida en {node!r}.")
        force[2 * node] += _finite(vector[0], f"Fx nodo {node}")
        force[2 * node + 1] += _finite(vector[1], f"Fy nodo {node}")

    restrained: list[int] = []
    for node, conditions in apoyos.items():
        if not isinstance(node, int) or not 0 <= node < count_nodes or len(conditions) != 2:
            raise ValueError(f"Condición de apoyo inválida en {node!r}.")
        restrained.extend(2 * node + axis for axis, fixed in enumerate(conditions) if fixed)
    if not restrained:
        raise ValueError("Se requiere al menos un grado de libertad restringido.")

    fixed = np.array(sorted(set(restrained)), dtype=int)
    free = np.array([dof for dof in range(dofs) if dof not in set(fixed)], dtype=int)
    displacement = np.zeros(dofs, dtype=float)
    if len(free):
        reduced = stiffness[np.ix_(free, free)]
        if np.linalg.matrix_rank(reduced) < len(free):
            raise ValueError("La estructura es inestable: matriz de rigidez singular.")
        try:
            displacement[free] = np.linalg.solve(reduced, force[free])
        except np.linalg.LinAlgError as error:
            raise ValueError("No se pudo resolver la matriz de rigidez.") from error

    reactions_vector = stiffness @ displacement - force
    strains: list[float] = []
    stresses: list[float] = []
    axial_forces: list[float] = []
    for i, j, area, modulus, length, cx, cy in validated:
        extension = cx * (displacement[2 * j] - displacement[2 * i]) + cy * (
            displacement[2 * j + 1] - displacement[2 * i + 1]
        )
        strain = extension / length
        stress = modulus * strain
        strains.append(float(strain))
        stresses.append(float(stress))
        axial_forces.append(float(stress * area))

    node_displacements = tuple(
        (float(displacement[2 * i]), float(displacement[2 * i + 1]))
        for i in range(count_nodes)
    )
    reactions = {
        node: (float(reactions_vector[2 * node]), float(reactions_vector[2 * node + 1]))
        for node in apoyos
    }
    return {
        "desplazamientos": node_displacements,
        "deformaciones": tuple(strains),
        "tensiones": tuple(stresses),
        "fuerzas_barras": tuple(axial_forces),
        "reacciones": reactions,
        "matriz_rigidez": stiffness,
    }
