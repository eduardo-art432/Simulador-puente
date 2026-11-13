"""Operaciones básicas con vectores bidimensionales."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

Vector = tuple[float, float]


def _numero_finito(valor: float, nombre: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{nombre} debe ser un número.") from error
    if not math.isfinite(numero):
        raise ValueError(f"{nombre} debe ser finito.")
    return numero


def componentes_vector(magnitud: float, angulo: float) -> Vector:
    """Descompone la magnitud usando un ángulo en grados desde el eje +X."""
    magnitud = _numero_finito(magnitud, "La magnitud")
    angulo_rad = math.radians(_numero_finito(angulo, "El ángulo"))
    return magnitud * math.cos(angulo_rad), magnitud * math.sin(angulo_rad)


def magnitud_vector(x: float, y: float) -> float:
    """Calcula la magnitud evitando desbordamientos intermedios."""
    return math.hypot(
        _numero_finito(x, "La componente x"),
        _numero_finito(y, "La componente y"),
    )


def _validar_vector(vector: Sequence[float], indice: int) -> Vector:
    try:
        if len(vector) != 2:
            raise ValueError
        return (
            _numero_finito(vector[0], f"La componente x del vector {indice}"),
            _numero_finito(vector[1], f"La componente y del vector {indice}"),
        )
    except (TypeError, IndexError) as error:
        raise ValueError(f"El vector {indice} debe contener dos componentes (x, y).") from error
    except ValueError as error:
        if str(error):
            raise
        raise ValueError(f"El vector {indice} debe contener dos componentes (x, y).") from error


def sumar_vectores(vectores: Iterable[Sequence[float]]) -> Vector:
    """Suma una colección de pares (x, y); acepta también un iterable vacío."""
    resultado_x = resultado_y = 0.0
    try:
        for indice, vector in enumerate(vectores, start=1):
            x, y = _validar_vector(vector, indice)
            resultado_x += x
            resultado_y += y
    except TypeError as error:
        raise TypeError("Se esperaba un iterable de vectores (x, y).") from error
    return resultado_x, resultado_y


def angulo_vector(x: float, y: float) -> float:
    """Devuelve el ángulo en grados en [-180, 180]; el vector cero tiene ángulo 0."""
    x = _numero_finito(x, "La componente x")
    y = _numero_finito(y, "La componente y")
    if x == 0 and y == 0:
        return 0.0
    return math.degrees(math.atan2(y, x))


def resultante_vectores(vectores: Iterable[Sequence[float]]) -> tuple[float, float, float, float]:
    """Devuelve (magnitud, ángulo, componente x, componente y) de la resultante."""
    resultado_x, resultado_y = sumar_vectores(vectores)
    return (
        magnitud_vector(resultado_x, resultado_y),
        angulo_vector(resultado_x, resultado_y),
        resultado_x,
        resultado_y,
    )
