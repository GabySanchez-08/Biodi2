from Pantallas.Generar_Reporte import generar_reporte_pdf
import os

# Simulación de datos mínimos
datos_prueba = {
    "dni": "12345678",
    "fecha_registro": "2025-07-12",
    "edad": "28",
    "tecnico_id": "offline",  # para evitar conexión a Firestore
    "observaciones": "Paciente sin antecedentes. Se observan mapas dentro de parámetros normales."
}


# Generar el PDF de prueba
generar_reporte_pdf(datos_prueba, ruta_salida="reporte_prueba.pdf")

print("✅ PDF generado como reporte_prueba.pdf")
import os
print("📂 Directorio actual:", os.getcwd())