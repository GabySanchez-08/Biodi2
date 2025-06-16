import cv2
import numpy as np
import matplotlib.pyplot as plt

def reducir_grises(imagen_gray, niveles=8):
    factor = 256 // niveles
    return (imagen_gray // factor) * factor

# === Cargar imagen ===
ruta = "ojo3.jpeg"
img = cv2.imread(ruta)
if img is None:
    raise FileNotFoundError("❌ No se pudo cargar la imagen. Verifica la ruta y el nombre.")

# Convertimos a RGB para matplotlib
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# === Detectar patrón de puntos ===
green = img[:, :, 1]
blur = cv2.GaussianBlur(green, (5, 5), 1.0)
binary = cv2.adaptiveThreshold(
    blur, 255,
    cv2.ADAPTIVE_THRESH_MEAN_C,
    cv2.THRESH_BINARY_INV,
    11, 7
)
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Paso 1: Filtrar candidatos circulares
puntos = []
for c in contours:
    area = cv2.contourArea(c)
    if 5 < area < 100:
        per = cv2.arcLength(c, True)
        circ = 4 * np.pi * area / (per**2 + 1e-6)
        if 0.6 < circ < 1.3:
            M = cv2.moments(c)
            if M["m00"] != 0:
                puntos.append((int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])))

if not puntos:
    print("❌ No se detectaron puntos del patrón.")
    exit()

# Paso 2: Centro y radio del patrón
xs, ys = zip(*puntos)
cx_patron = int(np.mean(xs))
cy_patron = int(np.mean(ys))
radios = [np.hypot(x - cx_patron, y - cy_patron) for x, y in puntos]
r_patron = int(np.mean(radios))
print(f"✅ Puntos detectados: {len(puntos)}, radio medio patrón: {r_patron}px")

# ROI centrada en el patrón (120% del radio)
roi_r = int(1.2 * r_patron)
h, w = img.shape[:2]
x1, y1 = max(cx_patron - roi_r, 0), max(cy_patron - roi_r, 0)
x2, y2 = min(cx_patron + roi_r, w), min(cy_patron + roi_r, h)

# === Preparar gris ecualizado para iris ===
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray_eq = cv2.equalizeHist(gray)

# === Detección del iris con HoughCircles ===
roi_gray = gray_eq[y1:y2, x1:x2]
roi_blur = cv2.medianBlur(roi_gray, 5)
circulos = cv2.HoughCircles(
    roi_blur,
    cv2.HOUGH_GRADIENT,
    dp=1.2,
    minDist=50,
    param1=100,
    param2=30,
    minRadius=int(0.8 * r_patron),
    maxRadius=int(1.2 * r_patron)
)

# === Preparar lienzos de visualización ===
img_vis = img_rgb.copy()
gray_reducida = reducir_grises(gray_eq, niveles=8)
img_gray_vis = cv2.cvtColor(gray_reducida, cv2.COLOR_GRAY2RGB)

# --- Dibujar patrón: puntos en rojo y círculo celeste ---
for lienzo in (img_vis, img_gray_vis):
    for x, y in puntos:
        cv2.circle(lienzo, (x, y), 2, (255, 0, 0), -1)         # puntos en rojo
    cv2.circle(lienzo, (cx_patron, cy_patron), r_patron,
               (255, 255, 0), 2)                             # patrón en celeste
    cv2.circle(lienzo, (cx_patron, cy_patron), 4,
               (0, 255, 255), -1)                            # centro en amarillo
    cv2.rectangle(lienzo, (x1, y1), (x2, y2),
                  (0, 255, 0), 2)                            # ROI en verde

# --- Dibujar iris (si se detectó) en verde ---
if circulos is not None:
    circulos = np.round(circulos[0, :]).astype(int)
    x_c, y_c, r_c = circulos[0]
    cx_iris, cy_iris, r_iris = x_c + x1, y_c + y1, r_c
    titulo = f"Iris detectado | Radio: {r_iris}px"
    for lienzo in (img_vis, img_gray_vis):
        cv2.circle(lienzo, (cx_iris, cy_iris), r_iris, (0, 255, 0), 2)
        cv2.circle(lienzo, (cx_iris, cy_iris), 4, (0, 255, 0), -1)
else:
    titulo = "❌ No se detectó el iris"

# === Mostrar resultados ===
_, g_chan, _ = cv2.split(img_rgb)
fig, axs = plt.subplots(1, 3, figsize=(16, 6))

axs[0].imshow(img_vis)
axs[0].set_title("RGB con detección")
axs[0].axis("off")

axs[1].imshow(img_gray_vis)
axs[1].set_title(titulo)
axs[1].axis("off")

axs[2].imshow(g_chan, cmap='gray')
axs[2].set_title("Canal verde")
axs[2].axis("off")

plt.tight_layout()
plt.show()