
import numpy as np
import matplotlib.pyplot as plt
import cv2
from scipy.interpolate import griddata
from scipy.optimize import least_squares
from scipy.ndimage import gaussian_filter
from sklearn.cluster import DBSCAN, KMeans

def generar_mapa_elevacion(img_color):
    """
    Recibe una imagen de entrada (numpy array) y retorna una figura de matplotlib
    con el mapa de elevación corneal interpolado.
    """
    img = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)

    # Paso 1: Ecualización e inversión
    img_eq = cv2.equalizeHist(img)
    img_inv = cv2.bitwise_not(img_eq)

    # Paso 2: Suavizado
    img_blur = gaussian_filter(img_inv, sigma=0.8)

    # Paso 3: HoughCircles para template
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
        raise RuntimeError("No se detectaron círculos.")

    circles = np.uint16(np.around(circles))
    x0, y0, r0 = circles[0][0]
    template = img_blur[y0 - r0:y0 + r0 + 1, x0 - r0:x0 + r0 + 1].astype(np.float32)
    template = (template - template.mean()) / (template.std() + 1e-5)

    # Paso 4: Template matching
    img_norm = img_blur.astype(np.float32)
    img_norm = (img_norm - img_norm.mean()) / (img_norm.std() + 1e-5)
    result = cv2.matchTemplate(img_norm, template, cv2.TM_CCOEFF_NORMED)

    threshold = 0.55
    ys, xs = np.where(result >= threshold)
    points = list(zip(xs, ys))

    # Paso 5: Agrupamiento DBSCAN
    clustering = DBSCAN(eps=r0, min_samples=1).fit(np.array(points))
    labels = clustering.labels_
    unique_labels = np.unique(labels)

    # Paso 6: Offset
    offset = (template.shape[1] // 2, template.shape[0] // 2)
    corrected_points = []
    for lbl in unique_labels:
        pts = np.array(points)[labels == lbl]
        mean_pt = pts.mean(axis=0)
        corrected = mean_pt + np.array(offset)
        corrected_points.append(tuple(corrected.astype(int)))

    # Paso 7: Filtrado por ROI
    corrected = np.array(corrected_points)
    mask = (
        (corrected[:, 0] >= 30) & (corrected[:, 0] <= 450) &
        (corrected[:, 1] >= 40) & (corrected[:, 1] <= 270)
    )
    filtered = corrected[mask]
    x_real, y_real = filtered[:, 0], filtered[:, 1]

    # Paso 8: Coordenadas físicas centradas
    center_x, center_y = 163, 145
    scale = 0.03
    x_cm = (x_real - center_x) * scale
    y_cm = (y_real - center_y) * scale
    real_points_cm = np.stack((x_cm, y_cm), axis=1)

    # Paso 9: Filtrado por meridiano
    def filtrar_por_meridiano(real_points_cm, meridiano_deg, tolerance_cm=0.17):
        angle_rad = np.radians(meridiano_deg)
        direction = np.array([np.cos(angle_rad), np.sin(angle_rad)])
        projections = np.dot(real_points_cm, direction)
        projected = np.outer(projections, direction)
        dist_perpendicular = np.linalg.norm(real_points_cm - projected, axis=1)
        mask = dist_perpendicular <= tolerance_cm
        puntos_cercanos = real_points_cm[mask]
        proyecciones_centrales = projections[mask]
        indices_ordenados = np.argsort(proyecciones_centrales)
        puntos_ordenados = puntos_cercanos[indices_ordenados]
        return puntos_ordenados

    meridianos = [0, 22, 45, 67, 92, 115, 136, 158]
    angulos = [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5]
    puntos_por_meridiano = {}

    for m in meridianos:
        puntos = filtrar_por_meridiano(real_points_cm, meridiano_deg=m)
        puntos = puntos[np.linalg.norm(puntos, axis=1) <= 5.5]
        puntos_por_meridiano[m] = puntos

    # Paso 10: Mapa de elevación
    xAll, yAll, zAll = [], [], []
    R = 7.8
    for meridiano, angulo in zip(meridianos, angulos):
        puntos = puntos_por_meridiano[meridiano]
        if meridiano == 90:
            y_vals = puntos[:, 1]
        elif meridiano == 0:
            y_vals = puntos[:, 0]
        else:
            y_vals = puntos[:, 1]

        z_teorico = 2 * (y_vals ** 2) / (2 * R)

        theta = np.radians(angulo)
        x = y_vals * np.cos(theta)
        y = y_vals * np.sin(theta)

        xAll.extend(x)
        yAll.extend(y)
        zAll.extend(z_teorico)

    xAll = np.array(xAll)
    yAll = np.array(yAll)
    zAll = np.array(zAll)
    zAll_adj = -zAll + 1

    xq, yq = np.meshgrid(
        np.linspace(xAll.min(), xAll.max(), 200),
        np.linspace(yAll.min(), yAll.max(), 200)
    )
    zq = griddata((xAll, yAll), zAll_adj, (xq, yq), method='cubic')

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(xq, yq, zq, cmap='jet', edgecolor='none')
    fig.colorbar(surf)
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Elevación (mm)')
    ax.set_title('Mapa de Elevación Corneal con surf')
    ax.view_init(elev=30, azim=135)

    fig.savefig('mapa_elevacion.jpg', dpi=300, bbox_inches='tight')
    return 'mapa_elevacion.jpg'
