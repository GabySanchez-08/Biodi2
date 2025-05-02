import os
from datetime import datetime
from fpdf import FPDF
from firebase_config import bucket
from Generar_Topografia import generar_mapa_topografico

def generar_reporte_pdf(datos: dict):
    dni = datos.get("dni")
    fecha = datos.get("fecha_registro")

    # Agregar hora actual
    hora_actual = datetime.now().strftime("%H:%M:%S")
    datos["hora"] = hora_actual

    # Determinar topografías disponibles
    mapa_izq = generar_mapa_topografico("ojo_izquierdo.jpg", "mapa_izquierdo.jpg") if os.path.exists("ojo_izquierdo.jpg") else None
    mapa_der = generar_mapa_topografico("ojo_derecho.jpg", "mapa_derecho.jpg") if os.path.exists("ojo_derecho.jpg") else None

    # Crear PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Reporte de Evaluación Corneal", ln=True, align="C")
    pdf.ln(10)

    for key, val in datos.items():
        pdf.cell(200, 10, f"{key.capitalize()}: {val}", ln=True)

    pdf.ln(10)

    if mapa_der:
        pdf.image(mapa_der, x=10, y=pdf.get_y(), w=90)
    if mapa_izq:
        pdf.image(mapa_izq, x=110, y=pdf.get_y(), w=90)

    path_pdf = f"{dni}_{fecha}_reporte_nuevo.pdf"
    pdf.output(path_pdf)

    # Subir a Firebase Storage
    blob = bucket.blob(f"pacientes/{dni}/{fecha}/{dni}_{fecha}_reporte.pdf")
    blob.upload_from_filename(path_pdf)
    os.remove(path_pdf)