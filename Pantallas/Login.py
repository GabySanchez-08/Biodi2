from Base_App import Base_App
import flet as ft
from Menu_Principal import Menu_Principal
from firebase_auth_config import auth

class Login(Base_App):
    def mostrar(self):
        self.limpiar()
        logo = self.cargar_logo()

        user_input = ft.TextField(label="Usuario", autofocus=True, width=400)
        pass_input = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=400)
        mensaje = ft.Text("", size=14)

        ayuda_mensaje = ft.Container(
            content=ft.Text("", size=14, color="gray", text_align=ft.TextAlign.CENTER),
            alignment=ft.alignment.center,
            width=450,
            padding=10
        )

        def mostrar_ayuda(e):
            ayuda_mensaje.content.value = "Por el momento no se pueden recuperar contraseñas desde nuestra app. Por favor, contáctese con la institución a la que pertenece."
            self.page.update()

        def validar_credenciales(e=None):
            usuario = user_input.value.strip()
            contraseña = pass_input.value.strip()

            if not usuario or not contraseña:
                mensaje.value = "Completa todos los campos"
                mensaje.color = "red"
                self.page.update()
                return

            correo = f"{usuario.lower()}@keratotech.com"

            try:
                user = auth.sign_in_with_email_and_password(correo, contraseña)
                if usuario.upper().startswith("TEC"):
                    rol = "TEC"
                elif usuario.upper().startswith("MED"):
                    rol = "MED"
                else:
                    mensaje.value = "Usuario no reconocido como TEC o MED"
                    mensaje.color = "red"
                    self.page.update()
                    return

                Menu_Principal(self.page, usuario=usuario.upper(), rol=rol).mostrar()

            except Exception as err:
                mensaje.value = "Credenciales inválidas"
                mensaje.color = "red"
                print(f"Error: {err}")
                self.page.update()

        # Cambios clave aquí
        def enfocar_contraseña(e):
            pass_input.focus()  # ✅ Enfoca directamente el campo de contraseña
            self.page.update()

        user_input.on_submit = enfocar_contraseña
        pass_input.on_submit = validar_credenciales

        login_layout = ft.Column([
            logo,
            ft.Text("Hola, Bienvenido a KeratoTECH", size=30, weight="bold", color="#1E88E5"),
            ft.Text("Inicio de sesión", size=20),
            user_input,
            pass_input,
            ft.ElevatedButton("Ingresar", on_click=validar_credenciales),
            mensaje,
            ft.TextButton("¿No tienes tu usuario y contraseña?", on_click=mostrar_ayuda),
            ayuda_mensaje
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20)

        self.page.add(ft.Container(content=login_layout, alignment=ft.alignment.center, expand=True))
        self.page.update()