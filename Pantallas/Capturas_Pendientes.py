import os
import json
import shutil
import zipfile
import flet as ft
from datetime import datetime
import urllib.request
from Pantallas.Base_App import Base_App

try:
    from firebase_config import db, bucket
except ImportError:
    db = bucket = None


class Capturas_Pendientes(Base_App):
    def __init__(self, page, usuario=None, rol=None):
        super().__init__(page, usuario, rol)
        self.modo_online = self.hay_conexion()

    def hay_conexion(self):
        try:
            urllib.request.urlopen('https://www.google.com', timeout=3)
            return True
        except:
            return False

    def mostrar(self):
        self.limpiar()
        self.lista_pacientes = self.obtener_capturas_locales()

        columnas = [
            ft.DataColumn(label=ft.Text("DNI")),
            ft.DataColumn(label=ft.Text("Fecha")),
            ft.DataColumn(label=ft.Text("Estado")),
            ft.DataColumn(label=ft.Text("Acciones")),
        ]

        filas = []
        for ruta in self.lista_pacientes:
            nombre = os.path.basename(ruta)
            if "_" not in nombre or nombre.startswith("."):
                continue
            dni, fecha = nombre.split("_", 1)

            datos_path = next((os.path.join(ruta, f) for f in os.listdir(ruta) if f.endswith("_datos.json")), None)
            if not datos_path or not os.path.exists(datos_path):
                continue
            estado = "Pendiente de subir"
            if not os.path.exists(datos_path):
                continue
            with open(datos_path) as f:
                try:
                    datos = json.load(f)
                    if datos.get("subido") is True:
                        estado = "Subido"
                except json.JSONDecodeError:
                    continue

            acciones = []
            export_btn = ft.ElevatedButton("Exportar ZIP", on_click=lambda e, r=ruta: self.exportar_zip(r))
            acciones.append(export_btn)

            if self.modo_online and estado != "Subido":
                subir_btn = ft.ElevatedButton("Subir paciente", on_click=lambda e, r=ruta: self.subir_paciente(r))
                acciones.append(subir_btn)

            filas.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(dni)),
                    ft.DataCell(ft.Text(fecha)),
                    ft.DataCell(ft.Text(estado)),
                    ft.DataCell(ft.Row(acciones, spacing=5)),
                ])
            )

        tabla = ft.DataTable(columns=columnas, rows=filas)

        self.page.add(
            ft.Column([
                ft.Text("Capturas guardadas localmente", size=24, weight="bold"),
                tabla,
                ft.Divider(),
                ft.ElevatedButton("Volver al menú", on_click=self.volver_menu)
            ], scroll=ft.ScrollMode.ALWAYS)
        )
        self.page.update()

    def obtener_capturas_locales(self):
        base = "capturas_pendientes"
        if not os.path.exists(base):
            return []
        return [os.path.join(base, carpeta) for carpeta in os.listdir(base)
                if os.path.isdir(os.path.join(base, carpeta)) and "_" in carpeta and not carpeta.startswith(".")]

    def exportar_zip(self, ruta):
        from flet import FilePicker
        picker = FilePicker()
        self.page.overlay.append(picker)
        self.page.update()

        def cuando_selecciona_destino(e):
            if not picker.result or not picker.result.path:
                return
            destino = picker.result.path

            with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for carpeta_raiz, _, archivos in os.walk(ruta):
                    for archivo in archivos:
                        archivo_completo = os.path.join(carpeta_raiz, archivo)
                        arcname = os.path.relpath(archivo_completo, ruta)
                        zipf.write(archivo_completo, arcname=arcname)

            self.page.snack_bar = ft.SnackBar(ft.Text("ZIP exportado correctamente."))
            self.page.snack_bar.open = True
            self.page.update()

        picker.on_result = cuando_selecciona_destino
        dni, fecha = os.path.basename(ruta).split("_", 1)
        picker.save_file(dialog_title="Guardar ZIP como", file_name=f"{dni}_{fecha}.zip")

    def subir_paciente(self, ruta):
        datos_path = os.path.join(ruta, "datos.json")
        if not os.path.exists(datos_path):
            return

        with open(datos_path, "r") as f:
            datos = json.load(f)

        dni = datos.get("dni")
        fecha = datos.get("fecha_registro")

        if not all([dni, fecha]):
            return

        # Subir imágenes
        for archivo in os.listdir(ruta):
            if archivo.endswith(".jpg"):
                local_file = os.path.join(ruta, archivo)
                blob = bucket.blob(f"pacientes/{dni}/{fecha}/imagenes/{archivo}")
                blob.upload_from_filename(local_file)

        # Subir datos
        db.collection("pacientes").document(dni).collection("registros").document(fecha).set(datos)

        # Marcar como subido
        datos["subido"] = True
        with open(datos_path, "w") as f:
            json.dump(datos, f, indent=2)

        # Eliminar archivos
        shutil.rmtree(ruta)

        self.page.snack_bar = ft.SnackBar(ft.Text(f"Paciente {dni} subido con éxito."))
        self.page.snack_bar.open = True
        self.mostrar()

    def volver_menu(self, e):
        if self.modo_online:
            from Pantallas.Menu_Principal import Menu_Principal
            Menu_Principal(self.page, usuario=self.usuario, rol=self.rol).mostrar()
        else:
            from Pantallas.Menu_Offline import Menu_Offline
            Menu_Offline(self.page).mostrar()