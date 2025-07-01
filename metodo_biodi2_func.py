import cv2
import matplotlib.pyplot as plt
import os 

def metodo_biodi2(image_path: str, mostrar_resultados: bool = True):
    import cv2
    import numpy as np
    from scipy.ndimage import gaussian_filter
    from sklearn.cluster import DBSCAN, KMeans
    from matplotlib import pyplot as plt
    import os

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"No se encontró la imagen: {image_path}")

    img_color = cv2.imread(image_path)
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    img_eq = cv2.equalizeHist(img)
    img_inv = cv2.bitwise_not(img_eq)
    img_blur = gaussian_filter(img_inv, sigma=0.8)

    circles = cv2.HoughCircles(
        img_blur.astype(np.uint8),
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=10,
        param1=30,
        param2=8,
        minRadius=3,
        maxRadius=5
    )

    if circles is None:
        raise RuntimeError("No se detectaron círculos Hough para usar como template.")

    circles = np.uint16(np.around(circles))
    x0, y0, r0 = circles[0][0]
    patch_size = 2 * r0 + 1
    template = img_blur[y0 - r0:y0 + r0 + 1, x0 - r0:x0 + r0 + 1].astype(np.float32)
    template = (template - template.mean()) / (template.std() + 1e-5)

    # Template Matching
    result = cv2.matchTemplate(img_blur.astype(np.float32), template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.52
    loc = np.where(result >= threshold)
    puntos = list(zip(*loc[::-1]))

    # Agrupar detecciones cercanas (clustering)
    db = DBSCAN(eps=5, min_samples=1).fit(puntos)
    labels = db.labels_
    puntos_filtrados = []

    for i in np.unique(labels):
        cluster = np.array([p for p, l in zip(puntos, labels) if l == i])
        centroid = cluster.mean(axis=0)
        puntos_filtrados.append(centroid)

    puntos_filtrados = np.array(puntos_filtrados)

    # Corregir orientación usando KMeans para estimar centro
    kmeans = KMeans(n_clusters=1).fit(puntos_filtrados)
    centro = kmeans.cluster_centers_[0]
    puntos_corr = puntos_filtrados - centro

    # Dibujar los puntos en la imagen original
    img_resultado = img_color.copy()  # Hacer una copia de la imagen original para dibujar

    for punto in puntos_filtrados:
        cv2.circle(img_resultado, tuple(punto.astype(int)), 5, (0, 0, 255), -1)  # Puntos rojos

    if mostrar_resultados:
        plt.figure(figsize=(8, 8))
        plt.imshow(img_resultado)
        plt.title("Imagen con puntos detectados")
        plt.axis("off")
        plt.show()

    return img_resultado  # Devolver la imagen modificada con los puntos



# Ruta de la imagen a probar
image_path = "ruta/a/tu/imagen.jpg"  # Reemplaza con la ruta de tu imagen

# Asegúrate de que la imagen exista
if not os.path.exists(image_path):
    print(f"Error: No se encontró la imagen en la ruta {image_path}")
else:
    # Llamar a la función metodo_biodi2
    img_resultado = metodo_biodi2(image_path, mostrar_resultados=True)

    # Mostrar la imagen con los puntos detectados
    plt.figure(figsize=(8, 8))
    plt.imshow(cv2.cvtColor(img_resultado, cv2.COLOR_BGR2RGB))  # Convertir BGR a RGB para mostrar correctamente
    plt.title("Imagen con puntos detectados")
    plt.axis("off")
    plt.show()