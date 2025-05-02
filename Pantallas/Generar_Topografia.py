import cv2

def generar_mapa_topografico(imagen_entrada, salida):
    try:
        img = cv2.imread(imagen_entrada)
        if img is None:
            return None
        # Simulación de procesamiento: convertir a escala de grises
        img_procesada = cv2.applyColorMap(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLORMAP_JET)
        cv2.imwrite(salida, img_procesada)
        return salida
    except Exception as e:
        print(f"[ERROR] Al generar topografía: {e}")
        return None
    
    