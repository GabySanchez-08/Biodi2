# === Archivo: Menu_Offline.py ===
from Base_App import Base_App
import flet as ft

class Menu_Offline(Base_App):
    def mostrar(self):
        self.limpiar()
        logo = self.cargar_logo()
        from datetime import datetime
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")

        saludo = ft.Text("Modo sin conexión", size=22, weight="bold", color="orange", text_align=ft.TextAlign.CENTER)
        fecha = ft.Text(f"Fecha y hora: {fecha_actual}", size=12, color="gray", text_align=ft.TextAlign.CENTER)

        # Sección Evaluación Offline
        seccion_evaluacion = ft.Column([
            ft.Text("Captura local", size=20, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.ElevatedButton("Conectar dispositivo y capturar imagen", on_click=lambda e: ft.SnackBar(ft.Text("Captura offline")).open),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        # Sección Pendientes
        seccion_pendientes = ft.Column([
            ft.Text("Capturas pendientes", size=20, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.ElevatedButton("Ver capturas locales", on_click=lambda e: ft.SnackBar(ft.Text("Ver capturas pendientes")).open)
            # Aquí no sube porque no hay conexión
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)


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
                        seccion_pendientes
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=25),
                    alignment=ft.alignment.center,
                    expand=True
                ),
            ])
        )
        self.page.update()