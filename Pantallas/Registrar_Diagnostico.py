from Base_App import Base_App
import flet as ft
from datetime import datetime
from fpdf import FPDF
from firebase_config import bucket, db
import os

class Registrar_Diagnostico(Base_App):
    def __init__(self, page, dni, fecha, usuario=None, rol=None):
        super().__init__(page, usuario, rol)
        self.dni = dni
        self.fecha = fecha

    def mostrar(self):
        self.limpiar()

        self.diagnostico_input = ft.TextField(label="Escribe el diagnóstico", multiline=True, min_lines=6, expand=True)
        self.estado = ft.Text("", size=14)

        guardar_btn = ft.ElevatedButton("Guardar diagnóstico", on_click=self.guardar_diagnostico, bgcolor="green", color="white")
        volver_btn = ft.TextButton("← Volver", on_click=self.volver)

        self.page.add(
            ft.Container(
                ft.Column([
                    self.cargar_logo(),
                    ft.Text(f"Registrar diagnóstico para {self.dni} ({self.fecha})", size=22, weight="bold"),
                    self.diagnostico_input,
                    self.estado,
                    ft.Row([guardar_btn, volver_btn], alignment=ft.MainAxisAlignment.END, spacing=20)
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.START),
                expand=True,
                padding=20,
                alignment=ft.alignment.top_center
            )
        )
        self.page.update()

    def guardar_diagnostico(self, e):
        texto = self.diagnostico_input.value.strip()
        if not texto:
            self.estado.value = "El campo de diagnóstico está vacío."
            self.estado.color = "red"
            self.page.update()
            return

        # Guardar texto en Firestore
        try:
            db.collection("pacientes").document(self.dni).collection("registros").document(self.fecha).update({
                "diagnostico": texto
            })
        except Exception as err:
            print(f"[ERROR] No se pudo guardar en Firestore: {err}")
            self.estado.value = "Error al guardar en la base de datos."
            self.estado.color = "red"
            self.page.update()
            return

        # Crear y subir PDF
        nombre_pdf = f"{self.dni}_{self.fecha}_diagnostico.pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, f"Diagnóstico - {self.fecha}", ln=True, align="C")
        pdf.ln(10)
        pdf.multi_cell(0, 10, texto)
        pdf.output(nombre_pdf)

        try:
            blob = bucket.blob(f"pacientes/{self.dni}/{self.fecha}/{nombre_pdf}")
            blob.upload_from_filename(nombre_pdf)
            os.remove(nombre_pdf)
            self.estado.value = "Diagnóstico guardado correctamente."
            self.estado.color = "green"
            self.page.update()
        except Exception as err:
            print(f"[ERROR] No se pudo subir el PDF: {err}")
            self.estado.value = "Error al subir el archivo PDF."
            self.estado.color = "red"
            self.page.update()

    def volver(self, e):
        from Ver_Historial import Ver_Historial
        Ver_Historial(self.page, self.usuario, self.rol).mostrar()