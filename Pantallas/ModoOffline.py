# === Archivo: ModoOffline.py ===
from Base_App import Base_App
from Menu_Offline import Menu_Offline

class ModoOffline(Base_App):
    def mostrar(self):
        self.limpiar()
        import flet as ft

        def seguir(e):
            Menu_Offline(self.page).mostrar()

        def reintentar(e):
            from ControladorConexion import ControladorConexion
            ControladorConexion(self.page).verificar_estado()

        self.page.add(
            ft.Column([
                ft.Text("No hay conexión a Internet", size=28, weight="bold", color="red"),
                ft.Text("Puedes seguir trabajando en modo offline o reintentar."),
                ft.Row([
                    ft.ElevatedButton("Seguir sin conexión", on_click=seguir),
                    ft.ElevatedButton("Reintentar", on_click=reintentar)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20, expand=True)
        )
        self.page.update()