from Pantallas.Base_App import Base_App
import flet as ft
import os
import base64
import json
from datetime import datetime
from Pantallas.firebase_config import db, bucket
from Pantallas.Generar_Reporte import generar_reporte_pdf

class Formulario_Subida(Base_App):
    def mostrar(self):
        self.limpiar()

        # Crear campos de formulario
        self.nombre = ft.TextField(label="Nombre del paciente", expand=True)
        self.dni = ft.TextField(label="DNI", expand=True)
        self.edad = ft.TextField(label="Edad", expand=True)
        self.sexo = ft.Dropdown(label="Sexo", options=[
            ft.dropdown.Option("Masculino"),
            ft.dropdown.Option("Femenino"),
            ft.dropdown.Option("Otro")
        ])
        self.observaciones = ft.TextField(label="Observaciones", multiline=True, min_lines=3, expand=True)
        self.resultado = ft.Text("", size=16)

        # Checkbox e imágenes
        self.ojo_derecho_checked = ft.Checkbox(label="Ojo derecho", value=False)
        self.ojo_izquierdo_checked = ft.Checkbox(label="Ojo izquierdo", value=False)

        self.imagen_derecha = ft.Image(src_base64="", width=250, height=250, visible=False)
        self.imagen_izquierda = ft.Image(src_base64="", width=250, height=250, visible=False)

        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.file_picker2 = ft.FilePicker(on_result=self.on_file2_picked)
        self.page.overlay.extend([self.file_picker, self.file_picker2])
        self.enviar_btn = ft.ElevatedButton("Guardar y Enviar", on_click=self.guardar_todo, bgcolor="green")
        self.page.add(
            ft.Stack([
                ft.Container(
                    ft.Column([
                        ft.TextButton("← Volver al menú", on_click=self.volver_menu),
                        self.cargar_logo(),
                        ft.Text("Subir escaneo y registrar paciente", size=24, weight="bold"),
                        ft.Row([
                            self.ojo_derecho_checked,
                            ft.ElevatedButton("Seleccionar imagen ojo derecho", on_click=self.seleccionar_derecha)
                        ]),
                        self.imagen_derecha,
                        ft.Row([
                            self.ojo_izquierdo_checked,
                            ft.ElevatedButton("Seleccionar imagen ojo izquierdo", on_click=self.seleccionar_izquierda)
                        ]),
                        self.imagen_izquierda,
                        ft.Divider(),
                        self.nombre, self.dni, self.edad, self.sexo, self.observaciones,
                        self.enviar_btn,
                        self.resultado
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20),
                    alignment=ft.alignment.center,
                    expand=True
                )
            ])
        )
        self.page.update()

    def seleccionar_derecha(self, e):
        if self.ojo_derecho_checked.value:
            self.file_picker.pick_files(allow_multiple=False, dialog_title="Seleccionar imagen ojo derecho")
        else:
            self.imagen_derecha.visible = False
            self.page.update()

    def seleccionar_izquierda(self, e):
        if self.ojo_izquierdo_checked.value:
            self.file_picker2.pick_files(allow_multiple=False, dialog_title="Seleccionar imagen ojo izquierdo")
        else:
            self.imagen_izquierda.visible = False
            self.page.update()

    def on_file_picked(self, e):
        if e.files:
            with open(e.files[0].path, "rb") as f:
                self.imagen_derecha.src_base64 = base64.b64encode(f.read()).decode("utf-8")
                self.imagen_derecha.visible = True
                self.page.update()

    def on_file2_picked(self, e):
        if e.files:
            with open(e.files[0].path, "rb") as f:
                self.imagen_izquierda.src_base64 = base64.b64encode(f.read()).decode("utf-8")
                self.imagen_izquierda.visible = True
                self.page.update()

    def guardar_todo(self, e):
        if not (self.nombre.value and self.dni.value and self.edad.value and self.sexo.value):
            self.resultado.value = "Faltan datos obligatorios."
            self.resultado.color = "red"
            self.page.update()
            return

        # Mostrar ruedita de carga
        self.resultado.value = "Enviando datos..."
        self.resultado.color = "black"
        self.enviar_btn.disabled = True
        self.page.update()

        fecha = datetime.now().strftime("%d-%m-%Y")
        hora = datetime.now().strftime("%H:%M:%S")

        datos = {
            "nombre": self.nombre.value,
            "dni": self.dni.value,
            "edad": self.edad.value,
            "sexo": self.sexo.value,
            "observaciones": self.observaciones.value,
            "fecha_registro": fecha,
            "hora_registro": hora,
            "tecnico_id": self.usuario if self.usuario else "offline"
        }

        # Subir imágenes si existen
        if self.imagen_derecha.visible and self.file_picker.result:
            path_local = self.file_picker.result.files[0].path
            blob = bucket.blob(f"pacientes/{self.dni.value}/{fecha}/imagenes/ojo_derecho.jpg")
            blob.upload_from_filename(path_local)
            datos["url_ojo_derecho"] = blob.public_url

        if self.imagen_izquierda.visible and self.file_picker2.result:
            path_local = self.file_picker2.result.files[0].path
            blob = bucket.blob(f"pacientes/{self.dni.value}/{fecha}/imagenes/ojo_izquierdo.jpg")
            blob.upload_from_filename(path_local)
            datos["url_ojo_izquierdo"] = blob.public_url

        # Subir JSON local
        path_json_local = f"{self.dni.value}_formulario.json"
        with open(path_json_local, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)

        blob_formulario = bucket.blob(f"pacientes/{self.dni.value}/{fecha}/formulario.json")
        blob_formulario.upload_from_filename(path_json_local)

        db.collection("pacientes").document(self.dni.value).collection("registros").document(fecha).set(datos)

        if os.path.exists(path_json_local):
            os.remove(path_json_local)

        # 🔽 Generar reporte PDF
        generar_reporte_pdf(datos)

        # Eliminar imágenes locales
        for archivo in ["ojo_derecho.jpg", "ojo_izquierdo.jpg"]:
            if os.path.exists(archivo):
                os.remove(archivo)

        self.mostrar_confirmacion()
        self.mostrar_confirmacion()

    def mostrar_confirmacion(self):
        self.page.clean()
        boton_menu = ft.ElevatedButton("Volver al menú principal", on_click=self.volver_menu, bgcolor="blue", color="white")

        contenido = ft.Column([
            self.cargar_logo(),
            ft.Text("Datos enviados correctamente", size=24, weight="bold", color="green", text_align=ft.TextAlign.CENTER),
            boton_menu
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=30)

        self.page.add(
            ft.Container(
                content=contenido,
                alignment=ft.alignment.center,
                expand=True
            )
        )
        self.page.update()

    def volver_menu(self, e):
        from Pantallas.Menu_Principal import Menu_Principal
        Menu_Principal(self.page, usuario=self.usuario, rol=self.rol).mostrar()