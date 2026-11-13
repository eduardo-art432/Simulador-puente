"""Cálculos de equilibrio estático para puentes simplemente apoyados."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def _numero_finito(valor: float, nombre: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{nombre} debe ser un número.") from error
    if not math.isfinite(numero):
        raise ValueError(f"{nombre} debe ser finito.")
    return numero


def reacciones_apoyos(
    longitud: float,
    cargas: Iterable[Sequence[float]],
) -> tuple[float, float]:
    """Calcula las reacciones verticales de una viga apoyada en sus extremos.

    ``longitud`` se expresa en metros. ``cargas`` contiene pares
    ``(posición, fuerza)``: la posición se mide desde el apoyo izquierdo y
    la fuerza en newtons. Las fuerzas positivas apuntan hacia abajo; las
    negativas representan fuerzas hacia arriba. Devuelve ``(R_izquierda,
    R_derecha)`` en newtons, positivas hacia arriba.

    El cálculo aplica equilibrio vertical y de momentos. Admite varias cargas
    puntuales y cargas ubicadas directamente sobre los apoyos.
    """
    longitud = _numero_finito(longitud, "La longitud")
    if longitud <= 0:
        raise ValueError("La longitud del puente debe ser mayor que cero.")

    cargas_validadas: list[tuple[float, float]] = []
    try:
        for indice, carga in enumerate(cargas, start=1):
            try:
                if len(carga) != 2:
                    raise ValueError
                posicion = _numero_finito(carga[0], f"La posición de la carga {indice}")
                fuerza = _numero_finito(carga[1], f"La fuerza de la carga {indice}")
            except (TypeError, IndexError) as error:
                raise ValueError(
                    f"La carga {indice} debe ser un par (posición, fuerza)."
                ) from error
            except ValueError as error:
                if str(error):
                    raise
                raise ValueError(
                    f"La carga {indice} debe ser un par (posición, fuerza)."
                ) from error

            if not 0 <= posicion <= longitud:
                raise ValueError(
                    f"La posición de la carga {indice} debe estar entre 0 y {longitud} m."
                )
            cargas_validadas.append((posicion, fuerza))
    except TypeError as error:
        raise TypeError("Las cargas deben ser un iterable de pares (posición, fuerza).") from error

    fuerza_total = math.fsum(fuerza for _, fuerza in cargas_validadas)
    momento_izquierdo = math.fsum(
        posicion * fuerza for posicion, fuerza in cargas_validadas
    )
    reaccion_derecha = momento_izquierdo / longitud
    reaccion_izquierda = fuerza_total - reaccion_derecha
    return reaccion_izquierda, reaccion_derecha
