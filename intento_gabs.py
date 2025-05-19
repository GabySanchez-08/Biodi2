import cv2
import numpy as np
import matplotlib.pyplot as plt

def reducir_grises(imagen_gray, niveles=16):
    factor = 256 // niveles
    return (imagen_gray // factor) * factor

# === Cargar imagen ===
ruta = "ojo_con_patron.jpeg"  # Asegúrate que esté en el mismo directorio
img = cv2.imread(ruta)
if img is None:
    raise FileNotFoundError("❌ No se pudo cargar la imagen. Verifica la ruta y el nombre.")

img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# === Detectar patrón de puntos oscuros en canal verde ===
green = img[:, :, 1]
blur = cv2.GaussianBlur(green, (5, 5), 1.0)
_, binary = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

puntos = []
for c in contours:
    area = cv2.contourArea(c)
    if 5 < area < 80:
        M = cv2.moments(c)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            puntos.append((cx, cy))

if not puntos:
    print("❌ No se detectaron puntos del patrón.")
    exit()

# === Centroide del patrón y radio medio ===
xs, ys = zip(*puntos)
cx_patron = int(np.mean(xs))
cy_patron = int(np.mean(ys))
radios = [np.sqrt((x - cx_patron)**2 + (y - cy_patron)**2) for (x, y) in puntos]
r_patron = int(np.mean(radios))

# === ROI centrada en el patrón (150% del radio) ===
roi_r = int(1.5 * r_patron)
h, w = img.shape[:2]
x1 = max(cx_patron - roi_r, 0)
y1 = max(cy_patron - roi_r, 0)
x2 = min(cx_patron + roi_r, w)
y2 = min(cy_patron + roi_r, h)

# === Imagen en grises ecualizada y reducida a 4 tonalidades ===
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray_eq = cv2.equalizeHist(gray)
gray_reducida = reducir_grises(gray_eq, niveles=4)

# === Buscar el iris por umbral dentro de la ROI ===
roi_gray = gray_reducida[y1:y2, x1:x2]
_, mask = cv2.threshold(roi_gray, 60, 255, cv2.THRESH_BINARY_INV)

# Detectar contornos
contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
mejor_contorno = None
mejor_radio = 0
cx_iris, cy_iris = None, None

for c in contornos:
    area = cv2.contourArea(c)
    if area > 300:
        (x, y), radius = cv2.minEnclosingCircle(c)
        circularidad = 4 * np.pi * area / (cv2.arcLength(c, True) ** 2 + 1e-6)
        if 0.4 < circularidad < 1.2 and radius > mejor_radio:
            mejor_contorno = c
            mejor_radio = radius
            cx_iris, cy_iris = int(x), int(y)

# === Visualización ===
gray_reducida_rgb = cv2.cvtColor(gray_reducida, cv2.COLOR_GRAY2RGB)
img_gray_vis = gray_reducida_rgb.copy()
img_vis = img_rgb.copy()

# Dibujar patrón y ROI
for canvas in [img_vis, img_gray_vis]:
    for x, y in puntos:
        cv2.circle(canvas, (x, y), 2, (255, 0, 0), -1)
    cv2.circle(canvas, (cx_patron, cy_patron), r_patron, (0, 255, 0), 2)
    cv2.circle(canvas, (cx_patron, cy_patron), 4, (0, 255, 255), -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (255, 0, 0), 2)

# Dibujar iris estimado si fue detectado
if mejor_contorno is not None:
    cx_abs = cx_iris + x1
    cy_abs = cy_iris + y1
    r_abs = int(mejor_radio)
    for canvas in [img_vis, img_gray_vis]:
        cv2.circle(canvas, (cx_abs, cy_abs), r_abs, (0, 0, 255), 2)
        cv2.circle(canvas, (cx_abs, cy_abs), 4, (0, 0, 255), -1)
    titulo = f"Iris detectado por umbral | Radio: {r_abs}px"
else:
    titulo = "❌ No se detectó el iris por umbral"

# Mostrar imágenes
fig, axs = plt.subplots(1, 2, figsize=(16, 6))
axs[0].imshow(img_vis)
axs[0].set_title("RGB con círculos")
axs[0].axis("off")

axs[1].imshow(img_gray_vis)
axs[1].set_title(titulo)
axs[1].axis("off")

plt.tight_layout()
plt.show()