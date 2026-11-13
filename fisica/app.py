import math
import pygame
from .truss import resolver_celosia
from dataclasses import replace
from .materials import MATERIALES_EDUCATIVOS, Seccion
from .structural import DisenoBarra, analizar_estado_celosia
from .vehicles import EstadoVehiculo, VEHICULOS_EDUCATIVOS
from .visualization import (
    color_por_utilizacion,
    proyectar_ejes_px,
    proyectar_nodos_deformados,
    proyectar_serie_temporal,
    proyectar_vector_fuerza_px,
)
from .vehicle_visuals import dibujar_vehiculo_vectorial, geometria_visual, perfil_para_clave

def main():

    import pygame

    # ==========================================
    # 1. CONFIGURACION INICIAL
    # ==========================================

    pygame.init()

    ANCHO = 1200
    ALTO = 750

    pantalla = pygame.display.set_mode((ANCHO, ALTO))

    pygame.display.set_caption("Simulador de puentes en equilibrio")

    reloj = pygame.time.Clock()

    # ==========================================
    # 2. COLORES
    # ==========================================

    FONDO = (8, 15, 27)
    PANEL = (17, 28, 43)
    PANEL_CLARO = (34, 52, 72)

    BLANCO = (240, 245, 250)
    GRIS = (150, 165, 180)

    AZUL = (54, 169, 238)
    VERDE = (47, 220, 164)
    ROJO = (255, 91, 105)
    AMARILLO = (255, 196, 87)
    ROJO_CLARO = (255, 133, 137)
    VIDRIO = (92, 205, 231)
    RUEDA = (12, 19, 30)
    ARO = (178, 204, 218)

    # ==========================================
    # 3. TIPOGRAFIAS
    # ==========================================

    titulo = pygame.font.SysFont("Segoe UI", 27, bold=True)
    subtitulo = pygame.font.SysFont("Segoe UI", 18, bold=True)
    texto = pygame.font.SysFont("Segoe UI", 14)
    pequeno = pygame.font.SysFont("Segoe UI", 12)

    # ==========================================
    # 4. VARIABLES DE SIMULACION
    # ==========================================

    masa = 1000
    tipo_vehiculo = "Personalizado"
    masas_vehiculos = {
        "Sedán": 1500,
        "SUV": 2200,
        "Camioneta": 2400,
        "Autobús urbano": 12000,
        "Autobús interurbano": 15000,
        "Camión 2 ejes": 18000,
        "Camión 3 ejes": 18000,
        "Camión articulado 5 ejes": 30000,
        "Personalizado": 1000,
    }
    rotacion_rueda_rad = 0.0
    deformacion_amplificada = True
    factor_amplificacion = 250
    mostrar_mapa_esfuerzos = True
    arrastrando_control_visual = False
    historial_respuesta = []
    velocidad = 60
    aceleracion = 2.0
    modo_movimiento = "MRUA"
    tiempo_simulacion = 0.0
    registrar_descarga_final = False
    historial_movimiento = []
    cargas_personalizadas = []
    carga_seleccionada = None
    arrastrando_carga = False
    desplazamiento_arrastre = 0.0

    GRAVEDAD = 9.81
    LONGITUD_PUENTE_M = 60.0
    LUZ_CABLE_M = 40.0
    FLECHA_CABLE_M = 6.0
    POSICIONES_PENDOLAS_PX = tuple(range(520, 941, 60))
    CAPACIDAD_TENSION_DEMO = 60000.0
    CAPACIDAD_COMPRESION_DEMO = 50000.0
    CAPACIDAD_CABLE_DEMO = 60000.0
    CAPACIDAD_PENDOLA_DEMO = 20000.0
    CAPACIDAD_TORRE_DEMO = 50000.0
    CAPACIDAD_ANCLAJE_DEMO = 65000.0
    UMBRAL_ADVERTENCIA = 0.80

    nodos_pantalla = [
        (370, 430), (490, 430), (610, 430), (730, 430),
        (850, 430), (970, 430), (1090, 430),
        (430, 330), (550, 330), (670, 330),
        (790, 330), (910, 330), (1030, 330),
    ]
    barras_puente = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
        (7, 8), (8, 9), (9, 10), (10, 11), (11, 12),
        (0, 7), (7, 1), (1, 8), (8, 2), (2, 9), (9, 3),
        (3, 10), (10, 4), (4, 11), (11, 5), (5, 12), (12, 6),
    ]
    tipo_puente = "Celosía"
    # La escala es 12 píxeles por metro; el eje y físico apunta hacia arriba.
    nodos_fisicos = [((x - 370) / 12, (430 - y) / 12) for x, y in nodos_pantalla]
    material_educativo = MATERIALES_EDUCATIVOS["acero_s275"]
    seccion_educativa = Seccion.circulo("Sección de referencia Ø150 mm", 0.15)
    disenos_barras = [
        DisenoBarra(f"Barra {indice + 1:02d}", material_educativo, seccion_educativa)
        for indice in range(len(barras_puente))
    ]

    simulando = False
    colapso_activo = False
    colapso_progreso = 0.0
    causa_colapso = ""
    punto_colapso_x = None

    posicion_vehiculo = 370

    velocidad_actual = 0
    analisis_celosia = None
    barra_critica_actual = (0.0, None, 0.0, CAPACIDAD_TENSION_DEMO)
    cargas_nodos_actuales = {}
    cargas_por_fuente_actuales = {}
    analisis_colgante = {}
    analisis_educativo_actual = None

    # ==========================================
    # 5. FUNCIONES GENERALES
    # ==========================================

    def dibujar_texto(mensaje, fuente, color, x, y):

        superficie = fuente.render(mensaje, True, color)

        pantalla.blit(superficie, (x, y))


    def dibujar_panel(x, y, ancho, alto, color=PANEL):
        pygame.draw.rect(
            pantalla,
            (7, 12, 21),
            (x, y + 3, ancho, alto),
            border_radius=10,
        )
        pygame.draw.rect(
            pantalla,
            color,
            (x, y, ancho, alto),
            border_radius=10
        )
        pygame.draw.rect(
            pantalla,
            PANEL_CLARO,
            (x, y, ancho, alto),
            width=1,
            border_radius=10,
        )
        pygame.draw.line(pantalla, (54, 74, 98), (x + 12, y + 1), (x + ancho - 12, y + 1), 1)


    def dibujar_boton(mensaje, x, y, ancho, alto, color):
        rect = pygame.Rect(x, y, ancho, alto)
        hover = rect.collidepoint(pygame.mouse.get_pos())
        color_boton = tuple(min(255, canal + (22 if hover else 0)) for canal in color)
        borde = tuple(min(255, canal + 34) for canal in color_boton)
        pygame.draw.rect(
            pantalla,
            (8, 13, 23),
            (x, y + 3, ancho, alto),
            border_radius=7,
        )
        pygame.draw.rect(
            pantalla,
            color_boton,
            rect,
            border_radius=7,
        )
        pygame.draw.rect(pantalla, borde, rect, width=1, border_radius=7)
        pygame.draw.line(pantalla, borde, (x + 8, y + 2), (x + ancho - 8, y + 2), 1)

        superficie = texto.render(mensaje, True, BLANCO)

        rect = superficie.get_rect(
            center=(x + ancho // 2, y + alto // 2)
        )

        pantalla.blit(superficie, rect)


    def obtener_especificacion_vehiculo():
        claves = {
            "Sedán": "sedan",
            "SUV": "suv", "Camioneta": "camioneta",
            "Autobús urbano": "autobus_urbano", "Autobús interurbano": "autobus_interurbano",
            "Camión 2 ejes": "camion_2_ejes", "Camión 3 ejes": "camion_3_ejes",
            "Camión articulado 5 ejes": "camion_articulado_5_ejes",
        }
        base = VEHICULOS_EDUCATIVOS.get(claves.get(tipo_vehiculo, "sedan"))
        return replace(base, masa_kg=float(masa))

    def clave_visual_vehiculo():
        return {
            "Sedán": "sedan", "SUV": "suv",
            "Camioneta": "camioneta", "Autobús urbano": "autobus_urbano",
            "Autobús interurbano": "autobus_interurbano", "Camión 2 ejes": "camion_2_ejes",
            "Camión 3 ejes": "camion_3_ejes", "Camión articulado 5 ejes": "camion_articulado_5_ejes",
            "Personalizado": "personalizado",
        }.get(tipo_vehiculo, "personalizado")


    def iniciar_colapso(causa, posicion_x=None):
        nonlocal colapso_activo, colapso_progreso, causa_colapso, punto_colapso_x, simulando
        if not colapso_activo and simulando:
            colapso_activo = True
            colapso_progreso = 0.0
            causa_colapso = causa
            punto_colapso_x = posicion_x if posicion_x is not None else posicion_vehiculo
        simulando = False


    # ==========================================
    # 6. ENCABEZADO
    # ==========================================

    def dibujar_encabezado():

        pygame.draw.rect(
            pantalla,
            PANEL,
            (0, 0, ANCHO, 85)
        )
        pygame.draw.rect(pantalla, VERDE, (0, 82, ANCHO, 3))
        pygame.draw.circle(pantalla, VERDE, (47, 43), 19, 2)
        pygame.draw.line(pantalla, VERDE, (33, 49), (61, 49), 2)
        pygame.draw.line(pantalla, VERDE, (36, 45), (42, 31), 2)
        pygame.draw.line(pantalla, VERDE, (42, 31), (50, 45), 2)
        pygame.draw.line(pantalla, VERDE, (50, 45), (57, 34), 2)

        dibujar_texto(
            "SIMULADOR DE PUENTES",
            titulo,
            BLANCO,
            76,
            25
        )

        pygame.draw.line(pantalla, PANEL_CLARO, (790, 20), (790, 65), 1)
        dibujar_texto("FÍSICA APLICADA  ·  EQUILIBRIO", texto, VERDE, 815, 25)
        dibujar_texto("ESTRUCTURAS  /  EN VIVO", pequeno, GRIS, 815, 48)


    # ==========================================
    # 7. PANEL DE CONTROLES
    # ==========================================

    def dibujar_controles():

        carga_actual = (
            cargas_personalizadas[carga_seleccionada]
            if carga_seleccionada is not None
            else None
        )

        dibujar_panel(25, 110, 260, 615)

        dibujar_texto(
            "CONFIG. DEL VEHÍCULO",
            subtitulo,
            BLANCO,
            45,
            130
        )

        pygame.draw.line(
            pantalla,
            GRIS,
            (45, 165),
            (265, 165),
            1
        )

        # Parámetros del vehículo
        dibujar_texto("Masa del vehículo", texto, BLANCO, 45, 178)
        dibujar_texto(f"{masa} kg", texto, VERDE, 45, 202)
        dibujar_boton("-", 175, 197, 35, 28, ROJO)
        dibujar_boton("+", 220, 197, 35, 28, VERDE)

        dibujar_texto("Velocidad objetivo", texto, BLANCO, 45, 238)
        dibujar_texto(f"{velocidad} km/h", texto, VERDE, 45, 262)
        dibujar_boton("-", 175, 257, 35, 28, ROJO)
        dibujar_boton("+", 220, 257, 35, 28, VERDE)

        dibujar_texto("Aceleración", texto, BLANCO, 45, 298)
        dibujar_texto(f"{aceleracion:.1f} m/s²", texto, VERDE, 45, 322)
        dibujar_boton("-", 175, 317, 35, 28, ROJO)
        dibujar_boton("+", 220, 317, 35, 28, VERDE)

        # Carga externa ajustable
        dibujar_texto("Magnitud de carga", texto, BLANCO, 45, 358)
        magnitud_visible = f"{carga_actual['magnitud']:,.0f} N" if carga_actual else "—"
        dibujar_texto(magnitud_visible, texto, AMARILLO, 45, 382)
        dibujar_boton("-", 175, 377, 35, 28, ROJO)
        dibujar_boton("+", 220, 377, 35, 28, VERDE)

        dibujar_texto("Dirección (+X = 0°)", texto, BLANCO, 45, 418)
        angulo_visible = f"{carga_actual['angulo']:.0f}°" if carga_actual else "—"
        dibujar_texto(angulo_visible, texto, AMARILLO, 45, 442)
        dibujar_boton("-", 175, 437, 35, 28, ROJO)
        dibujar_boton("+", 220, 437, 35, 28, VERDE)

        seleccion_visible = (
            f"CARGA {carga_seleccionada + 1} / {len(cargas_personalizadas)}"
            if carga_actual else "SIN CARGA SELECCIONADA"
        )
        dibujar_texto(seleccion_visible, pequeno, GRIS, 45, 470)
        dibujar_boton("+ NUEVA", 45, 486, 100, 31, AZUL if len(cargas_personalizadas) < 5 else PANEL_CLARO)
        dibujar_boton(
            "ELIMINAR",
            155, 486, 100, 31,
            ROJO if carga_actual else PANEL_CLARO,
        )

        dibujar_boton("INICIAR", 45, 526, 100, 32, PANEL_CLARO if colapso_activo else VERDE)
        dibujar_boton("PAUSAR", 155, 526, 100, 32, AZUL)
        dibujar_boton("REINICIAR", 45, 568, 210, 32, PANEL_CLARO)
        dibujar_texto("TIPO DE VEHÍCULO  ‹  ›", pequeno, GRIS, 45, 606)
        dibujar_boton(tipo_vehiculo, 45, 628, 210, 34, AZUL if tipo_vehiculo != "Personalizado" else PANEL_CLARO)
        dibujar_boton("DEF. AMPL. ON" if deformacion_amplificada else "DEF. REAL", 45, 670, 102, 24, AZUL if deformacion_amplificada else PANEL_CLARO)
        dibujar_boton("MAPA ON" if mostrar_mapa_esfuerzos else "MAPA OFF", 153, 670, 102, 24, VERDE if mostrar_mapa_esfuerzos else PANEL_CLARO)
        pygame.draw.line(pantalla, GRIS, (48, 709), (252, 709), 4)
        slider_x = round(48 + (factor_amplificacion - 1) / 499 * 204)
        pygame.draw.line(pantalla, AZUL, (48, 709), (slider_x, 709), 4)
        pygame.draw.circle(pantalla, BLANCO, (slider_x, 709), 7)
        dibujar_texto(f"Amplificación visual: ×{factor_amplificacion}", pequeno, GRIS, 45, 690)


    # ==========================================
    # 8. ESTRUCTURA DEL PUENTE
    # ==========================================

    def distancia_a_segmento(punto, inicio, fin):
        px, py = punto
        ax, ay = inicio
        bx, by = fin
        dx = bx - ax
        dy = by - ay
        longitud2 = dx * dx + dy * dy
        if longitud2 == 0:
            return math.hypot(px - ax, py - ay)
        proporcion = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / longitud2))
        cercano_x = ax + proporcion * dx
        cercano_y = ay + proporcion * dy
        return math.hypot(px - cercano_x, py - cercano_y)


    def elemento_bajo_puntero(punto):
        posiciones_actuales = [posicion_nodo_dibujado(i) for i in range(len(nodos_pantalla))]
        nodo_cercano = min(
            range(len(nodos_pantalla)),
            key=lambda indice: math.dist(punto, posiciones_actuales[indice]),
        )
        if math.dist(punto, posiciones_actuales[nodo_cercano]) <= 13:
            return "nudo", nodo_cercano

        barra_cercana = min(
            range(len(barras_puente)),
            key=lambda indice: distancia_a_segmento(
                punto,
                posiciones_actuales[barras_puente[indice][0]],
                posiciones_actuales[barras_puente[indice][1]],
            ),
        )
        inicio, fin = barras_puente[barra_cercana]
        if distancia_a_segmento(punto, posiciones_actuales[inicio], posiciones_actuales[fin]) <= 9:
            return "barra", barra_cercana
        return None


    def formato_fuerza(valor):
        if abs(valor) < 0.05:
            valor = 0.0
        return f"{valor:+,.1f} N"


    def capacidad_barra(fuerza):
        return CAPACIDAD_TENSION_DEMO if fuerza >= 0 else CAPACIDAD_COMPRESION_DEMO

    def posicion_cable_px(x):
        proporcion = max(0.0, min(1.0, (x - 490) / 480))
        flecha = 72
        return round(330 + flecha * 4 * proporcion * (1 - proporcion))

    def posicion_tablero_px(x):
        return 441

    def posicion_nodo_dibujado(indice):
        if analisis_educativo_actual is not None and tipo_puente == "Celosía":
            projected = proyectar_nodos_deformados(
                nodos_fisicos,
                analisis_educativo_actual["desplazamientos"],
                (370, 430),
                12,
                amplificada=deformacion_amplificada,
                factor_amplificacion=factor_amplificacion,
            )
            x, y = projected[indice]
        else:
            x, y = nodos_pantalla[indice]
        return x, y

    def desplazamiento_visual_tablero(posicion_x_m):
        """Interpola el desplazamiento nodal real con el mismo factor de vista."""
        if analisis_educativo_actual is None:
            return (0.0, 0.0)
        deck = sorted(
            (i for i, node in enumerate(nodos_fisicos)
             if math.isclose(node[1], min(point[1] for point in nodos_fisicos), abs_tol=1e-9)),
            key=lambda i: nodos_fisicos[i][0],
        )
        if posicion_x_m <= nodos_fisicos[deck[0]][0]:
            pair = (deck[0], deck[0])
        elif posicion_x_m >= nodos_fisicos[deck[-1]][0]:
            pair = (deck[-1], deck[-1])
        else:
            pair = next((deck[i], deck[i + 1]) for i in range(len(deck) - 1)
                        if nodos_fisicos[deck[i]][0] <= posicion_x_m <= nodos_fisicos[deck[i + 1]][0])
        i, j = pair
        x_i, x_j = nodos_fisicos[i][0], nodos_fisicos[j][0]
        t = 0.0 if i == j else (posicion_x_m - x_i) / (x_j - x_i)
        ux_i, uy_i = analisis_educativo_actual["desplazamientos"][i]
        ux_j, uy_j = analisis_educativo_actual["desplazamientos"][j]
        factor = factor_amplificacion if deformacion_amplificada else 1.0
        return ((ux_i * (1-t) + ux_j*t) * 12 * factor,
                -(uy_i * (1-t) + uy_j*t) * 12 * factor)

    def punto_aplicacion_carga(carga):
        """Devuelve el punto de contacto con el tablero en su geometría dibujada."""
        desplazamiento_x, desplazamiento_y = desplazamiento_visual_tablero(
            (carga["x"] - 370) / 12
        )
        return round(carga["x"] + desplazamiento_x), round(441 + desplazamiento_y)

    def calcular_analisis_colgante():
        """Modelo ideal: cable parabólico, carga distribuida equivalente y péndolas a tensión."""
        cargas_puntuales = [(posicion_vehiculo, masa * GRAVEDAD)]
        for carga in cargas_personalizadas:
            fy = carga["magnitud"] * math.sin(math.radians(carga["angulo"]))
            if fy < 0:
                cargas_puntuales.append((carga["x"], -fy))

        peso_total = sum(peso for _, peso in cargas_puntuales)
        w = peso_total / LONGITUD_PUENTE_M
        tension_horizontal = w * LUZ_CABLE_M ** 2 / (8 * FLECHA_CABLE_M)
        x_torre_izquierda = 10.0
        x_torre_derecha = 50.0

        fuerzas_pendolas = [0.0] * len(POSICIONES_PENDOLAS_PX)
        posiciones_pendolas_m = [(x - 370) / 12 for x in POSICIONES_PENDOLAS_PX]
        compresion_izquierda = 0.0
        compresion_derecha = 0.0
        for posicion_px, carga_puntual in cargas_puntuales:
            posicion_m = (posicion_px - 370) / 12
            # Cada carga puntual se reparte entre las dos péndolas vecinas.
            if posicion_m <= posiciones_pendolas_m[0]:
                fuerzas_pendolas[0] += carga_puntual
            elif posicion_m >= posiciones_pendolas_m[-1]:
                fuerzas_pendolas[-1] += carga_puntual
            else:
                indice = next(
                    i for i in range(len(posiciones_pendolas_m) - 1)
                    if posiciones_pendolas_m[i] <= posicion_m <= posiciones_pendolas_m[i + 1]
                )
                fraccion = (posicion_m - posiciones_pendolas_m[indice]) / (
                    posiciones_pendolas_m[indice + 1] - posiciones_pendolas_m[indice]
                )
                fuerzas_pendolas[indice] += carga_puntual * (1 - fraccion)
                fuerzas_pendolas[indice + 1] += carga_puntual * fraccion

            if posicion_m < x_torre_izquierda:
                compresion_izquierda += carga_puntual
            elif posicion_m > x_torre_derecha:
                compresion_derecha += carga_puntual
            else:
                fraccion_derecha = (posicion_m - x_torre_izquierda) / LUZ_CABLE_M
                compresion_izquierda += carga_puntual * (1 - fraccion_derecha)
                compresion_derecha += carga_puntual * fraccion_derecha

        fuerzas_pendolas = [max(0.0, fuerza) for fuerza in fuerzas_pendolas]
        reaccion_derecha = sum(
            peso * ((x - 370) / 12) / LONGITUD_PUENTE_M
            for x, peso in cargas_puntuales
        )
        tension_resultante_anclaje = max(
            math.hypot(tension_horizontal, compresion_izquierda),
            math.hypot(tension_horizontal, compresion_derecha),
        )
        return {
            "peso_total": peso_total,
            "reaccion_izquierda": max(0.0, peso_total - reaccion_derecha),
            "reaccion_derecha": max(0.0, reaccion_derecha),
            "w": w,
            "tension_horizontal": tension_horizontal,
            "tension_anclaje": tension_resultante_anclaje,
            "compresion_torre_izquierda": max(0.0, compresion_izquierda),
            "compresion_torre_derecha": max(0.0, compresion_derecha),
            "fuerzas_pendolas": tuple(fuerzas_pendolas),
            "pendola_maxima": max(fuerzas_pendolas, default=0.0),
        }

    def dibujar_fondo_escena():
        """Fondo nocturno con ciudad, agua y luz ambiental bajo el puente."""
        escena = pygame.Rect(316, 170, 848, 440)
        pygame.draw.rect(pantalla, (13, 25, 42), escena, border_radius=8)
        for franja in range(12):
            y = 175 + franja * 23
            tono = (14 + franja, 28 + franja, 45 + franja)
            pygame.draw.line(pantalla, tono, (320, y), (1160, y), 22)
        pygame.draw.circle(pantalla, (35, 61, 82), (1040, 230), 42)
        pygame.draw.circle(pantalla, (45, 77, 96), (1040, 230), 31)
        # Silueta urbana tenue en ambas márgenes.
        edificios_izq = [(320, 365, 36, 95), (357, 340, 43, 120), (401, 375, 32, 85), (435, 352, 44, 108)]
        edificios_der = [(1035, 355, 36, 105), (1073, 330, 42, 130), (1117, 366, 42, 94)]
        for ex, ey, ew, eh in edificios_izq + edificios_der:
            pygame.draw.rect(pantalla, (19, 37, 54), (ex, ey, ew, eh))
            pygame.draw.line(pantalla, (34, 64, 79), (ex, ey), (ex + ew, ey), 2)
            for wx in range(ex + 8, ex + ew - 3, 12):
                for wy in range(ey + 12, ey + eh - 5, 17):
                    pygame.draw.rect(pantalla, (74, 111, 112), (wx, wy, 3, 5))
        # Río y reflejos horizontales.
        pygame.draw.rect(pantalla, (10, 31, 47), (318, 462, 844, 145))
        for i in range(13):
            y = 474 + i * 10
            x = 335 + (i * 47) % 360
            pygame.draw.line(pantalla, (21, 65 + (i % 3) * 5, 77), (x, y), (x + 45 + (i % 4) * 11, y), 1)
            pygame.draw.line(pantalla, (23, 57, 70), (x + 410, y + 4), (x + 438, y + 4), 1)

    def dibujar_puente():
        puntero = pygame.mouse.get_pos()
        inspeccion = elemento_bajo_puntero(puntero)
        barra_resaltada = inspeccion[1] if inspeccion and inspeccion[0] == "barra" else None
        nudo_resaltado = inspeccion[1] if inspeccion and inspeccion[0] == "nudo" else None
        nodos_visuales = [posicion_nodo_dibujado(i) for i in range(len(nodos_pantalla))]

        # Sombra estructural y acero con canto para dar profundidad a la celosía.
        for inicio, final in barras_puente:
            pygame.draw.line(pantalla, (5, 12, 21), nodos_visuales[inicio], nodos_visuales[final], 12)
        for indice, (inicio, final) in enumerate(barras_puente):
            if indice == barra_resaltada:
                color = AMARILLO
                grosor = 8
            elif analisis_celosia is None or not mostrar_mapa_esfuerzos:
                color = GRIS
                grosor = 5
            else:
                fuerza = analisis_celosia["fuerzas_barras"][indice]
                utilizacion = analisis_educativo_actual["elementos"][indice]["utilizacion_maxima"]
                category = color_por_utilizacion(fuerza, utilizacion)
                color = {
                    "falla": ROJO,
                    "cerca_capacidad": AMARILLO,
                    "baja_traccion": (25, 112, 88),
                    "baja_compresion": (33, 91, 133),
                    "traccion": VERDE,
                    "compresion": AZUL,
                }[category]
                grosor = 5

            pygame.draw.line(
                pantalla,
                (7, 17, 27),
                nodos_visuales[inicio],
                nodos_visuales[final],
                grosor + 4
            )
            pygame.draw.line(
                pantalla,
                color,
                nodos_visuales[inicio],
                nodos_visuales[final],
                grosor
            )

        # Referencia punteada: geometría original del puente, solo al amplificar.
        if deformacion_amplificada:
            for inicio, final in barras_puente:
                x1, y1 = nodos_pantalla[inicio]
                x2, y2 = nodos_pantalla[final]
                length = math.hypot(x2 - x1, y2 - y1)
                markers = max(1, round(length / 7))
                for marker in range(0, markers + 1, 2):
                    fraction = min(1.0, marker / markers)
                    point = (round(x1 + (x2 - x1) * fraction), round(y1 + (y2 - y1) * fraction))
                    pygame.draw.circle(pantalla, (80, 96, 110), point, 1)
            for x, y in nodos_pantalla:
                pygame.draw.circle(pantalla, (80, 96, 110), (x, y), 3, 1)

        # Nodos

        for indice, posicion in enumerate(nodos_visuales):

            pygame.draw.circle(pantalla, (8, 19, 29), posicion, 10)
            pygame.draw.circle(pantalla, AMARILLO if indice == nudo_resaltado else (111, 224, 211), posicion, 7)
            pygame.draw.circle(pantalla, (229, 250, 245), posicion, 2)
            # Pernos de unión visibles en las placas de los nudos.
            pygame.draw.circle(pantalla, (219, 237, 232), (posicion[0] + 4, posicion[1] - 3), 1)

        # El tablero y sus marcas siguen los mismos nodos inferiores deformados.
        tablero_superior = [(nodos_visuales[i][0], nodos_visuales[i][1] + 11) for i in range(7)]
        tablero_inferior = [(x, y + 20) for x, y in tablero_superior]
        pygame.draw.polygon(pantalla, (5, 13, 23), tablero_superior + tablero_inferior)
        pygame.draw.lines(pantalla, (74, 116, 132), False, tablero_superior, 5)
        pygame.draw.polygon(pantalla, (31, 57, 70), tablero_superior + tablero_inferior, 3)
        for i in range(6):
            ax, ay = tablero_superior[i]
            bx, by = tablero_superior[i + 1]
            for fraction in (0.18, 0.53, 0.88):
                start = (round(ax + (bx - ax) * fraction), round(ay + (by - ay) * fraction + 12))
                end_fraction = min(0.98, fraction + 0.12)
                end = (round(ax + (bx - ax) * end_fraction), round(ay + (by - ay) * end_fraction + 12))
                pygame.draw.line(pantalla, (120, 151, 146), start, end, 2)
        # Columnas, bases y apoyos mecánicos en los extremos.
        for px in (370, 1090):
            pygame.draw.rect(pantalla, (31, 52, 63), (px - 14, 470, 28, 75))
            pygame.draw.rect(pantalla, (55, 82, 91), (px - 21, 468, 42, 7), border_radius=2)
            pygame.draw.rect(pantalla, (73, 101, 107), (px - 25, 540, 50, 7), border_radius=2)
            pygame.draw.line(pantalla, (100, 132, 133), (px - 18, 489), (px + 18, 489), 2)

        # Apoyos

        for px in (370, 1090):
            pygame.draw.rect(pantalla, (158, 184, 183), (px - 18, 466, 36, 5), border_radius=2)
            pygame.draw.circle(pantalla, (211, 229, 218), (px - 7, 473), 4)
            pygame.draw.circle(pantalla, (211, 229, 218), (px + 7, 473), 4)
            pygame.draw.rect(pantalla, (84, 112, 119), (px - 22, 478, 44, 5), border_radius=2)


    def dibujar_reacciones():
        """Dibuja los vectores de reacción calculados en los apoyos del solver."""
        if analisis_educativo_actual is None:
            return
        reactions = analisis_educativo_actual["reacciones"]
        supports = (
            (0, "R₁", 315),
            (6, "R₂", 1040),
        )
        magnitudes = [math.hypot(*reactions.get(node, (0.0, 0.0))) for node, _, _ in supports]
        max_magnitude = max(magnitudes, default=0.0)
        if max_magnitude <= 0.05:
            return
        scale = 38 / max_magnitude
        for node, label, text_x in supports:
            fx, fy = reactions.get(node, (0.0, 0.0))
            magnitude = math.hypot(fx, fy)
            if magnitude <= 0.05:
                continue
            support_x, support_y = posicion_nodo_dibujado(node)
            origin = (support_x, support_y + 52)
            tip = proyectar_vector_fuerza_px(origin, (fx, fy), scale)
            dx, dy = tip[0] - origin[0], tip[1] - origin[1]
            length = math.hypot(dx, dy)
            if length > 0:
                pygame.draw.line(pantalla, VIDRIO, origin, tip, 3)
                ux, uy = dx / length, dy / length
                px, py = -uy, ux
                head_base = (tip[0] - ux * 8, tip[1] - uy * 8)
                pygame.draw.polygon(pantalla, VIDRIO, [
                    tip,
                    (round(head_base[0] + px * 4), round(head_base[1] + py * 4)),
                    (round(head_base[0] - px * 4), round(head_base[1] - py * 4)),
                ])
            reaction_x_kn = 0.0 if abs(fx) < 0.05 else fx / 1000
            reaction_y_kn = 0.0 if abs(fy) < 0.05 else fy / 1000
            dibujar_texto(
                f"{label}=({reaction_x_kn:+.1f}, {reaction_y_kn:+.1f}) kN",
                pequeno,
                VIDRIO,
                text_x,
                516,
            )


    def dibujar_puente_colgante():
        """Representa cable principal, péndolas, torres, diagonales y anclajes."""
        color_acero = (124, 176, 183)
        torres = (490, 970)
        for torre_x in torres:
            desplazamiento_cabeza = 0
            # Montantes comprimidos con crucetas en X entre ambas columnas.
            pygame.draw.line(pantalla, (5, 12, 21), (torre_x - 13 + desplazamiento_cabeza, 300), (torre_x - 13, 442), 10)
            pygame.draw.line(pantalla, (5, 12, 21), (torre_x + 13 + desplazamiento_cabeza, 300), (torre_x + 13, 442), 10)
            pygame.draw.line(pantalla, color_acero, (torre_x - 10 + desplazamiento_cabeza, 304), (torre_x - 10, 441), 5)
            pygame.draw.line(pantalla, color_acero, (torre_x + 10 + desplazamiento_cabeza, 304), (torre_x + 10, 441), 5)
            pygame.draw.line(pantalla, (190, 211, 196), (torre_x - 19 + desplazamiento_cabeza, 307), (torre_x + 19 + desplazamiento_cabeza, 307), 6)
            for y in (340, 385, 425):
                pygame.draw.line(pantalla, AZUL, (torre_x - 10, y), (torre_x + 10, y + 32), 2)
                pygame.draw.line(pantalla, AZUL, (torre_x + 10, y), (torre_x - 10, y + 32), 2)

        # Cable de anclaje y cable principal parabólico (entre torres).
        pygame.draw.line(pantalla, (5, 12, 21), (370, 405), (490, 330), 10)
        pygame.draw.line(pantalla, AMARILLO, (370, 405), (490, 330), 4)
        cable = [(x, posicion_cable_px(x)) for x in range(490, 971, 4)]
        pygame.draw.lines(pantalla, (5, 12, 21), False, cable, 10)
        pygame.draw.lines(pantalla, AMARILLO, False, cable, 5)
        pygame.draw.line(pantalla, (5, 12, 21), (970, 330), (1090, 405), 10)
        pygame.draw.line(pantalla, AMARILLO, (970, 330), (1090, 405), 4)
        pygame.draw.line(pantalla, AMARILLO, (350, 405), (370, 405), 4)
        pygame.draw.line(pantalla, AMARILLO, (1090, 405), (1090, 420), 4)
        dibujar_texto("ANCLAJE", pequeno, AMARILLO, 322, 385)
        dibujar_texto("CABLE PRINCIPAL", pequeno, AMARILLO, 676, 365)
        dibujar_texto("TORRE · C", pequeno, AZUL, 414, 310)
        dibujar_texto("TORRE · C", pequeno, AZUL, 932, 310)

        # Péndolas verticales, cada una trabaja a tensión.
        for indice, x in enumerate(POSICIONES_PENDOLAS_PX):
            y_cable = posicion_cable_px(x)
            y_tablero = posicion_tablero_px(x)
            pygame.draw.line(pantalla, (5, 12, 21), (x, y_cable), (x, y_tablero), 5)
            pygame.draw.line(pantalla, VERDE, (x, y_cable), (x, y_tablero), 2)
            pygame.draw.circle(pantalla, (226, 247, 231), (x, y_cable), 3)

        # Bloques de anclaje fijan los extremos del cable principal.
        for x in (350, 1090):
            pygame.draw.rect(pantalla, (54, 82, 94), (x - 12, 398, 24, 28), border_radius=3)
            pygame.draw.rect(pantalla, (141, 176, 178), (x - 16, 423, 32, 6), border_radius=2)
            pygame.draw.circle(pantalla, (207, 223, 211), (x, 405), 3)

        # Tablero, carriles y apoyos en los extremos.
        pygame.draw.rect(pantalla, (5, 13, 23), (337, 442, 786, 25), border_radius=3)
        pygame.draw.rect(pantalla, (74, 116, 132), (340, 441, 780, 5), border_radius=2)
        pygame.draw.rect(pantalla, (31, 57, 70), (340, 446, 780, 16))
        pygame.draw.line(pantalla, (96, 145, 151), (340, 462), (1120, 462), 2)
        for mark_x in range(356, 1110, 42):
            pygame.draw.line(pantalla, (120, 151, 146), (mark_x, 454), (mark_x + 19, 454), 2)
        # Viga rigidizadora con diagonales entre las dos torres.
        riel_superior = [(x, 466) for x in range(490, 971, 20)]
        riel_inferior = [(x, y + 22) for x, y in riel_superior]
        pygame.draw.lines(pantalla, (76, 113, 127), False, riel_superior, 3)
        pygame.draw.lines(pantalla, (76, 113, 127), False, riel_inferior, 3)
        for panel in range(8):
            x0 = 490 + panel * 60
            x1 = x0 + 60
            y0 = 466
            y1 = 466
            y0b, y1b = y0 + 22, y1 + 22
            pygame.draw.line(pantalla, (89, 137, 149), (x0, y0), (x1, y1b), 2)
            pygame.draw.line(pantalla, (89, 137, 149), (x0, y0b), (x1, y1), 2)
        for px in (370, 1090):
            pygame.draw.rect(pantalla, (31, 52, 63), (px - 14, 470, 28, 75))
            pygame.draw.rect(pantalla, (55, 82, 91), (px - 21, 468, 42, 7), border_radius=2)
            pygame.draw.rect(pantalla, (73, 101, 107), (px - 25, 540, 50, 7), border_radius=2)
            pygame.draw.rect(pantalla, (158, 184, 183), (px - 18, 466, 36, 5), border_radius=2)
            pygame.draw.circle(pantalla, (211, 229, 218), (px - 7, 473), 4)
            pygame.draw.circle(pantalla, (211, 229, 218), (px + 7, 473), 4)


    def dibujar_inspector_colgante():
        """Muestra la magnitud física del cable, péndola o torre bajo el cursor."""
        if not analisis_colgante:
            return
        mx, my = pygame.mouse.get_pos()
        detalle = None
        if any(abs(mx - x) <= 18 and 390 <= my <= 432 for x in (350, 1090)):
            detalle = ("ANCLAJE · TRACCIÓN", f"{analisis_colgante['tension_anclaje']:,.0f} N", AMARILLO)
        elif any(abs(mx - x) <= 14 and 300 <= my <= 442 for x in (490, 970)):
            lado = "izquierda" if mx < 730 else "derecha"
            fuerza = analisis_colgante[f"compresion_torre_{lado}"]
            detalle = ("TORRE · COMPRESIÓN", f"{fuerza:,.0f} N", AZUL)
        else:
            cable = [(370, 405)] + [(x, posicion_cable_px(x)) for x in range(490, 971, 4)] + [(1090, 405)]
            for inicio, fin in zip(cable, cable[1:]):
                if distancia_a_segmento((mx, my), inicio, fin) <= 7:
                    detalle = ("CABLE · TENSIÓN H", f"{analisis_colgante['tension_horizontal']:,.0f} N", AMARILLO)
                    break
            if detalle is None:
                for indice, x in enumerate(POSICIONES_PENDOLAS_PX):
                    if distancia_a_segmento((mx, my), (x, posicion_cable_px(x)), (x, posicion_tablero_px(x))) <= 6:
                        fuerza = analisis_colgante["fuerzas_pendolas"][indice]
                        detalle = (f"PÉNDOLA {indice + 1} · TENSIÓN", f"{fuerza:,.0f} N", VERDE)
                        break
        if detalle:
            encabezado, valor, color = detalle
            panel = pygame.Rect(min(990, mx + 15), min(575, my + 15), 165, 48)
            pygame.draw.rect(pantalla, PANEL, panel, border_radius=7)
            pygame.draw.rect(pantalla, color, panel, 2, border_radius=7)
            dibujar_texto(encabezado, pequeno, color, panel.x + 8, panel.y + 6)
            dibujar_texto(valor, texto, BLANCO, panel.x + 8, panel.y + 24)


    def dibujar_inspector():
        if analisis_celosia is None:
            return
        puntero = pygame.mouse.get_pos()
        inspeccion = elemento_bajo_puntero(puntero)
        if inspeccion is None:
            return

        tipo, indice = inspeccion
        lineas = []
        ancho_panel = 350

        if tipo == "barra":
            inicio, fin = barras_puente[indice]
            fuerza = analisis_celosia["fuerzas_barras"][indice]
            estado = analisis_celosia["estado_barras"][indice]
            member = analisis_educativo_actual["elementos"][indice]
            utilizacion = member["utilizacion_maxima"]
            capacidad = member["capacidades"].get(member["criterio_critico"].replace("fluencia_traccion", "fluencia_traccion_n").replace("rotura_traccion", "rotura_traccion_n").replace("pandeo_euler", "pandeo_euler_n").replace("aplastamiento_compresion", "aplastamiento_compresion_n").replace("conexion", "conexion_n").replace("deformacion", "desplazamiento_limite_m"), 0.0)
            factor_seguridad = capacidad / abs(fuerza) if abs(fuerza) > 0.05 else float("inf")
            color_estado = (
                ROJO if utilizacion >= 1.0
                else AMARILLO if utilizacion >= UMBRAL_ADVERTENCIA
                else VERDE if estado == "Tensión"
                else AZUL if estado == "Compresión"
                else GRIS
            )
            encabezado = f"BARRA {indice + 1:02d} · N{inicio + 1} ↔ N{fin + 1}"
            lineas = [
                (f"Estado: {estado}", color_estado),
                (f"Fuerza axial: {formato_fuerza(fuerza)}", BLANCO),
                (f"Criterio: {member['criterio_critico']} · Cap.: {capacidad:,.0f}", GRIS),
                (f"Utilización: {utilizacion:.0%} · FS: {factor_seguridad:.2f}", color_estado),
                ("Tensión positiva · Compresión negativa", GRIS),
            ]
            if utilizacion >= 1.0:
                lineas.append(("¡LÍMITE SUPERADO!", ROJO))
        else:
            nodo = indice
            encabezado = f"NUDO {nodo + 1} · SUMA DE FUERZAS"
            sum_x, sum_y = cargas_nodos_actuales.get(nodo, (0.0, 0.0))
            componentes_barras = []

            for indice_barra, (inicio, fin) in enumerate(barras_puente):
                if nodo == inicio:
                    otro = fin
                elif nodo == fin:
                    otro = inicio
                else:
                    continue

                dx = nodos_fisicos[otro][0] - nodos_fisicos[nodo][0]
                dy = nodos_fisicos[otro][1] - nodos_fisicos[nodo][1]
                longitud = math.hypot(dx, dy)
                fuerza_axial = analisis_celosia["fuerzas_barras"][indice_barra]
                fuerza_x = fuerza_axial * dx / longitud
                fuerza_y = fuerza_axial * dy / longitud
                sum_x += fuerza_x
                sum_y += fuerza_y
                componentes_barras.append((indice_barra, fuerza_x, fuerza_y))

            reaccion_x, reaccion_y = analisis_celosia["reacciones"].get(nodo, (0.0, 0.0))
            sum_x += reaccion_x
            sum_y += reaccion_y

            for indice_barra, fuerza_x, fuerza_y in componentes_barras:
                estado = analisis_celosia["estado_barras"][indice_barra]
                color = VERDE if estado == "Tensión" else AZUL if estado == "Compresión" else GRIS
                abreviatura = "T" if estado == "Tensión" else "C" if estado == "Compresión" else "0"
                lineas.append((
                    f"B{indice_barra + 1:02d} {abreviatura}: Fx {formato_fuerza(fuerza_x)}; "
                    f"Fy {formato_fuerza(fuerza_y)}",
                    color,
                ))

            for nombre, cargas_fuente in cargas_por_fuente_actuales.items():
                carga_x, carga_y = cargas_fuente.get(nodo, (0.0, 0.0))
                if abs(carga_x) > 0.05 or abs(carga_y) > 0.05:
                    lineas.append((
                        f"{nombre}: Fx {formato_fuerza(carga_x)}; Fy {formato_fuerza(carga_y)}",
                        ROJO,
                    ))
            if abs(reaccion_x) > 0.05 or abs(reaccion_y) > 0.05:
                lineas.append((
                    f"Apoyo: Rx {formato_fuerza(reaccion_x)}; Ry {formato_fuerza(reaccion_y)}",
                    AMARILLO,
                ))

            resultante = math.hypot(sum_x, sum_y)
            lineas.append((f"ΣFx = {formato_fuerza(sum_x)}", BLANCO))
            lineas.append((f"ΣFy = {formato_fuerza(sum_y)}", BLANCO))
            lineas.append((f"|ΣF| = {resultante:.2f} N  ✓", VERDE))

        alto_panel = 34 + len(lineas) * 18
        mouse_x, mouse_y = puntero
        panel_x = mouse_x + 16
        if panel_x + ancho_panel > 1170:
            panel_x = mouse_x - ancho_panel - 16
        panel_x = max(315, min(1170 - ancho_panel, panel_x))
        panel_y = mouse_y + 16
        if panel_y + alto_panel > 615:
            panel_y = mouse_y - alto_panel - 16
        panel_y = max(170, min(615 - alto_panel, panel_y))

        pygame.draw.rect(
            pantalla, PANEL, (panel_x, panel_y, ancho_panel, alto_panel), border_radius=8
        )
        pygame.draw.rect(
            pantalla,
            ROJO if tipo == "barra" and analisis_educativo_actual["elementos"][indice]["estado"] == "falla"
            else AZUL if tipo == "barra" else VERDE,
            (panel_x, panel_y, ancho_panel, alto_panel), 2, border_radius=8
        )
        dibujar_texto(encabezado, pequeno, BLANCO, panel_x + 10, panel_y + 8)
        for numero, (mensaje, color) in enumerate(lineas):
            dibujar_texto(mensaje, pequeno, color, panel_x + 10, panel_y + 28 + numero * 18)


    # ==========================================
    # 9. DIBUJAR VEHICULO Y CARGA
    # ==========================================

    def dibujar_vehiculo_respaldo():
        clip_anterior = pantalla.get_clip()
        pantalla.set_clip(pygame.Rect(305, 170, 870, 440))
        x = int(posicion_vehiculo)
        especificacion = obtener_especificacion_vehiculo()
        axle_xs = proyectar_ejes_px(x, especificacion.posiciones_ejes_m, 12)
        road_y = 430
        axle_deflections = [
            desplazamiento_visual_tablero((posicion_vehiculo - 370) / 12 + offset)[1]
            for offset in especificacion.posiciones_ejes_m
        ]
        mean_deflection = sum(axle_deflections) / len(axle_deflections)
        body_layer = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)

        vidrio = (24, 48, 70)
        body_left = min(axle_xs) - 14
        body_right = max(axle_xs) + 18
        pygame.draw.ellipse(body_layer, (9, 16, 27), (body_left - 8, 440, body_right - body_left + 16, 8))

        if tipo_vehiculo == "Autobús":
            cuerpo = pygame.Rect(body_left, 382, body_right - body_left, 52)
            pygame.draw.rect(body_layer, (35, 119, 186), cuerpo, border_radius=8)
            pygame.draw.rect(body_layer, (112, 190, 235), cuerpo, 2, border_radius=8)
            pygame.draw.rect(body_layer, (27, 61, 87), (body_left + 9, 387, 23, 39), border_radius=3)
            pygame.draw.line(body_layer, (164, 208, 230), (body_left + 31, 388), (body_left + 31, 427), 2)
            for window_x in range(body_left + 38, body_right - 28, 26):
                pygame.draw.rect(body_layer, vidrio, (window_x, 390, 20, 20), border_radius=3)
                pygame.draw.line(body_layer, (83, 145, 176), (window_x + 3, 393), (window_x + 3, 407), 1)
            pygame.draw.rect(body_layer, (18, 48, 71), (body_right - 25, 389, 16, 10), border_radius=2)
            pygame.draw.line(body_layer, (204, 225, 232), (body_right - 21, 395), (body_right - 12, 395), 1)
            pygame.draw.line(body_layer, (190, 229, 247), (body_left + 7, 415), (body_right - 8, 415), 2)
        elif tipo_vehiculo.startswith("Camión") or tipo_vehiculo == "Camión":
            caja = pygame.Rect(body_left, 387, body_right - body_left - 28, 45)
            pygame.draw.rect(body_layer, (47, 105, 156), caja, border_radius=4)
            pygame.draw.rect(body_layer, (102, 181, 222), caja, 2, border_radius=4)
            for panel_x in range(body_left + 12, caja.right - 4, 18):
                pygame.draw.line(body_layer, (75, 137, 178), (panel_x, 391), (panel_x, 427), 1)
            pygame.draw.line(body_layer, (255, 191, 74), (body_left + 5, 424), (caja.right - 3, 424), 3)
            cab_x = body_right - 40
            pygame.draw.polygon(body_layer, (217, 137, 48), [(cab_x, 401), (body_right - 8, 401), (body_right + 4, 416), (body_right + 4, 433), (cab_x, 433)])
            pygame.draw.polygon(body_layer, (255, 205, 126), [(cab_x + 7, 405), (body_right - 12, 405), (body_right - 3, 416), (cab_x + 7, 416)])
            pygame.draw.line(body_layer, (125, 72, 34), (cab_x + 4, 420), (cab_x + 4, 431), 2)
            pygame.draw.circle(body_layer, (238, 218, 174), (cab_x + 10, 423), 2)
            pygame.draw.rect(body_layer, (42, 53, 61), (body_right - 8, 419, 8, 10), border_radius=2)
            pygame.draw.line(body_layer, (255, 224, 145), (body_right + 1, 422), (body_right + 3, 422), 3)
        else:
            carroceria = [(body_left, 429), (body_left + 4, 412), (body_left + 19, 407),
                          (body_left + 31, 391), (body_left + 50, 387),
                          (body_right - 18, 393), (body_right - 4, 408),
                          (body_right + 4, 416), (body_right + 4, 430)]
            pygame.draw.polygon(body_layer, (183, 47, 61), carroceria)
            pygame.draw.polygon(body_layer, ROJO_CLARO, carroceria, 2)
            pygame.draw.polygon(body_layer, vidrio, [(body_left + 23, 405), (body_left + 34, 392), (body_left + 49, 392), (body_left + 49, 405)])
            pygame.draw.polygon(body_layer, (29, 70, 94), [(body_left + 53, 392), (body_right - 19, 397), (body_right - 9, 405), (body_left + 53, 405)])
            pygame.draw.line(body_layer, (110, 35, 48), (body_left + 51, 405), (body_left + 51, 428), 2)
            pygame.draw.line(body_layer, (255, 148, 135), (body_left + 54, 407), (body_right - 11, 409), 1)
            pygame.draw.line(body_layer, (255, 148, 135), (body_left + 54, 414), (body_left + 72, 414), 1)
            pygame.draw.line(body_layer, (246, 192, 117), (body_right, 414), (body_right + 3, 414), 3)
            pygame.draw.line(body_layer, (255, 92, 85), (body_left + 2, 417), (body_left + 5, 417), 3)
            pygame.draw.line(body_layer, (205, 215, 221), (body_right - 5, 429), (body_right + 2, 428), 2)

        for axle_x in axle_xs:
            pygame.draw.arc(body_layer, (19, 31, 41), (axle_x - 11, 421, 22, 22), 0, math.pi, 2)

        pantalla.blit(body_layer, (0, round(mean_deflection)))

        # Las ruedas y marcas de contacto usan exactamente las posiciones de eje del modelo.
        for axle_index, (axle_x, wheel_count, axle_shift) in enumerate(zip(axle_xs, especificacion.ruedas_por_eje, axle_deflections)):
            wheel_base_y = round(435 + axle_shift)
            axle_road_y = round(road_y + 13 + axle_shift)
            pygame.draw.line(pantalla, (178, 204, 218), (axle_x, round(419 + mean_deflection)), (axle_x, axle_road_y - 5), 2)
            wheel_centers_y = (433, 437) if wheel_count > 2 else (435,)
            for wheel_y in wheel_centers_y:
                center_y = wheel_base_y + wheel_y - 435
                pygame.draw.circle(pantalla, RUEDA, (axle_x, center_y), 8 if wheel_y == 435 else 7)
                pygame.draw.circle(pantalla, (48, 62, 77), (axle_x, center_y), 5)
                pygame.draw.circle(pantalla, ARO, (axle_x, center_y), 2)
            pygame.draw.circle(pantalla, AMARILLO, (axle_x, axle_road_y), 3)
            dibujar_texto(f"E{axle_index + 1}", pequeno, BLANCO, axle_x - 7, axle_road_y + 2)

        # Flecha de peso

        pygame.draw.line(
            pantalla,
            AMARILLO,
            (x, round(355 + mean_deflection)),
            (x, round(380 + mean_deflection)),
            3
        )

        pygame.draw.polygon(
            pantalla,
            AMARILLO,
            [
                (x - 7, round(373 + mean_deflection)),
                (x + 7, round(373 + mean_deflection)),
                (x, round(383 + mean_deflection))
            ]
        )

        dibujar_texto(
            f"{masa * GRAVEDAD:.0f} N",
            pequeno,
            AMARILLO,
            x - 28,
            round(338 + mean_deflection)
        )
        pantalla.set_clip(clip_anterior)


    def dibujar_vehiculo():
        """Renderiza el perfil visual conectado a la especificación física seleccionada."""
        clip_anterior = pantalla.get_clip()
        pantalla.set_clip(pygame.Rect(305, 170, 870, 440))
        spec = obtener_especificacion_vehiculo()
        visual_key = clave_visual_vehiculo()
        visual_profile = perfil_para_clave(visual_key)
        reference_x = float(posicion_vehiculo)
        axle_deflections = [
            desplazamiento_visual_tablero((posicion_vehiculo - 370) / 12 + offset)[1]
            for offset in spec.posiciones_ejes_m
        ]
        mean_deflection = sum(axle_deflections) / len(axle_deflections)
        axle_relative_offsets = [value - mean_deflection for value in axle_deflections]
        geometry = dibujar_vehiculo_vectorial(
            pantalla,
            pygame,
            spec,
            visual_profile,
            reference_x,
            443 + mean_deflection,
            12,
            rotacion_rueda_rad=rotacion_rueda_rad,
            offsets_verticales_ejes_px=axle_relative_offsets,
        )
        for index, (axle_x, axle_shift) in enumerate(zip(geometry["ejes_px"], axle_deflections), start=1):
            contact_y = round(443 + axle_shift)
            pygame.draw.circle(pantalla, AMARILLO, (axle_x, contact_y), 2)
            dibujar_texto(f"E{index}", pequeno, BLANCO, axle_x - 6, contact_y + 2)

        cg_x, _ = geometry["centro_masa_px"]
        techo_vehiculo_y = round(443 + mean_deflection - spec.altura_m * 12)
        punta_flecha_y = techo_vehiculo_y - 2
        pygame.draw.line(
            pantalla,
            AMARILLO,
            (cg_x, punta_flecha_y - 20),
            (cg_x, punta_flecha_y - 5),
            2,
        )
        pygame.draw.polygon(
            pantalla,
            AMARILLO,
            [(cg_x - 5, punta_flecha_y - 7), (cg_x + 5, punta_flecha_y - 7), (cg_x, punta_flecha_y)],
        )
        etiqueta_peso = f"W={masa * GRAVEDAD:,.0f} N"
        etiqueta_superficie = pequeno.render(etiqueta_peso, True, AMARILLO)
        etiqueta_x = cg_x - etiqueta_superficie.get_width() // 2
        etiqueta_y = techo_vehiculo_y - 42
        pantalla.blit(etiqueta_superficie, (etiqueta_x, etiqueta_y))
        pantalla.set_clip(clip_anterior)


    def dibujar_ficha_vehiculo():
        spec = obtener_especificacion_vehiculo()
        gaps = " / ".join(f"{abs(a-b):.1f}" for a, b in zip(spec.posiciones_ejes_m, spec.posiciones_ejes_m[1:])) or "—"
        distribution = " / ".join(f"{fraction*100:.0f}" for fraction in spec.fracciones_peso_ejes)
        wheels = " / ".join(str(count) for count in spec.ruedas_por_eje)
        line1 = f"{spec.nombre.upper()} · {masa:,.0f} kg · {len(spec.posiciones_ejes_m)} ejes · separación {gaps} m · reparto {distribution}%"
        line2 = f"L×A×H {spec.longitud_m:.2f}×{spec.ancho_m:.2f}×{spec.altura_m:.2f} m · CM ({spec.centro_masa_x_m:.2f}, {spec.centro_masa_y_m:.2f}) m · ruedas/eje {wheels}"
        dibujar_panel(325, 587, 840, 34, color=(13, 23, 36))
        font_info = pygame.font.SysFont("Segoe UI", 11)
        dibujar_texto(line1, font_info, BLANCO, 336, 591)
        dibujar_texto(line2, font_info, GRIS, 336, 606)


    def dibujar_carga():
        for indice, carga in enumerate(cargas_personalizadas):
            punta_x, punta_y = punto_aplicacion_carga(carga)
            angulo_rad = math.radians(carga["angulo"])
            direccion_x = math.cos(angulo_rad)
            direccion_y = -math.sin(angulo_rad)
            cola_x = punta_x - direccion_x * 58
            cola_y = punta_y - direccion_y * 58
            seleccionada = indice == carga_seleccionada
            color = AMARILLO if seleccionada else ROJO
            grosor = 6 if seleccionada else 4

            pygame.draw.line(
                pantalla, color, (round(cola_x), round(cola_y)),
                (punta_x, punta_y), grosor
            )
            base_x = punta_x - direccion_x * 14
            base_y = punta_y - direccion_y * 14
            perpendicular_x = -direccion_y * 7
            perpendicular_y = direccion_x * 7
            pygame.draw.polygon(
                pantalla,
                color,
                [
                    (punta_x, punta_y),
                    (round(base_x + perpendicular_x), round(base_y + perpendicular_y)),
                    (round(base_x - perpendicular_x), round(base_y - perpendicular_y)),
                ],
            )
            etiqueta_x = max(330, min(1020, punta_x - 65))
            posicion_metros = (carga["x"] - 370) / 12
            dibujar_texto(
                f"C{indice + 1} · {carga['magnitud']:,.0f} N · {carga['angulo']:.0f}° · x={posicion_metros:.1f} m",
                pequeno,
                color,
                etiqueta_x,
                min(round(cola_y) - 18, 300) - 15 * (indice % 3),
            )


    # ==========================================
    # 10. AREA DE SIMULACION
    # ==========================================

    def dibujar_area_simulacion():

        dibujar_panel(305, 110, 870, 510)
        dibujar_fondo_escena()

        dibujar_texto(
            "PUENTE CELOSÍA · 60 M",
            subtitulo,
            BLANCO,
            330,
            130
        )
        dibujar_boton("MRU [M]", 850, 123, 105, 30, VERDE if modo_movimiento == "MRU" else PANEL_CLARO)
        dibujar_boton("MRUA [A]", 965, 123, 110, 30, AZUL if modo_movimiento == "MRUA" else PANEL_CLARO)

        if tipo_puente == "Colgante":
            pygame.draw.rect(pantalla, AMARILLO, (330, 158, 12, 12), border_radius=3)
            dibujar_texto("Cable: tensión", pequeno, GRIS, 348, 155)
            pygame.draw.rect(pantalla, VERDE, (455, 158, 12, 12), border_radius=3)
            dibujar_texto("Péndolas: tensión", pequeno, GRIS, 473, 155)
            pygame.draw.rect(pantalla, AZUL, (625, 158, 12, 12), border_radius=3)
            dibujar_texto("Torres: compresión", pequeno, GRIS, 643, 155)
        else:
            pygame.draw.rect(pantalla, VERDE, (330, 158, 12, 12), border_radius=3)
            dibujar_texto("Tracción", pequeno, GRIS, 348, 155)
            pygame.draw.rect(pantalla, AZUL, (409, 158, 12, 12), border_radius=3)
            dibujar_texto("Compresión", pequeno, GRIS, 427, 155)
            pygame.draw.rect(pantalla, (25, 112, 88), (514, 158, 8, 12), border_radius=2)
            pygame.draw.rect(pantalla, (33, 91, 133), (522, 158, 8, 12), border_radius=2)
            dibujar_texto("U <20%", pequeno, GRIS, 534, 155)
            pygame.draw.rect(pantalla, AMARILLO, (622, 158, 12, 12), border_radius=3)
            dibujar_texto("U ≥80%", pequeno, GRIS, 640, 155)
            pygame.draw.rect(pantalla, ROJO, (696, 158, 12, 12), border_radius=3)
            dibujar_texto("U ≥100%", pequeno, GRIS, 714, 155)
        pygame.draw.rect(pantalla, ROJO_CLARO, (779, 158, 12, 12), border_radius=3)
        dibujar_texto("Carga externa", pequeno, GRIS, 797, 155)
        if tipo_puente == "Celosía":
            pygame.draw.rect(pantalla, VIDRIO, (875, 158, 12, 12), border_radius=3)
            dibujar_texto("Reacciones", pequeno, GRIS, 893, 155)

        if tipo_puente == "Colgante":
            dibujar_puente_colgante()
        else:
            dibujar_puente()
            dibujar_reacciones()

        dibujar_vehiculo()
        if not colapso_activo:
            dibujar_carga()

        referencia_geometrica = " · punteado = sin deformar" if deformacion_amplificada else ""
        dibujar_texto(
            f"Modo: {modo_movimiento} · deformación {'×' + str(factor_amplificacion) if deformacion_amplificada else 'real'}{referencia_geometrica}",
            pequeno,
            AMARILLO,
            330,
            530
        )

        dibujar_grafica_movimiento()

        dibujar_texto("Mapa: verde tracción · azul compresión · oscuro <20% · amarillo ≥80% · rojo ≥100%" if mostrar_mapa_esfuerzos else "Mapa de esfuerzos desactivado",
                      pequeno, GRIS, 330, 548)

        estado = "¡COLAPSO!" if colapso_activo else "EN MOVIMIENTO" if simulando else "EN PAUSA"

        color_estado = ROJO if colapso_activo else VERDE if simulando else AMARILLO

        dibujar_texto(
            estado,
            texto,
            color_estado,
            330,
            572
        )
        dibujar_ficha_vehiculo()

        if tipo_puente == "Colgante":
            dibujar_inspector_colgante()
        else:
            dibujar_inspector()


    def dibujar_grafica_movimiento():
        """Respuesta espacial, evolución temporal y fuerzas internas del motor."""
        boxes = [(330, 178, 262, 112), (602, 178, 262, 112), (874, 178, 282, 112)]
        for box in boxes:
            pygame.draw.rect(pantalla, (18, 29, 43), box, border_radius=7)
            pygame.draw.rect(pantalla, PANEL_CLARO, box, 1, border_radius=7)

        # Perfil de desplazamiento vertical nodal contra posición longitudinal.
        x0, y0, width, height = boxes[0]
        dibujar_texto("PERFIL · x [m] / v [mm]", pequeno, BLANCO, x0 + 8, y0 + 6)
        left, right, top, bottom = x0 + 43, x0 + width - 8, y0 + 31, y0 + 72
        if analisis_educativo_actual:
            profile = sorted(
                ((nodos_fisicos[i][0], displacement)
                 for i, displacement in enumerate(analisis_educativo_actual["desplazamientos"])),
                key=lambda sample: sample[0],
            )
            extent_mm = max(max(abs(displacement[1]) for _, displacement in profile) * 1000, 0.05)
            extent_m = extent_mm / 1000
            for fraction in (0.0, 0.5, 1.0):
                grid_x = round(left + fraction * (right - left))
                pygame.draw.line(pantalla, (48, 64, 78), (grid_x, top), (grid_x, bottom), 1)
            zero_y = round((top + bottom) / 2)
            pygame.draw.line(pantalla, (92, 111, 127), (left, zero_y), (right, zero_y), 1)
            points = proyectar_nodos_deformados(
                tuple((x, 0.0) for x, _ in profile),
                tuple((0.0, displacement[1]) for _, displacement in profile),
                (left, zero_y),
                ((right - left) / LONGITUD_PUENTE_M, (bottom - top) / (2 * extent_m)),
                amplificada=False,
                factor_amplificacion=1,
            )
            if len(points) > 1:
                pygame.draw.lines(pantalla, VIDRIO, False, points, 2)
            for point in points:
                pygame.draw.circle(pantalla, BLANCO, point, 2)
            for fraction, label in ((0.0, "0"), (0.5, "30"), (1.0, "60")):
                label_surface = pequeno.render(label, True, GRIS)
                label_x = round(left + fraction * (right - left) - label_surface.get_width() / 2)
                pantalla.blit(label_surface, (label_x, y0 + 75))
            for ratio, label in ((0.0, f"+{extent_mm:.1f}"), (0.5, "0"), (1.0, f"−{extent_mm:.1f}")):
                label_surface = pequeno.render(label, True, GRIS)
                label_y = round(top + ratio * (bottom - top) - label_surface.get_height() / 2)
                pantalla.blit(label_surface, (x0 + 3, label_y))
            dibujar_texto(f"|v| máx. {analisis_educativo_actual['desplazamiento_vertical_maximo_m']*1000:.2f} mm", pequeno, VIDRIO, x0 + 8, y0 + height - 15)
        else:
            dibujar_texto("Sin perfil estructural", pequeno, GRIS, left, top + 20)

        # Evolución temporal de desplazamiento máximo (mm) y utilización (%).
        x0, y0, width, height = boxes[1]
        dibujar_texto("t[s] · δ[mm] U[%] ΣRy[kN] · normalizados", pequeno, BLANCO, x0 + 8, y0 + 6)
        left, right, top, bottom = x0 + 25, x0 + width - 12, y0 + 31, y0 + 72
        pygame.draw.line(pantalla, GRIS, (left, bottom), (right, bottom), 1)
        if len(historial_respuesta) > 1:
            samples = historial_respuesta[-100:]
            max_delta = max(max(s[2] for s in samples), 0.05)
            max_use = max(max(s[3] for s in samples), 0.05)
            reactions_kn = [(sample[4] + sample[5]) / 1000 for sample in samples]
            max_reaction = max(max(abs(value) for value in reactions_kn), 0.05)
            pygame.draw.lines(
                pantalla, VIDRIO, False,
                proyectar_serie_temporal(samples, 0, 2, (left, top, right, bottom), (0, max_delta)), 2,
            )
            pygame.draw.lines(
                pantalla, AMARILLO, False,
                proyectar_serie_temporal(samples, 0, 3, (left, top, right, bottom), (0, max_use)), 2,
            )
            zero_y = round(bottom - (0 - (-max_reaction)) / (2 * max_reaction) * (bottom - top))
            pygame.draw.line(pantalla, (58, 75, 89), (left, zero_y), (right, zero_y), 1)
            reaction_samples = [(sample[0], value) for sample, value in zip(samples, reactions_kn)]
            pygame.draw.lines(
                pantalla, VERDE, False,
                proyectar_serie_temporal(
                    reaction_samples, 0, 1, (left, top, right, bottom), (-max_reaction, max_reaction)
                ), 2,
            )
            dibujar_texto(f"t={samples[0][0]:.1f}s", pequeno, GRIS, left, y0 + 77)
            end_label = pequeno.render(f"{samples[-1][0]:.1f}s", True, GRIS)
            pantalla.blit(end_label, (right - end_label.get_width(), y0 + 77))
            dibujar_texto(f"δ {samples[-1][2]:.1f} mm", pequeno, VIDRIO, x0 + 8, y0 + height - 15)
            dibujar_texto(f"U {samples[-1][3]:.0%}", pequeno, AMARILLO, x0 + 91, y0 + height - 15)
            dibujar_texto(f"ΣRy {reactions_kn[-1]:+.0f} kN", pequeno, VERDE, x0 + 155, y0 + height - 15)
        else:
            dibujar_texto("Pulsa INICIAR para registrar", pequeno, GRIS, left, top + 18)

        # Cinco barras más solicitadas en el estado actual, magnitud axial en kN.
        x0, y0, width, height = boxes[2]
        dibujar_texto("FUERZA AXIAL · TOP 5 [kN]", pequeno, BLANCO, x0 + 8, y0 + 6)
        if analisis_educativo_actual:
            rankings = sorted(
                enumerate(analisis_educativo_actual["fuerzas_barras"]),
                key=lambda pair: abs(pair[1]), reverse=True,
            )[:5]
            max_force = max((abs(force) for _, force in rankings), default=1.0) or 1.0
            for row, (index, force) in enumerate(rankings):
                yy = y0 + 27 + row * 15
                dibujar_texto(f"B{index + 1:02d}", pequeno, GRIS, x0 + 8, yy)
                bar_width = round(abs(force) / max_force * 128)
                color = VERDE if force >= 0 else AZUL
                pygame.draw.rect(pantalla, color, (x0 + 42, yy + 3, bar_width, 8), border_radius=3)
                dibujar_texto(f"{force/1000:+.1f}", pequeno, color, x0 + 178, yy)
        else:
            dibujar_texto("Sin fuerzas calculadas", pequeno, GRIS, x0 + 8, y0 + 44)


    # ==========================================
    # 11. PANEL DE RESULTADOS
    # ==========================================

    def dibujar_resultados():

        dibujar_panel(305, 630, 870, 95)

        if tipo_puente == "Colgante":
            datos = analisis_colgante
            titulo_resultados = "PUENTE COLAPSADO" if colapso_activo else "ANÁLISIS DEL PUENTE COLGANTE"
            color_titulo = ROJO if colapso_activo else BLANCO
            dibujar_texto(titulo_resultados, subtitulo, color_titulo, 325, 644)
            if colapso_activo:
                dibujar_texto("Reduce la carga y pulsa REINICIAR", pequeno, ROJO, 650, 644)
            else:
                dibujar_texto(
                    f"H = wL²/(8f) · w={datos.get('w', 0):,.1f} N/m · L=40 m · f=6 m",
                    pequeno, AMARILLO, 650, 644,
                )
            dibujar_texto("CAPACIDADES DEMO", pequeno, GRIS, 325, 666)
            dibujar_texto(
                f"Reacción izq.: {datos.get('reaccion_izquierda', 0):,.0f} N",
                texto, VERDE, 325, 684,
            )
            dibujar_texto(
                f"Reacción der.: {datos.get('reaccion_derecha', 0):,.0f} N",
                texto, VERDE, 535, 684,
            )
            fuerza_neta = masa * (aceleracion if modo_movimiento == "MRUA" else 0.0)
            dibujar_texto(f"2ª ley: {fuerza_neta:,.0f} N", texto, AMARILLO, 790, 684)
            dibujar_texto(f"Velocidad: {velocidad_actual * 3.6:.1f} km/h", texto, BLANCO, 985, 684)
            dibujar_texto(f"Cable H: {datos.get('tension_horizontal', 0):,.0f} N", texto, AMARILLO, 325, 708)
            dibujar_texto(f"Péndola máx.: {datos.get('pendola_maxima', 0):,.0f} N", texto, VERDE, 535, 708)
            dibujar_texto(
                f"Torres C: {datos.get('compresion_torre_izquierda', 0):,.0f} / {datos.get('compresion_torre_derecha', 0):,.0f} N",
                texto, AZUL, 790, 708,
            )
            dibujar_texto(f"Anclaje T: {datos.get('tension_anclaje', 0):,.0f} N", texto, AMARILLO, 985, 708)
            return

        peso = masa * GRAVEDAD

        fuerza_total = peso + sum(carga["magnitud"] for carga in cargas_personalizadas)

        if analisis_celosia is None:
            reaccion_izquierda = reaccion_derecha = 0.0
            tension_maxima = compresion_maxima = 0.0
            utilizacion_maxima = 0.0
            factor_seguridad_minimo = float("inf")
        else:
            reacciones = analisis_celosia["reacciones"]
            fuerzas_barras = analisis_celosia["fuerzas_barras"]
            reaccion_izquierda = reacciones[0][1]
            reaccion_derecha = reacciones[6][1]
            tension_maxima = max((f for f in fuerzas_barras if f > 0), default=0.0)
            compresion_maxima = max((-f for f in fuerzas_barras if f < 0), default=0.0)
            utilizacion_maxima, _, _, capacidad_critica = barra_critica_actual
            fuerza_critica = barra_critica_actual[2]
            factor_seguridad_minimo = (
                capacidad_critica / abs(fuerza_critica)
                if abs(fuerza_critica) > 0.05
                else float("inf")
            )

        dibujar_texto("ANÁLISIS · ACERO S275 · Ø150 mm", subtitulo, BLANCO, 325, 644)

        if colapso_activo:
            aviso = f"COLAPSO · {causa_colapso}"
            color_aviso = ROJO
        elif utilizacion_maxima >= 1.0:
            indice_critico = barra_critica_actual[1]
            aviso = f"LÍMITE SUPERADO · BARRA {indice_critico + 1:02d}"
            color_aviso = ROJO
        elif utilizacion_maxima >= UMBRAL_ADVERTENCIA:
            indice_critico = barra_critica_actual[1]
            aviso = f"ALERTA · BARRA {indice_critico + 1:02d} AL {utilizacion_maxima:.0%}"
            color_aviso = AMARILLO
        elif analisis_educativo_actual and analisis_educativo_actual["estado"] == "advertencia":
            aviso = "ADVERTENCIA · ELEMENTO AL 80% O MÁS"
            color_aviso = AMARILLO
        else:
            aviso = "ESTRUCTURA ESTABLE · MODELO EDUCATIVO"
            color_aviso = GRIS
        dibujar_texto(aviso, pequeno, color_aviso, 690, 646)

        dibujar_texto(f"Reacción izquierda  {reaccion_izquierda:,.0f} N", texto, VERDE, 325, 675)
        dibujar_texto(f"Reacción derecha  {reaccion_derecha:,.0f} N", texto, VERDE, 600, 675)
        dibujar_texto(f"Tensión máxima  {tension_maxima:,.0f} N", texto, VERDE, 865, 675)
        dibujar_texto(f"Compresión máx.  {compresion_maxima:,.0f} N", texto, AZUL, 325, 704)
        desplazamiento_mm = (
            analisis_educativo_actual["desplazamiento_vertical_maximo_m"] * 1000
            if analisis_educativo_actual else 0.0
        )
        dibujar_texto(f"Desplazamiento máx.  {desplazamiento_mm:.2f} mm", texto, AMARILLO, 600, 704)
        fs_texto = f"∞" if math.isinf(factor_seguridad_minimo) else f"{factor_seguridad_minimo:.2f}"
        dibujar_texto(f"Uso máx. {utilizacion_maxima:.0%} · FS {fs_texto}", texto, color_aviso, 865, 704)


    def agregar_carga(posicion_x=None):
        nonlocal carga_seleccionada
        if len(cargas_personalizadas) >= 5:
            return False
        if posicion_x is None:
            posiciones_candidatas = [
                730, 610, 850, 490, 970, 370, 1090,
                430, 550, 670, 790, 910, 1030,
            ]
            posicion_x = next(
                (
                    candidata for candidata in posiciones_candidatas
                    if all(abs(candidata - carga["x"]) >= 45 for carga in cargas_personalizadas)
                ),
                730.0,
            )

        cargas_personalizadas.append({
            "x": max(370.0, min(1090.0, float(posicion_x))),
            "magnitud": 5000.0,
            "angulo": 270.0,
        })
        carga_seleccionada = len(cargas_personalizadas) - 1
        return True


    def carga_bajo_puntero(punto):
        coincidencias = []
        for indice, carga in enumerate(cargas_personalizadas):
            angulo_rad = math.radians(carga["angulo"])
            punta = punto_aplicacion_carga(carga)
            cola = (
                punta[0] - math.cos(angulo_rad) * 58,
                punta[1] + math.sin(angulo_rad) * 58,
            )
            distancia = distancia_a_segmento(punto, cola, punta)
            if distancia <= 13:
                coincidencias.append((distancia, indice))
        return min(coincidencias)[1] if coincidencias else None


    # ==========================================
    # 12. DETECTAR CLICS
    # ==========================================

    def manejar_clic(posicion_mouse):

        nonlocal masa
        nonlocal tipo_vehiculo
        nonlocal velocidad
        nonlocal aceleracion
        nonlocal carga_seleccionada
        nonlocal simulando
        nonlocal posicion_vehiculo
        nonlocal velocidad_actual
        nonlocal rotacion_rueda_rad
        nonlocal tiempo_simulacion
        nonlocal historial_movimiento
        nonlocal registrar_descarga_final
        nonlocal colapso_activo
        nonlocal colapso_progreso
        nonlocal causa_colapso
        nonlocal punto_colapso_x

        x, y = posicion_mouse
        carga_actual = (
            cargas_personalizadas[carga_seleccionada]
            if carga_seleccionada is not None
            else None
        )

        # Selector de tipo de vehículo. Ajustar la masa manual activa Personalizado.
        if 628 <= y <= 662 and 45 <= x <= 255:
            if simulando:
                return
            opciones = list(masas_vehiculos)
            tipo_vehiculo = opciones[(opciones.index(tipo_vehiculo) + 1) % len(opciones)]
            masa = masas_vehiculos[tipo_vehiculo]
            selected_spec = obtener_especificacion_vehiculo()
            selected_profile = perfil_para_clave(clave_visual_vehiculo())
            rear_extent = selected_spec.longitud_m - selected_profile.voladizo_delantero_m
            posicion_vehiculo = 730 + (rear_extent - selected_profile.voladizo_delantero_m) * 6
            velocidad_actual = 0.0
            rotacion_rueda_rad = 0.0
            tiempo_simulacion = 0.0
            registrar_descarga_final = False
            historial_movimiento.clear()
            historial_respuesta.clear()
            return

        # Masa

        if 197 <= y <= 225:

            if 175 <= x <= 210:
                masa = max(500, masa - 100)

            elif 220 <= x <= 255:
                masa += 100

        # Velocidad

        elif 257 <= y <= 285:

            if 175 <= x <= 210:
                velocidad = max(0, velocidad - 5)

            elif 220 <= x <= 255:
                velocidad += 5

        # Aceleracion

        elif 317 <= y <= 345 and modo_movimiento == "MRUA":

            if 175 <= x <= 210:
                aceleracion = max(0, aceleracion - 0.5)

            elif 220 <= x <= 255:
                aceleracion += 0.5

        # Magnitud de la carga seleccionada.

        elif 377 <= y <= 405:

            if carga_actual and 175 <= x <= 210:
                carga_actual["magnitud"] = max(0, carga_actual["magnitud"] - 500)

            elif carga_actual and 220 <= x <= 255:
                carga_actual["magnitud"] += 500

        # Dirección de la carga seleccionada, medida desde el eje +X.
        elif 437 <= y <= 465:

            if carga_actual and 175 <= x <= 210:
                carga_actual["angulo"] = (carga_actual["angulo"] - 5) % 360

            elif carga_actual and 220 <= x <= 255:
                carga_actual["angulo"] = (carga_actual["angulo"] + 5) % 360

        # Añadir una carga o eliminar la que está seleccionada.
        elif 486 <= y <= 517:
            if 45 <= x <= 145:
                agregar_carga()
            elif 155 <= x <= 255 and carga_actual:
                del cargas_personalizadas[carga_seleccionada]
                if cargas_personalizadas:
                    carga_seleccionada = min(
                        carga_seleccionada, len(cargas_personalizadas) - 1
                    )
                else:
                    carga_seleccionada = None

        # Iniciar

        elif 526 <= y <= 558:

            if 45 <= x <= 145:
                if not colapso_activo:
                    spec = obtener_especificacion_vehiculo()
                    limite_salida = 1090 + abs(min(spec.posiciones_ejes_m)) * 12
                    if tiempo_simulacion <= 0.0 or posicion_vehiculo > limite_salida:
                        posicion_vehiculo = 370 + abs(min(spec.posiciones_ejes_m)) * 12
                        velocidad_actual = 0.0
                        rotacion_rueda_rad = 0.0
                        tiempo_simulacion = 0.0
                        historial_movimiento.clear()
                        historial_respuesta.clear()
                        registrar_descarga_final = False
                    simulando = True
                    if modo_movimiento == "MRU" and velocidad_actual <= 0:
                        velocidad_actual = velocidad / 3.6

        # Pausar

            elif 155 <= x <= 255:
                simulando = False

        # Reiniciar

        elif 568 <= y <= 600:

            if 45 <= x <= 255:

                simulando = False

                posicion_vehiculo = 370

                velocidad_actual = 0
                rotacion_rueda_rad = 0.0
                tiempo_simulacion = 0.0
                historial_movimiento.clear()
                historial_respuesta.clear()
                registrar_descarga_final = False
                colapso_activo = False
                colapso_progreso = 0.0
                causa_colapso = ""
                punto_colapso_x = None


    def repartir_carga_nodal(cargas_nodos, posicion_x, fuerza_x, fuerza_y):
        posicion_relativa = max(0.0, min(6.0, (posicion_x - 370) / 120))
        nodo_izquierdo = int(posicion_relativa)
        nodo_derecho = min(nodo_izquierdo + 1, 6)
        fraccion = posicion_relativa - nodo_izquierdo
        for nodo, proporcion in (
            (nodo_izquierdo, 1 - fraccion),
            (nodo_derecho, fraccion),
        ):
            if proporcion == 0:
                continue
            fx_anterior, fy_anterior = cargas_nodos.get(nodo, (0.0, 0.0))
            cargas_nodos[nodo] = (
                fx_anterior + fuerza_x * proporcion,
                fy_anterior + fuerza_y * proporcion,
            )

    # ==========================================
    # 13. BUCLE PRINCIPAL
    # ==========================================

    ejecutando = True

    while ejecutando:

        tiempo = reloj.tick(60) / 1000

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:

                ejecutando = False

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_m:
                    modo_movimiento = "MRU"
                    aceleracion = 0.0
                    velocidad_actual = velocidad / 3.6
                elif evento.key == pygame.K_a:
                    modo_movimiento = "MRUA"
                    aceleracion = max(0.5, aceleracion)

            if evento.type == pygame.MOUSEBUTTONDOWN:

                if evento.button == 1:
                    mouse_x, mouse_y = evento.pos
                    if 45 <= mouse_x <= 147 and 670 <= mouse_y <= 694:
                        deformacion_amplificada = not deformacion_amplificada
                    elif 153 <= mouse_x <= 255 and 670 <= mouse_y <= 694:
                        mostrar_mapa_esfuerzos = not mostrar_mapa_esfuerzos
                    elif 45 <= mouse_x <= 255 and 702 <= mouse_y <= 718:
                        arrastrando_control_visual = True
                        factor_amplificacion = max(1, min(500, round(1 + (mouse_x - 48) / 204 * 499)))
                    elif 850 <= mouse_x <= 955 and 123 <= mouse_y <= 153:
                        modo_movimiento = "MRU"
                        aceleracion = 0.0
                        velocidad_actual = velocidad / 3.6
                    elif 965 <= mouse_x <= 1075 and 123 <= mouse_y <= 153:
                        modo_movimiento = "MRUA"
                        aceleracion = max(0.5, aceleracion)
                    elif 330 <= mouse_x <= 1130 and 350 <= mouse_y <= 455:
                        seleccion_en_pantalla = carga_bajo_puntero(evento.pos)
                        if seleccion_en_pantalla is not None:
                            carga_seleccionada = seleccion_en_pantalla
                            desplazamiento_arrastre = (
                                mouse_x - cargas_personalizadas[carga_seleccionada]["x"]
                            )
                        else:
                            if not agregar_carga(mouse_x):
                                continue
                            desplazamiento_arrastre = 0.0
                        arrastrando_carga = True
                    else:
                        manejar_clic(evento.pos)

            elif evento.type == pygame.MOUSEMOTION:
                if arrastrando_control_visual:
                    factor_amplificacion = max(1, min(500, round(1 + (evento.pos[0] - 48) / 204 * 499)))
                elif arrastrando_carga and carga_seleccionada is not None:
                    cargas_personalizadas[carga_seleccionada]["x"] = max(
                        370.0,
                        min(1090.0, float(evento.pos[0]) - desplazamiento_arrastre),
                    )

            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                arrastrando_carga = False
                arrastrando_control_visual = False

        # Movimiento del vehiculo

        if simulando:

            velocidad_objetivo = velocidad / 3.6

            aceleracion_efectiva = aceleracion if modo_movimiento == "MRUA" else 0.0
            velocidad_anterior = velocidad_actual
            velocidad_actual += aceleracion_efectiva * tiempo

            velocidad_actual = min(
                velocidad_actual,
                velocidad_objetivo
            )

            radio_rueda = obtener_especificacion_vehiculo().radio_rueda_m
            rotacion_rueda_rad = (rotacion_rueda_rad +
                                  (velocidad_anterior + velocidad_actual) * 0.5 * tiempo / radio_rueda) % math.tau

            posicion_vehiculo += velocidad_actual * tiempo * 12
            tiempo_simulacion += tiempo
            historial_movimiento.append((tiempo_simulacion, (posicion_vehiculo - 370) / 12, velocidad_actual, aceleracion_efectiva))
            if len(historial_movimiento) > 300:
                del historial_movimiento[:-300]

            # Detener tras sacar el último eje del tablero. Mantener la posición
            # fuera del puente permite que el solver elástico muestre la descarga.
            vehiculo_en_salida = obtener_especificacion_vehiculo()
            limite_salida = 1090 + abs(min(vehiculo_en_salida.posiciones_ejes_m)) * 12
            if posicion_vehiculo > limite_salida:
                simulando = False
                velocidad_actual = 0
                registrar_descarga_final = True

        # Las cargas sobre el tablero se convierten en cargas nodales
        # equivalentes, repartidas entre los dos nodos inferiores vecinos.
        spec_vehiculo = obtener_especificacion_vehiculo()
        estado_vehiculo = EstadoVehiculo(
            (posicion_vehiculo - 370) / 12,
            velocidad_actual,
            aceleracion if modo_movimiento == "MRUA" else 0.0,
        )
        cargas_vehiculo = {}
        # La vista de fuerzas por nodo conserva el detalle del vehículo completo;
        # la ruta educativa usa la distribución física por ejes.
        cargas_vehiculo[0] = (0.0, 0.0)
        cargas_por_fuente_actuales = {"Vehículo": cargas_vehiculo}
        for indice_carga, carga in enumerate(cargas_personalizadas):
            cargas_usuario = {}
            angulo_rad = math.radians(carga["angulo"])
            repartir_carga_nodal(
                cargas_usuario,
                carga["x"],
                carga["magnitud"] * math.cos(angulo_rad),
                carga["magnitud"] * math.sin(angulo_rad),
            )
            cargas_por_fuente_actuales[f"Carga {indice_carga + 1}"] = cargas_usuario

        cargas_usuario_nodos = {}
        for nombre_fuente, cargas_fuente in cargas_por_fuente_actuales.items():
            if nombre_fuente == "Vehículo":
                continue
            for nodo, (fuerza_x, fuerza_y) in cargas_fuente.items():
                fx_anterior, fy_anterior = cargas_usuario_nodos.get(nodo, (0.0, 0.0))
                cargas_usuario_nodos[nodo] = (fx_anterior + fuerza_x, fy_anterior + fuerza_y)

        cargas_nodos = {}
        for cargas_fuente in cargas_por_fuente_actuales.values():
            for nodo, (fuerza_x, fuerza_y) in cargas_fuente.items():
                fx_anterior, fy_anterior = cargas_nodos.get(nodo, (0.0, 0.0))
                cargas_nodos[nodo] = (fx_anterior + fuerza_x, fy_anterior + fuerza_y)

        fuerza_total = masa * GRAVEDAD + sum(
            carga["magnitud"] for carga in cargas_personalizadas
        )
        cargas_nodos_actuales = cargas_nodos
        analisis_colgante = calcular_analisis_colgante()

        if tipo_puente == "Colgante":
            analisis_celosia = None
            analisis_educativo_actual = None
            barra_critica_actual = (0.0, None, 0.0, CAPACIDAD_TENSION_DEMO)
        else:
            analisis_educativo_actual = analizar_estado_celosia(
                nodos_fisicos,
                barras_puente,
                disenos_barras,
                cargas_usuario_nodos,
                {0: (True, True), 6: (False, True)},
                spec_vehiculo,
                estado_vehiculo,
            )
            analisis_celosia = analisis_educativo_actual
            cargas_nodos_actuales = analisis_educativo_actual["cargas_nodales_combinadas_n"]
            indice_critico = analisis_educativo_actual["elemento_mas_solicitado"]["indice"]
            fuerza_critica = analisis_celosia["fuerzas_barras"][indice_critico]
            capacidad_estimada = (
                abs(fuerza_critica) / analisis_educativo_actual["utilizacion_maxima"]
                if analisis_educativo_actual["utilizacion_maxima"] > 0 else float("inf")
            )
            barra_critica_actual = (
                analisis_educativo_actual["utilizacion_maxima"], indice_critico,
                fuerza_critica, capacidad_estimada,
            )
            if simulando or registrar_descarga_final:
                historial_respuesta.append((
                    tiempo_simulacion,
                    (posicion_vehiculo - 370) / 12,
                    analisis_educativo_actual["desplazamiento_vertical_maximo_m"] * 1000,
                    analisis_educativo_actual["utilizacion_maxima"],
                    analisis_educativo_actual["reacciones"][0][1],
                    analisis_educativo_actual["reacciones"][6][1],
                    tuple(analisis_educativo_actual["fuerzas_barras"]),
                ))
                if len(historial_respuesta) > 600:
                    del historial_respuesta[:-600]
                registrar_descarga_final = False

        if not colapso_activo and simulando:
            if tipo_puente == "Colgante":
                demandas = [
                    ("Cable", analisis_colgante["tension_horizontal"], CAPACIDAD_CABLE_DEMO),
                    ("Péndola", analisis_colgante["pendola_maxima"], CAPACIDAD_PENDOLA_DEMO),
                    ("Torre", max(
                        analisis_colgante["compresion_torre_izquierda"],
                        analisis_colgante["compresion_torre_derecha"],
                    ), CAPACIDAD_TORRE_DEMO),
                    ("Anclaje", analisis_colgante["tension_anclaje"], CAPACIDAD_ANCLAJE_DEMO),
                ]
                elemento, demanda, capacidad = max(demandas, key=lambda fila: fila[1] / fila[2])
                if demanda >= capacidad:
                    if elemento == "Péndola":
                        indice_falla = max(
                            range(len(analisis_colgante["fuerzas_pendolas"])),
                            key=analisis_colgante["fuerzas_pendolas"].__getitem__,
                        )
                        posicion_falla = POSICIONES_PENDOLAS_PX[indice_falla]
                    elif elemento == "Torre":
                        posicion_falla = (
                            490 if analisis_colgante["compresion_torre_izquierda"]
                            >= analisis_colgante["compresion_torre_derecha"] else 970
                        )
                    elif elemento == "Anclaje":
                        posicion_falla = (
                            350 if analisis_colgante["compresion_torre_izquierda"]
                            >= analisis_colgante["compresion_torre_derecha"] else 1090
                        )
                    else:
                        posicion_falla = 730
                    iniciar_colapso(
                        f"{elemento}: {demanda:,.0f} N supera {capacidad:,.0f} N",
                        posicion_falla,
                    )
            elif barra_critica_actual[0] >= 1.0:
                _, indice, fuerza, capacidad = barra_critica_actual
                inicio, fin = barras_puente[indice]
                posicion_falla = (nodos_pantalla[inicio][0] + nodos_pantalla[fin][0]) / 2
                iniciar_colapso(
                    f"Barra {indice + 1}: {abs(fuerza):,.0f} N supera {capacidad:,.0f} N",
                    posicion_falla,
                )

        # Dibujar interfaz

        pantalla.fill(FONDO)

        dibujar_encabezado()

        dibujar_controles()

        dibujar_area_simulacion()

        dibujar_resultados()

        pygame.display.flip()


    # ==========================================
    # 14. CERRAR PYGAME
    # ==========================================

    pygame.quit()

if __name__ == "__main__":
    main()


