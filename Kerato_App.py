import flet as ft
from PIL import Image
import base64
import asyncio
import os

# Función que cargará el logo de nuestro aplicativo

def cargar_logo():
    ruta = "assets/Logo_app.jpg"
    if not os.path.exists(ruta):
        return None
    with open(ruta, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

async def main(page: ft.Page):
    
    page.title = "KERATO TECH - Escaneo y Diagnóstico" #Titulo de la app
    page.bgcolor = "#aebee8" #Color del Fondo de la App
    page.scroll = ft.ScrollMode.AUTO
    
    # Splash screen centrado con logo base64
    logo_base64 = cargar_logo()
    if logo_base64:
        splash = ft.Container(
            content=ft.Column([
                ft.Image(src_base64=logo_base64, width=250, height=250),
                ft.Text("Cargando...", size=18),
                ft.ProgressRing()
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
        page.add(splash)
        page.update()
        await asyncio.sleep(1)
        page.controls.clear()

# FUNCIONES DE CADA PANTALLA
    '''
    # === LOGIN ===
    def mostrar_login():
        user_input = ft.TextField(label="Usuario", autofocus=True)
        pass_input = ft.TextField(label="Contraseña", password=True, can_reveal_password=True)
        mensaje = ft.Text("", size=14)

        def validar_credenciales(e):
            if user_input.value == "admin" and pass_input.value == "1234":
                mostrar_menu_principal()
            else:
                mensaje.value = "Credenciales inválidas"
                mensaje.color = "red"
                page.update()

        login_layout = ft.Column([
            ft.Text("KERATO TECH", size=30, weight="bold", color="#5E35B1"),
            ft.Text("Inicio de sesión", size=20),
            user_input,
            pass_input,
            ft.ElevatedButton("Ingresar", on_click=validar_credenciales),
            mensaje
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        page.controls.clear()
        page.add(login_layout)
        page.update()
    '''
    # === MENÚ PRINCIPAL ===
    def mostrar_menu_principal():
        def navegar_a(nombre):
            page.snack_bar = ft.SnackBar(ft.Text(f"Se presionó: {nombre}"))
            page.snack_bar.open = True
            page.update()

        # Cargar logo en base64
        logo_base64 = cargar_logo()  # Asegúrate de tener esta función en tu código
        logo_img = ft.Image(src_base64=logo_base64, width=200, height=200)

        # Contenido centrado en la pantalla completa
        contenido = ft.Container(
            content=ft.Column([
                logo_img,
                ft.Text("BIENVENIDO", size=26, weight="bold"),
                ft.Text("Seleccione una opción para continuar:", size=18),
                ft.ElevatedButton("Conectar dispositivo", on_click=lambda e: navegar_a("Conectar dispositivo")),
                ft.ElevatedButton("Escanear imagen", on_click=lambda e: navegar_a("Escanear imagen")),
                ft.ElevatedButton("Subir escaneo ya hecho", on_click=mostrar_formulario_subida),
                ft.ElevatedButton("Acceder a archivos anteriores", on_click=lambda e: navegar_a("Archivos previos"))
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )

        page.controls.clear()
        page.add(contenido)
        page.update()
    
    #Cuando la persona elige la opción "SUBIR ESCANEO"
    def mostrar_formulario_subida(e=None):
        page.controls.clear()

        ojo_derecho_checked = ft.Checkbox(label="Ojo derecho", value=False)
        ojo_izquierdo_checked = ft.Checkbox(label="Ojo izquierdo", value=False)

        imagen_derecha = ft.Image(src_base64="", width=250, height=250, visible=False)
        imagen_izquierda = ft.Image(src_base64="", width=250, height=250, visible=False)

        def imagen_a_base64(path):
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            return None

        def seleccionar_derecha(e):
            if ojo_derecho_checked.value:
                file_picker.pick_files(allow_multiple=False, dialog_title="Seleccionar imagen ojo derecho")
            else:
                imagen_derecha.visible = False
                page.update()

        def seleccionar_izquierda(e):
            if ojo_izquierdo_checked.value:
                file_picker2.pick_files(allow_multiple=False, dialog_title="Seleccionar imagen ojo izquierdo")
            else:
                imagen_izquierda.visible = False
                page.update()

        def on_file_picked(e):
            if e.files:
                base64_img = imagen_a_base64(e.files[0].path)
                imagen_derecha.src_base64 = base64_img
                imagen_derecha.visible = True
                page.update()

        def on_file2_picked(e):
            if e.files:
                base64_img = imagen_a_base64(e.files[0].path)
                imagen_izquierda.src_base64 = base64_img
                imagen_izquierda.visible = True
                page.update()

        file_picker = ft.FilePicker(on_result=on_file_picked)
        file_picker2 = ft.FilePicker(on_result=on_file2_picked)
        page.overlay.extend([file_picker, file_picker2])

        nombre = ft.TextField(label="Nombre del paciente", expand=True)
        dni = ft.TextField(label="DNI", expand=True)
        edad = ft.TextField(label="Edad", expand=True)
        sexo = ft.Dropdown(label="Sexo", options=[
            ft.dropdown.Option("Masculino"),
            ft.dropdown.Option("Femenino"),
            ft.dropdown.Option("Otro")
        ])
        observaciones = ft.TextField(label="Observaciones", multiline=True, min_lines=3, expand=True)

        resultado = ft.Text("", size=16)

        def enviar_todo(e):
            campos = [nombre.value, dni.value, edad.value, sexo.value]
            if any(not c for c in campos):
                resultado.value = "Faltan datos obligatorios."
                resultado.color = "red"
            else:
                resultado.value = "Datos enviados correctamente ✅"
                resultado.color = "green"
            page.update()

        enviar_btn = ft.ElevatedButton("Enviar", on_click=enviar_todo, bgcolor="green", color="white")

        page.add(
            ft.Column([
                ft.Text("Subir escaneo y registrar paciente", size=24, weight="bold"),
                ft.Row([ojo_derecho_checked, ft.ElevatedButton("Seleccionar imagen ojo derecho", on_click=seleccionar_derecha)]),
                imagen_derecha,
                ft.Row([ojo_izquierdo_checked, ft.ElevatedButton("Seleccionar imagen ojo izquierdo", on_click=seleccionar_izquierda)]),
                imagen_izquierda,
                ft.Divider(),
                nombre, dni, edad, sexo, observaciones,
                enviar_btn,
                resultado
            ], spacing=15)
        )
        page.update()

    # Opcion 1: Mostrar pantalla de login al cargar
    #mostrar_login()
    # Opcion 2: Iniciar directamente al menu_principal
    mostrar_menu_principal()

ft.app(target=main)
