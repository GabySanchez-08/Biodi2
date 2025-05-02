from Base_App import Base_App
import flet as ft
import os
from Formulario_subida import Formulario_Subida
from Capturar_Ojos import Capturar_Ojos
from Ver_Historial import Ver_Historial  # Suponiendo que tengas este módulo

class Menu_Principal(Base_App):

    def mostrar(self):
        self.limpiar()
        logo = self.cargar_logo()
        from datetime import datetime
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")

        saludo = ft.Text(f"Bienvenido, {'Especialista' if self.rol == 'MED' else 'Técnico'}", size=22, weight="bold", text_align=ft.TextAlign.CENTER)
        fecha = ft.Text(f"Fecha y hora: {fecha_actual}", size=12, color="gray", text_align=ft.TextAlign.CENTER)

        botones_evaluacion = [
            ft.ElevatedButton("Conectar dispositivo y escanear córnea", on_click=lambda e: self.preparar_captura()),
            ft.ElevatedButton("Subir imagen manualmente", on_click=lambda e: Formulario_Subida(self.page, self.usuario, self.rol).mostrar())
        ]

        botones_pendientes = [
            ft.ElevatedButton("Ver capturas locales", on_click=lambda e: ft.SnackBar(ft.Text("Ver capturas locales")).open),
            ft.ElevatedButton("Subir capturas pendientes", on_click=lambda e: ft.SnackBar(ft.Text("Subir capturas pendientes")).open)
        ]

        botones_historial = [
            ft.ElevatedButton("Ver historial de pacientes", on_click=lambda e: Ver_Historial(self.page).mostrar())
        ]

        # Sección Evaluación
        seccion_evaluacion = ft.Column([
            ft.Text("Evaluación", size=20, weight="bold"),
            *botones_evaluacion
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        # Sección Capturas pendientes
        seccion_pendientes = ft.Column([
            ft.Text("Capturas pendientes", size=20, weight="bold"),
            *botones_pendientes
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        # Sección Historial
        seccion_historial = ft.Column([
            ft.Text("Historial y reportes", size=20, weight="bold"),
            *botones_historial
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        # Sección Opcional
        seccion_opciones = ft.Column([
            ft.Text("Opciones", size=20, weight="bold"),
            ft.ElevatedButton("Mi perfil", on_click=lambda e: ft.SnackBar(ft.Text("Perfil")).open),
            ft.ElevatedButton("Guía rápida de uso", on_click=lambda e: ft.SnackBar(ft.Text("Guía")).open)
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
        #Borra las capturas viejas en el caché para comenzar de 0
        for archivo in ["ojo_derecho.jpg", "ojo_izquierdo.jpg"]:
            if os.path.exists(archivo):
                os.remove(archivo)
        from Capturar_Ojos import Capturar_Ojos
        Capturar_Ojos(self.page, self.usuario, self.rol).mostrar()