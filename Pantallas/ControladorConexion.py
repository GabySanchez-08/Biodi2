# === Archivo: ControladorConexion.py ===
import urllib.request
from Login import Login
from ModoOffline import ModoOffline

class ControladorConexion:
    def __init__(self, page):
        self.page = page

    def hay_conexion(self):
        try:
            urllib.request.urlopen('https://www.google.com', timeout=3)
            return True
        except:
            return False

    def verificar_estado(self):
        if self.hay_conexion():
            Login(self.page).mostrar()
        else:
            ModoOffline(self.page).mostrar()