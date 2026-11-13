"""Análisis estático de celosías planas por equilibrio en los nodos."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np


_TIPOS_APOYO = {"articulado", "rodillo_vertical"}


def _numero_finito(valor: float, nombre: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{nombre} debe ser un número.") from error
    if not math.isfinite(numero):
        raise ValueError(f"{nombre} debe ser finito.")
    return numero


def resolver_celosia(
    nodos: Sequence[Sequence[float]],
    barras: Sequence[Sequence[int]],
    cargas: Mapping[int, Sequence[float]],
    apoyos: Mapping[int, str],
) -> dict[str, object]:
    """Calcula fuerzas axiales y reacciones en una celosía plana.

    Args:
        nodos: Coordenadas ``(x, y)`` de cada unión, en metros.
        barras: Pares de índices ``(nodo_inicio, nodo_fin)``.
        cargas: Mapa ``índice_nodo: (Fx, Fy)`` en newtons. Una fuerza hacia
            abajo tiene componente ``Fy`` negativa.
        apoyos: Mapa de nodos a ``"articulado"`` (restringe x e y) o
            ``"rodillo_vertical"`` (restringe y y permite movimiento en x).

    Returns:
        Diccionario con ``fuerzas_barras`` (tensión positiva, compresión
        negativa), ``estado_barras`` (texto por barra) y ``reacciones``
        (componentes ``(Rx, Ry)`` por nodo apoyado).

    Raises:
        ValueError: Si la geometría, los índices, los apoyos o el equilibrio
            no permiten una solución estática única.
    """
    if len(nodos) < 2:
        raise ValueError("La celosía debe tener al menos dos nodos.")

    puntos: list[tuple[float, float]] = []
    for indice, nodo in enumerate(nodos):
        if len(nodo) != 2:
            raise ValueError(f"El nodo {indice} debe tener coordenadas (x, y).")
        puntos.append((
            _numero_finito(nodo[0], f"La coordenada x del nodo {indice}"),
            _numero_finito(nodo[1], f"La coordenada y del nodo {indice}"),
        ))

    cantidad_nodos = len(puntos)
    barras_validadas: list[tuple[int, int, float, float]] = []
    for indice, barra in enumerate(barras):
        if len(barra) != 2:
            raise ValueError(f"La barra {indice} debe indicar dos índices de nodo.")
        inicio, fin = barra
        if not isinstance(inicio, int) or not isinstance(fin, int):
            raise TypeError(f"Los índices de la barra {indice} deben ser enteros.")
        if not (0 <= inicio < cantidad_nodos and 0 <= fin < cantidad_nodos):
            raise ValueError(f"La barra {indice} referencia un nodo inexistente.")
        if inicio == fin:
            raise ValueError(f"La barra {indice} no puede conectar un nodo consigo mismo.")

        dx = puntos[fin][0] - puntos[inicio][0]
        dy = puntos[fin][1] - puntos[inicio][1]
        longitud = math.hypot(dx, dy)
        if longitud == 0:
            raise ValueError(f"La barra {indice} tiene longitud cero.")
        barras_validadas.append((inicio, fin, dx / longitud, dy / longitud))

    if not barras_validadas:
        raise ValueError("La celosía debe contener al menos una barra.")
    if not apoyos:
        raise ValueError("La celosía debe tener apoyos definidos.")

    apoyos_validados: dict[int, str] = {}
    for nodo, tipo in apoyos.items():
        if not isinstance(nodo, int) or not 0 <= nodo < cantidad_nodos:
            raise ValueError(f"El índice de apoyo {nodo!r} no corresponde a un nodo.")
        if tipo not in _TIPOS_APOYO:
            raise ValueError(
                f"Tipo de apoyo inválido en el nodo {nodo}: usa 'articulado' "
                "o 'rodillo_vertical'."
            )
        apoyos_validados[nodo] = tipo

    fuerzas_externas = np.zeros((cantidad_nodos, 2), dtype=float)
    for nodo, fuerza in cargas.items():
        if not isinstance(nodo, int) or not 0 <= nodo < cantidad_nodos:
            raise ValueError(f"La carga referencia un nodo inexistente: {nodo!r}.")
        if len(fuerza) != 2:
            raise ValueError(f"La carga del nodo {nodo} debe ser (Fx, Fy).")
        fuerzas_externas[nodo, 0] += _numero_finito(fuerza[0], f"Fx del nodo {nodo}")
        fuerzas_externas[nodo, 1] += _numero_finito(fuerza[1], f"Fy del nodo {nodo}")

    # Incógnitas: primero fuerza axial de cada barra; luego reacciones de apoyo.
    columnas_reaccion: dict[tuple[int, str], int] = {}
    cantidad_incognitas = len(barras_validadas)
    for nodo, tipo in apoyos_validados.items():
        componentes = ("x", "y") if tipo == "articulado" else ("y",)
        for componente in componentes:
            columnas_reaccion[nodo, componente] = cantidad_incognitas
            cantidad_incognitas += 1

    matriz = np.zeros((2 * cantidad_nodos, cantidad_incognitas), dtype=float)
    for indice, (inicio, fin, ux, uy) in enumerate(barras_validadas):
        matriz[2 * inicio, indice] = ux
        matriz[2 * inicio + 1, indice] = uy
        matriz[2 * fin, indice] = -ux
        matriz[2 * fin + 1, indice] = -uy

    for (nodo, componente), columna in columnas_reaccion.items():
        fila = 2 * nodo + (0 if componente == "x" else 1)
        matriz[fila, columna] = 1.0

    vector_cargas = -fuerzas_externas.reshape(-1)
    rango = np.linalg.matrix_rank(matriz)
    if rango < cantidad_incognitas:
        raise ValueError(
            "La celosía es inestable o estáticamente indeterminada; "
            "revisa la geometría, las barras y los apoyos."
        )

    solucion, _, _, _ = np.linalg.lstsq(matriz, vector_cargas, rcond=None)
    residuo = matriz @ solucion - vector_cargas
    escala = max(1.0, float(np.max(np.abs(vector_cargas))))
    if float(np.max(np.abs(residuo))) > 1e-8 * escala:
        raise ValueError(
            "Las cargas no pueden equilibrarse con esta celosía; "
            "revisa sus apoyos y configuración."
        )

    fuerzas_barras = solucion[: len(barras_validadas)]
    umbral = max(1.0, float(np.max(np.abs(fuerzas_barras)))) * 1e-9
    estados = tuple(
        "Tensión" if fuerza > umbral else "Compresión" if fuerza < -umbral else "Sin carga"
        for fuerza in fuerzas_barras
    )

    reacciones: dict[int, tuple[float, float]] = {}
    for nodo in apoyos_validados:
        rx = solucion[columnas_reaccion[nodo, "x"]] if (nodo, "x") in columnas_reaccion else 0.0
        ry = solucion[columnas_reaccion[nodo, "y"]] if (nodo, "y") in columnas_reaccion else 0.0
        reacciones[nodo] = (float(rx), float(ry))

    return {
        "fuerzas_barras": tuple(float(fuerza) for fuerza in fuerzas_barras),
        "estado_barras": estados,
        "reacciones": reacciones,
    }
