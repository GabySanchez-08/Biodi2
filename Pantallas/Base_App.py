import flet as ft

class Base_App:
    logo_precalculado = None
    logo_precalculado2 = None

    def __init__(self, page, usuario=None, rol=None):
        self.page = page
        self.usuario = usuario
        self.rol = rol
        
    def limpiar(self):
        """Limpia la pantalla"""
        if self.page:
            self.page.controls.clear()
            self.page.update()
    
    def cargar_logo(self, ancho=180):
        import base64, os
        import flet as ft

        if Base_App.logo_precalculado:
            return ft.Image(src_base64=Base_App.logo_precalculado, width=ancho)
        
        ruta = "assets/logo_app_pucp2.png"
        if os.path.exists(ruta):
            with open(ruta, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode("utf-8")
                Base_App.logo_precalculado = img_base64
                return ft.Image(src_base64=img_base64, width=ancho)

        return ft.Text("KERATO TECH", size=12, weight="bold")
    
    def cargar_logo_pucp(self, ancho=150):
        import base64, os
        import flet as ft

        if Base_App.logo_precalculado2:
            return ft.Image(src_base64=Base_App.logo_precalculado2, width=ancho)
        
        ruta2 = "assets/logo_pucp3.png"
        if os.path.exists(ruta2):
            with open(ruta2, "rb") as f:
                img_base64_2 = base64.b64encode(f.read()).decode("utf-8")
                Base_App.logo_precalculado2 = img_base64_2
                return ft.Image(src_base64=img_base64_2, width=ancho)

        return ft.Text("KERATO TECH", size=24, weight="bold")
    