import cv2
import os
import numpy as np
from Pantallas.Generar_Mapa_Elevacion import generar_mapas_y_sacar_numeros

def generar_mapa_topografico(imagen_entrada):
    """
    Genera y renombra mapas topográficos (tangencial y diferencia), adaptándolos a 300x300 sin distorsión
    ni pérdida de calidad: se escala solo si es necesario y se centra en un canvas blanco.
    """
    if not os.path.exists(imagen_entrada):
        print(f"[ERROR] Imagen no encontrada: {imagen_entrada}")
        return []

    # Generar los mapas
    generar_mapas_y_sacar_numeros(imagen_entrada)

    # Determinar lado
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

    for original, nuevo_path in archivos_generados.items():
        if os.path.exists(original):
            os.rename(original, nuevo_path)

            # Leer imagen
            img = cv2.imread(nuevo_path)
            h, w = img.shape[:2]

            # Solo escalar si es mayor a 300x300
            if h > 300 or w > 300:
                scale = min(300 / w, 300 / h)
                new_w, new_h = int(w * scale), int(h * scale)
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                h, w = img.shape[:2]

            # Canvas blanco
            canvas = np.full((300, 300, 3), 200, dtype=np.uint8)
            x_offset = (300 - w) // 2
            y_offset = (300 - h) // 2

            # Insertar imagen centrada
            canvas[y_offset:y_offset + h, x_offset:x_offset + w] = img
            cv2.imwrite(nuevo_path, canvas)
            rutas_finales.append(nuevo_path)
            print(f"[✔] Guardado sin pérdida: {nuevo_path}")
        else:
            print(f"[⚠] No se encontró: {original}")

    return rutas_finales