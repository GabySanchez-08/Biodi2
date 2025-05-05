# === Archivo: Formulario_Paciente.py ===
from Base_App import Base_App
import flet as ft
import os
from datetime import datetime
from firebase_config import db, bucket
from Generar_Reporte import generar_reporte_pdf

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

        self.capturas_label = ft.Text(self.detectar_capturas(), size=16, color="blue")

        self.enviar_btn = ft.ElevatedButton("Guardar y Enviar", on_click=self.guardar_todo, bgcolor="green")
        self.boton_volver = ft.Container(
            content=ft.TextButton("← Volver a captura", on_click=self.volver_atras),
            alignment=ft.alignment.top_left,
            padding=10
        )

        self.page.add(
            ft.Stack([
                self.boton_volver,
                ft.Container(
                    ft.Column([
                        self.cargar_logo(),
                        ft.Text("Formulario de paciente", size=24, weight="bold"),
                        self.capturas_label,
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

    def detectar_capturas(self):
        od = os.path.exists("ojo_derecho.jpg")
        oi = os.path.exists("ojo_izquierdo.jpg")
        if od and oi:
            return "Capturas listas: Ojo derecho y ojo izquierdo"
        elif od:
            return "Captura lista: Solo ojo derecho"
        elif oi:
            return "Captura lista: Solo ojo izquierdo"
        else:
            return "No hay capturas disponibles"

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

        # Subir imágenes
        for ojo in ["derecho", "izquierdo"]:
            local_file = f"ojo_{ojo}.jpg"
            if os.path.exists(local_file):
                blob = bucket.blob(f"pacientes/{self.dni.value}/{fecha}/imagenes/{fecha}_{local_file}")
                blob.upload_from_filename(local_file)
                datos[f"url_ojo_{ojo}"] = blob.public_url

        # Subir datos
        db.collection("pacientes").document(self.dni.value).collection("registros").document(fecha).set(datos)

        # Generar y subir reporte
        generar_reporte_pdf(datos)

        # Eliminar imágenes locales
        for archivo in ["ojo_derecho.jpg", "ojo_izquierdo.jpg"]:
            if os.path.exists(archivo):
                os.remove(archivo)

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

    def volver_atras(self, e):
        from Capturar_Ojos import Capturar_Ojos
        Capturar_Ojos(self.page, usuario=self.usuario, rol=self.rol).mostrar()

    def volver_menu(self, e):
        from Menu_Principal import Menu_Principal
        Menu_Principal(self.page, usuario=self.usuario, rol=self.rol).mostrar()