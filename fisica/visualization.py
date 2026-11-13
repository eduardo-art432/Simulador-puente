"""Proyecciones visuales puras; no alteran resultados físicos del análisis."""

from __future__ import annotations

from collections.abc import Sequence


def proyectar_nodos_deformados(
    nodos_m: Sequence[Sequence[float]],
    desplazamientos_m: Sequence[Sequence[float]],
    origen_px: Sequence[float],
    escala_px_m: float | Sequence[float],
    *,
    amplificada: bool,
    factor_amplificacion: float,
) -> tuple[tuple[int, int], ...]:
    """Transforma coordenadas físicas más u nodal a píxeles; factor solo visual.

    La escala puede ser un escalar para ambos ejes o ``(escala_x, escala_y)``.
    La coordenada vertical física sigue positiva hacia arriba; la conversión a
    píxeles invierte ese sentido porque en pantalla Y crece hacia abajo.
    """
    if len(nodos_m) != len(desplazamientos_m):
        raise ValueError("Debe haber un desplazamiento para cada nodo.")
    if isinstance(escala_px_m, (int, float)):
        scale_x = scale_y = float(escala_px_m)
    else:
        if len(escala_px_m) != 2:
            raise ValueError("La escala anisotrópica requiere los valores X e Y.")
        scale_x, scale_y = (float(value) for value in escala_px_m)
    if scale_x <= 0 or scale_y <= 0 or factor_amplificacion <= 0:
        raise ValueError("Las escalas visuales deben ser positivas.")
    factor = factor_amplificacion if amplificada else 1.0
    ox, oy = origen_px
    return tuple(
        (round(ox + (node[0] + disp[0] * factor) * scale_x),
         round(oy - (node[1] + disp[1] * factor) * scale_y))
        for node, disp in zip(nodos_m, desplazamientos_m)
    )


def proyectar_ejes_px(posicion_referencia_px: float, offsets_ejes_m: Sequence[float], escala_px_m: float) -> tuple[int, ...]:
    """Proyecta al dibujo las posiciones de eje que usa el modelo de cargas."""
    return tuple(round(posicion_referencia_px + offset * escala_px_m) for offset in offsets_ejes_m)


def proyectar_vector_fuerza_px(
    origen_px: Sequence[float],
    fuerza_n: Sequence[float],
    escala_px_n: float,
) -> tuple[int, int]:
    """Proyecta un vector de fuerza; +Y físico apunta hacia arriba."""
    if len(origen_px) != 2 or len(fuerza_n) != 2 or escala_px_n <= 0:
        raise ValueError("Origen, fuerza o escala inválidos para proyectar el vector.")
    ox, oy = origen_px
    fx, fy = fuerza_n
    return round(ox + fx * escala_px_n), round(oy - fy * escala_px_n)


def proyectar_serie_temporal(
    muestras: Sequence[Sequence[float]],
    indice_tiempo: int,
    indice_valor: int,
    area_px: Sequence[float],
    rango_valor: Sequence[float],
) -> tuple[tuple[int, int], ...]:
    """Proyecta muestras usando tiempo real y un rango físico explícito.

    ``area_px`` es (izquierda, arriba, derecha, abajo); ``rango_valor`` es
    (mínimo, máximo). Se usa para mantener fiel la separación temporal aun
    cuando el intervalo entre fotogramas varía.
    """
    if len(area_px) != 4 or len(rango_valor) != 2:
        raise ValueError("El área requiere cuatro límites y el rango dos valores.")
    left, top, right, bottom = (float(value) for value in area_px)
    minimum, maximum = (float(value) for value in rango_valor)
    if right < left or bottom < top or maximum <= minimum:
        raise ValueError("El área y el rango de valores deben ser crecientes.")
    if not muestras:
        return ()
    times = [float(sample[indice_tiempo]) for sample in muestras]
    if any(b < a for a, b in zip(times, times[1:])):
        raise ValueError("Las muestras deben estar ordenadas cronológicamente.")
    first_time, last_time = times[0], times[-1]
    duration = last_time - first_time
    points = []
    for sample, timestamp in zip(muestras, times):
        value = float(sample[indice_valor])
        x_ratio = 0.0 if duration == 0 else (timestamp - first_time) / duration
        y_ratio = min(1.0, max(0.0, (value - minimum) / (maximum - minimum)))
        points.append((round(left + x_ratio * (right - left)),
                       round(bottom - y_ratio * (bottom - top))))
    return tuple(points)


def color_por_utilizacion(fuerza_axial_n: float, utilizacion: float) -> str:
    """Clave semántica para mapa: tracción/compresión, nivel y falla."""
    if utilizacion >= 1.0:
        return "falla"
    if utilizacion >= 0.8:
        return "cerca_capacidad"
    if utilizacion < 0.2:
        return "baja_traccion" if fuerza_axial_n >= 0 else "baja_compresion"
    return "traccion" if fuerza_axial_n >= 0 else "compresion"
