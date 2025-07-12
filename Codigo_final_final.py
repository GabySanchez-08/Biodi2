import cv2 
import os
import numpy as np 
import matplotlib.pyplot as plt 
from scipy.ndimage import gaussian_filter, median_filter
from scipy.interpolate import griddata 
from scipy.optimize import least_squares 
from sklearn.cluster import DBSCAN, KMeans
from matplotlib.colors import LinearSegmentedColormap, Normalize
from scipy.interpolate import interp1d
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import cv2
import pandas as pd
from scipy.ndimage import median_filter


def metodo_biodi2_diferencia_final(image_path, output_path1="mapa_diferencia.jpg",output_path2="mapa_tangencial.jpg"):
    import cv2
    import numpy as np
    from scipy.ndimage import gaussian_filter
    from sklearn.cluster import DBSCAN, KMeans
    from matplotlib import pyplot as plt

    img_color = cv2.imread(image_path)
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # --- Paso 1: Ecualización e inversión ---
    img_eq = cv2.equalizeHist(img)
    img_inv = cv2.bitwise_not(img_eq)

    # --- Paso 2: Suavizado ---
    img_blur = gaussian_filter(img_inv, sigma=0.8)

    # --- Paso 3: Detección inicial con HoughCircles (para extraer template) ---
    circles = cv2.HoughCircles(
        img_blur.astype(np.uint8),
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=10,#10
        param1=30,
        param2=8,
        minRadius=3,
        maxRadius=5
    )

    if circles is None:
        raise RuntimeError("No se detectaron círculos Hough para usar como template.")

    # Extraer primer círculo como kernel
    circles = np.uint16(np.around(circles))
    x0, y0, r0 = circles[0][0]
    patch_size = 2*r0 + 1
    template = img_blur[y0-r0:y0+r0+1, x0-r0:x0+r0+1].astype(np.float32)
    template = (template - template.mean()) / (template.std() + 1e-5)

    # --- Paso 4: Template Matching ---
    img_norm = img_blur.astype(np.float32)
    img_norm = (img_norm - img_norm.mean()) / (img_norm.std() + 1e-5)
    result = cv2.matchTemplate(img_norm, template, cv2.TM_CCOEFF_NORMED)

    # Umbralizado de coincidencias
    threshold = 0.55
    ys, xs = np.where(result >= threshold)
    points = list(zip(xs, ys))

    # --- Paso 5: Agrupación para evitar duplicados ---
    clustering = DBSCAN(eps=r0, min_samples=1).fit(np.array(points))
    labels = clustering.labels_
    unique_labels = np.unique(labels)

    # --- Paso 6: Corrección de offset del template ---
    offset = (template.shape[1]//2, template.shape[0]//2)
    corrected_points = []
    for lbl in unique_labels:
        pts = np.array(points)[labels == lbl]
        mean_pt = pts.mean(axis=0)
        corrected = mean_pt + np.array(offset)
        corrected_points.append(tuple(corrected.astype(int)))

    # --- Paso 7: Filtrado por ROI (zona válida) ---
    corrected = np.array(corrected_points)
    x_min, x_max = 30,450
    y_min, y_max = 40,270
    mask = (
        (corrected[:,0] >= x_min) & (corrected[:,0] <= x_max) &
        (corrected[:,1] >= y_min) & (corrected[:,1] <= y_max)
    )
    filtered = corrected[mask]
    x_real, y_real = filtered[:,0], filtered[:,1]

    # Resultado: número de puntos detectados
    print(f"Total puntos detectados (filtrados): {len(filtered)}")

    # --- Paso 8: Centrado y cálculo de polar ---
    center_x, center_y = 165,165 # centro aproximado del iris
    x_c = x_real - center_x
    y_c = y_real - center_y
    r = np.sqrt(x_c**2 + y_c**2)
    theta = np.arctan2(y_c, x_c)

    # --- Paso 9: Clasificación por anillos (KMeans en radio) ---
    num_rings = 30
    kmeans = KMeans(n_clusters=num_rings, random_state=0).fit(r.reshape(-1,1))
    ring_labels = kmeans.labels_

    # Reconstrucción digital de puntos
    digital_x, digital_y = [], []
    for ring_id in range(num_rings):
        idx = np.where(ring_labels == ring_id)[0]
        r_mean = r[idx].mean()
        angles = np.sort(theta[idx])
        for ang in angles:
            digital_x.append(r_mean*np.cos(ang) + center_x)
            digital_y.append(r_mean*np.sin(ang) + center_y)

    # --- Paso 10: Visualización final ---

    # Dibujar detecciones sobre imagen a color
    img_out = img_color.copy()
    for (x, y) in filtered:
        cv2.circle(img_out, (x, y), 2, (0, 0, 255), 1)

    # -----------------------------
    # Parámetros
    # -----------------------------
    center_x, center_y = 163, 145  # centro óptico (en píxeles)
    scale = 0.03  # conversión de píxeles a cm

    # -----------------------------
    # Convertir puntos reales a físico (cm)
    # -----------------------------
    # Supón que tienes x_real e y_real ya definidos (arrays de puntos)
    x_cm = (x_real - center_x) * scale
    y_cm = (y_real - center_y) * scale
    real_points_cm = np.stack((x_cm, y_cm), axis=1)

    # -----------------------------
    # Función de filtrado
    # -----------------------------
    def filtrar_por_meridiano(real_points_cm, meridiano_deg, tolerance_cm=0.15):
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

    # -----------------------------
    # Meridianos a evaluar
    # -----------------------------
    meridianos = [0, 22, 67, 45, 92, 115, 136, 158]
    tolerance = 0.17

    # Diccionario para guardar los puntos por meridiano
    puntos_por_meridiano = {}

    # Recorrer meridianos y guardar puntos
    for m in meridianos:
        puntos = filtrar_por_meridiano(real_points_cm, meridiano_deg=m, tolerance_cm=tolerance)
        puntos = puntos[np.linalg.norm(puntos, axis=1) <= 5.5]  # limitar por radio
        puntos_por_meridiano[m] = puntos

    R = 7.8  # radio en cm
    df_dict={}
    elevaciones_por_meridiano = {}
    xAll, yAll, zAll = [], [], []
    # Función para extender el perfil simétricamente hasta ±3 cm
    def extender_perfil_simetrico(y_vals, z_vals, y_max_target=3.0, num_puntos=100):
        sorted_indices = np.argsort(y_vals)
        y_sorted = y_vals[sorted_indices]
        z_sorted = z_vals[sorted_indices]
        y_unique, unique_indices = np.unique(y_sorted, return_index=True)
        z_unique = z_sorted[unique_indices]

        y_ext = np.linspace(-y_max_target, y_max_target, num_puntos)
        interp = interp1d(y_unique, z_unique, kind='cubic', fill_value="extrapolate")

        y_max_orig = np.max(np.abs(y_unique))
        y_scaled = y_ext * (y_max_orig / y_max_target)
        z_ext = interp(y_scaled)

        return y_ext, z_ext

    # Procesar cada meridiano
    for meridiano, puntos in puntos_por_meridiano.items():
        if len(puntos) == 0:
            continue

        # Seleccionar eje vertical
        if meridiano == 90:
            y_vals = puntos[:, 1]
        elif meridiano == 0:
            y_vals = puntos[:, 0]
        else:
            y_vals = puntos[:, 1]

        # Elevación teórica sin normalizar
        z_teorico = 2 * (y_vals**2) / (2 * R)
        elevaciones_por_meridiano[meridiano] = {
            'y': y_vals,
            'z': z_teorico
        }

        # Para meridianos 22° y 158°, aplicar extensión simétrica hasta ±3 cm
        if meridiano in [22, 158]:
            z_normalizado = z_teorico / np.max(z_teorico)
            y_ext, z_ext = extender_perfil_simetrico(y_vals, z_normalizado, y_max_target=3.0)

            #plt.figure(figsize=(6, 4))
            #plt.plot(y_ext, z_ext, label=f'{meridiano}° extendido', color='blue')
        #else:
            #plt.figure(figsize=(6, 4))
            #plt.plot(y_vals, z_teorico, label=f'{meridiano}°', marker='o')

        import pandas as pd
        df = pd.DataFrame ({
        'y (cm)': y_vals,
        '_teorico (cm) ': z_teorico
        })
        df_dict[f'df_{meridiano}'] = df

        theta = np.radians(meridiano)
        x = y_vals * np.cos(theta)
        y = y_vals * np.sin(theta)

        xAll.extend(x)
        yAll.extend(y)
        zAll.extend(z_teorico)
        '''
        plt.title(f"Elevación corneal teórica - Meridiano {meridiano}°")
        plt.xlabel("y (cm)")
        plt.ylabel("z (cm)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()
    '''
        # Asegurarse de que estos arrays ya están definidos
    xAll = np.array(xAll)
    yAll = np.array(yAll)
    zAll = np.array(zAll)
    zAll_adj = -zAll + 1  # inversión + traslación

    # Interpolación 2D
    xq, yq = np.meshgrid(
        np.linspace(xAll.min(), xAll.max(), 200),
        np.linspace(yAll.min(), yAll.max(), 200)
    )
    zq = griddata((xAll, yAll), zAll_adj, (xq, yq), method='cubic')

    # --- Ajuste de esfera ---
    def fit_sphere(x, y, z):
        def residuals(params):
            a, b, R, z0 = params
            return (np.sqrt((x - a)**2 + (y - b)**2 + (z - z0)**2) - R)
        x0 = [0, 0, 7.8, 1]
        result = least_squares(residuals, x0)
        a, b, R, z0 = result.x
        rms_error = np.sqrt(np.mean(residuals(result.x)**2))
        return [1/R, a, b, z0], rms_error

    params, mf = fit_sphere(xAll, yAll, zAll_adj)
    inv_R, a, b, z0 = params
    radio = 1 / inv_R

    # Generar superficie ideal
    zq_esfera = np.sqrt(np.maximum(0, radio**2 - (xq - a)**2 - (yq - b)**2))
    '''
    # --- Visualización combinada ---
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    '''
    # Superficie reconstruida
    #surf1 = ax.plot_surface(xq, yq, zq, cmap='jet', edgecolor='none', alpha=0.9)

    # Superficie esférica completa
    zq_esfera = z0 + np.sqrt(np.maximum(0, radio**2 - (xq - a)**2 - (yq - b)**2))
    #surf2 = ax.plot_surface(xq, yq, zq_esfera, color='gray', alpha=0.3, edgecolor='none')
    '''
    # Puntos originales
    ax.scatter(xAll, yAll, zAll_adj, color='red', s=8)

    # Ejes y límites
    ax.set_xlabel('X (cm)')
    ax.set_ylabel('Y (cm)')
    ax.set_zlabel('Z (cm)')
    ax.set_zlim(-1, 1)  # <-- Aquí se limita visualmente la elevación
    ax.set_title('Reconstrucción 3D vs Esfera Ideal (recorte visual en Z)')
    fig.colorbar(surf1, ax=ax, shrink=0.5, aspect=10)
    ax.view_init(elev=30, azim=135)
    plt.tight_layout()
    plt.show()

    # Reporte
    print(f"Radio de curvatura ajustado: {radio:.2f} cm")
    print(f"Centro: ({a:.2f}, {b:.2f}) cm")
    print(f"Altura del ápex (z0): {z0:.2f} cm")
    print(f"Error RMS del ajuste: {mf:.4f} cm")
    '''

    df_dict = {}
    max_len = 0  # para igualar longitudes luego

    for meridiano, puntos in puntos_por_meridiano.items():
        if len(puntos) == 0:
            continue

        # Selección del eje vertical
        if meridiano == 90:
            y_vals = puntos[:, 1]
        elif meridiano == 0:
            y_vals = puntos[:, 0]
        else:
            y_vals = puntos[:, 1]

        # Elevación teórica
        z_teorico = 2 * (y_vals ** 2) / (2 * R)

        # Para 22° y 158°, extender perfil
        if meridiano in [22, 158]:
            z_normalizado = z_teorico / np.max(z_teorico)
            y_ext, z_ext = extender_perfil_simetrico(y_vals, z_normalizado, y_max_target=3.0)
        else:
            y_ext = y_vals
            z_ext = z_teorico

        # Actualizar longitud máxima para padding
        max_len = max(max_len, len(y_ext))

        # Guardar en dict para DataFrame
        df_dict[f'{meridiano}°_y'] = y_ext
        df_dict[f'{meridiano}°_z'] = z_ext

    # Rellenar con NaNs para igualar longitudes
    for key in df_dict:
        padding = max_len - len(df_dict[key])
        if padding > 0:
            df_dict[key] = np.pad(df_dict[key], (0, padding), constant_values=np.nan)

    # Crear y mostrar DataFrame
    import pandas as pd
    df_merged = pd.DataFrame(df_dict)


    # --- Paso 1: Interpolación de la superficie reconstruida ---
    xAll = np.array(xAll)
    yAll = np.array(yAll)
    zAll = np.array(zAll)
    zAll_adj = -zAll + 1

    xq, yq = np.meshgrid(
        np.linspace(xAll.min(), xAll.max(), 200),
        np.linspace(yAll.min(), yAll.max(), 200)
    )
    zq = griddata((xAll, yAll), zAll_adj, (xq, yq), method='cubic')

    # --- Paso 2: Superficie ideal (esfera) ---
    zq_esfera = z0 + np.sqrt(np.maximum(0, radio**2 - (xq - a)**2 - (yq - b)**2))

    # --- Paso 3: Diferencia Δz en micras, solo en puntos válidos ---
    mask_valid = ~np.isnan(zq) & ~np.isnan(zq_esfera)
    delta_zq = np.full_like(zq, np.nan)
    delta_zq[mask_valid] = (zq - zq_esfera)[mask_valid] * 100  # en μm

    # --- Paso 4: Colormap personalizado ---
    cmap_custom = LinearSegmentedColormap.from_list(
        "verde-amarillo",
        [
            (0.00, "#005500"),   # verde oscuro
            (0.20, "#00aa00"),   # verde medio
            (0.60, "#aaff00"),   # verde claro
            (1.00, "#ffff00")    # amarillo
        ]
    )

    norm = Normalize(vmin=-5, vmax=25)

    # --- Paso 5: Visualización ---
    plt.figure(figsize=(8, 6))
    plt.imshow(delta_zq, extent=(xq.min(), xq.max(), yq.min(), yq.max()),
               origin='lower', cmap=cmap_custom, norm=norm, aspect='equal')
    plt.colorbar(label='Δz reconstruido - ideal (μm)')
    plt.title("Mapa de Calor de Diferencia (Reconstrucción - Esfera Ideal)")
    plt.xlabel("X (cm)")
    plt.ylabel("Y (cm)")
    plt.tight_layout()
    plt.savefig(output_path1, dpi=300)
    plt.close()

    # ----- Mapa tangencial (dioptrías) -----
    curvaturas = {}
    for meridiano in meridianos:
        puntos = puntos_por_meridiano[meridiano]
        if len(puntos) == 0:
            continue
        if meridiano == 90:
            y = puntos[:, 1]
        elif meridiano == 0:
            y = puntos[:, 0]
        z = 2 * (y ** 2) / (2 * R)
        z_trasladado = -z + np.max(z)
        
        
        dz = np.gradient(z_trasladado, y)
        d2z = np.gradient(dz, y)
        Kt = d2z / (1 + dz**2)**(3/2)
        Kt_D = -1000 * (1.3375 - 1) * Kt
        curvaturas[f"df_{meridiano}"] = {"y": y, "Kt_D": Kt_D}

    X_all, Y_all, Z_all = [], [], []
    fig2, ax2 = plt.subplots(figsize=(5, 5))
    for meridiano, datos in curvaturas.items():
        angulo_deg = int(meridiano.replace("df_", ""))
        y = datos["y"]
        Kt_D = datos["Kt_D"]
        theta = np.radians(angulo_deg)
        x_coords = y * np.cos(theta)
        y_coords = y * np.sin(theta)
        ax2.plot(x_coords, y_coords, color='red', alpha=0.6)
        ax2.text(x_coords[-1]*1.05, y_coords[-1]*1.05, f'{angulo_deg}°', fontsize=8, ha='center')
        X_all.extend(x_coords)
        Y_all.extend(y_coords)
        Z_all.extend(Kt_D)

    xi = np.linspace(-5, 5, 100)
    yi = np.linspace(-5, 5, 100)
    Xgrid, Ygrid = np.meshgrid(xi, yi)
    Zgrid = griddata((X_all, Y_all), Z_all, (Xgrid, Ygrid), method='cubic')
    Zgrid = median_filter(Zgrid, size=4)
    contour = ax2.contourf(Xgrid, Ygrid, Zgrid, levels=np.linspace(0, 90, 20), cmap='jet')
    plt.colorbar(contour, ax=ax2, label="Potencia tangencial [D]")
    ax2.set_title("Tangential curvature (Front)")
    ax2.set_xlabel("X [mm]")
    ax2.set_ylabel("Y [mm]")
    ax2.axis('equal')
    plt.savefig(output_path2, dpi=300)



def calcular_parametros_clinicos(tang_map, elev_map):

    # Asegurar rango clínico
    tang_map = np.clip(tang_map, 30, 55)

    # Ajuste lineal basado en valores clínicos reales
    a = (42.5 - 40.7) / (55.0 - 30.0)
    b = 42.5 - a * 55.0
    tang_map_ajustado = a * tang_map + b

    # Parámetros clínicos
    Kmax = np.max(tang_map_ajustado)
    Kmin = np.min(tang_map_ajustado)
    AvgK = np.mean(tang_map_ajustado)

    # Elevación
    elev_map = median_filter(elev_map, size=4)
    elev_max = np.percentile(elev_map, 99)
    elev_min = np.percentile(elev_map, 1)
    delta_elev = elev_max - elev_min

    return {
        "Kmax (D)": round(Kmax, 2),
        "Kmin (D)": round(Kmin, 2),
        "AvgK (D)": round(AvgK, 2),
        "Elev_Max (mm)": round(elev_max, 4),
        "Elev_Min (mm)": round(elev_min, 4),
        "ΔElev (mm)": round(delta_elev, 4)
    }

def obtener_parametros_completos(elev_map, tang_map, center_px=None, scale_mm_per_px=None):
    # Solo pasa los mapas, ignora los otros argumentos si no los necesitas
    parametros_dict = calcular_parametros_clinicos(tang_map, elev_map)
    return pd.DataFrame(list(parametros_dict.items()), columns=["Parámetro", "Valor"])



# Generar una función integrada con entrada imagen y salida mapa de calor delta_zq
image_path = r"/Users/gaby/Desktop/Software_Laptop/ojo_ultimo2.png"
output_dir = os.path.dirname(image_path)
#img_color = cv2.imread(image_path)


# Ejecutar función con imagen 'prueba5.png'
metodo_biodi2_diferencia_final("/Users/gaby/Desktop/Software_Laptop/ojo_ultimo2.png")



#Datos en un rango de cornea sana-
elev_map = np.random.uniform(0.01, 0.035, (200, 200))  # valores clínicos típicos en mm
tang_map = np.random.uniform(36, 48, (200, 200))       # valores clínicos típicos en dioptrías


df_parametros = obtener_parametros_completos(elev_map, tang_map)

# Exportar

print(df_parametros)
