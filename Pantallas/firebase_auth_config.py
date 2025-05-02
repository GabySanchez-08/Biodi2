import pyrebase

firebase_config = {
    "apiKey": "AIzaSyDWuC-FA40ier_YZ49C1cKB5GuQq_JgpQ8",
    "authDomain": "keratotech-66ab6.firebaseapp.com",
    "databaseURL": "",  # ← Agrega esto para evitar el error
    "projectId": "keratotech-66ab6",
    "storageBucket": "keratotech-66ab6.appspot.com",
    "messagingSenderId": "1061855911257",
    # "appId": "opcional"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()