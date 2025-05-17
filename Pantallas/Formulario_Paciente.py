from Pantallas.Base_App import Base_App
import flet as ft
import os
from datetime import datetime, date
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

        self.campos_bloqueados = False

    def mostrar(self):
        self.limpiar()

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

        self.capturas_label = ft.Text(self.detectar_capturas(), size=16, color="blue")

        self.mensaje_usuario = ft.Text(
            f"Este registro quedará asociado al usuario que realiza la captura." if self.usuario else "Modo offline: el usuario no será registrado.",
            size=14,
            italic=True,
            color="gray"
        )

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
                    self.dni,
                    ft.Row([self.nombre, self.btn_edit_nombre]),
                    ft.Row([self.apellido, self.btn_edit_apellido]),
                    ft.Row([self.fecha_nac_field, self.btn_edit_fecha]),
                    self.edad,
                    ft.Row([self.sexo, self.btn_edit_sexo]),
                    ft.Row([self.numero_contacto, self.btn_edit_contacto]),
                    ft.Row([self.correo_contacto, self.btn_edit_correo]),
                    self.observaciones,
                    self.mensaje_usuario,
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

    def actualizar_edad_desde_texto(self, e):
        texto_fecha = self.fecha_nac_field.value.strip()
        try:
            fecha_dt = datetime.strptime(texto_fecha, "%d-%m-%Y").date()
            self.edad.value = str(self.calcular_edad(fecha_dt))
        except:
            self.edad.value = ""
        self.page.update()

    def calcular_edad(self, fecha):
        hoy = date.today()
        return hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))

    def buscar_paciente(self, e):
        if not self.modo_online:
            return
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
                self.fecha_nac_field.disabled= True
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

                self.campos_bloqueados = True

        except Exception as err:
            print(f"[ERROR] al buscar paciente: {err}")

        self.page.update()

    def desbloquear_campo(self, campo):
        campo.disabled = False
        self.page.update()

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
        }

        if self.modo_online:
            datos["tecnico_id"] = self.usuario if self.usuario else "offline"
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
        db.collection("pacientes_base").document(self.dni.value).set({
            "nombre": self.nombre.value,
            "apellido": self.apellido.value,
            "fecha_nacimiento": self.fecha_nac_field.value,
            "sexo": self.sexo.value,
            "numero_contacto": self.numero_contacto.value,
            "correo_contacto": self.correo_contacto.value
        }, merge=True)
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

        with open(os.path.join(ruta_base, f"{self.dni.value}_{fecha}_datos.json"), "w") as f:
            json.dump(datos, f, indent=2)

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
        Capturar_Ojos(self.page, self.usuario, self.rol).mostrar()

    def volver_menu(self, e):
        if self.modo_online:
            from Pantallas.Menu_Principal import Menu_Principal
            Menu_Principal(self.page, self.usuario, self.rol).mostrar()
        else:
            from Pantallas.Menu_Offline import Menu_Offline
            Menu_Offline(self.page).mostrar()
