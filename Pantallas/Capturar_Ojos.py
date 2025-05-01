# === Archivo: Capturar_Ojos.py ===
from Base_App import Base_App
import flet as ft
import cv2
import base64
import asyncio
import os

class Capturar_Ojos(Base_App):
    def mostrar(self):
        self.limpiar()

        self.escaneando_derecho = True
        self.captura_realizada = False
        self.stream_running = False
        self.camera_index = 0
        self.available_cameras = self.detectar_camaras()

        self.imagen_preview = ft.Image(width=400, height=400, fit=ft.ImageFit.CONTAIN)
        self.titulo_ojos = ft.Text("Capturando ojo derecho", size=20, weight="bold")
        self.estado = ft.Text("Imagen actual del ojo derecho", size=16, weight="bold")

        self.dropdown_camaras = ft.Dropdown(
            label="Selecciona una cámara",
            options=[ft.dropdown.Option(str(i)) for i in self.available_cameras],
            value=str(self.camera_index),
            on_change=self.cambiar_camara
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
                        self.estado,
                        self.botones
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
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
        self.stream_running = True
        self.page.run_task(self.actualizar_stream)

    async def actualizar_stream(self):
        while self.stream_running:
            ret, frame = self.cap.read()
            if ret and not self.captura_realizada:
                _, buf = cv2.imencode(".jpg", frame)
                img_base64 = buf.tobytes()
                self.imagen_preview.src_base64 = base64.b64encode(img_base64).decode('utf-8')
                self.page.update()
            await asyncio.sleep(0.05)

    def capturar(self, e):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                filename = "ojo_derecho.jpg" if self.escaneando_derecho else "ojo_izquierdo.jpg"
                cv2.imwrite(filename, frame)
                _, buf = cv2.imencode(".jpg", frame)
                img_base64 = buf.tobytes()
                self.imagen_preview.src_base64 = base64.b64encode(img_base64).decode('utf-8')
                self.captura_realizada = True
                self.actualizar_textos()
                self.borrar_btn.disabled = False
                self.capturar_btn.disabled = True
                self.continuar_btn.disabled = False
                self.page.update()

    def borrar(self, e):
        ojo = "ojo_derecho.jpg" if self.escaneando_derecho else "ojo_izquierdo.jpg"
        if os.path.exists(ojo):
            os.remove(ojo)
        self.captura_realizada = False
        self.borrar_btn.disabled = True
        self.capturar_btn.disabled = False
        self.continuar_btn.disabled = not (os.path.exists("ojo_derecho.jpg") or os.path.exists("ojo_izquierdo.jpg"))
        self.actualizar_textos()
        self.page.update()

    def cambiar_ojo(self, e):
        self.escaneando_derecho = not self.escaneando_derecho
        self.actualizar_textos()

        ojo = "derecho" if self.escaneando_derecho else "izquierdo"
        if os.path.exists(f"ojo_{ojo}.jpg"):
            frame = cv2.imread(f"ojo_{ojo}.jpg")
            _, buf = cv2.imencode(".jpg", frame)
            img_base64 = buf.tobytes()
            self.imagen_preview.src_base64 = base64.b64encode(img_base64).decode('utf-8')
            self.captura_realizada = True
            self.borrar_btn.disabled = False
            self.capturar_btn.disabled = True
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
        from Formulario_Paciente import Formulario_Paciente
        Formulario_Paciente(self.page).mostrar()

    def volver_menu(self, e):
        print("[INFO] Botón 'Volver al menú' presionado")
        self.detener_stream()
        from Menu_Principal import Menu_Principal
        Menu_Principal(self.page).mostrar()

    def detener_stream(self):
        self.stream_running = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

    def actualizar_textos(self):
        ojo = "derecho" if self.escaneando_derecho else "izquierdo"
        self.titulo_ojos.value = f"Capturando ojo {ojo}"
        self.estado.value = f"Imagen actual del ojo {ojo}"