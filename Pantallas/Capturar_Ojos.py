# === Archivo: Capturar_Ojos.py ===
from Pantallas.Base_App import Base_App
import flet as ft
import cv2
import base64
import asyncio
import os
import numpy as np

class Capturar_Ojos(Base_App):
    def __init__(self, page, usuario=None, rol=None):
        super().__init__(page, usuario, rol)
        self.mostrando_todos = False
        self.zoom_muestra = 1.0
        self.imagen_original = None

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
            min=0, max=255, divisions=20,
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

        self.botones = ft.Row([
            self.capturar_btn, self.borrar_btn, self.cambiar_ojo_btn, self.continuar_btn
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
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.stream_running = True
        self.zoom_slider.visible = True
        self.focus_slider.visible = True
        self.page.update()
        self.page.run_task(self.actualizar_stream)

    async def actualizar_stream(self):
        while self.stream_running:
            ret, frame = self.cap.read()
            if ret and not self.captura_realizada:
                h, w, _ = frame.shape
                crop_h = int(h * 0.7)
                crop_w = int(w * 0.7)
                start_y = (h - crop_h) // 2
                start_x = (w - crop_w) // 2
                frame = frame[start_y:start_y+crop_h, start_x:start_x+crop_w]

                kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
                #frame = cv2.filter2D(frame, -1, kernel)

                height, width, _ = frame.shape
                cx, cy = width // 2, height // 2
                cv2.line(frame, (0, cy), (width, cy), (0, 255, 0), 4)
                cv2.line(frame, (cx, 0), (cx, height), (0, 255, 0), 4)
                cv2.circle(frame, (cx, cy), 12, (0, 255, 0), -1)

                _, buf = cv2.imencode(".jpg", frame)
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
                self.imagen_original = frame.copy()
                self.aplicar_zoom_muestra()

                self.captura_realizada = True

                self.zoom_slider_preview.visible = True
                self.actualizar_textos()
                self.borrar_btn.disabled = False
                self.capturar_btn.disabled = True
                self.continuar_btn.disabled = False
                self.zoom_slider.visible = False
                self.focus_slider.visible = False
                self.page.update()

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
        self.imagen_original = None
        self.imagen_preview.width = 1200
        self.imagen_preview.height = 700
        self.borrar_btn.disabled = True
        self.capturar_btn.disabled = False
        self.continuar_btn.disabled = not (
            os.path.exists("ojo_derecho.jpg") or os.path.exists("ojo_izquierdo.jpg")
        )
        self.actualizar_textos()
        self.page.update()

    def cambiar_zoom(self, e):
        if hasattr(self, 'cap') and self.cap.isOpened():
            if not self.cap.set(cv2.CAP_PROP_ZOOM, self.zoom_slider.value):
                print("[ERROR] No se pudo cambiar el zoom")

    def cambiar_enfoque(self, e):
        if hasattr(self, 'cap') and self.cap.isOpened():
            if not self.cap.set(cv2.CAP_PROP_FOCUS, self.focus_slider.value):
                print("[ERROR] No se pudo cambiar el enfoque")

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

    def actualizar_textos(self):
        ojo = "derecho" if self.escaneando_derecho else "izquierdo"
        self.titulo_ojos.value = f"Capturando ojo {ojo}"
        self.estado.value = f"Imagen actual del ojo {ojo}"
