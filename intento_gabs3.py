import cv2
import numpy as np



def reducir_grises(imagen_gray, niveles=8):
    factor = 256 // niveles
    return (imagen_gray // factor) * factor

def detectar_patron_e_iris(frame):
    if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
        print("No llega imagen")
        return None

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    gray_eq = cv2.equalizeHist(gray)
    gray_reducida = reducir_grises(gray_eq, 8)

    green = frame[:, :, 1]
    blur = cv2.GaussianBlur(green, (5, 5), 1.0)
    binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 7)
    contornos, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    puntos = []
    for c in contornos:
        area = cv2.contourArea(c)
        if 5 < area < 100:
            perimetro = cv2.arcLength(c, True)
            circularidad = 4 * np.pi * area / (perimetro ** 2 + 1e-6)
            if 0.6 < circularidad < 1.3:
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    puntos.append((cx, cy))

    if not puntos:
        return None
    
    puntos_filtrados = puntos

    if len(puntos_filtrados) < 5:
        return None

    xs, ys = zip(*puntos_filtrados)
    cx_patron = int(np.mean(xs))
    cy_patron = int(np.mean(ys))
    radios = [np.sqrt((x - cx_patron)**2 + (y - cy_patron)**2) for (x, y) in puntos_filtrados]
    r_patron = int(1.2*np.mean(radios))

    roi_r = int(1.2 * r_patron)
    h, w = frame.shape[:2]
    margin = 10
    x1 = max(cx_patron - roi_r - margin, 0)
    y1 = max(cy_patron - roi_r - margin, 0)
    x2 = min(cx_patron + roi_r + margin, w)
    y2 = min(cy_patron + roi_r + margin, h)
    coords_roi = (x1, y1, x2, y2)
    roi_img = frame[y1:y2, x1:x2]

    roi_gray = gray_reducida[y1:y2, x1:x2]
    _, mask = cv2.threshold(roi_gray, 70, 255, cv2.THRESH_BINARY_INV)
    contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    mejor_contorno = None
    mejor_radio = 0
    cx_iris, cy_iris = None, None

    for c in contornos:
        area = cv2.contourArea(c)
        if area > 300:
            (x, y), radius = cv2.minEnclosingCircle(c)
            circularidad = 4 * np.pi * area / (cv2.arcLength(c, True) ** 2 + 1e-6)
            if 0.4 < circularidad < 1.2 and 20 < radius < 200 and radius > mejor_radio:
                mejor_contorno = c
                mejor_radio = radius
                cx_iris, cy_iris = int(x), int(y)

    if mejor_contorno is not None:
        cx_abs = cx_iris + x1
        cy_abs = cy_iris + y1
        r_abs = int(mejor_radio)
        return (cx_patron, cy_patron, r_patron, cx_abs, cy_abs, r_abs, roi_img, coords_roi)
    else:
        return None
    


def dibujar_circulos_y_cuadrados(frame, cx_patron, cy_patron, r_patron, cx_abs, cy_abs, r_abs):
    # Dibujar los círculos y cuadrado sobre la imagen
    imagen_con_circulos = frame.copy()

    # Círculo verde para el patrón
    cv2.circle(imagen_con_circulos, (cx_patron, cy_patron), r_patron, (0, 255, 0), 2)
    # Círculo rojo para el iris
    cv2.circle(imagen_con_circulos, (cx_abs, cy_abs), r_abs, (0, 0, 255), 2)

    # Cuadrado alrededor del patrón
    cv2.rectangle(imagen_con_circulos, (cx_patron - r_patron, cy_patron - r_patron), 
                  (cx_patron + r_patron, cy_patron + r_patron), (255, 0, 0), 2)

    # Cuadrado alrededor del iris
    cv2.rectangle(imagen_con_circulos, (cx_abs - r_abs, cy_abs - r_abs), 
                  (cx_abs + r_abs, cy_abs + r_abs), (255, 255, 0), 2)

    # Mostrar la imagen con círculos y cuadrados
    cv2.imshow("Imagen con círculos y cuadrados", imagen_con_circulos)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# Ruta de la imagen
ruta_imagen = 'ojo_izquierdo_gabs.jpg'

# Cargar la imagen
frame = cv2.imread(ruta_imagen)

# Verificar si la imagen se cargó correctamente
if frame is None:
    print("No se pudo cargar la imagen.")
else:
    # Llamar a la función para detectar el patrón y el iris
    resultado = detectar_patron_e_iris(frame)

    if resultado is not None:
        # Si se detectó el patrón y el iris, extraer los resultados
        cx_patron, cy_patron, r_patron, cx_abs, cy_abs, r_abs, roi_img, coords_roi = resultado
        print(f"Centro del patrón: ({cx_patron}, {cy_patron}), Radio del patrón: {r_patron}")
        print(f"Centro del iris: ({cx_abs}, {cy_abs}), Radio del iris: {r_abs}")
        
        # Llamar a la función para dibujar los círculos y cuadrados
        dibujar_circulos_y_cuadrados(frame, cx_patron, cy_patron, r_patron, cx_abs, cy_abs, r_abs)
    else:
        print("No se detectó el patrón o el iris.")