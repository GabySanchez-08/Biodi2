import flet as ft
from Pantallas.ControladorConexion import ControladorConexion

async def main(page: ft.Page):
    page.title = "KeratoTECH - Sistema de Escaneo Ocular"

    # ✅ Pantalla completa (no necesita await)
    page.window_maximized = True
    # También puedes usar esto para modo kiosko:
    # page.window_full_screen = True

    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = ft.Colors.BLUE_50
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE_900)

    # Verificar conexión y mostrar pantalla inicial
    controlador = ControladorConexion(page)
    controlador.verificar_estado()


# ✅ Ejecutar en entorno asincrónico
import asyncio

if __name__ == "__main__":
    asyncio.run(ft.app_async(target=main, view=ft.AppView.FLET_APP))