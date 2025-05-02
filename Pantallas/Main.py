# === Archivo: Main.py ===
import flet as ft
from Login import Login
from ControladorConexion import ControladorConexion

async def main(page: ft.Page):
    page.title = "KeratoTECH - Sistema de Escaneo Ocular"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = ft.Colors.BLUE_50  # Fondo azul claro profesional

    # Establece el tema con semilla de color azul oscuro
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE_900)

    # Verificar conexión y cargar vista inicial
    controlador = ControladorConexion(page)
    controlador.verificar_estado()

ft.app(target=main)