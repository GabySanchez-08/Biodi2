import cv2
import os
from Pantallas.Generar_Mapa_Elevacion import generar_mapas_y_sacar_numeros
from Pantallas.Generar_Parametros import obtener_parametros_completos

def generar_mapa_topografico(imagen_entrada):
    """
    Genera mapas topográficos (tangencial y diferencia) y los renombra según el ojo (derecho o izquierdo).
    Devuelve el DataFrame de parámetros correspondientes al ojo evaluado.
    """
    if not os.path.exists(imagen_entrada):
        print(f"[ERROR] Imagen no encontrada: {imagen_entrada}")
        return None

    # Generar los mapas base
    tang_map, elev_map = generar_mapas_y_sacar_numeros(imagen_entrada)
    df_parametros = obtener_parametros_completos(elev_map, tang_map)

    # Detectar lado del ojo
    if "derecho" in imagen_entrada.lower():
        lado = "derecho"
    elif "izquierdo" in imagen_entrada.lower():
        lado = "izquierdo"
    else:
        lado = "desconocido"

    # Renombrar archivos de imagen
    archivos_generados = {
        "mapa_tangencial.jpg": f"mapa_tangencial_{lado}.jpg",
        "mapa_diferencia.jpg": f"mapa_diferencia_{lado}.jpg"
    }

    for original, nuevo_nombre in archivos_generados.items():
        if os.path.exists(original):
            os.rename(original, nuevo_nombre)
            print(f"[✔] Renombrado como: {nuevo_nombre}")
        else:
            print(f"[⚠] No se encontró: {original}")

    return df_parametros