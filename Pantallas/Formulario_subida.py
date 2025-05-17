from Pantallas.Base_App import Base_App
import flet as ft
import os
import base64
import json
from datetime import datetime, date
from Pantallas.firebase_config import db, bucket
from Pantallas.Generar_Reporte import generar_reporte_pdf

class Formulario_Subida(Base_App):
    def mostrar(self):
        self.limpiar()

        self.ojo_derecho_checked = ft.Checkbox(label="Ojo derecho", value=False)
        self.ojo_izquierdo_checked = ft.Checkbox(label="Ojo izquierdo", value=False)

        self.imagen_derecha = ft.Image(src_base64="", width=250, height=250, visible=False)
        self.imagen_izquierda = ft.Image(src_base64="", width=250, height=250, visible=False)

        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.file_picker2 = ft.FilePicker(on_result=self.on_file2_picked)
        self.page.overlay.extend([self.file_picker, self.file_picker2])

        self.dni = ft.TextField(label="DNI del paciente", expand=True, on_change=self.buscar_paciente)

        self.nombre = ft.TextField(label="Nombre", expand=True, disabled=False)
        self.btn_edit_nombre = ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar nombre", visible=False, on_click=lambda e: self.desbloquear_campo(self.nombre))

        self.apellido = ft.TextField(label="Apellido", expand=True, disabled=False)
        self.btn_edit_apellido = ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar apellido", visible=False, on_click=lambda e: self.desbloquear_campo(self.apellido))

        self.fecha_nac_field = ft.TextField(label="Fecha de nacimiento (dd-mm-aaaa)", expand=True, disabled=False, on_change=self.actualizar_edad_desde_texto)
        self.btn_edit_fecha = ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar fecha", visible=False, on_click=lambda e: self.desbloquear_campo(self.fecha_nac_field))

        self.edad = ft.TextField(label="Edad", expand=True, read_only=True)

        self.sexo = ft.Dropdown(label="Sexo", options=[
            ft.dropdown.Option("Masculino"),
            ft.dropdown.Option("Femenino"),
            ft.dropdown.Option("Otro")
        ], disabled=False)
        self.btn_edit_sexo = ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar sexo", visible=False, on_click=lambda e: self.desbloquear_campo(self.sexo))

        self.numero_contacto = ft.TextField(label="Número de contacto", expand=True, disabled=False)
        self.btn_edit_contacto = ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar número", visible=False, on_click=lambda e: self.desbloquear_campo(self.numero_contacto))

        self.correo_contacto = ft.TextField(label="Correo de contacto", expand=True, disabled=False)
        self.btn_edit_correo = ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar correo", visible=False, on_click=lambda e: self.desbloquear_campo(self.correo_contacto))

        self.observaciones = ft.TextField(label="Observaciones", multiline=True, min_lines=3, expand=True)
        self.resultado = ft.Text("", size=20, weight="bold", text_align=ft.TextAlign.CENTER)

        self.enviar_btn = ft.ElevatedButton("Guardar y Enviar", on_click=self.guardar_todo, bgcolor="green")

        self.page.add(
            ft.Container(
                ft.Column([
                    ft.Text("Subir escaneo y registrar paciente", size=24, weight="bold"),
                    ft.Row([self.ojo_derecho_checked, ft.ElevatedButton("Seleccionar imagen ojo derecho", on_click=self.seleccionar_derecha)]),
                    self.imagen_derecha,
                    ft.Row([self.ojo_izquierdo_checked, ft.ElevatedButton("Seleccionar imagen ojo izquierdo", on_click=self.seleccionar_izquierda)]),
                    self.imagen_izquierda,
                    self.dni,
                    ft.Row([self.nombre, self.btn_edit_nombre]),
                    ft.Row([self.apellido, self.btn_edit_apellido]),
                    ft.Row([self.fecha_nac_field, self.btn_edit_fecha]),
                    self.edad,
                    ft.Row([self.sexo, self.btn_edit_sexo]),
                    ft.Row([self.numero_contacto, self.btn_edit_contacto]),
                    ft.Row([self.correo_contacto, self.btn_edit_correo]),
                    self.observaciones,
                    self.enviar_btn,
                    self.resultado
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.START),
                expand=True,
                alignment=ft.alignment.top_center
            )
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
            self.path_derecha = e.files[0].path
            with open(self.path_derecha, "rb") as f:
                self.imagen_derecha.src_base64 = base64.b64encode(f.read()).decode("utf-8")
                self.imagen_derecha.visible = True
            self.page.update()

    def on_file2_picked(self, e):
        if e.files:
            self.path_izquierda = e.files[0].path
            with open(self.path_izquierda, "rb") as f:
                self.imagen_izquierda.src_base64 = base64.b64encode(f.read()).decode("utf-8")
                self.imagen_izquierda.visible = True
            self.page.update()

    def actualizar_edad_desde_texto(self, e):
        texto_fecha = self.fecha_nac_field.value.strip()
        try:
            fecha_dt = datetime.strptime(texto_fecha, "%d-%m-%Y").date()
            hoy = date.today()
            edad = hoy.year - fecha_dt.year - ((hoy.month, hoy.day) < (fecha_dt.month, fecha_dt.day))
            self.edad.value = str(edad)
        except:
            self.edad.value = ""
        self.page.update()

    def buscar_paciente(self, e):
        dni = self.dni.value.strip()
        if len(dni) < 8:
            return

        self.nombre.value = ""
        self.apellido.value = ""
        self.fecha_nac_field.value = ""
        self.edad.value = ""
        self.sexo.value = ""
        self.numero_contacto.value = ""
        self.correo_contacto.value = ""

        self.nombre.disabled = False
        self.apellido.disabled = False
        self.fecha_nac_field.disabled = False
        self.sexo.disabled = False
        self.numero_contacto.disabled = False
        self.correo_contacto.disabled = False

        self.btn_edit_nombre.visible = False
        self.btn_edit_apellido.visible = False
        self.btn_edit_fecha.visible = False
        self.btn_edit_sexo.visible = False
        self.btn_edit_contacto.visible = False
        self.btn_edit_correo.visible = False

        try:
            doc = db.collection("pacientes_base").document(dni).get()
            if doc.exists:
                data = doc.to_dict()
                self.nombre.value = data.get("nombre", "")
                self.nombre.disabled = True
                self.btn_edit_nombre.visible = True

                self.apellido.value = data.get("apellido", "")
                self.apellido.disabled = True
                self.btn_edit_apellido.visible = True

                fecha_str = data.get("fecha_nacimiento", "")
                if fecha_str:
                    self.fecha_nac_field.value = fecha_str
                    try:
                        fecha_dt = datetime.strptime(fecha_str, "%d-%m-%Y").date()
                        self.edad.value = str(self.calcular_edad(fecha_dt))
                    except:
                        pass
                self.fecha_nac_field.disabled = True
                self.btn_edit_fecha.visible = True

                self.edad.disabled = True

                self.sexo.value = data.get("sexo", "")
                self.sexo.disabled = True
                self.btn_edit_sexo.visible = True

                self.numero_contacto.value = data.get("numero_contacto", "")
                self.numero_contacto.disabled = True
                self.btn_edit_contacto.visible = True

                self.correo_contacto.value = data.get("correo_contacto", "")
                self.correo_contacto.disabled = True
                self.btn_edit_correo.visible = True

        except Exception as err:
            print(f"[ERROR] al buscar paciente: {err}")

        self.page.update()

    def desbloquear_campo(self, campo):
        campo.disabled = False
        self.page.update()

    def calcular_edad(self, fecha):
        hoy = date.today()
        return hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))

    def guardar_todo(self, e):
        if not (self.nombre.value and self.apellido.value and self.dni.value and self.fecha_nac_field.value and self.sexo.value):
            self.resultado.value = "Faltan datos obligatorios."
            self.resultado.color = "red"
            self.page.update()
            return

        self.resultado.value = "Guardando..."
        self.resultado.color = "black"
        self.enviar_btn.disabled = True
        self.page.update()

        fecha = datetime.now().strftime("%d-%m-%Y")
        hora = datetime.now().strftime("%H:%M:%S")

        datos = {
            "nombre": self.nombre.value,
            "apellido": self.apellido.value,
            "dni": self.dni.value,
            "fecha_nacimiento": self.fecha_nac_field.value,
            "edad": self.edad.value,
            "sexo": self.sexo.value,
            "numero_contacto": self.numero_contacto.value,
            "correo_contacto": self.correo_contacto.value,
            "observaciones": self.observaciones.value,
            "fecha_registro": fecha,
            "hora_registro": hora,
            "tecnico_id": self.usuario if self.usuario else "offline"
        }

        if hasattr(self, "path_derecha"):
            blob = bucket.blob(f"pacientes/{self.dni.value}/{fecha}/imagenes/ojo_derecho.jpg")
            blob.upload_from_filename(self.path_derecha)
            datos["url_ojo_derecho"] = blob.public_url

        if hasattr(self, "path_izquierda"):
            blob = bucket.blob(f"pacientes/{self.dni.value}/{fecha}/imagenes/ojo_izquierdo.jpg")
            blob.upload_from_filename(self.path_izquierda)
            datos["url_ojo_izquierdo"] = blob.public_url

        db.collection("pacientes").document(self.dni.value).collection("registros").document(fecha).set(datos)
        db.collection("pacientes_base").document(self.dni.value).set({
            "nombre": self.nombre.value,
            "apellido": self.apellido.value,
            "fecha_nacimiento": self.fecha_nac_field.value,
            "sexo": self.sexo.value,
            "numero_contacto": self.numero_contacto.value,
            "correo_contacto": self.correo_contacto.value
        }, merge=True)

        generar_reporte_pdf(datos)

        self.resultado.value = "Datos enviados correctamente."
        self.resultado.color = "green"
        self.page.update()
