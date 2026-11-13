"""Catálogo y render vectorial 2D; separado de masas y distribución de cargas."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .vehicles import EspecificacionVehiculo


@dataclass(frozen=True)
class PerfilVisual:
    estilo: str
    color_carroceria: tuple[int, int, int]
    color_realce: tuple[int, int, int]
    voladizo_delantero_m: float


PERFILES_VISUALES: dict[str, PerfilVisual] = {
    "sedan": PerfilVisual("sedan", (174, 47, 60), (255, 137, 125), 0.82),
    "automovil": PerfilVisual("sedan", (174, 47, 60), (255, 137, 125), 0.82),
    "suv": PerfilVisual("suv", (45, 116, 157), (111, 195, 222), 0.90),
    "camioneta": PerfilVisual("pickup", (183, 115, 48), (255, 202, 114), 0.92),
    "autobus_urbano": PerfilVisual("city_bus", (35, 119, 186), (132, 211, 241), 1.15),
    "autobus_interurbano": PerfilVisual("coach", (43, 121, 150), (123, 214, 222), 1.40),
    "autobus": PerfilVisual("city_bus", (35, 119, 186), (132, 211, 241), 1.15),
    "camion_2_ejes": PerfilVisual("rigid_truck", (185, 122, 49), (255, 205, 126), 1.25),
    "camion_3_ejes": PerfilVisual("rigid_truck", (185, 122, 49), (255, 205, 126), 1.30),
    "camion": PerfilVisual("rigid_truck", (185, 122, 49), (255, 205, 126), 1.30),
    "camion_articulado_5_ejes": PerfilVisual("articulated", (192, 124, 50), (255, 208, 132), 1.45),
    "camion_5_ejes": PerfilVisual("articulated", (192, 124, 50), (255, 208, 132), 1.45),
    "personalizado": PerfilVisual("sedan", (110, 105, 169), (190, 183, 246), 0.82),
}


def perfil_para_clave(clave: str) -> PerfilVisual:
    return PERFILES_VISUALES.get(clave, PERFILES_VISUALES["personalizado"])


def geometria_visual(
    vehiculo: EspecificacionVehiculo,
    perfil: PerfilVisual,
    eje_referencia_x_px: float,
    tablero_y_px: float,
    escala_px_m: float,
) -> dict[str, Any]:
    """Devuelve dimensiones proyectadas y centros de rueda desde los ejes físicos."""
    if escala_px_m <= 0:
        raise ValueError("La escala gráfica debe ser positiva.")
    wheel_xs = tuple(
        round(eje_referencia_x_px + offset * escala_px_m)
        for offset in vehiculo.posiciones_ejes_m
    )
    return {
        "ruedas_px": tuple((x, round(tablero_y_px - vehiculo.radio_rueda_m * escala_px_m)) for x in wheel_xs),
        "ejes_px": wheel_xs,
        "longitud_px": round(vehiculo.longitud_m * escala_px_m),
        "altura_px": round(vehiculo.altura_m * escala_px_m),
        "centro_masa_px": (
            round(eje_referencia_x_px + vehiculo.centro_masa_x_m * escala_px_m),
            round(tablero_y_px - vehiculo.centro_masa_y_m * escala_px_m),
        ),
        "separaciones_ejes_m": tuple(
            round(abs(a - b), 2)
            for a, b in zip(vehiculo.posiciones_ejes_m, vehiculo.posiciones_ejes_m[1:])
        ),
    }


def dibujar_vehiculo_vectorial(
    superficie,
    pygame_module,
    vehiculo: EspecificacionVehiculo,
    perfil: PerfilVisual,
    eje_referencia_x_px: float,
    tablero_y_px: float,
    escala_px_m: float,
    *,
    rotacion_rueda_rad: float = 0.0,
    offsets_verticales_ejes_px: tuple[float, ...] | list[float] | None = None,
) -> dict[str, Any]:
    """Renderiza un modelo vectorial de alta resolución con ejes físicos reales."""
    pygame = pygame_module
    geometry = geometria_visual(vehiculo, perfil, eje_referencia_x_px, tablero_y_px, escala_px_m)
    supersample = 2
    scale = escala_px_m * supersample
    margin = 0.20
    left_m = -(vehiculo.longitud_m - perfil.voladizo_delantero_m) - margin
    right_m = perfil.voladizo_delantero_m + margin
    width = max(1, round((right_m - left_m) * scale))
    height = max(1, round((vehiculo.altura_m + vehiculo.radio_rueda_m + margin) * scale))
    road_local_y = round((vehiculo.altura_m + vehiculo.radio_rueda_m + margin / 2) * scale)
    reference_local_x = round(-left_m * scale)
    layer = pygame.Surface((width, height), pygame.SRCALPHA)

    def X(x_m: float) -> int:
        return round(reference_local_x + x_m * scale)

    def Y(height_from_road_m: float) -> int:
        return round(road_local_y - height_from_road_m * scale)

    body_left = -(vehiculo.longitud_m - perfil.voladizo_delantero_m)
    body_right = perfil.voladizo_delantero_m
    body_bottom = vehiculo.radio_rueda_m * 0.58
    body_top = vehiculo.altura_m
    body_color = perfil.color_carroceria
    highlight = perfil.color_realce
    dark = (18, 29, 40)
    glass = (20, 49, 70)
    glass_light = (102, 175, 202)
    metal = (169, 190, 201)
    lamp = (255, 224, 151)
    rear_lamp = (255, 81, 76)

    # Sombra y chasis.
    pygame.draw.ellipse(layer, (5, 12, 20, 115), (X(body_left - 0.12), Y(0.02), X(body_right + 0.12) - X(body_left - 0.12), round(0.16 * scale)))
    pygame.draw.line(layer, (39, 50, 59), (X(body_left + 0.35), Y(body_bottom + 0.05)), (X(body_right - 0.08), Y(body_bottom + 0.05)), max(2, round(0.12 * scale)))

    wheel_centers = [
        (offset, -vehiculo.radio_rueda_m)
        for offset in vehiculo.posiciones_ejes_m
    ]
    axle_offsets = list(offsets_verticales_ejes_px or [0.0] * len(vehiculo.posiciones_ejes_m))
    if len(axle_offsets) != len(vehiculo.posiciones_ejes_m):
        raise ValueError("Debe proporcionarse un ajuste visual por cada eje.")
    wheel_r = vehiculo.radio_rueda_m

    if perfil.estilo in {"city_bus", "coach"}:
        pts = [(body_left, body_bottom), (body_left, body_top - 0.32),
               (body_left + 0.35, body_top), (body_right - 0.45, body_top),
               (body_right, body_top - 0.35), (body_right, body_bottom)]
        pygame.draw.polygon(layer, body_color, [(X(x), Y(y)) for x, y in pts])
        pygame.draw.lines(layer, highlight, True, [(X(x), Y(y)) for x, y in pts], max(2, round(0.07 * scale)))
        pygame.draw.line(layer, (19, 65, 92), (X(body_left + 0.12), Y(body_bottom + 0.30)), (X(body_right - 0.10), Y(body_bottom + 0.30)), round(0.12 * scale))
        window_bottom, window_top = body_top - 1.35, body_top - 0.38
        pygame.draw.polygon(layer, glass, [(X(body_right - 1.28), Y(window_bottom)), (X(body_right - 0.20), Y(window_bottom)), (X(body_right - 0.42), Y(window_top)), (X(body_right - 1.18), Y(window_top + 0.05))])
        pygame.draw.line(layer, glass_light, (X(body_right - 1.12), Y(window_top + 0.10)), (X(body_right - 0.50), Y(window_top + 0.10)), max(1, round(0.04 * scale)))
        window_x = body_left + 0.45
        while window_x < body_right - 1.5:
            if window_x < body_right - 1.4:
                pygame.draw.rect(layer, glass, (X(window_x), Y(window_top), round(0.88 * scale), round((window_top-window_bottom)*scale)), border_radius=round(0.10*scale))
                pygame.draw.line(layer, glass_light, (X(window_x + 0.08), Y(window_top - 0.08)), (X(window_x + 0.55), Y(window_top - 0.08)), max(1, round(0.035 * scale)))
                pygame.draw.line(layer, highlight, (X(window_x + 0.96), Y(window_top)), (X(window_x + 0.96), Y(window_bottom)), max(1, round(0.035 * scale)))
            window_x += 1.18 if perfil.estilo == "city_bus" else 1.35
        # Puerta acristalada, escalones y franjas de identificación.
        door_x = body_right - (2.25 if perfil.estilo == "city_bus" else 1.85)
        pygame.draw.rect(layer, (18, 44, 62), (X(door_x), Y(body_top - 0.34), round(0.88*scale), round((body_top-body_bottom-0.35)*scale)), border_radius=round(0.08*scale))
        pygame.draw.line(layer, highlight, (X(door_x + 0.44), Y(body_top - 0.35)), (X(door_x + 0.44), Y(body_bottom + 0.18)), max(1, round(0.04*scale)))
        pygame.draw.line(layer, highlight, (X(body_left + 0.12), Y(body_bottom + 0.52)), (X(body_right - 0.08), Y(body_bottom + 0.52)), max(1, round(0.07*scale)))
        # Detalles frontales y bajos específicos de servicio.
        pygame.draw.polygon(layer, (24, 65, 88), [
            (X(body_right - 1.05), Y(body_top - 0.48)),
            (X(body_right - 0.42), Y(body_top - 0.40)),
            (X(body_right - 0.52), Y(body_top - 0.90)),
            (X(body_right - 1.05), Y(body_top - 0.94)),
        ])
        pygame.draw.line(layer, (10, 37, 54), (X(body_right - 0.16), Y(body_bottom + 0.28)), (X(body_right - 0.16), Y(body_bottom + 0.72)), max(1, round(0.06 * scale)))
        pygame.draw.line(layer, lamp, (X(body_right - 0.08), Y(body_bottom + 0.48)), (X(body_right + 0.03), Y(body_bottom + 0.48)), max(2, round(0.08 * scale)))
        pygame.draw.line(layer, rear_lamp, (X(body_left + 0.02), Y(body_bottom + 0.50)), (X(body_left + 0.14), Y(body_bottom + 0.50)), max(2, round(0.08 * scale)))
        pygame.draw.line(layer, (173, 202, 211), (X(body_left + 0.25), Y(body_bottom + 0.25)), (X(body_right - 0.20), Y(body_bottom + 0.25)), max(1, round(0.04 * scale)))
        if perfil.estilo == "coach":
            # Compartimientos de equipaje y juntas de panel en el interurbano.
            luggage_y = body_bottom + 0.38
            pygame.draw.line(layer, (24, 80, 99), (X(body_left + 1.55), Y(luggage_y)), (X(body_right - 2.95), Y(luggage_y)), max(1, round(0.035 * scale)))
            for seam_x in (body_left + 3.1, body_left + 5.3, body_right - 3.0):
                if seam_x < body_right - 2.9:
                    pygame.draw.line(layer, (24, 80, 99), (X(seam_x), Y(body_bottom + 0.28)), (X(seam_x), Y(body_bottom + 0.82)), max(1, round(0.035 * scale)))
        else:
            # Ventanas bajas, acceso de piso bajo y banda de ruta urbana.
            pygame.draw.line(layer, (171, 219, 235), (X(body_left + 0.20), Y(body_bottom + 0.44)), (X(body_right - 0.20), Y(body_bottom + 0.44)), max(1, round(0.035 * scale)))
    elif perfil.estilo == "articulated":
        # Semirremolque separado de la cabina; el punto de articulación es visible.
        trailer_right = -4.7
        trailer_top = body_top
        pygame.draw.rect(layer, body_color, (X(body_left), Y(trailer_top), X(trailer_right) - X(body_left), round((trailer_top - body_bottom - 0.15) * scale)), border_radius=round(0.10 * scale))
        pygame.draw.rect(layer, highlight, (X(body_left), Y(trailer_top), X(trailer_right) - X(body_left), round((trailer_top - body_bottom - 0.15) * scale)), max(2, round(0.07 * scale)), border_radius=round(0.10 * scale))
        for slat_x in [body_left + 0.5 + i * 0.75 for i in range(max(0, int((trailer_right-body_left-0.6)/0.75)) )]:
            pygame.draw.line(layer, (139, 89, 47), (X(slat_x), Y(body_top - 0.14)), (X(slat_x), Y(body_bottom + 0.28)), max(1, round(0.035*scale)))
        pygame.draw.line(layer, (255, 191, 74), (X(body_left+0.08), Y(body_bottom+0.42)), (X(trailer_right-0.08), Y(body_bottom+0.42)), max(2,round(0.09*scale)))
        pygame.draw.line(layer, (75, 82, 88), (X(trailer_right), Y(body_bottom + 0.28)), (X(trailer_right + 0.55), Y(body_bottom + 0.28)), max(2, round(0.12*scale)))
        cab_left, cab_right = -4.1, body_right
        cab_pts = [(cab_left, body_bottom), (cab_left, body_top-0.35), (cab_left+0.34, body_top-0.15), (cab_right-0.35, body_top-0.16), (cab_right, body_top-0.76), (cab_right, body_bottom)]
        pygame.draw.polygon(layer, (49, 105, 145), [(X(x), Y(y)) for x,y in cab_pts])
        pygame.draw.lines(layer, (143, 201, 224), True, [(X(x), Y(y)) for x,y in cab_pts], max(2,round(0.07*scale)))
        pygame.draw.polygon(layer, glass, [(X(cab_right-1.12),Y(body_top-0.42)),(X(cab_right-0.18),Y(body_top-0.66)),(X(cab_right-0.18),Y(body_top-1.28)),(X(cab_right-1.12),Y(body_top-1.28))])
        pygame.draw.line(layer, (66, 75, 82), (X(trailer_right+0.05), Y(body_bottom+0.52)), (X(cab_left-0.15), Y(body_bottom+0.52)), max(2,round(0.08*scale)))
        pygame.draw.line(layer, glass_light, (X(cab_right-0.98), Y(body_top-0.54)), (X(cab_right-0.34), Y(body_top-0.70)), max(1, round(0.035 * scale)))
        pygame.draw.line(layer, (25, 62, 84), (X(cab_right-0.28), Y(body_bottom+0.42)), (X(cab_right-0.28), Y(body_top-1.42)), max(1, round(0.04 * scale)))
        pygame.draw.line(layer, metal, (X(cab_right-0.18), Y(body_top-0.73)), (X(cab_right+0.12), Y(body_top-0.66)), max(1, round(0.04 * scale)))
        pygame.draw.line(layer, dark, (X(cab_right+0.08), Y(body_top-0.64)), (X(cab_right+0.20), Y(body_top-0.64)), max(1, round(0.04 * scale)))
        pygame.draw.rect(layer, (40, 54, 63), (X(cab_right-0.48), Y(body_bottom+0.62), round(0.42*scale), round(0.14*scale)), border_radius=2)
        pygame.draw.line(layer, lamp, (X(body_right-0.08), Y(body_bottom+0.52)), (X(body_right+0.04), Y(body_bottom+0.52)), max(2, round(0.08*scale)))
        pygame.draw.line(layer, rear_lamp, (X(body_left+0.04), Y(body_bottom+0.50)), (X(body_left+0.12), Y(body_bottom+0.50)), max(2, round(0.08*scale)))
        pygame.draw.line(layer, metal, (X(body_right-0.16), Y(body_bottom+0.20)), (X(body_right+0.18), Y(body_bottom+0.20)), max(2, round(0.08*scale)))
    elif perfil.estilo == "rigid_truck":
        box_right = body_right - 2.7
        pygame.draw.rect(layer, (54, 121, 161), (X(body_left), Y(body_top-0.08), X(box_right)-X(body_left), round((body_top-body_bottom-0.28)*scale)), border_radius=round(0.08*scale))
        pygame.draw.rect(layer, (139, 197, 221), (X(body_left), Y(body_top-0.08), X(box_right)-X(body_left), round((body_top-body_bottom-0.28)*scale)), max(2,round(0.06*scale)), border_radius=round(0.08*scale))
        for slat_x in [body_left + 0.45 + i*0.72 for i in range(max(0,int((box_right-body_left-0.4)/0.72)))]:
            pygame.draw.line(layer, (79, 153, 190), (X(slat_x),Y(body_top-0.18)),(X(slat_x),Y(body_bottom+0.32)),max(1,round(0.035*scale)))
        pygame.draw.line(layer,(255,191,74),(X(body_left+0.08),Y(body_bottom+0.48)),(X(box_right-0.08),Y(body_bottom+0.48)),max(2,round(0.09*scale)))
        cab_left, cab_right = box_right - 0.12, body_right
        cab_pts=[(cab_left,body_bottom),(cab_left,body_top-0.40),(cab_left+0.26,body_top-0.12),(cab_right-0.48,body_top-0.12),(cab_right,body_top-0.75),(cab_right,body_bottom)]
        pygame.draw.polygon(layer,perfil.color_carroceria,[(X(x),Y(y)) for x,y in cab_pts])
        pygame.draw.lines(layer,perfil.color_realce,True,[(X(x),Y(y)) for x,y in cab_pts],max(2,round(0.06*scale)))
        pygame.draw.polygon(layer,glass,[(X(cab_right-1.08),Y(body_top-0.48)),(X(cab_right-0.16),Y(body_top-0.70)),(X(cab_right-0.16),Y(body_top-1.28)),(X(cab_right-1.08),Y(body_top-1.28))])
        pygame.draw.line(layer,glass_light,(X(cab_right-0.94),Y(body_top-0.57)),(X(cab_right-0.34),Y(body_top-0.72)),max(1,round(0.035*scale)))
        pygame.draw.line(layer,(46,72,88),(X(cab_right-0.25),Y(body_bottom+0.42)),(X(cab_right-0.25),Y(body_top-1.42)),max(1,round(0.04*scale)))
        pygame.draw.line(layer,metal,(X(cab_right-0.16),Y(body_top-0.78)),(X(cab_right+0.12),Y(body_top-0.70)),max(1,round(0.04*scale)))
        pygame.draw.line(layer,dark,(X(cab_right+0.09),Y(body_top-0.68)),(X(cab_right+0.22),Y(body_top-0.68)),max(1,round(0.04*scale)))
        pygame.draw.line(layer,highlight,(X(box_right-0.25),Y(body_bottom+0.78)),(X(box_right-0.25),Y(body_top-0.10)),max(1,round(0.04*scale)))
        pygame.draw.rect(layer,(226,174,81),(X(cab_right-0.50),Y(body_bottom+0.62),round(0.38*scale),round(0.13*scale)),border_radius=2)
        pygame.draw.line(layer,(130,83,43),(X(cab_right-1.0),Y(body_top-1.48)),(X(cab_right-0.22),Y(body_top-1.48)),max(1,round(0.045*scale)))
        pygame.draw.rect(layer,(43,57,66),(X(cab_right-0.22),Y(body_bottom+0.60),round(0.18*scale),round(0.58*scale)),border_radius=2)
        pygame.draw.line(layer,lamp,(X(body_right-0.07),Y(body_bottom+0.48)),(X(body_right+0.04),Y(body_bottom+0.48)),max(2,round(0.08*scale)))
        pygame.draw.line(layer,rear_lamp,(X(body_left+0.03),Y(body_bottom+0.48)),(X(body_left+0.13),Y(body_bottom+0.48)),max(2,round(0.08*scale)))
        pygame.draw.line(layer,metal,(X(body_right-0.18),Y(body_bottom+0.18)),(X(body_right+0.18),Y(body_bottom+0.18)),max(2,round(0.08*scale)))
    else:
        # Auto, SUV y pickup con perfiles de techo y parte trasera diferenciados.
        roof_height = body_top
        if perfil.estilo == "sedan":
            # Cabina algo más retrasada: deja el cofre claramente hacia +X.
            cabin = [(body_left+0.55, body_bottom+0.63),
                     (body_left+1.42, roof_height-0.12),
                     (body_right-1.65, roof_height-0.12),
                     (body_right-0.83, body_bottom+0.67)]
        elif perfil.estilo == "suv":
            cabin = [(body_left+0.52, body_bottom+0.60),
                     (body_left+1.35, roof_height-0.12),
                     (body_right-1.65, roof_height-0.12),
                     (body_right-0.82, body_bottom+0.58)]
        else:
            cabin = [(body_left+1.25, body_bottom+0.60),
                     (body_left+2.05, roof_height-0.12),
                     (body_right-1.65, roof_height-0.12),
                     (body_right-0.82, body_bottom+0.58)]
        silhouette=[(body_left,body_bottom+0.1),(body_left+0.08,body_bottom+0.48),*cabin,(body_right-0.12,body_bottom+0.52),(body_right,body_bottom+0.12)]
        pygame.draw.polygon(layer,body_color,[(X(x),Y(y)) for x,y in silhouette])
        pygame.draw.lines(layer,highlight,False,[(X(x),Y(y)) for x,y in silhouette],max(2,round(0.07*scale)))
        if perfil.estilo == "pickup":
            bed_left=body_left+0.16
            pygame.draw.rect(layer,(60,70,77),(X(bed_left),Y(body_bottom+0.62),X(body_left+1.20)-X(bed_left),round(0.12*scale)))
            pygame.draw.line(layer,highlight,(X(bed_left),Y(body_bottom+0.72)),(X(body_left+1.28),Y(body_bottom+0.72)),max(1,round(0.04*scale)))
        # Cristales facetados: la ventana delantera ocupa el lado derecho del vehículo.
        rear_window = [
            (cabin[0][0] + 0.12, cabin[0][1] + 0.08),
            (cabin[1][0] + 0.10, cabin[1][1] - 0.08),
            (cabin[1][0] + 0.68, cabin[1][1] - 0.08),
            (cabin[1][0] + 0.68, cabin[0][1] + 0.08),
        ]
        front_window = [
            (cabin[1][0] + 0.76, cabin[1][1] - 0.08),
            (cabin[2][0] - 0.12, cabin[2][1] - 0.08),
            (cabin[3][0] - 0.12, cabin[3][1] + 0.08),
            (cabin[1][0] + 0.76, cabin[0][1] + 0.08),
        ]
        pygame.draw.polygon(layer, glass, [(X(x), Y(y)) for x, y in rear_window])
        pygame.draw.polygon(layer, (29, 70, 94), [(X(x), Y(y)) for x, y in front_window])
        pygame.draw.line(layer, glass_light,
                         (X(rear_window[0][0] + 0.08), Y(rear_window[1][1] + 0.08)),
                         (X(rear_window[2][0] - 0.12), Y(rear_window[1][1] + 0.08)),
                         max(1, round(0.035 * scale)))
        # Pilar B, marco del parabrisas lateral y juntas de las puertas.
        pygame.draw.line(layer, metal, (X(cabin[1][0] + 0.72), Y(cabin[1][1] - 0.12)),
                         (X(cabin[1][0] + 0.72), Y(body_bottom + 0.56)), max(1, round(0.045 * scale)))
        door_seams = (body_left + 2.05, body_right - 0.38) if perfil.estilo == "sedan" else (body_left + 2.25, body_right - 0.40)
        for seam_x in door_seams:
            pygame.draw.line(layer, (68, 78, 83), (X(seam_x), Y(body_bottom + 0.30)),
                             (X(seam_x), Y(body_bottom + 0.92)), max(1, round(0.035 * scale)))
        handle_x = body_right - 0.86
        pygame.draw.line(layer, metal, (X(handle_x), Y(body_bottom + 0.78)),
                         (X(handle_x + 0.20), Y(body_bottom + 0.78)), max(1, round(0.05 * scale)))
        # Espejo, líneas de carácter, faldón y parachoques.
        pygame.draw.line(layer, dark, (X(body_right - 0.42), Y(body_bottom + 0.94)),
                         (X(body_right - 0.24), Y(body_bottom + 1.02)), max(1, round(0.045 * scale)))
        pygame.draw.ellipse(layer, metal, (X(body_right - 0.29), Y(body_bottom + 1.08), round(0.20 * scale), round(0.12 * scale)))
        pygame.draw.line(layer, highlight, (X(body_left + 0.45), Y(body_bottom + 0.42)),
                         (X(body_right - 0.35), Y(body_bottom + 0.42)), max(1, round(0.045 * scale)))
        pygame.draw.line(layer, dark, (X(body_left + 0.50), Y(body_bottom + 0.24)),
                         (X(body_right - 0.32), Y(body_bottom + 0.24)), max(1, round(0.09 * scale)))
        pygame.draw.line(layer, metal, (X(body_left + 0.22), Y(body_bottom + 0.18)),
                         (X(body_right + 0.10), Y(body_bottom + 0.18)), max(1, round(0.06 * scale)))
        # Frente orientado a +X, el sentido de avance: parrilla y faro delante;
        # calavera y portón quedan detrás, junto a la carrocería trasera.
        grille_w = 0.25 if perfil.estilo == "sedan" else 0.30
        grille_h = 0.36 if perfil.estilo == "sedan" else 0.42
        grille_rect = pygame.Rect(
            X(body_right - grille_w * 0.72),
            Y(body_bottom + 0.57),
            max(2, round(grille_w * scale)),
            max(3, round(grille_h * scale)),
        )
        pygame.draw.rect(layer, (26, 37, 45), grille_rect, border_radius=max(1, round(0.035 * scale)))
        for vent_y in (0.08, 0.16, 0.24):
            pygame.draw.line(layer, (132, 151, 158),
                             (grille_rect.left + 1, grille_rect.top + round(vent_y * scale)),
                             (grille_rect.right - 1, grille_rect.top + round(vent_y * scale)), 1)
        headlight_rect = pygame.Rect(
            X(body_right - 0.13), Y(body_bottom + 0.79),
            max(3, round(0.22 * scale)), max(3, round(0.20 * scale)),
        )
        pygame.draw.rect(layer, (255, 239, 187), headlight_rect, border_radius=2)
        pygame.draw.line(layer, (255, 249, 221), headlight_rect.midtop, headlight_rect.midbottom, 1)
        tail_rect = pygame.Rect(
            X(body_left + 0.04), Y(body_bottom + 0.72),
            max(2, round(0.11 * scale)), max(2, round(0.25 * scale)),
        )
        pygame.draw.rect(layer, rear_lamp, tail_rect, border_radius=2)
        pygame.draw.line(layer, (255, 156, 140), tail_rect.midtop, tail_rect.midbottom, 1)
        # Capó y defensas hacen reconocible el frente incluso en escala pequeña.
        pygame.draw.line(layer, highlight, (X(body_right - 1.0), Y(body_bottom + 0.79)),
                         (X(body_right - 0.24), Y(body_bottom + 0.72)), max(1, round(0.035 * scale)))
        pygame.draw.line(layer, metal, (X(body_right - 0.22), Y(body_bottom + 0.18)),
                         (X(body_right + 0.15), Y(body_bottom + 0.18)), max(2, round(0.08 * scale)))
        pygame.draw.line(layer, metal, (X(body_left - 0.08), Y(body_bottom + 0.18)),
                         (X(body_left + 0.30), Y(body_bottom + 0.18)), max(2, round(0.08 * scale)))
        if perfil.estilo == "suv":
            # Barras de techo y una luneta trasera alta distinguen el volumen SUV.
            pygame.draw.line(layer, metal, (X(body_left + 1.20), Y(body_top + 0.06)),
                             (X(body_right - 0.34), Y(body_top + 0.06)), max(1, round(0.04 * scale)))
            pygame.draw.line(layer, metal, (X(body_left + 1.40), Y(body_top + 0.14)),
                             (X(body_right - 0.48), Y(body_top + 0.14)), max(1, round(0.04 * scale)))
        elif perfil.estilo == "pickup":
            # Caja abierta con nervaduras visibles, separada de la cabina.
            for rib_x in (body_left + 0.32, body_left + 0.58, body_left + 0.84):
                pygame.draw.line(layer, (112, 87, 60), (X(rib_x), Y(body_bottom + 0.63)),
                                 (X(rib_x), Y(body_bottom + 0.79)), max(1, round(0.035 * scale)))
            pygame.draw.line(layer, metal, (X(body_left + 1.18), Y(body_bottom + 0.60)),
                             (X(body_left + 1.18), Y(body_bottom + 0.90)), max(1, round(0.05 * scale)))

    # Guardabarros sobre las coordenadas exactas de eje.
    for axle_x_m, vertical_offset in zip(vehiculo.posiciones_ejes_m, axle_offsets):
        pygame.draw.arc(layer,(24,34,43),(X(axle_x_m-wheel_r*1.13),Y(wheel_r*0.82)-round(vertical_offset*supersample),round(wheel_r*2.26*scale),round(wheel_r*2.05*scale)),math.pi,2*math.pi,max(1,round(0.07*scale)))

    # Vector de ruedas y rines giratorios. Ejes dobles permanecen centrados en el punto de carga.
    for axle_x_m, wheel_count, vertical_offset in zip(vehiculo.posiciones_ejes_m, vehiculo.ruedas_por_eje, axle_offsets):
        center=(X(axle_x_m),Y(wheel_r)-round(vertical_offset*supersample))
        radius=max(3,round(wheel_r*scale))
        pygame.draw.circle(layer,(12,18,25),center,radius)
        pygame.draw.circle(layer,(63,75,85),center,round(radius*0.78))
        pygame.draw.circle(layer,(177,196,206),center,round(radius*0.55))
        pygame.draw.circle(layer,(40,53,62),center,round(radius*0.35))
        pygame.draw.circle(layer,(203,219,225),center,max(1,round(radius*0.12)))
        for spoke in range(6):
            angle=rotacion_rueda_rad+spoke*math.tau/6
            endpoint=(round(center[0]+math.cos(angle)*radius*0.48),round(center[1]+math.sin(angle)*radius*0.48))
            pygame.draw.line(layer,(226,235,237),center,endpoint,max(1,round(0.035*scale)))
        if wheel_count > 2:
            # Dual trasero, misma coordenada longitudinal del eje, ligeramente desplazado en altura.
            pygame.draw.circle(layer,(19,27,35),(center[0],center[1]-max(1,round(radius*0.30))),round(radius*0.62),max(1,round(radius*0.12)))

    screen_left = round(eje_referencia_x_px + left_m * escala_px_m)
    screen_top = round(tablero_y_px - road_local_y / supersample)
    smooth = pygame.transform.smoothscale(layer, (max(1, round(width/supersample)), max(1, round(height/supersample))))
    superficie.blit(smooth,(screen_left,screen_top))
    return geometry
