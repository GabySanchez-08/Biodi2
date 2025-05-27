import cv2
import numpy as np
import matplotlib.pyplot as plt

# === Rutas de las imágenes ===
rutas = ["ojo_derecho.jpg","ojo_izquierdo.jpg","foto_con_patron.jpeg", "foto_con_patron2.jpeg", "foto_con_patron3.jpeg"]
titulos = ["ojo_derecho.jpg","ojo_izquierdo.jpg","foto_con_patron", "foto_con_patron2", "foto_con_patron3"]

imagenes_con_patron = []
resultados = []

for ruta, titulo in zip(rutas, titulos):
    img = cv2.imread(ruta)
    if img is None:
        imagenes_con_patron.append(None)
        resultados.append((titulo, None, None, None, None))
        continue

    output = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (7, 7), 1.5)
    # Alternativa 1 (más robusta a cambios de iluminación)
    binarizada = cv2.adaptiveThreshold(gray_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 15, 3)
    contornos, _ = cv2.findContours(binarizada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pupila_encontrada = False

    for cnt in contornos:
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        if 80 <= radius <= 180:
            center = (int(x), int(y))
            radius = int(radius)

            mask = np.zeros_like(gray)
            cv2.drawContours(mask, [cnt], -1, 255, -1)
            media = cv2.mean(gray, mask=mask)[0]
            if media < 160:
                cv2.circle(output, center, radius, (0, 255, 0), 2)
                cv2.circle(output, center, 2, (255, 0, 0), 3)

                green = img[:, :, 1]
                roi_mask = np.zeros_like(gray)
                cv2.circle(roi_mask, center, radius, 255, -1)
                green_eq = cv2.equalizeHist(green)
                green_blur = cv2.GaussianBlur(green_eq, (5, 5), 1.0)
                binary_green = cv2.adaptiveThreshold(green_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                                     cv2.THRESH_BINARY_INV, 11, 5)
                puntos_bin = cv2.bitwise_and(binary_green, binary_green, mask=roi_mask)
                puntos_contornos, _ = cv2.findContours(puntos_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                puntos = []
                for pc in puntos_contornos:
                    area = cv2.contourArea(pc)
                    if 4 < area < 120:
                        M = cv2.moments(pc)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            if cv2.pointPolygonTest(cnt, (cx, cy), False) >= 0:
                                puntos.append((cx, cy))
                                cv2.circle(output, (cx, cy), 3, (255, 165, 0), -1)

                if len(puntos) >= 100:
                    puntos_np = np.array(puntos)
                    (x_p, y_p), r_p = cv2.minEnclosingCircle(puntos_np)
                    cv2.circle(output, (int(x_p), int(y_p)), int(r_p), (0, 0, 255), 2)
                    print(f"✅ {titulo}: {len(puntos)} puntos detectados")
                    resultados.append((titulo, center, radius, (int(x_p), int(y_p)), int(r_p)))
                else:
                    print(f"⚠️ {titulo}: solo {len(puntos)} puntos encontrados — descartado")
                    resultados.append((titulo, None, None, None, None))

                pupila_encontrada = True
                break

    if not pupila_encontrada:
        print(f"⚠️ No se detectó pupila válida en {titulo}")
        resultados.append((titulo, None, None, None, None))

    imagenes_con_patron.append(output)

# Mostrar resultados visuales
fig, axs = plt.subplots(1, 3, figsize=(18, 6))
for ax, img, titulo in zip(axs, imagenes_con_patron, titulos):
    if img is not None:
        ax.imshow(img)
        ax.set_title(titulo)
    else:
        ax.text(0.5, 0.5, "Imagen no cargada", ha="center", va="center")
    ax.axis("off")
plt.tight_layout()
plt.show()

