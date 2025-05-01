# === Archivo: Formulario_Paciente.py ===
from Base_App import Base_App
import flet as ft
import os
from datetime import datetime
from firebase_config import db, bucket

class Formulario_Paciente(Base_App):
    def mostrar(self):
        self.limpiar()

        self.nombre = ft.TextField(label="Nombre del paciente", expand=True)
        self.dni = ft.TextField(label="DNI", expand=True)
        self.edad = ft.TextField(label="Edad", expand=True)
        self.sexo = ft.Dropdown(label="Sexo", options=[
            ft.dropdown.Option("Masculino"),
            ft.dropdown.Option("Femenino"),
            ft.dropdown.Option("Otro")
        ])
        self.observaciones = ft.TextField(label="Observaciones", multiline=True, min_lines=3, expand=True)
        self.resultado = ft.Text("", size=20, weight="bold", text_align=ft.TextAlign.CENTER)

        ojo_derecho_tomado = os.path.exists("ojo_derecho.jpg")
        ojo_izquierdo_tomado = os.path.exists("ojo_izquierdo.jpg")

        if ojo_derecho_tomado and ojo_izquierdo_tomado:
            capturas_info = "Capturas listas: Ojo derecho y ojo izquierdo"
        elif ojo_derecho_tomado:
            capturas_info = "Captura lista: Solo ojo derecho"
        elif ojo_izquierdo_tomado:
            capturas_info = "Captura lista: Solo ojo izquierdo"
        else:
            capturas_info = "No hay capturas disponibles"

        self.capturas_label = ft.Text(capturas_info, size=16, color="blue")

        self.enviar_btn = ft.ElevatedButton("Guardar y Enviar", on_click=self.guardar_todo, bgcolor="green")
        self.boton_volver = ft.Container(
            content=ft.TextButton("← Volver a captura", on_click=self.volver_atras),
            alignment=ft.alignment.top_left,
            padding=10
        )

        self.column_formulario = ft.Column([
            self.cargar_logo(),
            ft.Text("Formulario de paciente", size=24, weight="bold"),
            self.capturas_label,
            self.nombre, self.dni, self.edad, self.sexo, self.observaciones,
            self.enviar_btn,
            self.resultado
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20)

        self.page.add(
            ft.Stack([
                self.boton_volver,
                ft.Container(
                    self.column_formulario,
                    alignment=ft.alignment.center,
                    expand=True
                )
            ])
        )
        self.page.update()

    def guardar_todo(self, e):
        if not (self.nombre.value and self.dni.value and self.edad.value and self.sexo.value):
            self.resultado.value = "Faltan datos obligatorios."
            self.resultado.color = "red"
            self.page.update()
            return

        fecha_actual = datetime.now().strftime("%d-%m-%Y")

        datos = {
            "nombre": self.nombre.value,
            "dni": self.dni.value,
            "edad": self.edad.value,
            "sexo": self.sexo.value,
            "observaciones": self.observaciones.value,
            "fecha_registro": fecha_actual
        }

        ojo_derecho_tomado = os.path.exists("ojo_derecho.jpg")
        ojo_izquierdo_tomado = os.path.exists("ojo_izquierdo.jpg")

        if ojo_derecho_tomado:
            blob_od = bucket.blob(f"pacientes/{self.dni.value}/{fecha_actual}/imagenes/ojo_derecho.jpg")
            blob_od.upload_from_filename("ojo_derecho.jpg")
            datos["url_ojo_derecho"] = blob_od.public_url

        if ojo_izquierdo_tomado:
            blob_oi = bucket.blob(f"pacientes/{self.dni.value}/{fecha_actual}/imagenes/ojo_izquierdo.jpg")
            blob_oi.upload_from_filename("ojo_izquierdo.jpg")
            datos["url_ojo_izquierdo"] = blob_oi.public_url

        db.collection("pacientes").document(self.dni.value).collection("registros").document(fecha_actual).set(datos)

        if ojo_derecho_tomado and os.path.exists("ojo_derecho.jpg"):
            os.remove("ojo_derecho.jpg")
        if ojo_izquierdo_tomado and os.path.exists("ojo_izquierdo.jpg"):
            os.remove("ojo_izquierdo.jpg")

        self.mostrar_confirmacion()

    def mostrar_confirmacion(self):
        # Limpia los elementos anteriores
        self.page.clean()

        boton_menu = ft.ElevatedButton(
            "Volver al menú principal",
            on_click=self.volver_menu,
            bgcolor="blue",
            color="white"
        )

        self.page.add(
            ft.Column([
                self.cargar_logo(),
                ft.Text("Datos enviados correctamente", size=24, weight="bold", color="green", text_align=ft.TextAlign.CENTER),
                boton_menu
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=30)
        )
        self.page.update()

    def volver_atras(self, e):
        from Capturar_Ojos import Capturar_Ojos
        Capturar_Ojos(self.page).mostrar()

    def volver_menu(self, e):
        from Menu_Principal import Menu_Principal
        Menu_Principal(self.page).mostrar()