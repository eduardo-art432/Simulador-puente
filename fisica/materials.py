"""Materiales y secciones educativos para elementos de celosía.

Valores de referencia aproximados para ejercicios; no sustituyen normas,
certificados ni especificaciones de un proyecto real. Unidades SI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    nombre: str
    modulo_elasticidad_pa: float
    densidad_kg_m3: float
    limite_fluencia_traccion_pa: float | None
    resistencia_ultima_traccion_pa: float
    resistencia_compresion_pa: float

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise ValueError("El material debe tener nombre.")
        for field in (
            "modulo_elasticidad_pa", "densidad_kg_m3",
            "resistencia_ultima_traccion_pa", "resistencia_compresion_pa",
        ):
            value = getattr(self, field)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{field} debe ser finito y positivo.")
        fy = self.limite_fluencia_traccion_pa
        if fy is not None and (not math.isfinite(fy) or fy <= 0):
            raise ValueError("El límite de fluencia debe ser positivo o None.")


@dataclass(frozen=True)
class Seccion:
    """Propiedades geométricas de una barra: área A e inercia mínima I."""

    nombre: str
    area_m2: float
    inercia_minima_m4: float

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise ValueError("La sección debe tener nombre.")
        if not math.isfinite(self.area_m2) or self.area_m2 <= 0:
            raise ValueError("El área debe ser finita y positiva.")
        if not math.isfinite(self.inercia_minima_m4) or self.inercia_minima_m4 <= 0:
            raise ValueError("La inercia mínima debe ser finita y positiva.")

    @classmethod
    def rectangulo(cls, nombre: str, ancho_m: float, alto_m: float) -> "Seccion":
        """Crea una sección rectangular maciza; I corresponde al eje débil."""
        if not all(math.isfinite(v) and v > 0 for v in (ancho_m, alto_m)):
            raise ValueError("Ancho y alto deben ser finitos y positivos.")
        menor, mayor = sorted((ancho_m, alto_m))
        return cls(nombre, ancho_m * alto_m, mayor * menor**3 / 12)

    @classmethod
    def circulo(cls, nombre: str, diametro_m: float) -> "Seccion":
        if not math.isfinite(diametro_m) or diametro_m <= 0:
            raise ValueError("El diámetro debe ser finito y positivo.")
        area = math.pi * diametro_m**2 / 4
        return cls(nombre, area, math.pi * diametro_m**4 / 64)


# Valores típicos redondeados, destinados a aprendizaje introductorio.
MATERIALES_EDUCATIVOS: dict[str, Material] = {
    "acero_s275": Material("Acero estructural S275 (referencia)", 200e9, 7850, 275e6, 430e6, 275e6),
    "hormigon_c30": Material("Hormigón C30 (referencia)", 33e9, 2400, None, 3e6, 30e6),
    "madera_c24": Material("Madera C24 (referencia)", 11e9, 420, None, 14e6, 21e6),
}


def propiedades_elemento(
    material: Material,
    seccion: Seccion,
    longitud_m: float,
    factor_longitud_efectiva: float = 1.0,
) -> dict[str, float]:
    """Devuelve propiedades derivadas de una barra; Euler solo es elástico ideal."""
    if not math.isfinite(longitud_m) or longitud_m <= 0:
        raise ValueError("La longitud debe ser finita y positiva.")
    if not math.isfinite(factor_longitud_efectiva) or factor_longitud_efectiva <= 0:
        raise ValueError("El factor de longitud efectiva debe ser positivo.")
    return {
        "masa_kg": material.densidad_kg_m3 * seccion.area_m2 * longitud_m,
        "rigidez_axial_n_m": material.modulo_elasticidad_pa * seccion.area_m2 / longitud_m,
        "longitud_efectiva_m": factor_longitud_efectiva * longitud_m,
        "carga_critica_euler_n": (
            math.pi**2 * material.modulo_elasticidad_pa * seccion.inercia_minima_m4
            / (factor_longitud_efectiva * longitud_m) ** 2
        ),
    }
