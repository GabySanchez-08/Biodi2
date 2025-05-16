import cv2
import numpy as np

# Iniciar cámara
cap = cv2.VideoCapture(0)
cap.set(3, 1920)
cap.set(4, 1080)

box_size = 160  # Tamaño del recuadro de seguimiento

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # --- 1. Extraer solo el canal verde ---
    green = frame[:, :, 1]
    h, w = green.shape
    cx, cy = w // 2, h // 2
    cv2.circle(frame, (cx, cy), 2, (0, 255, 0), -1)
    intensity = green[cy, cx]
    cv2.putText(frame, f"Intensidad canal G (centro): {intensity}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # --- 2. Umbral fijo (binarización del canal verde) ---
    _, binary_fixed = cv2.threshold(green, 95, 255, cv2.THRESH_BINARY_INV)

    # Detección de contornos en la imagen binarizada
    contours, _ = cv2.findContours(binary_fixed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_dist = float("inf")
    pupila = None

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 2500 < area < 8000:
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            if dist < min_dist:
                min_dist = dist
                pupila = (int(x), int(y), int(radius))

    # Dibujar recuadro de seguimiento directamente sobre la imagen original
    if pupila:
        x, y, r = pupila
        top_left = (x - box_size // 2, y - box_size // 2)
        bottom_right = (x + box_size // 2, y + box_size // 2)
        cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
        cv2.putText(frame, f"Pupila: x={x}, y={y}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Mostrar ventanas
    cv2.imshow("1. Imagen original con seguimiento", frame)
    cv2.imshow("2. Umbral fijo (canal verde)", binary_fixed)

    if cv2.waitKey(1) == 27:  # ESC para salir
        break

cap.release()
cv2.destroyAllWindows()