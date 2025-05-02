import firebase_admin
from firebase_admin import credentials, firestore, storage

# Ruta a tu archivo de credenciales .json (descargado desde Firebase)
cred = credentials.Certificate("keratotech-66ab6-firebase-adminsdk-fbsvc-efece39084.json")

# Inicializa Firebase con Firestore y Storage

firebase_admin.initialize_app(cred, {
    'storageBucket': 'keratotech-66ab6.firebasestorage.app'
})

# Cliente para Firestore
db = firestore.client()

# Cliente para Storage
bucket = storage.bucket()