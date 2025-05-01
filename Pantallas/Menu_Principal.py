from Base_App import Base_App
import flet as ft
import os
from Formulario_subida import Formulario_Subida
from Capturar_Ojos import Capturar_Ojos

class Menu_Principal(Base_App):

    def mostrar(self):
        self.limpiar()
        logo = self.cargar_logo()
        from datetime import datetime
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")

        saludo = ft.Text("Bienvenido, Profesional de salud", size=22, weight="bold", text_align=ft.TextAlign.CENTER)
        fecha = ft.Text(f"Fecha y hora: {fecha_actual}", size=12, color="gray", text_align=ft.TextAlign.CENTER)

        # Sección Evaluación
        seccion_evaluacion = ft.Column([
            ft.Text("Evaluación", size=20, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.ElevatedButton(
                "Conectar dispositivo y escanear córnea",
                on_click=lambda e: self.preparar_captura()
            ),
            ft.ElevatedButton(
                "Subir imagen manualmente",
                on_click=lambda e: Formulario_Subida(self.page).mostrar()
            )
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        # Sección Pendientes
        seccion_pendientes = ft.Column([
            ft.Text("Capturas pendientes", size=20, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.ElevatedButton("Ver capturas locales", on_click=lambda e: ft.SnackBar(ft.Text("Ver capturas pendientes")).open),
            ft.ElevatedButton("Subir capturas pendientes", on_click=lambda e: ft.SnackBar(ft.Text("Subir capturas pendientes")).open)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        # Sección Historial
        seccion_historial = ft.Column([
            ft.Text("Historial y reportes", size=20, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.ElevatedButton("Ver escaneos enviados", on_click=lambda e: ft.SnackBar(ft.Text("Ver historial")).open),
            ft.ElevatedButton("Ver reportes procesados por IA", on_click=lambda e: ft.SnackBar(ft.Text("Ver reportes")).open)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        # Sección Opciones
        seccion_opciones = ft.Column([
            ft.Text("Opciones adicionales", size=20, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.ElevatedButton("Mi perfil", on_click=lambda e: ft.SnackBar(ft.Text("Ver perfil")).open),
            ft.ElevatedButton("Guía rápida de uso", on_click=lambda e: ft.SnackBar(ft.Text("Ver guía")).open)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        def cerrar_sesion(e):
            from Login import Login
            Login(self.page).mostrar()

        cerrar_btn = ft.Container(
            ft.ElevatedButton("Cerrar sesión", on_click=cerrar_sesion, bgcolor=ft.colors.RED_300, color=ft.colors.WHITE),
            alignment=ft.alignment.bottom_left,
            padding=10
        )

        self.page.add(
            ft.Stack([
                ft.Container(
                    ft.Column([
                        logo,
                        saludo,
                        fecha,
                        ft.Divider(),
                        seccion_evaluacion,
                        ft.Divider(),
                        seccion_pendientes,
                        ft.Divider(),
                        seccion_historial,
                        ft.Divider(),
                        seccion_opciones
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=25),
                    alignment=ft.alignment.center,
                    expand=True
                ),
                cerrar_btn
            ])
        )
        self.page.update()

    def preparar_captura(self):
        """Borra las capturas viejas y pasa a Capturar_Ojos."""
        for archivo in ["ojo_derecho.jpg", "ojo_izquierdo.jpg"]:
            if os.path.exists(archivo):
                os.remove(archivo)
        from Capturar_Ojos import Capturar_Ojos
        Capturar_Ojos(self.page).mostrar()