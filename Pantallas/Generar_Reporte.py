from fpdf import FPDF
from datetime import datetime
import os
from Pantallas.firebase_config import db, bucket
from Pantallas.Generar_Topografia import generar_mapa_topografico
from PIL import Image
import smtplib
from email.message import EmailMessage

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

    mapas_der = generar_mapa_topografico("ojo_derecho.jpg") if os.path.exists("ojo_derecho.jpg") else []
    mapas_izq = generar_mapa_topografico("ojo_izquierdo.jpg") if os.path.exists("ojo_izquierdo.jpg") else []

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "REPORTE DE EVALUACIÓN CORNEAL", ln=True, align="C")
    pdf.ln(5)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, "Datos del paciente", ln=True, fill=True)

    def campo(label, valor):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(45, 10, f"{label}:", ln=False)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"{valor}", ln=True)

    campo("Nombre", f"{paciente_data.get('nombre', '')} {paciente_data.get('apellido', '')}")
    campo("DNI", dni)
    campo("Fecha de nacimiento", paciente_data.get("fecha_nacimiento", ""))
    campo("Edad", datos.get("edad", ""))
    campo("Sexo", paciente_data.get("sexo", ""))
    campo("Número", paciente_data.get("numero_contacto", ""))
    campo("Correo", paciente_data.get("correo_contacto", ""))

    pdf.ln(5)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, "Datos de captura", ln=True, fill=True)

    campo("Fecha de registro", fecha)
    campo("Hora del examen", hora_actual)
    campo("Capturado por", f"{tecnico_data.get('nombre', '')} {tecnico_data.get('apellido', '')}")
    campo("Lugar de captura", tecnico_data.get("sede", "No registrado"))

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Observaciones generales", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, datos.get("observaciones", "Sin observaciones registradas."))


    # === Agregar mapas de topografía corneal ===
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Análisis Topográfico Corneal", ln=True)
    pdf.ln(5)

    # Coordenadas para las imágenes (2 filas, 2 columnas)
    posiciones = [(10, 70), (105, 70), (10, 160), (105, 160)]  # x, y para cada una
    mapas_der = [
        "mapa_tangencial_derecho.jpg",
        "mapa_diferencia_derecho.jpg"
    ]
    mapas_izq = [
        "mapa_tangencial_izquierdo.jpg",
        "mapa_diferencia_izquierdo.jpg"
    ]

    # Función para insertar imagen o placeholder
    def insertar_mapa(mapa_path, x, y, texto_fallback):
        if os.path.exists(mapa_path):
            with Image.open(mapa_path) as img:
                img_w, img_h = img.size
                max_w, max_h = 90, 90
                ratio = min(max_w / img_w, max_h / img_h)
                new_w = img_w * ratio
                new_h = img_h * ratio
                pdf.image(mapa_path, x=x, y=y, w=new_w, h=new_h)
        else:
            pdf.rect(x, y, 90, 90)
            pdf.set_xy(x + 5, y + 40)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(80, 5, texto_fallback, align="C")

    # Insertar mapas del ojo derecho
    for i, mapa in enumerate(mapas_der):
        x, y = posiciones[i]
        insertar_mapa(mapa, x, y, f"Mapa derecho {i+1}\n(No disponible)")

    # Insertar mapas del ojo izquierdo
    for i, mapa in enumerate(mapas_izq):
        x, y = posiciones[i + 2]
        insertar_mapa(mapa, x, y, f"Mapa izquierdo {i+1}\n(No disponible)")

    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 6, "Este informe es un preanálisis basado en los datos topográficos capturados. La interpretación médica debe considerar los hallazgos visuales junto con estos resultados, evaluando signos sugestivos de queratocono como el aumento de la curvatura, desplazamiento inferior del punto más delgado y asimetría corneal.")

    path_pdf = ruta_salida or f"{dni}_{fecha}_reporte.pdf"
    pdf.output(path_pdf)

    if bucket:
        blob = bucket.blob(f"pacientes/{dni}/{fecha}/{os.path.basename(path_pdf)}")
        blob.upload_from_filename(path_pdf)

    # Enviar correo
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
            f"Atentamente,\n"
            f"Unidad de Diagnóstico Corneal\n"
            f"Centro de Salud Visual"
        )
        
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(remitente, clave)
                smtp.send_message(msg)
            print("[INFO] Correo enviado exitosamente.")
        except Exception as e:
            print(f"[ERROR] No se pudo enviar el correo: {e}")
        

    #os.remove(path_pdf)