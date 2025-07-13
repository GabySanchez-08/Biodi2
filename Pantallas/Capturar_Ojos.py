# === Archivo: Capturar_Ojos.py ===
from Pantallas.Base_App import Base_App
import flet as ft
import cv2
import base64
import asyncio
import os
import numpy as np
import platform

class Capturar_Ojos(Base_App):
    def __init__(self, page, usuario=None, rol=None):
        super().__init__(page, usuario, rol)
        self.mostrando_todos = False
        self.imagen_original = None
        self.auto_captura_activada = False
        self.historial_iris = []
        self.recorte_frame = 0.7 # Este es el zoom/recorte que se le hace al frame para que se vea de más cerca
        self.radio_guia = 150
        self.candidatos = []
        self.puntajes = []

    def mostrar(self):
        self.limpiar()

        self.escaneando_derecho = True
        self.captura_realizada = False
        self.stream_running = False
        self.camera_index = 0
        self.available_cameras = self.detectar_camaras()

        self.imagen_preview = ft.Image(
            width = 600,
            height=600,
            fit=ft.ImageFit.CONTAIN  # mantener proporciones sin deformar
        )

        self.titulo_ojos = ft.Text("Capturando ojo derecho", size=20, weight="bold")
        self.estado = ft.Text("Imagen actual del ojo derecho", size=16, weight="bold")

        self.dropdown_camaras = ft.Dropdown(
            label="Selecciona una cámara",
            options=[ft.dropdown.Option(str(i)) for i in self.available_cameras],
            value=str(self.camera_index),
            on_change=self.cambiar_camara
        )

        self.focus_slider = ft.Slider(
            min=0, max=200, divisions=20,
            label="Enfoque",
            on_change=self.cambiar_enfoque,
            value=0,
            width=1200,
            visible=False
        )

        self.capturar_btn = ft.ElevatedButton("Capturar", on_click=self.capturar)
        self.borrar_btn = ft.ElevatedButton("Borrar", on_click=self.borrar, disabled=True)
        self.cambiar_ojo_btn = ft.ElevatedButton("Cambiar de ojo", on_click=self.cambiar_ojo)
        self.continuar_btn = ft.ElevatedButton("Continuar", on_click=self.continuar, disabled=True)

        self.activar_auto_btn = ft.ElevatedButton("Comenzar captura automática", on_click=self.activar_captura_automatica)

        self.botones = ft.Row([
            self.capturar_btn, self.activar_auto_btn, self.borrar_btn, self.cambiar_ojo_btn, self.continuar_btn
        ], alignment=ft.MainAxisAlignment.CENTER)

        def on_volver_menu_click(e):
            self.volver_menu(e)

        self.page.add(
            ft.Stack([
                ft.Container(
                    ft.Column([
                        ft.TextButton("← Volver al menú", on_click=on_volver_menu_click),
                        self.cargar_logo(),
                        self.titulo_ojos,
                        self.dropdown_camaras,
                        self.imagen_preview,
                        self.focus_slider,
                        self.estado,
                        self.botones
                    ], alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                       spacing=15),
                    alignment=ft.alignment.center,
                    expand=True
                )
            ])
        )
        self.page.update()
        self.iniciar_stream()

    def detectar_camaras(self):
        disponibles = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.read()[0]:
                disponibles.append(i)
            cap.release()
        return disponibles if disponibles else [0]


    def iniciar_stream(self):
        # Cerrar cámara anterior si ya estaba abierta
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

        # Seleccionar backend más rápido según el sistema operativo
        sistema = platform.system()
        if sistema == "Windows":
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)  # DirectShow
            self.calentar_camara()
        elif sistema == "Darwin":  # macOS
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_AVFOUNDATION)  # AVFoundation
        else:
            self.cap = cv2.VideoCapture(self.camera_index)  # Linux o fallback
   
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        # Establecer resolución alta (Full HD)
        

        # Confirmar si la resolución fue aceptada
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"[INFO] Resolución cámara: {int(actual_width)}x{int(actual_height)}")

        self.cap.set(cv2.CAP_PROP_ZOOM, 120)
        
        # Iniciar flujo de video
        self.stream_running = True
        self.focus_slider.visible = True
        self.page.update()
        self.page.run_task(self.actualizar_stream)


    def obtener_marco_limites(self, ret, frame):
        h, w, _ = frame.shape
        side = int(min(h, w) * self.recorte_frame)
        y0 = (h - side) // 2
        x0 = (w - side) // 2
        frame_crop = frame[y0:y0 + side, x0:x0 + side]
         
        # Centro del círculo guía
        cx = side // 2
        cy = side // 2

        # Coordenadas del recorte
        x1 = max(cx - self.radio_guia, 0)
        y1 = max(cy - self.radio_guia, 0)
        x2 = min(cx + self.radio_guia, side)
        y2 = min(cy + self.radio_guia, side)

        # Recortar el ROI exacto alrededor del círculo ESTA ES LA IMAGEN A USAR
        roi = frame_crop[y1:y2, x1:x2]

        return (frame_crop,roi)  


    async def actualizar_stream(self):

        while self.stream_running:
            ret, frame = self.cap.read()
            if ret and not self.captura_realizada:
                frame_crop, roi_ojo = self.obtener_marco_limites(ret, frame)
                frame_mostrar = frame_crop.copy()

                # Centro del ROI (guía visual y centro esperado del iris)
                h_crop, w_crop = frame_crop.shape[:2]
                cx_fixed, cy_fixed = w_crop // 2, h_crop // 2

                # Intentar detectar el patrón (opcional)
                resultado_patron = self.detectar_patron(frame_crop)
                if resultado_patron:
                    cx_patron, cy_patron, r_patron = resultado_patron
                else:
                    cx_patron = cy_patron = r_patron = None

                # Detección del iris (siempre se intenta)
                resultado_iris = self.detectar_iris(frame_crop, cx_fixed, cy_fixed, self.radio_guia)

                if resultado_iris:
                    cx_iris, cy_iris, r_iris, roi_img = resultado_iris

                    # Dibujar iris
                    cv2.drawMarker(frame_mostrar, (cx_iris, cy_iris), (255, 0, 0),
                                markerType=cv2.MARKER_CROSS, markerSize=15, thickness=2)
                    cv2.circle(frame_mostrar, (cx_iris, cy_iris), r_iris, (255, 0, 0), 2)

                    # Evaluar alineación con centro y tamaño esperado
                    distancia_centro = np.linalg.norm([cx_fixed - cx_iris, cy_fixed - cy_iris])
                    tolerancia_posicion = 15

                    radio_relativo = r_iris / self.radio_guia
                    bien_centrado = distancia_centro < tolerancia_posicion
                    radio_esperado = 0.9 < radio_relativo < 1.1
                    color_iris = (255, 0, 0)  # Azul por defecto
                    # === NUEVO: usar historial para capturar solo si está alineado varios frames ===
                    if bien_centrado and radio_esperado:
                        self.historial_iris.append(True)
                        ret, frame = self.cap.read()
                        if not ret:
                            continue
                        frame_crop, roi_ojo = self.obtener_marco_limites(ret, frame)

                        score = self.sharpness(roi_ojo)
                        self.puntajes.append(score)
                        self.candidatos.append(roi_ojo)
                        print("capturando temporal")

                    else:
                        self.historial_iris.append(False)

                    # Mantener solo los últimos 5 frames
                    if len(self.historial_iris) > 5:
                        self.historial_iris.pop(0)

                    #print(self.historial_iris)
                    # Verificar si ha estado alineado por 5 frames seguidos
                    if len(self.historial_iris) == 5 and all(self.historial_iris):
                        print(f"🟢 Iris estable durante 3 frames. Capturando… (radio: {r_iris:.1f}, centro Δ: {distancia_centro:.1f})")
                        self.capturar(None)
                        self.historial_iris.clear()
                        break
                    else:
                        # Evaluar precaptura para cambiar color
                        casi_centrado = distancia_centro < 1.5 * tolerancia_posicion
                        radio_casi_esperado = 0.85 < radio_relativo < 1.15
                        color_iris = (0, 255, 255) if casi_centrado and radio_casi_esperado else (255, 0, 0)
                        print(f"🔶 Iris fuera de rango - Δ centro: {distancia_centro:.1f}, radio: {r_iris:.1f} ({radio_relativo*100:.1f}%)")

                    # Dibujar el iris
                    cv2.drawMarker(frame_mostrar, (cx_iris, cy_iris), color_iris,
                                markerType=cv2.MARKER_CROSS, markerSize=15, thickness=2)
                    cv2.circle(frame_mostrar, (cx_iris, cy_iris), r_iris, color_iris, 2)
                # Mostrar patrón si se detecta
                if resultado_patron:
                    cv2.drawMarker(frame_mostrar, (cx_patron, cy_patron), (0, 255, 0),
                                markerType=cv2.MARKER_CROSS, markerSize=15, thickness=2)
                    cv2.circle(frame_mostrar, (cx_patron, cy_patron), r_patron, (0, 255, 0), 2)

                # Dibujar guías
                cv2.circle(frame_mostrar, (cx_fixed, cy_fixed), self.radio_guia, (0, 0, 255), 2)
                cv2.line(frame_mostrar, (0, cy_fixed), (w_crop, cy_fixed), (0, 0, 255), 2)
                cv2.line(frame_mostrar, (cx_fixed, 0), (cx_fixed, h_crop), (0, 0, 255), 2)

                # Mostrar en interfaz
                _, buf = cv2.imencode(".jpg", frame_mostrar)
                img_base64 = buf.tobytes()
                self.imagen_preview.src_base64 = base64.b64encode(img_base64).decode('utf-8')
                self.page.update()

            await asyncio.sleep(0.05)

    def capturar(self, e):
        if not self.cap.isOpened():
            return

        for i in range(6-len(self.candidatos)):
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame_crop, roi_ojo = self.obtener_marco_limites(ret, frame)

            #nombre_candidata = f"candidata{i+1}.jpg"
            #cv2.imwrite(nombre_candidata, roi_ojo)

            score = self.sharpness(roi_ojo)
            self.puntajes.append(score)
            self.candidatos.append(roi_ojo)

            #print(f"[🔍] Nitidez de {nombre_candidata}: {score:.2f}")

        if self.candidatos:
            indice_mejor = self.puntajes.index(max(self.puntajes))
            mejor = self.candidatos[indice_mejor]
            nombre_mejor = f"candidata{indice_mejor+1}.jpg"
            #print(f"[✅] Imagen más nítida: {nombre_mejor} con puntaje {puntajes[indice_mejor]:.2f}")

            filename = "ojo_derecho.jpg" if self.escaneando_derecho else "ojo_izquierdo.jpg"
            cv2.imwrite(filename, mejor)
            self.procesar_post_captura(mejor)
            self.candidatos = []
            self.puntajes = []

    def borrar(self, e):
        ojo = "ojo_derecho.jpg" if self.escaneando_derecho else "ojo_izquierdo.jpg"
        if os.path.exists(ojo):
            os.remove(ojo)

        self.captura_realizada = False
        self.focus_slider.visible = True
        self.imagen_original = None
        self.imagen_preview.width = 600
        self.imagen_preview.height = 600
        self.borrar_btn.disabled = True
        self.capturar_btn.disabled = False
        self.auto_captura_activada = False
        self.activar_auto_btn.disabled = False
        self.continuar_btn.disabled = not (
            os.path.exists("ojo_derecho.jpg") or os.path.exists("ojo_izquierdo.jpg")
        )
        self.actualizar_textos()

        # 🔁 Reiniciar stream forzadamente
        self.detener_stream()
        self.iniciar_stream()

        self.page.update()


    def procesar_post_captura(self, frame):
        self.imagen_original = frame.copy()

        # Forzar ajuste visual correcto
        frame_resized = cv2.resize(frame, (600, 600), interpolation=cv2.INTER_LINEAR)
        _, buf = cv2.imencode(".jpg", frame_resized)
        img_base64 = buf.tobytes()
        self.imagen_preview.src_base64 = base64.b64encode(img_base64).decode("utf-8")

        self.captura_realizada = True
        self.actualizar_textos()
        self.borrar_btn.disabled = False
        self.capturar_btn.disabled = True
        self.activar_auto_btn.disabled = True
        self.continuar_btn.disabled = False
        self.focus_slider.visible = False
        self.page.update()

    def cambiar_enfoque(self, e):
        if hasattr(self, 'cap') and self.cap.isOpened():
            if not self.cap.set(cv2.CAP_PROP_FOCUS, self.focus_slider.value):
                print("[ERROR] No se pudo cambiar el enfoque")
            valor_actual = self.cap.get(cv2.CAP_PROP_FOCUS)
            print(f"[INFO] Enfoque actual: {valor_actual}")

    def cambiar_ojo(self, e):
        self.escaneando_derecho = not self.escaneando_derecho
        self.actualizar_textos()
        ojo = "derecho" if self.escaneando_derecho else "izquierdo"
        path = f"ojo_{ojo}.jpg"

        if os.path.exists(path):
            frame = cv2.imread(path)
            self.imagen_original = frame.copy()
            self.captura_realizada = True
            self.borrar_btn.disabled = False
            self.capturar_btn.disabled = True
            self.focus_slider.visible = False

        else:
            self.borrar(None)
        self.page.update()

    def cambiar_camara(self, e):
        self.camera_index = int(self.dropdown_camaras.value)
        self.iniciar_stream()

    def continuar(self, e):
        if not (os.path.exists("ojo_derecho.jpg") or os.path.exists("ojo_izquierdo.jpg")):
            print("[ADVERTENCIA] No se ha capturado ningún ojo. No se puede continuar.")
            return
        self.detener_stream()
        from Pantallas.Formulario_Paciente import Formulario_Paciente
        Formulario_Paciente(self.page, usuario=self.usuario, rol=self.rol).mostrar()

    def volver_menu(self, e):
        print("[INFO] Botón 'Volver al menú' presionado")
        self.detener_stream()
        from Pantallas.Menu_Principal import Menu_Principal
        Menu_Principal(self.page, self.usuario, self.rol).mostrar()

    def detener_stream(self):
        self.stream_running = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        self.focus_slider.visible = False
        self.page.update()
    
    def actualizar_textos(self):
        ojo = "derecho" if self.escaneando_derecho else "izquierdo"
        self.titulo_ojos.value = f"Capturando ojo {ojo}"
        self.estado.value = f"Imagen actual del ojo {ojo}"

    def reducir_grises(self, imagen_gray, niveles=8):
        factor = 256 // niveles
        return (imagen_gray // factor) * factor

    def detectar_patron(self, frame):
        h, w = frame.shape[:2]
        cx_fixed, cy_fixed = w // 2, h // 2

        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask, (cx_fixed, cy_fixed), self.radio_guia, 255, -1)
        frame_masked = cv2.bitwise_and(frame, frame, mask=mask)
        green = frame_masked[:, :, 1]
        gray = cv2.cvtColor(frame_masked, cv2.COLOR_BGR2GRAY)
        gray_eq = cv2.equalizeHist(gray)
        gray_reducida = self.reducir_grises(gray_eq, 8)

        blur = cv2.GaussianBlur(green, (5, 5), 1.0)
        binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                        cv2.THRESH_BINARY_INV, 11, 7)
        contornos, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        puntos = []
        for c in contornos:
            area = cv2.contourArea(c)
            if 5 < area < 100:
                perimetro = cv2.arcLength(c, True)
                circularidad = 4 * np.pi * area / (perimetro**2 + 1e-6)
                if 0.6 < circularidad < 1.3:
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        if mask[cy, cx] == 255:
                            puntos.append((cx, cy))

        if len(puntos) < 5:
            return None

        xs, ys = zip(*puntos)
        cx_patron = int(np.mean(xs))
        cy_patron = int(np.mean(ys))
        radios = [np.sqrt((x - cx_patron)**2 + (y - cy_patron)**2) for (x, y) in puntos]
        r_patron = int(1.2 * np.mean(radios))

        return (cx_patron, cy_patron, r_patron)

    def detectar_iris(self, frame, cx_base, cy_base, radio_guia):
        """
        Busca el iris alrededor del centro estimado (cx_base, cy_base), en una región del 200% del radio_guia.
        Retorna: (cx_iris, cy_iris, r_iris, roi_img) o None si no se encuentra.
        """
        h, w = frame.shape[:2]
        radio_busqueda = int(2.0 * radio_guia)

        # Definir región de interés (ROI)
        x1 = max(cx_base - radio_busqueda, 0)
        y1 = max(cy_base - radio_busqueda, 0)
        x2 = min(cx_base + radio_busqueda, w)
        y2 = min(cy_base + radio_busqueda, h)

        roi_img = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        gray_eq = cv2.equalizeHist(gray)
        gray_red = self.reducir_grises(gray_eq, 8)

        _, mask = cv2.threshold(gray_red, 70, 255, cv2.THRESH_BINARY_INV)
        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        mejor_radio = 0
        mejor_contorno = None
        cx_iris, cy_iris = None, None

        for c in contornos:
            area = cv2.contourArea(c)
            if area > 300:
                (x, y), radius = cv2.minEnclosingCircle(c)
                circularidad = 4 * np.pi * area / (cv2.arcLength(c, True) ** 2 + 1e-6)

                # Condiciones geométricas del iris
                if 0.4 < circularidad < 1.2:
                    if 0.8 * radio_guia < radius < 1.2 * radio_guia and radius > mejor_radio:
                        mejor_radio = radius
                        mejor_contorno = c
                        cx_iris, cy_iris = int(x), int(y)

        if mejor_contorno is not None:
            cx_abs = cx_iris + x1
            cy_abs = cy_iris + y1
            r_abs = int(mejor_radio)
            return (cx_abs, cy_abs, r_abs, roi_img)
        else:
            return None
    
    def activar_captura_automatica(self, e):
        self.auto_captura_activada = True
        self.activar_auto_btn.disabled = True
        #self.capturar_btn.disabled = True
        self.page.update()

    def calentar_camara(self):
        for _ in range(10):
            self.cap.read()

    def sharpness(self, image):
        """
        Calcula la nitidez de la imagen utilizando la varianza del laplaciano.
        Un valor mayor indica una imagen más nítida.
        """
        # Convertir a escala de grises si la imagen está en color
        if len(image.shape) > 2:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calcular el Laplaciano de la imagen
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        
        # Calcular la varianza del Laplaciano
        return laplacian.var()