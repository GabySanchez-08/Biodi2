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



#Datos en un rango de cornea sana-
elev_map = np.random.uniform(0.01, 0.035, (200, 200))  # valores clínicos típicos en mm
tang_map = np.random.uniform(36, 48, (200, 200))       # valores clínicos típicos en dioptrías


df_parametros = obtener_parametros_completos(elev_map, tang_map)

# Exportar

print(df_parametros)
