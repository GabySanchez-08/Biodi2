import cv2
import os
from Pantallas.Generar_Mapa_Elevacion import generar_mapa_elevacion  # Importamos la función generar_mapa_elevacion

def generar_mapa_topografico(imagen_entrada, salida_base):
    """
    Genera 3 mapas topográficos con distintos esquemas de color.
    Uno de los mapas es generado con la función de mapa de elevación.
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
    ]

    salidas = []
    

    # Leer la imagen
    img_color = img

    # Llamar a la función para generar el mapa de elevación
    mapa_elevacion_path = generar_mapa_elevacion(img_color)

    # Guardar el mapa de elevación con un nombre adecuado
    mapa_elevacion_salida = f"{salida_base}_elevacion.jpg"
    mapa_elevacion = cv2.imread(mapa_elevacion_path)
    cv2.imwrite(mapa_elevacion_salida, mapa_elevacion)

    salidas.append(mapa_elevacion_salida)

    # Generamos los otros mapas con esquemas de color
    for i, cmap in enumerate(colormaps, start=1):
        procesada = cv2.applyColorMap(gray, cmap)
        salida = f"{salida_base}_mapa{i}.jpg"
        cv2.imwrite(salida, procesada)
        salidas.append(salida)

    return salidas