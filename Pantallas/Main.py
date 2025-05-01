import flet as ft
from Login import Login

# === Archivo: Main.py ===
import flet as ft
from ControladorConexion import ControladorConexion

async def main(page: ft.Page):
    page.title = "KeratoTECH - Sistema de Escaneo Ocular"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = "#aebee8"

    controlador = ControladorConexion(page)
    controlador.verificar_estado()

ft.app(target=main)