# === Archivo: Formulario_Paciente.py ===
from Pantallas.Base_App import Base_App
import flet as ft
import os
from datetime import datetime
import urllib.request
import json

try:
    from Pantallas.firebase_config import db, bucket
except ImportError:
    db = bucket = None

from Pantallas.Generar_Reporte import generar_reporte_pdf

class Formulario_Paciente(Base_App):
    def __init__(self, page, usuario=None, rol=None):
        super().__init__(page, usuario, rol)
        if self.hay_conexion():
            self.modo_online = True
        else:
            self.modo_online = False

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

        self.page.add(
            ft.Container(
                ft.Column([
                    ft.Container(
                        content=ft.TextButton("← Volver a captura", on_click=self.volver_atras),
                        alignment=ft.alignment.center,
                        padding=10
                    ),
                    self.cargar_logo(),
                    ft.Text("Formulario de paciente", size=24, weight="bold"),
                    self.capturas_label,
                    self.nombre, self.dni, self.edad, self.sexo, self.observaciones,
                    self.enviar_btn,
                    self.resultado
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20),
                alignment=ft.alignment.top_center,
                expand=True
            )
        )
        self.page.update()

    def hay_conexion(self):
        try:
            urllib.request.urlopen('https://www.google.com', timeout=3)
            return True
        except:
            return False

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

        self.resultado.value = "Guardando..."
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

        if self.modo_online:
            self.guardar_online(datos, fecha)
        else:
            self.guardar_offline(datos, fecha)

        self.eliminar_imagenes_locales()
        self.mostrar_confirmacion()

    def guardar_online(self, datos, fecha):
        for ojo in ["derecho", "izquierdo"]:
            local_file = f"ojo_{ojo}.jpg"
            if os.path.exists(local_file):
                blob = bucket.blob(f"pacientes/{self.dni.value}/{fecha}/imagenes/{fecha}_{local_file}")
                blob.upload_from_filename(local_file)
                datos[f"url_ojo_{ojo}"] = blob.public_url

        db.collection("pacientes").document(self.dni.value).collection("registros").document(fecha).set(datos)
        generar_reporte_pdf(datos)

    def guardar_offline(self, datos, fecha):
        ruta_base = f"capturas_pendientes/{self.dni.value}_{fecha}"
        os.makedirs(ruta_base, exist_ok=True)

        for ojo in ["derecho", "izquierdo"]:
            archivo = f"ojo_{ojo}.jpg"
            if os.path.exists(archivo):
                nueva_ruta = os.path.join(ruta_base, f"{fecha}_{archivo}")
                os.rename(archivo, nueva_ruta)
                datos[f"archivo_local_ojo_{ojo}"] = nueva_ruta

        # Guardar el JSON con los datos del paciente
        with open(os.path.join(ruta_base, f"{self.dni.value}_{fecha}_datos.json"), "w") as f:
            json.dump(datos, f, indent=2)

        # Generar reporte en la misma carpeta
        generar_reporte_pdf(datos, ruta_salida=os.path.join(ruta_base, f"{self.dni.value}_{fecha}_reporte.pdf"))

    def eliminar_imagenes_locales(self):
        for archivo in ["ojo_derecho.jpg", "ojo_izquierdo.jpg"]:
            if os.path.exists(archivo):
                os.remove(archivo)

    def mostrar_confirmacion(self):
        self.page.clean()
        boton_menu = ft.ElevatedButton("Volver al menú principal", on_click=self.volver_menu, bgcolor="blue", color="white")

        contenido = ft.Column([
            self.cargar_logo(),
            ft.Text("Datos guardados correctamente", size=24, weight="bold", color="green", text_align=ft.TextAlign.CENTER),
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
        from Pantallas.Capturar_Ojos import Capturar_Ojos
        Capturar_Ojos(self.page, self.usuario,self.rol).mostrar()

    def volver_menu(self, e):
        if self.modo_online:
            from Pantallas.Menu_Principal import Menu_Principal
            Menu_Principal(self.page, usuario=self.usuario, rol=self.rol).mostrar()
        else:
            from Pantallas.Menu_Offline import Menu_Offline
            Menu_Offline(self.page).mostrar()
