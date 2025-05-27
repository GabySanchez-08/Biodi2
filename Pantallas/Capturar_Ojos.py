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
        self.zoom_muestra = 1.0
        self.imagen_original = None
        self.auto_captura_activada = False
        self.historial_alineacion = []

    def mostrar(self):
        self.limpiar()

        self.escaneando_derecho = True
        self.captura_realizada = False
        self.stream_running = False
        self.camera_index = 0
        self.available_cameras = self.detectar_camaras()

        self.imagen_preview = ft.Image(
            width=1200,
            height=700,
            fit=ft.ImageFit.CONTAIN  # mantener proporciones sin deformar
        )

        self.zoom_slider_preview = ft.Slider(
            min=1.0,
            max=2.0,
            divisions=10,
            label="Zoom de vista",
            on_change=self.zoom_muestra_changed,
            value=1.0,
            visible=False,
            width=1200
        )

        self.titulo_ojos = ft.Text("Capturando ojo derecho", size=20, weight="bold")
        self.estado = ft.Text("Imagen actual del ojo derecho", size=16, weight="bold")

        self.dropdown_camaras = ft.Dropdown(
            label="Selecciona una cámara",
            options=[ft.dropdown.Option(str(i)) for i in self.available_cameras],
            value=str(self.camera_index),
            on_change=self.cambiar_camara
        )

        self.zoom_slider = ft.Slider(
            min=100, max=120, divisions=1,
            label="Zoom",
            on_change=self.cambiar_zoom,
            value=100,
            width=1200,
            visible=False
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
                        self.zoom_slider_preview,
                        self.zoom_slider,
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

        # Iniciar flujo de video
        self.stream_running = True
        self.zoom_slider.visible = True
        self.focus_slider.visible = True
        self.page.update()
        self.page.run_task(self.actualizar_stream)

    async def actualizar_stream(self):
        lado = 24
        while self.stream_running:
            #print("whileok")
            ret, frame = self.cap.read()
            if ret and not self.captura_realizada:
                #print("entro al if de ret")
                h, w, _ = frame.shape
                crop_h = int(h * 0.7)
                crop_w = int(w * 0.7)
                start_y = (h - crop_h) // 2
                start_x = (w - crop_w) // 2
                frame_crop = frame[start_y:start_y + crop_h, start_x:start_x + crop_w]
                frame_mostrar = frame_crop.copy()  # copia solo para mostrar

                resultado = self.detectar_patron_e_iris(frame_crop)
                #resultado = 0

                if resultado:
                    print("entro al if de resultado")
                    cx_patron, cy_patron, r_patron, cx_iris, cy_iris, r_iris, roi_img, (x1, y1, x2, y2) = resultado
                    # Ajustar coordenadas al sistema de frame_crop si este proviene de un recorte
                    

                    # === Dibujo SOLO en frame_mostrar ===
                    # Marco rojo de ROI
                    cv2.rectangle(frame_mostrar, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    # Cruces en centros
                    cv2.drawMarker(frame_mostrar, (cx_patron, cy_patron), (0, 255, 0), markerType=cv2.MARKER_CROSS, markerSize=15, thickness=2)
                    cv2.drawMarker(frame_mostrar, (cx_iris, cy_iris), (255, 0, 0), markerType=cv2.MARKER_CROSS, markerSize=15, thickness=2)
                    # Círculo del patrón (verde)
                    cv2.circle(frame_mostrar, (cx_patron, cy_patron), r_patron, (0, 255, 0), 2)
                    # Círculo del iris (azul)
                    cv2.circle(frame_mostrar, (cx_iris, cy_iris), r_iris, (255, 0, 0), 2)

                    # Captura automática si está alineado
                    # Verificar alineación
                    delta = np.linalg.norm([cx_patron - cx_iris, cy_patron - cy_iris])
                    self.historial_alineacion.append(delta)
                    if len(self.historial_alineacion) > 10:
                        self.historial_alineacion.pop(0)

                    # Requiere al menos 5 frames consecutivos dentro del umbral
                    if self.auto_captura_activada and all(d < 15 for d in self.historial_alineacion[-5:]):
                        print("🟢 Estable y alineado. Capturando automáticamente...")
                        nombre_archivo = "ojo_derecho.jpg" if self.escaneando_derecho else "ojo_izquierdo.jpg"
                        cv2.imwrite(nombre_archivo, roi_img)
                        self.procesar_post_captura2(roi_img)
                        self.mostrar_mensaje_exito("¡Captura realizada automáticamente!")
                        break
                    #else:
                        #print(f"🔶 Desalineado o inestable. Δ={delta:.2f}")
                # Líneas guía fijas
                height, width, _ = frame_crop.shape
                cx_fixed, cy_fixed = width // 2, height // 2
                cv2.line(frame_mostrar, (0, cy_fixed), (width, cy_fixed), (0, 0, 255), 2)
                cv2.line(frame_mostrar, (cx_fixed, 0), (cx_fixed, height), (0, 0, 255), 2)
                cv2.rectangle(frame_mostrar,
                              (cx_fixed - lado // 2, cy_fixed - lado // 2),
                              (cx_fixed + lado // 2, cy_fixed + lado // 2),
                              (0, 0, 255), 2)

                # Mostrar en interfaz
                _, buf = cv2.imencode(".jpg", frame_mostrar)
                img_base64 = buf.tobytes()
                self.imagen_preview.src_base64 = base64.b64encode(img_base64).decode('utf-8')
                self.page.update()

            await asyncio.sleep(0.05)
            
    def capturar(self, e):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                h, w, _ = frame.shape
                crop_h = int(h * 0.7)
                crop_w = int(w * 0.7)
                start_y = (h - crop_h) // 2
                start_x = (w - crop_w) // 2
                frame = frame[start_y:start_y+crop_h, start_x:start_x+crop_w]

                kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
                #frame = cv2.filter2D(frame, -1, kernel)

                filename = "ojo_derecho.jpg" if self.escaneando_derecho else "ojo_izquierdo.jpg"
                cv2.imwrite(filename, frame)
                self.procesar_post_captura(frame)

    def aplicar_zoom_muestra(self):
        if self.imagen_original is None:
            return

        frame = self.imagen_original.copy()
        h, w, _ = frame.shape

        zoom_factor = self.zoom_muestra
        zoom_h = int(h / zoom_factor)
        zoom_w = int(w / zoom_factor)

        start_y = (h - zoom_h) // 2
        start_x = (w - zoom_w) // 2

        frame_zoom = frame[start_y:start_y + zoom_h, start_x:start_x + zoom_w]
        frame_zoom = cv2.resize(frame_zoom, (1200, 700), interpolation=cv2.INTER_LINEAR)

        _, buf = cv2.imencode(".jpg", frame_zoom)
        img_base64 = buf.tobytes()
        self.imagen_preview.src_base64 = base64.b64encode(img_base64).decode("utf-8")
        self.page.update()


    def borrar(self, e):
        ojo = "ojo_derecho.jpg" if self.escaneando_derecho else "ojo_izquierdo.jpg"
        if os.path.exists(ojo):
            os.remove(ojo)

        self.captura_realizada = False
        self.zoom_slider_preview.visible = False
        self.zoom_muestra = 1.0
        self.zoom_slider.visible = True
        self.focus_slider.visible = True
        self.imagen_original = None
        self.imagen_preview.width = 1200
        self.imagen_preview.height = 700
        self.borrar_btn.disabled = True
        self.capturar_btn.disabled = False
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
        frame_resized = cv2.resize(frame, (1200, 700), interpolation=cv2.INTER_LINEAR)
        _, buf = cv2.imencode(".jpg", frame_resized)
        img_base64 = buf.tobytes()
        self.imagen_preview.src_base64 = base64.b64encode(img_base64).decode("utf-8")

        self.captura_realizada = True
        self.zoom_slider_preview.visible = True
        self.actualizar_textos()
        self.borrar_btn.disabled = False
        self.capturar_btn.disabled = True
        self.continuar_btn.disabled = False
        self.zoom_slider.visible = False
        self.focus_slider.visible = False
        self.page.update()

    def procesar_post_captura2(self, frame):
        self.imagen_original = frame.copy()

        # Forzar ajuste visual correcto
        frame_resized = cv2.resize(frame, (700, 700), interpolation=cv2.INTER_LINEAR)
        _, buf = cv2.imencode(".jpg", frame_resized)
        img_base64 = buf.tobytes()
        self.imagen_preview.src_base64 = base64.b64encode(img_base64).decode("utf-8")

        self.captura_realizada = True
        self.zoom_slider_preview.visible = True
        self.actualizar_textos()
        self.borrar_btn.disabled = False
        self.capturar_btn.disabled = True
        self.continuar_btn.disabled = False
        self.zoom_slider.visible = False
        self.focus_slider.visible = False
        self.page.update()

    def cambiar_zoom(self, e):
        if hasattr(self, 'cap') and self.cap.isOpened():
            if not self.cap.set(cv2.CAP_PROP_ZOOM, self.zoom_slider.value):
                print("[ERROR] No se pudo cambiar el zoom")
            valor_actual = self.cap.get(cv2.CAP_PROP_ZOOM)
            print(f"[INFO] Zoom actual: {valor_actual}")

    def cambiar_enfoque(self, e):
        if hasattr(self, 'cap') and self.cap.isOpened():
            if not self.cap.set(cv2.CAP_PROP_FOCUS, self.focus_slider.value):
                print("[ERROR] No se pudo cambiar el enfoque")
            valor_actual = self.cap.get(cv2.CAP_PROP_FOCUS)
            print(f"[INFO] Enfoque actual: {valor_actual}")


    def zoom_muestra_changed(self, e):
        self.zoom_muestra = e.control.value
        self.aplicar_zoom_muestra()

    def cambiar_ojo(self, e):
        self.escaneando_derecho = not self.escaneando_derecho
        self.actualizar_textos()
        ojo = "derecho" if self.escaneando_derecho else "izquierdo"
        path = f"ojo_{ojo}.jpg"

        if os.path.exists(path):
            frame = cv2.imread(path)
            self.imagen_original = frame.copy()
            self.aplicar_zoom_muestra()
            self.zoom_slider_preview.visible = True
            self.captura_realizada = True
            self.borrar_btn.disabled = False
            self.capturar_btn.disabled = True
            self.zoom_slider.visible = False
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
        self.zoom_slider.visible = False
        self.focus_slider.visible = False
        self.page.update()
    
    def mostrar_mensaje_exito(self, texto):
        dlg = ft.AlertDialog(
            title=ft.Text(texto, text_align="center", size=18),
            actions=[ft.TextButton("Aceptar", on_click=lambda e: self.page.dialog.close())]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def actualizar_textos(self):
        ojo = "derecho" if self.escaneando_derecho else "izquierdo"
        self.titulo_ojos.value = f"Capturando ojo {ojo}"
        self.estado.value = f"Imagen actual del ojo {ojo}"

    def detectar_patron_e_iris(self, frame, niveles_gris=16, umbral_bin=60):
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            print("no llega imagen")
            return None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.GaussianBlur(gray, (7, 7), 1.5)
        _, binarizada = cv2.threshold(gray_blur, 50, 255, cv2.THRESH_BINARY_INV)

        contornos, _ = cv2.findContours(binarizada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contornos:
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            if 100 <= radius <= 160:
                print("✅ Radio en rango para iris.")
                center = (int(x), int(y))
                radius = int(radius)
                print(radius)
                mask = np.zeros_like(gray)
                cv2.drawContours(mask, [cnt], -1, 255, -1)
                media = cv2.mean(gray, mask=mask)[0]
                if media < 80:
                    print("🟢 Iris validado por oscuridad.")
                    print("iris ok")
                    # Detección de patrón dentro del iris
                    green = frame[:, :, 1]
                    roi_mask = np.zeros_like(gray)
                    cv2.circle(roi_mask, center, radius, 255, -1)
                    green_eq = cv2.equalizeHist(green)
                    green_blur = cv2.GaussianBlur(green_eq, (5, 5), 1.0)
                    binary_green = cv2.adaptiveThreshold(green_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                                        cv2.THRESH_BINARY_INV, 11, 5)
                    puntos_bin = cv2.bitwise_and(binary_green, binary_green, mask=roi_mask)
                    puntos_contornos, _ = cv2.findContours(puntos_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    print(f"🔬 Puntos candidatos en ROI: {len(puntos_contornos)}")

                    puntos = []
                    for pc in puntos_contornos:
                        area = cv2.contourArea(pc)
                        if 4 < area < 120:
                            M = cv2.moments(pc)
                            if M["m00"] != 0:
                                cx = int(M["m10"] / M["m00"])
                                cy = int(M["m01"] / M["m00"])
                                #print("interesante")
                                if cv2.pointPolygonTest(cnt, (cx, cy), False) >= 0:
                                    puntos.append((cx, cy))
                    print(len(puntos))
                    if len(puntos) >= 40:
                        puntos_np = np.array(puntos)
                        (x_p, y_p), r_p = cv2.minEnclosingCircle(puntos_np)

                        # Recorte ROI de la zona alrededor de la pupila
                        x1 = max(center[0] - radius, 0)
                        y1 = max(center[1] - radius, 0)
                        x2 = min(center[0] + radius, frame.shape[1])
                        y2 = min(center[1] + radius, frame.shape[0])
                        roi_img = frame[y1:y2, x1:x2]
                        coords_roi = (x1, y1, x2, y2)

                        return (int(x_p), int(y_p), int(r_p), center[0], center[1], radius, roi_img, coords_roi)

        return None
        
    def activar_captura_automatica(self, e):
        self.auto_captura_activada = True
        self.activar_auto_btn.disabled = True
        self.page.update()

    def calentar_camara(self):
        for _ in range(10):
            self.cap.read()