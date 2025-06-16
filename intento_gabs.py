import cv2
import numpy as np
import matplotlib.pyplot as plt

def reducir_grises(imagen_gray, niveles=8):
    factor = 256 // niveles
    return (imagen_gray // factor) * factor

# === Cargar imagen ==
ruta = "ojo1.jpeg"
img = cv2.imread(ruta)
if img is None:
    raise FileNotFoundError("❌ No se pudo cargar la imagen. Verifica la ruta y el nombre.")

img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# === Detectar patrón de puntos con umbral adaptativo en canal verde ===
green = img[:, :, 1]
blur = cv2.GaussianBlur(green, (5, 5), 1.0)
binary = cv2.adaptiveThreshold(
    blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 7
)
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Paso 1: Detectar todos los puntos candidatos
puntos = []
for c in contours:
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
    print("❌ No se detectaron puntos del patrón.")
    exit()

# Paso 2: Calcular centro y radio inicial
xs, ys = zip(*puntos)
cx_patron = int(np.mean(xs))
cy_patron = int(np.mean(ys))
radios = [np.sqrt((x - cx_patron)**2 + (y - cy_patron)**2) for (x, y) in puntos]
r_patron = int(np.mean(radios))

# Paso 3: Filtrar puntos que estén dentro del círculo verde
puntos_filtrados = puntos
#[]
#for x, y in puntos:
#    dist = np.sqrt((x - cx_patron)**2 + (y - cy_patron)**2)
#    if dist < 1.2 * r_patron:
#        puntos_filtrados.append((x, y))

if len(puntos_filtrados) < 5:
    print("❌ Muy pocos puntos dentro del patrón, verifique iluminación.")
    exit()

# Paso 4: Recalcular centro y radio con los puntos filtrados
xs, ys = zip(*puntos_filtrados)
cx_patron = int(np.mean(xs))
cy_patron = int(np.mean(ys))
radios = [np.sqrt((x - cx_patron)**2 + (y - cy_patron)**2) for (x, y) in puntos_filtrados]
r_patron = int(np.mean(radios))
print(f"✅ Número de puntos dentro del círculo del patrón: {len(puntos_filtrados)}")
# === ROI centrada en el patrón (120% del radio) ===
roi_r = int(1.2 * r_patron)
h, w = img.shape[:2]
x1 = max(cx_patron - roi_r, 0)
y1 = max(cy_patron - roi_r, 0)
x2 = min(cx_patron + roi_r, w)
y2 = min(cy_patron + roi_r, h)

# === Imagen en grises ecualizada y reducida ===
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray_eq = cv2.equalizeHist(gray)
gray_reducida = reducir_grises(gray_eq, niveles=8)

# === Buscar el iris dentro de la ROI ===
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
        if 0.4 < circularidad < 1.2 and 150 < radius < 250 and radius > mejor_radio:
            mejor_contorno = c
            mejor_radio = radius
            cx_iris, cy_iris = int(x), int(y)

# === Visualización ===
gray_reducida_rgb = cv2.cvtColor(gray_reducida, cv2.COLOR_GRAY2RGB)
img_gray_vis = gray_reducida_rgb.copy()
img_vis = img_rgb.copy()

for canvas in [img_vis, img_gray_vis]:
    for x, y in puntos:
        cv2.circle(canvas, (x, y), 2, (255, 0, 0), -1)
    cv2.circle(canvas, (cx_patron, cy_patron), r_patron, (0, 255, 0), 2)
    cv2.circle(canvas, (cx_patron, cy_patron), 4, (0, 255, 255), -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 255, 0), 2)

if mejor_contorno is not None:
    cx_abs = cx_iris + x1
    cy_abs = cy_iris + y1
    r_abs = int(mejor_radio)
    for canvas in [img_vis, img_gray_vis]:
        cv2.circle(canvas, (cx_abs, cy_abs), r_abs, (0, 0, 255), 2)
        cv2.circle(canvas, (cx_abs, cy_abs), 4, (0, 0, 255), -1)
    titulo = f"Iris detectado | Radio: {r_abs}px"
else:
    titulo = " No se detectó el iris"

# Mostrar resultados
r, g, b = cv2.split(img_rgb)
fig, axs = plt.subplots(1, 3, figsize=(16, 6))
axs[0].imshow(img_vis)
axs[0].set_title("RGB con detección")
axs[0].axis("off")

axs[1].imshow(img_gray_vis)
axs[1].set_title(titulo)
axs[1].axis("off")

axs[2].imshow(g, cmap='gray')
axs[2].set_title("Canal verde")
axs[2].axis("off")

plt.tight_layout()
plt.show()