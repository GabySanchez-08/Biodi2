from Pantallas.Base_App import Base_App
import flet as ft
from datetime import datetime
from fpdf import FPDF
from Pantallas.firebase_config import bucket, db
import os
import smtplib
from email.message import EmailMessage

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

        paciente_doc = db.collection("pacientes_base").document(self.dni).get()
        paciente_data = paciente_doc.to_dict() if paciente_doc.exists else {}

        medico_doc = db.collection("usuarios").document(self.usuario).get()
        medico_data = medico_doc.to_dict() if medico_doc.exists else {}

        nombre_pdf = f"{self.dni}_{self.fecha}_diagnostico.pdf"
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "INFORME DE DIAGNÓSTICO MÉDICO", ln=True, align="C")
        pdf.ln(10)

        def campo(label, valor):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(45, 10, f"{label}:", ln=False)
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 10, valor, ln=True)

        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 10, "Datos del paciente", ln=True, fill=True)
        campo("Nombre", f"{paciente_data.get('nombre', '')} {paciente_data.get('apellido', '')}")
        campo("DNI", self.dni)
        campo("Fecha de nacimiento", paciente_data.get("fecha_nacimiento", ""))

        fecha_nac = paciente_data.get("fecha_nacimiento", "")
        edad = ""
        if fecha_nac:
            try:
                nacimiento = datetime.strptime(fecha_nac, "%d-%m-%Y")
                hoy = datetime.today()
                edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
            except:
                edad = "Error al calcular edad"
        campo("Edad", str(edad))
        campo("Sexo", paciente_data.get("sexo", ""))
        campo("Número", paciente_data.get("numero_contacto", ""))
        campo("Correo", paciente_data.get("correo_contacto", ""))

        pdf.ln(5)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 10, "Datos del profesional que realizó el diagnóstico", ln=True, fill=True)
        campo("Nombre", f"{medico_data.get('nombre', '')} {medico_data.get('apellido', '')}")
        campo("Sede", medico_data.get("sede", "No registrada"))
        campo("Fecha del diagnóstico", self.fecha)
        campo("Hora del diagnóstico", datetime.now().strftime("%H:%M:%S"))

        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Diagnóstico Clínico", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, texto)

        pdf.output(nombre_pdf)

        try:
            blob = bucket.blob(f"pacientes/{self.dni}/{self.fecha}/{nombre_pdf}")
            blob.upload_from_filename(nombre_pdf)
        except Exception as err:
            print(f"[ERROR] No se pudo subir el PDF: {err}")
            self.estado.value = "Error al subir el archivo PDF."
            self.estado.color = "red"
            self.page.update()
            return

        # Enviar correo
        correo_paciente = paciente_data.get("correo_contacto")
        if correo_paciente:
            remitente = "gabrielasanchezd08@gmail.com"
            clave = "qitf tyjl emkw vspn"
            msg = EmailMessage()
            msg["From"] = remitente
            msg["To"] = correo_paciente
            msg["Subject"] = "DIAGNÓSTICO CLÍNICO DE SU EVALUACIÓN OFTALMOLÓGICA"
            msg.set_content(
                f"Estimado(a) {paciente_data.get('nombre', '')} {paciente_data.get('apellido', '')},\n\n"
                f"Le saludamos cordialmente desde el centro de salud visual.\n\n"
                f"Adjunto a este mensaje encontrará el informe de diagnóstico clínico emitido por el profesional responsable {medico_data.get('nombre', '')} {medico_data.get('apellido', '')}, correspondiente a la evaluación oftalmológica realizada el día {self.fecha}.\n\n"
                f"Este documento contiene la interpretación médica de los resultados obtenidos previamente mediante topografía corneal u otros métodos diagnósticos. Le recomendamos revisar cuidadosamente su contenido y, de ser necesario, coordinar una cita de seguimiento con su médico tratante.\n\n"
                f"Si tiene alguna duda respecto al diagnóstico o necesita orientación adicional, no dude en comunicarse con nuestro equipo a través de los canales habituales.\n\n"
                f"Atentamente,\n"
                f"Unidad de Diagnóstico Corneal\n"
                f"Centro de Salud Visual"
            )
            try:
                with open(nombre_pdf, "rb") as f:
                    file_data = f.read()
                    msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=nombre_pdf)
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                    smtp.login(remitente, clave)
                    smtp.send_message(msg)
                print("[INFO] Correo enviado exitosamente.")
            except Exception as e:
                print(f"[ERROR] No se pudo enviar el correo: {e}")

        os.remove(nombre_pdf)
        self.estado.value = "Diagnóstico guardado y enviado correctamente."
        self.estado.color = "green"
        self.page.update()

    def volver(self, e):
        from Pantallas.Ver_Historial import Ver_Historial
        Ver_Historial(self.page, self.usuario, self.rol).mostrar()
