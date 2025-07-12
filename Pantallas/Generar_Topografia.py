import cv2
import os
from Pantallas.Generar_Mapa_Elevacion import generar_mapas_y_sacar_numeros

def generar_mapa_topografico(imagen_entrada):
    """
    Genera mapas topográficos (tangencial y diferencia) y los renombra según el ojo (derecho o izquierdo).
    No se modifican las dimensiones ni se centra en canvas.
    """
    if not os.path.exists(imagen_entrada):
        print(f"[ERROR] Imagen no encontrada: {imagen_entrada}")
        return []

    # Generar los mapas base
    generar_mapas_y_sacar_numeros(imagen_entrada)

    # Detectar lado del ojo
    if "derecho" in imagen_entrada.lower():
        lado = "derecho"
    elif "izquierdo" in imagen_entrada.lower():
        lado = "izquierdo"
    else:
        lado = "desconocido"

    archivos_generados = {
        "mapa_tangencial.jpg": f"mapa_tangencial_{lado}.jpg",
        "mapa_diferencia.jpg": f"mapa_diferencia_{lado}.jpg"
    }

    rutas_finales = []

    for original, nuevo_nombre in archivos_generados.items():
        if os.path.exists(original):
            os.rename(original, nuevo_nombre)
            rutas_finales.append(nuevo_nombre)
            print(f"[✔] Renombrado como: {nuevo_nombre}")
        else:
            print(f"[⚠] No se encontró: {original}")

    return rutas_finales