from Pantallas.Base_App import Base_App
import flet as ft
import os
from Pantallas.Formulario_subida import Formulario_Subida
from Pantallas.Ver_Historial import Ver_Historial
from Pantallas.Guia_Uso import Guia_Uso
from Pantallas.Capturas_Pendientes import Capturas_Pendientes

class Menu_Principal(Base_App):

    def mostrar(self):
        self.limpiar()
        logo = self.cargar_logo()
        from datetime import datetime
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")

        saludo = ft.Text(f"Bienvenido, {'Especialista' if self.rol == 'MED' else 'Técnico'}", size=22, weight="bold")
        fecha = ft.Text(f"Fecha y hora: {fecha_actual}", size=12, color="gray")

        # Header fijo
        header = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Cerrar sesión",
                    bgcolor=ft.colors.RED_300,
                    color=ft.colors.WHITE,
                    on_click=self.cerrar_sesion
                ),
                ft.TextButton(
                    content=ft.Row([
                        ft.Icon(ft.icons.PERSON_OUTLINE),
                        ft.Text("Mi perfil", size=14)
                    ],
                    spacing=5,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    on_click=self.ver_perfil
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10
        )

        botones_evaluacion = [
            ft.ElevatedButton("Conectar dispositivo y escanear córnea", on_click=lambda e: self.preparar_captura()),
            ft.ElevatedButton("Subir imagen manualmente", on_click=lambda e: Formulario_Subida(self.page, self.usuario, self.rol).mostrar())
        ]

        botones_pendientes = [
            
            ft.ElevatedButton("Ver capturas pendientes", on_click=lambda e: Capturas_Pendientes(self.page, self.usuario, self.rol).mostrar())
        ]

        botones_historial = [
            ft.ElevatedButton("Ver historial de pacientes", on_click=lambda e: Ver_Historial(self.page, usuario=self.usuario, rol=self.rol).mostrar())
        ]
        boton_guia = [
            ft.ElevatedButton("Guía de Uso", on_click=lambda e: Guia_Uso(self.page, usuario=self.usuario, rol=self.rol).mostrar())
        ]
        # Sección Evaluación
        seccion_evaluacion = ft.Column([
            ft.Text("Evaluación", size=20, weight="bold"),
            *botones_evaluacion
        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,)

        # Sección Capturas pendientes
        seccion_pendientes = ft.Column([
            ft.Text("Capturas pendientes", size=20, weight="bold"),
            *botones_pendientes
        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,)

        # Sección Historial
        seccion_historial = ft.Column([
            ft.Text("Historial y reportes", size=20, weight="bold"),
            *botones_historial
        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,)

        # Sección Opcional
        seccion_opciones = ft.Column([
            ft.Text("Opciones", size=20, weight="bold"),
            *boton_guia
        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,)

        self.page.add(
            ft.Column([
                header,
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
            ], spacing=25, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,)
        )
        self.page.update()

    def cerrar_sesion(self, e):
        from Pantallas.Login import Login
        Login(self.page).mostrar()

    def ver_perfil(self, e):
        ft.SnackBar(ft.Text("Mi perfil (en construcción)")).open

    def preparar_captura(self):
        for archivo in ["ojo_derecho.jpg", "ojo_izquierdo.jpg"]:
            if os.path.exists(archivo):
                os.remove(archivo)
        from Pantallas.Capturar_Ojos import Capturar_Ojos
        Capturar_Ojos(self.page, self.usuario, self.rol).mostrar()
