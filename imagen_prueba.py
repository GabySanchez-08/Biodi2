import flet as ft
import base64
import os


# Función auxiliar para convertir imagen a base64 para previsualización
def imagen_a_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return None

def main(page: ft.Page):
    page.title = "Subir escaneo y datos del paciente"
    page.scroll = ft.ScrollMode.AUTO

    # Estados
    ojo_derecho_checked = ft.Checkbox(label="Ojo derecho", value=False)
    ojo_izquierdo_checked = ft.Checkbox(label="Ojo izquierdo", value=False)

    imagen_derecha = ft.Image(src_base64="", width=250, height=250, visible=False)
    imagen_izquierda = ft.Image(src_base64="", width=250, height=250, visible=False)

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

    # File pickers
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

    # Formulario paciente
    nombre = ft.TextField(label="Nombre del paciente", expand=True)
    dni = ft.TextField(label="DNI", expand=True)
    edad = ft.TextField(label="Edad", expand=True)
    sexo = ft.Dropdown(label="Sexo", options=[ft.dropdown.Option("Masculino"), ft.dropdown.Option("Femenino"), ft.dropdown.Option("Otro")])
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

ft.app(target=main)