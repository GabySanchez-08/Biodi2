
import numpy as np
import pandas as pd
from scipy.ndimage import median_filter

def calcular_parametros_clinicos(tang_map, elev_map, mm_per_px=0.03):
    """
    Calcula parámetros clínicos topográficos a partir de mapas tangencial y de elevación.
    
    Parámetros:
    - tang_map: Mapa tangencial (matriz 2D)
    - elev_map: Mapa de elevación (matriz 2D) 
    - mm_per_px: Factor de conversión milímetros por píxel (default: 0.03)
    
    Retorna:
    - Diccionario con parámetros clínicos calculados
    """
    
    # ===== CONSTANTES DE CALIBRACIÓN =====
    FACTOR = 337.5  # Factor de conversión para obtener dioptrías
    KD_MIN, KD_MAX = 30, 55  # Rango válido de curvaturas corneales en dioptrías
    
    # ===== 1. CÁLCULO DE CURVATURA TANGENCIAL =====
    
    # Calcular gradientes de la superficie tangencial
    grad_y, grad_x = np.gradient(tang_map)
    
    # Convertir gradientes a unidades físicas (mm)
    grad_y_mm = grad_y / mm_per_px
    
    # Calcular segunda derivada para obtener curvatura
    d2z_dyy, _ = np.gradient(grad_y_mm)  # Nota: había un error de sintaxis aquí (grad*y_mm)
    d2z_dyy_mm = d2z_dyy / mm_per_px
    
    # Fórmula de curvatura tangencial
    # Kt = |d²z/dy²| / (1 + (dz/dy)²)^(3/2)
    Kt = np.abs(d2z_dyy_mm / (1 + grad_y_mm**2)**1.5)
    
    # Convertir curvatura a dioptrías usando factor de calibración
    Kd = FACTOR * Kt
    
    # ===== FILTRADO DE VALORES CLÍNICAMENTE VÁLIDOS =====
    # Mantener solo valores dentro del rango fisiológico de curvatura corneal
    Kd_valid = Kd[(Kd >= KD_MIN) & (Kd <= KD_MAX)]
    
    # ===== CÁLCULO DE PARÁMETROS ÓPTICOS BÁSICOS =====
    # K1 (curvatura más plana) - valor mínimo
    Kf_a = np.min(Kd_valid) if len(Kd_valid) > 0 else np.nan
    
    # K2 (curvatura más curva) - valor máximo  
    Ks_a = np.max(Kd_valid) if len(Kd_valid) > 0 else np.nan
    
    # Astigmatismo corneal - diferencia entre curvaturas principales
    CYL_a = Ks_a - Kf_a if not np.isnan(Ks_a) and not np.isnan(Kf_a) else np.nan
    
    # ===== 2. PROCESAMIENTO DEL MAPA DE ELEVACIÓN =====
    
    # Aplicar filtro mediano para reducir ruido en el mapa de elevación
    elev_map_filtered = median_filter(elev_map, size=4)
    
    # Eliminar valores NaN para cálculos estadísticos
    elev_valid = elev_map_filtered[~np.isnan(elev_map_filtered)]
    
    if elev_valid.size > 0:
        # Usar percentiles para evitar valores extremos outliers
        elev_max = np.percentile(elev_valid, 99)  # Elevación máxima (percentil 99)
        elev_min = np.percentile(elev_valid, 1)   # Elevación mínima (percentil 1)
        delta_elev = elev_max - elev_min          # Diferencia total de elevación
    else:
        # Si no hay datos válidos, asignar NaN
        elev_max = elev_min = delta_elev = np.nan
    
    # ===== 3. CALIBRACIÓN FINAL DE PARÁMETROS =====
    # Aplicar factores de calibración específicos obtenidos empíricamente
    Kf = Kf_a * 1.333  # Factor de calibración para K1
    Ks = Ks_a * 0.74   # Factor de calibración para K2  
    CYL = CYL_a * 0.05 # Factor de calibración para astigmatismo
    
    # Curvatura promedio (Km)
    AvgK = (Kf + Ks) / 2
    
    # ===== 4. CÁLCULO DE PARÁMETROS SMARTKC ADICIONALES =====
    
    # sim-K: Valores de curvatura simulada (ya los tenemos como K1 y K2)
    sim_K1 = Kf  # Curvatura más plana
    sim_K2 = Ks  # Curvatura más curva
    
    # diff: Diferencia entre curvaturas principales (astigmatismo)
    diff = abs(sim_K2 - sim_K1) if not np.isnan(sim_K2) and not np.isnan(sim_K1) else np.nan
    
    # mean-K: Curvatura promedio (equivalente a Km)
    mean_K = AvgK
    
    # aCLMI: Índice de asimetría corneal
    # Calculado como desviación estándar de las curvaturas válidas
    aclmi = np.std(Kd_valid) if len(Kd_valid) > 0 else np.nan
    
    # PPK: Poder corneal más pronunciado (valor máximo de curvatura)
    ppk = np.max(Kd_valid) if len(Kd_valid) > 0 else np.nan
    
    # KISA: Índice para detección de queratocono
    # Fórmula simplificada: función de astigmatismo y asimetría
    if not np.isnan(diff) and not np.isnan(aclmi) and not np.isnan(ppk):
        # KISA = (diff × aclmi × PPK) / 100
        kisa = (diff * aclmi * ppk) / 100
    else:
        kisa = np.nan
    
    # ===== ÍNDICES AVANZADOS DE DETECCIÓN DE QUERATOCONO =====
    
    # Función auxiliar para calcular índices por sectores
    def calcular_indices_sectores(curvatura_map, center_x, center_y, radio_mm=2.0):
        """
        Calcula valores promedio en diferentes sectores de la córnea
        """
        h, w = curvatura_map.shape
        centro_x, centro_y = w//2, h//2  # Asumir centro geométrico
        radio_px = int(radio_mm / mm_per_px)
        
        # Crear máscara circular
        y, x = np.ogrid[:h, :w]
        mask = (x - centro_x)**2 + (y - centro_y)**2 <= radio_px**2
        
        # Dividir en sectores (superior, inferior, nasal, temporal)
        sectores = {
            'superior': (y < centro_y) & mask,
            'inferior': (y >= centro_y) & mask,
            'nasal': (x < centro_x) & mask,
            'temporal': (x >= centro_x) & mask
        }
        
        valores_sectores = {}
        for nombre, sector_mask in sectores.items():
            valores_sector = curvatura_map[sector_mask]
            valores_sector = valores_sector[~np.isnan(valores_sector)]
            if len(valores_sector) > 0:
                valores_sectores[nombre] = np.mean(valores_sector)
            else:
                valores_sectores[nombre] = np.nan
        
        return valores_sectores
    
    
    # ===== 5. RETORNO DE RESULTADOS =====
    return {
        # Parámetros originales
        "K1 (D)": round(Kf, 2) if not np.isnan(Kf) else "",
        "K2 (D)": round(Ks, 2) if not np.isnan(Ks) else "",
        "Km (D)": round(AvgK, 2) if not np.isnan(AvgK) else "",
        "CYL": round(CYL, 2) if not np.isnan(CYL) else "",
        "Elev_Max (μm)": round(elev_max, 1) if not np.isnan(elev_max) else "",
        "Elev_Min (μm)": round(elev_min, 1) if not np.isnan(elev_min) else "",
        "ΔElev (μm)": round(delta_elev, 1) if not np.isnan(delta_elev) else "",
        
        # Parámetros adicionales
        "sim-K1": round(sim_K1, 2) if not np.isnan(sim_K1) else "",
        "sim-K2": round(sim_K2, 2) if not np.isnan(sim_K2) else "",
        "diff": round(diff, 2) if not np.isnan(diff) else "",
        "mean-K": round(mean_K, 2) if not np.isnan(mean_K) else "",
        "aCLMI": round(aclmi, 2) if not np.isnan(aclmi) else "",
        "PPK": round(ppk, 2) if not np.isnan(ppk) else "",
        "KISA (%)": round(kisa, 3) if not np.isnan(kisa) else "",
    }    
    

def obtener_parametros_completos(elev_map, tang_map):
    """
    Retorna un DataFrame con los parámetros clínicos en columnas.
    """
    parametros_dict = calcular_parametros_clinicos(tang_map, elev_map)
    return pd.DataFrame(list(parametros_dict.items()), columns=["Parámetro", "Valor"])



