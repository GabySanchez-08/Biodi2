from firebase_config import db

docs = db.collection("pacientes").stream()
for doc in docs:
    print("Documento encontrado:", doc.id)