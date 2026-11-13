
from fisica.vectors import (
    componentes_vector,
    magnitud_vector,
    sumar_vectores,
    resultante_vectores
)


# PRUEBA 1: DESCOMPOSICION

fx, fy = componentes_vector(1000, 30)

print("PRUEBA 1: COMPONENTES")

print("Fx:", round(fx, 2), "N")
print("Fy:", round(fy, 2), "N")


# PRUEBA 2: MAGNITUD

magnitud = magnitud_vector(3, 4)

print("\nPRUEBA 2: MAGNITUD")

print("Resultado:", magnitud)


# PRUEBA 3: SUMA DE VECTORES

vectores = [
    (100, 200),
    (300, 100),
    (-50, 150)
]

resultado = sumar_vectores(vectores)

print("\nPRUEBA 3: SUMA")

print("Rx:", resultado[0])
print("Ry:", resultado[1])


# PRUEBA 4: RESULTANTE

resultado_final = resultante_vectores(vectores)

print("\nPRUEBA 4: RESULTANTE")

print("Magnitud:", round(resultado_final[0], 2))
print("Angulo:", round(resultado_final[1], 2))
print("Rx:", resultado_final[2])
print("Ry:", resultado_final[3])