## ---- Login.py
from Pantallas.Base_App import Base_App
import flet as ft
from Pantallas.Menu_Principal import Menu_Principal
from Pantallas.firebase_auth_config import auth
from firebase_admin import firestore

class Login(Base_App):
    def mostrar(self):
        self.limpiar()
        logo = self.cargar_logo()

        # Cambiado: ahora se ingresa el correo directamente
        user_input = ft.TextField(label="Correo", autofocus=True, width=400)
        pass_input = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=400)
        mensaje = ft.Text("", size=14)

        ayuda_mensaje = ft.Container(
            content=ft.Text("", size=14, color="gray", text_align=ft.TextAlign.CENTER),
            alignment=ft.alignment.center,
            width=450,
            padding=10
        )

        def mostrar_ayuda(e):
            ayuda_mensaje.content.value = (
                "Por el momento no se pueden recuperar contraseñas desde nuestra app. "
                "Por favor, contáctese con la institución a la que pertenece."
            )
            self.page.update()

        def validar_credenciales(e=None):
            entrada_usuario = user_input.value.strip().lower()
            contraseña = pass_input.value.strip()

            if not entrada_usuario or not contraseña:
                mensaje.value = "Completa todos los campos"
                mensaje.color = "red"
                self.page.update()
                return

            # Autocompletar dominio si no se incluye
            if "@" not in entrada_usuario:
                correo = f"{entrada_usuario}@gmail.com"
            else:
                correo = entrada_usuario

            try:
                user = auth.sign_in_with_email_and_password(correo, contraseña)
                doc_id = correo.split("@")[0].lower()

                db = firestore.client()
                doc = db.collection("usuarios").document(doc_id).get()

                if not doc.exists:
                    mensaje.value = "Usuario no registrado en la base de datos"
                    mensaje.color = "red"
                    self.page.update()
                    return

                data = doc.to_dict()
                rol = data.get("rol")

                if rol not in ["MED", "TEC"]:
                    mensaje.value = "Rol no reconocido"
                    mensaje.color = "red"
                    self.page.update()
                    return

                Menu_Principal(self.page, usuario=doc_id, rol=rol).mostrar()

            except Exception as err:
                mensaje.value = "Credenciales inválidas"
                mensaje.color = "red"
                print(f"[ERROR] {err}")
                self.page.update()

        def enfocar_contraseña(e):
            pass_input.focus()
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