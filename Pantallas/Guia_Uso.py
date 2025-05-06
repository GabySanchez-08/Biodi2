from Pantallas.Base_App import Base_App
import flet as ft
import base64, os

class Guia_Uso(Base_App):
    def __init__(self, page, usuario=None, rol=None):
        super().__init__(page, usuario, rol)
        self.paso_actual = 0
        self.pasos = [
            {"titulo": "Paso 1", "descripcion": "Abre la aplicación y conecta el dispositivo.", "imagen": "assets/Logo_app.png"},
            {"titulo": "Paso 2", "descripcion": "Selecciona la opción 'Escanear'.", "imagen": "assets/Logo_app.png"},
            {"titulo": "Paso 3", "descripcion": "Captura la imagen del ojo correctamente centrada.", "imagen": "assets/Logo_app.png"},
            {"titulo": "Paso 4", "descripcion": "Guarda y continúa al formulario del paciente.", "imagen": "assets/Logo_app.png"},
        ]

    def mostrar(self):
        self.limpiar()

        self.titulo = ft.Text(self.pasos[self.paso_actual]["titulo"], size=20, weight="bold")
        self.descripcion = ft.Text(self.pasos[self.paso_actual]["descripcion"], size=16)
        self.imagen = self.cargar_imagen(self.pasos[self.paso_actual]["imagen"])

        self.flecha_atras = ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=self.anterior_paso)
        self.flecha_adelante = ft.IconButton(icon=ft.icons.ARROW_FORWARD, on_click=self.siguiente_paso)

        self.boton_mostrar_video = ft.TextButton(
            "▶ Ver video explicativo",
            url="https://firebasestorage.googleapis.com/v0/b/keratotech-66ab6.firebasestorage.app/o/assets%2Ftutorial.mp4?alt=media&token=8d23252a-a5a1-4ae3-b9c9-10ee6ce723e2",
            style=ft.ButtonStyle(color=ft.colors.BLUE),
        )

        self.pantalla = ft.Column([
            ft.TextButton("← Volver al menú", on_click=self.volver_menu),
            self.cargar_logo(),
            ft.Container(
                content=ft.Column([
                    self.titulo,
                    self.descripcion,
                    self.imagen,
                    ft.Row([self.flecha_atras, self.flecha_adelante], alignment=ft.MainAxisAlignment.CENTER),
                    self.boton_mostrar_video
                ],
                spacing=15,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                padding=20,
                bgcolor=ft.colors.GREY_100,
                border_radius=10
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.page.add(self.pantalla)
        self.page.update()

    def actualizar_pantalla(self):
        self.titulo.value = self.pasos[self.paso_actual]["titulo"]
        self.descripcion.value = self.pasos[self.paso_actual]["descripcion"]
        self.imagen.src_base64 = self.get_base64(self.pasos[self.paso_actual]["imagen"])
        self.page.update()

    def siguiente_paso(self, e):
        if self.paso_actual < len(self.pasos) - 1:
            self.paso_actual += 1
            self.actualizar_pantalla()

    def anterior_paso(self, e):
        if self.paso_actual > 0:
            self.paso_actual -= 1
            self.actualizar_pantalla()

    def volver_menu(self, e):
        from Pantallas.Menu_Principal import Menu_Principal
        Menu_Principal(self.page, self.usuario, self.rol).mostrar()

    def cargar_imagen(self, ruta, ancho=300):
        img_base64 = self.get_base64(ruta)
        return ft.Image(src_base64=img_base64, width=ancho, height=ancho) if img_base64 else ft.Text("Imagen no disponible")

    def get_base64(self, ruta):
        try:
            if os.path.exists(ruta):
                with open(ruta, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            print(f"[ERROR] No se pudo cargar la imagen: {e}")
        return None