from Pantallas.Base_App import Base_App
import flet as ft
from Pantallas.firebase_config import db
from firebase_admin import firestore
from datetime import datetime

class Ver_Perfil(Base_App):
    def __init__(self, page, usuario, rol):
        super().__init__(page, usuario, rol)
        self.datos = {}
        self.editando = False

    def mostrar(self):
        self.limpiar()
        self.datos = self.obtener_datos_usuario()

        if not self.datos:
            self.page.add(ft.Text("No se encontraron datos del usuario.", color="red"))
            return

        logo = self.cargar_logo()
        titulo = ft.Text("Mi Perfil", size=28, weight="bold", color="#1E88E5", text_align=ft.TextAlign.CENTER)

        nombre_completo = f"{self.datos.get('nombre', '')} {self.datos.get('apellido', '')}"
        correo = self.datos.get("correo", "")
        rol = self.datos.get("rol", "")
        sede = self.datos.get("sede", "No registrada")
        celular = self.datos.get("celular", "")

        # Inputs editables
        celular_input = ft.TextField(label="Celular", value=celular, width=300, visible=False)
        correo_input = ft.TextField(label="Correo", value=correo, width=300, visible=False)

        # Textos visibles cuando no se edita
        texto_celular = ft.Text(
            f"Número: {celular if celular else 'No hay número registrado aún'}",
            size=16,
            italic=not celular
        )
        texto_correo = ft.Text(
            f"Correo: {correo if correo else 'No registrado'}",
            size=16,
            italic=not correo
        )

        mensaje = ft.Text("", size=14, color="gray")

        def alternar_edicion(e):
            self.editando = not self.editando
            if self.editando:
                celular_input.visible = True
                correo_input.visible = True
                texto_celular.visible = False
                texto_correo.visible = False
                boton_editar.text = "Guardar"
            else:
                nuevo_cel = celular_input.value.strip()
                nuevo_correo = correo_input.value.strip()

                try:
                    db.collection("usuarios").document(self.usuario.lower()).update({
                        "celular": nuevo_cel,
                        "correo": nuevo_correo
                    })
                    ahora = datetime.now().strftime("%H:%M - %d/%m/%Y")
                    mensaje.value = f"Última actualización a las {ahora}"
                    mensaje.color = "green"

                    texto_celular.value = f"Número: {nuevo_cel if nuevo_cel else 'No hay número registrado aún'}"
                    texto_celular.italic = not nuevo_cel

                    texto_correo.value = f"Correo: {nuevo_correo if nuevo_correo else 'No registrado'}"
                    texto_correo.italic = not nuevo_correo

                except Exception as err:
                    mensaje.value = "Error al guardar los datos"
                    mensaje.color = "red"
                    print(f"[ERROR] {err}")

                celular_input.visible = False
                correo_input.visible = False
                texto_celular.visible = True
                texto_correo.visible = True
                boton_editar.text = "Editar"

            self.page.update()

        boton_editar = ft.TextButton("Editar", on_click=alternar_edicion)
        boton_volver = ft.ElevatedButton("Volver al menú", on_click=lambda e: self.volver())

        # Perfil general (no editable)
        campos = [
            ft.Text(f"{nombre_completo}", size=16),
            ft.Text(f"{'Médico Oftalmólogo' if rol == 'MED' else 'Técnico'}", size=16),
            ft.Text(f"Sede: {sede}", size=16),
        ]

        # Sección: Datos de contacto
        datos_contacto = ft.Column([
            ft.Row([
                ft.Text("Datos de contacto", size=17, weight="bold"),
                boton_editar
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20),

            texto_correo,
            correo_input,
            texto_celular,
            celular_input
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # Layout principal
        self.page.add(
            ft.Column([
                logo,
                titulo,
                ft.Column(campos, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                datos_contacto,
                mensaje,
                boton_volver
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=25)
        )
        self.page.update()

    def obtener_datos_usuario(self):
        try:
            doc = db.collection("usuarios").document(self.usuario.lower()).get()
            return doc.to_dict() if doc.exists else {}
        except Exception as e:
            print(f"[ERROR] No se pudo obtener el perfil: {e}")
            return {}

    def volver(self):
        from Pantallas.Menu_Principal import Menu_Principal
        Menu_Principal(self.page, self.usuario, self.rol).mostrar()