from Base_App import Base_App
import flet as ft
from Menu_Principal import Menu_Principal
class Login(Base_App):
    def mostrar(self):
        self.limpiar()
        logo = self.cargar_logo()

        user_input = ft.TextField(label="Usuario", autofocus=True, width=400)
        pass_input = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=400)
        mensaje = ft.Text("", size=14)

        # Mensaje de ayuda en un contenedor centrado
        ayuda_mensaje = ft.Container(
            content=ft.Text("", size=14, color="gray", text_align=ft.TextAlign.CENTER),
            alignment=ft.alignment.center,
            width=450,
            padding=10
        )

        def mostrar_ayuda(e):
            ayuda_mensaje.content.value = "Por el momento no se pueden recuperar contraseñas desde nuestra app. Por favor, contáctese con la institución a la que pertenece."
            self.page.update()

        def validar_credenciales(e):
            if user_input.value == "admin" and pass_input.value == "1234":
                Menu_Principal(self.page).mostrar() # <--- Aquí
            else:
                mensaje.value = "Credenciales inválidas"
                mensaje.color = "red"
                self.page.update()

        login_layout = ft.Column([
            logo,
            ft.Text("Hola, Bienvenido a KeratoTECH", size=30, weight="bold", color="#5E35B1"),
            ft.Text("Inicio de sesión", size=20),
            user_input,
            pass_input,
            ft.ElevatedButton("Ingresar", on_click=validar_credenciales),
            mensaje,
            ft.TextButton("¿No tienes tu usuario y contraseña?", on_click=mostrar_ayuda),
            ayuda_mensaje  # se muestra centrado y delgado
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20)

        self.page.add(ft.Container(content=login_layout, alignment=ft.alignment.center, expand=True))
        self.page.update()