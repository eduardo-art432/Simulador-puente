"""Herramientas de física para el simulador."""

from .equilibrium import reacciones_apoyos
from .truss import resolver_celosia
from .stiffness import resolver_celosia_rigidez
from .materials import MATERIALES_EDUCATIVOS, Material, Seccion, propiedades_elemento
from .failure import evaluar_elemento
from .vehicles import (
    EstadoVehiculo,
    EspecificacionVehiculo,
    VEHICULOS_EDUCATIVOS,
    distribuir_cargas_ejes,
)
from .structural import DisenoBarra, analizar_estado_celosia, buscar_primera_falla
from .visualization import color_por_utilizacion, proyectar_ejes_px, proyectar_nodos_deformados
from .vectors import (
    angulo_vector,
    componentes_vector,
    magnitud_vector,
    resultante_vectores,
    sumar_vectores,
)

__all__ = [
    "angulo_vector",
    "componentes_vector",
    "evaluar_elemento",
    "EstadoVehiculo",
    "EspecificacionVehiculo",
    "magnitud_vector",
    "MATERIALES_EDUCATIVOS",
    "Material",
    "reacciones_apoyos",
    "resolver_celosia",
    "resolver_celosia_rigidez",
    "Seccion",
    "VEHICULOS_EDUCATIVOS",
    "distribuir_cargas_ejes",
    "DisenoBarra",
    "analizar_estado_celosia",
    "buscar_primera_falla",
    "color_por_utilizacion",
    "proyectar_ejes_px",
    "proyectar_nodos_deformados",
    "propiedades_elemento",
    "resultante_vectores",
    "sumar_vectores",
]
