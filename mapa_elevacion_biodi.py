
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from scipy.optimize import least_squares

def generar_mapa_elevacion(puntos_por_meridiano):
    """
    Recibe un diccionario con puntos por meridiano y retorna una figura de matplotlib
    con el mapa de elevación corneal interpolado.
    """

    meridianos = [0, 22, 45, 67, 92, 115, 136, 158]
    angulos = [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5]

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

        z_teorico = 2 * (y_vals**2) / (2 * R)

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

    return fig
