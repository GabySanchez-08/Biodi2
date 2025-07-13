from fpdf import FPDF
from datetime import datetime
import os
from Pantallas.firebase_config import db, bucket
from Pantallas.Generar_Topografia import generar_mapa_topografico
from PIL import Image
import smtplib
from email.message import EmailMessage
import pandas as pd  # asegúrate de tenerlo arriba

def limpiar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return (
        texto.replace("μ", "μ")
             .replace("–", "-")
             .replace("—", "-")
    )

def generar_reporte_pdf(datos, ruta_salida=None):
    dni = datos.get("dni")
    fecha = datos.get("fecha_registro")
    hora_actual = datetime.now().strftime("%H:%M:%S")
    datos["hora"] = hora_actual

    paciente_doc = db.collection("pacientes_base").document(dni).get()
    paciente_data = paciente_doc.to_dict() if paciente_doc.exists else {}

    capturado_por = datos.get("tecnico_id", "Desconocido")
    usuario_doc = db.collection("usuarios").document(capturado_por).get() if capturado_por != "offline" else None
    tecnico_data = usuario_doc.to_dict() if usuario_doc and usuario_doc.exists else {}

    df_derecho = generar_mapa_topografico("ojo_derecho.jpg") if os.path.exists("ojo_derecho.jpg") else pd.DataFrame()
    df_izquierdo = generar_mapa_topografico("ojo_izquierdo.jpg") if os.path.exists("ojo_izquierdo.jpg") else pd.DataFrame()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)


    pdf.set_font("Times", "B", 16)
    pdf.cell(0, 10, "REPORTE DE EVALUACIÓN CORNEAL", ln=True, align="C")
    pdf.ln(5)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Times", "B", 14)
    pdf.cell(0, 10, "Datos del paciente", ln=True, fill=True)

    def campo(label, valor):
        pdf.set_font("Times", "B", 12)
        pdf.cell(45, 8, f"{label}:", ln=False)
        pdf.set_font("Times", "", 12)
        pdf.cell(0, 8, f"{valor}", ln=True)

    campo("Nombre", f"{paciente_data.get('nombre', '')} {paciente_data.get('apellido', '')}")
    campo("DNI", dni)
    campo("Fecha de nacimiento", paciente_data.get("fecha_nacimiento", ""))
    campo("Edad", datos.get("edad", ""))
    campo("Sexo", paciente_data.get("sexo", ""))
    campo("Número", paciente_data.get("numero_contacto", ""))
    campo("Correo", paciente_data.get("correo_contacto", ""))

    pdf.ln(5)
    pdf.set_font("Times", "B", 14)
    pdf.cell(0, 10, "Datos de captura", ln=True, fill=True)

    campo("Fecha de registro", fecha)
    campo("Hora del examen", hora_actual)
    campo("Capturado por", f"{tecnico_data.get('nombre', '')} {tecnico_data.get('apellido', '')}")
    campo("Lugar de captura", tecnico_data.get("sede", "No registrado"))

    pdf.ln(5)
    pdf.set_font("Times", 'B', 14)
    pdf.cell(0, 8, "Análisis Topográfico Corneal", ln=True)
    pdf.ln(5)

    def insertar_mapa_par(path1, label1, path2, label2):
        y_inicial = pdf.get_y()
        max_altura = 90
        ancho_img = 85

        def agregar_mapa(path, x, label):
            pdf.set_xy(x, y_inicial)
            pdf.set_font("Times", "B", 11)
            pdf.cell(ancho_img, 6, label, ln=True, align="C")
            pdf.set_xy(x, y_inicial + 6)
            if os.path.exists(path):
                with Image.open(path) as img:
                    img_w, img_h = img.size
                    ratio = min(ancho_img / img_w, max_altura / img_h)
                    w = img_w * ratio
                    h = img_h * ratio
                    pdf.image(path, x=x + (ancho_img - w) / 2, y=pdf.get_y(), w=w, h=h)
            else:
                pdf.set_fill_color(255, 255, 255)
                pdf.set_draw_color(0, 0, 0)
                pdf.rect(x, pdf.get_y(), ancho_img, max_altura)
                pdf.set_xy(x, pdf.get_y() + max_altura / 2 - 5)
                pdf.set_font("Times", "", 10)
                pdf.multi_cell(ancho_img, 5, "Imagen no disponible", align="C")

        agregar_mapa(path1, 10, label1)
        agregar_mapa(path2, 110, label2)
        pdf.set_y(y_inicial + max_altura + 10)


    # Eliminar mapas del ojo derecho
    if os.path.exists("mapa_tangencial_derecho.jpg") and os.path.exists("mapa_diferencia_derecho.jpg"):
        insertar_mapa_par("mapa_tangencial_derecho.jpg", "Tangencial (Ojo Derecho)",
                        "mapa_diferencia_derecho.jpg", "Diferencia (Ojo Derecho)")
        for f in ["mapa_tangencial_derecho.jpg", "mapa_diferencia_derecho.jpg"]:
            os.remove(f)

    if not df_derecho.empty:
        pdf.set_font("Times", "B", 12)
        pdf.cell(0, 10, "Parámetros cuantitativos (Ojo Derecho)", ln=True, align="C")

        col_widths = [90, 40]
        total_width = sum(col_widths)
        x_centro = (210 - total_width) / 2  # A4 width = 210mm

        for index, row in df_derecho.iterrows():
            pdf.set_x(x_centro)
            pdf.cell(col_widths[0], 7, limpiar_texto(row["Parámetro"]), border=1, align='C')
            pdf.cell(col_widths[1], 7, limpiar_texto(str(row["Valor"])), border=1, ln=True, align='C')

        pdf.ln(5)
        pdf.set_font("Times", "", 12)

    if pdf.get_y() > 170:
        pdf.add_page()

    if os.path.exists("mapa_tangencial_izquierdo.jpg") and os.path.exists("mapa_diferencia_izquierdo.jpg"):
        insertar_mapa_par("mapa_tangencial_izquierdo.jpg", "Tangencial (Ojo Izquierdo)",
                        "mapa_diferencia_izquierdo.jpg", "Diferencia (Ojo Izquierdo)")
        for f in ["mapa_tangencial_izquierdo.jpg", "mapa_diferencia_izquierdo.jpg"]:
            os.remove(f)
                
    if not df_izquierdo.empty:
        pdf.set_font("Times", "B", 12)
        pdf.cell(0, 10, "Parámetros cuantitativos (Ojo Izquierdo)", ln=True, align="C")

        for index, row in df_izquierdo.iterrows():
            pdf.set_x(x_centro)
            pdf.cell(col_widths[0], 7, limpiar_texto(row["Parámetro"]), border=1, align='C')
            pdf.cell(col_widths[1], 7, limpiar_texto(str(row["Valor"])), border=1, ln=True, align='C')

        pdf.ln(5)
        pdf.set_font("Times", "", 12)

    pdf.ln(5)
    pdf.set_font("Times", "B", 14)
    pdf.cell(0, 10, "Observaciones generales", ln=True)
    pdf.set_font("Times", "", 12)
    pdf.multi_cell(0, 10, datos.get("observaciones", "Sin observaciones registradas."))

    pdf.set_font("Times", '', 12)
    pdf.multi_cell(0, 6, "Este informe es un preanálisis basado en los datos topográficos capturados. La interpretación médica debe considerar los hallazgos visuales junto con estos resultados, evaluando signos sugestivos de queratocono como el aumento de la curvatura, desplazamiento inferior del punto más delgado y asimetría corneal.")

    path_pdf = ruta_salida or f"{dni}_{fecha}_reporte.pdf"
    pdf.output(path_pdf)

    if bucket:
        blob = bucket.blob(f"pacientes/{dni}/{fecha}/{os.path.basename(path_pdf)}")
        blob.upload_from_filename(path_pdf)

    correo_paciente = paciente_data.get("correo_contacto")
    if correo_paciente:
        remitente = "gabrielasanchezd08@gmail.com"
        clave = "qitf tyjl emkw vspn"
        msg = EmailMessage()
        msg["From"] = remitente
        msg["To"] = correo_paciente
        msg["Subject"] = "REPORTE DE EVALUACIÓN OFTALMOLÓGICA"
        msg.set_content(
            f"Estimado(a) {paciente_data.get('nombre', '')} {paciente_data.get('apellido', '')},\n\n"
            f"Le saludamos cordialmente desde el centro de evaluación oftalmológica del {tecnico_data.get('sede', 'N/D')}.\n\n"
            f"Adjunto a este mensaje encontrará el reporte técnico correspondiente a su evaluación corneal realizada el día {fecha}, elaborado por el profesional encargado {tecnico_data.get('nombre', '')} {tecnico_data.get('apellido', '')}.\n\n"
            f"Este documento contiene información capturada mediante herramientas de topografía corneal. Aún no incluye una interpretación médica o diagnóstico clínico oficial.\n\n"
            f"Una vez que el médico especialista revise esta información y registre su diagnóstico, usted recibirá un segundo correo con dicho informe.\n\n"
            f"Le recomendamos no tomar decisiones clínicas basadas únicamente en el presente documento. Para cualquier consulta, no dude en comunicarse con nosotros por los canales habituales.\n\n"
            f"Atentamente,\nUnidad de Diagnóstico Corneal\nCentro de Salud Visual"
        )

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(remitente, clave)
                smtp.send_message(msg)
            print("[INFO] Correo enviado exitosamente.")
        except Exception as e:
            print(f"[ERROR] No se pudo enviar el correo: {e}")
