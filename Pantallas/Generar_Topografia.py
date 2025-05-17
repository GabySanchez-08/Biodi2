import cv2
import os

def generar_mapa_topografico(imagen_entrada, salida_base):
    """
    Simula la generación de 4 mapas topográficos con distintos esquemas de color.
    """
    if not os.path.exists(imagen_entrada):
        print(f"[ERROR] Imagen no encontrada: {imagen_entrada}")
        return []

    img = cv2.imread(imagen_entrada)
    if img is None:
        print("[ERROR] No se pudo leer la imagen.")
        return []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    colormaps = [
        cv2.COLORMAP_JET,
        cv2.COLORMAP_HOT,
        cv2.COLORMAP_OCEAN,
        cv2.COLORMAP_SUMMER
    ]

    salidas = []
    for i, cmap in enumerate(colormaps, start=1):
        procesada = cv2.applyColorMap(gray, cmap)
        salida = f"{salida_base}_mapa{i}.jpg"
        cv2.imwrite(salida, procesada)
        salidas.append(salida)

    return salidas