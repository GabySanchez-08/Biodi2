# === Archivo: Ver_Historial.py ===
from Base_App import Base_App
import flet as ft
from firebase_config import db, bucket

class Ver_Historial(Base_App):
    def __init__(self, page, usuario=None, rol=None):
        super().__init__(page, usuario, rol)
        self.mostrando_todos = False 

    def mostrar(self):
        self.limpiar()

        self.search_input = ft.TextField(label="Buscar DNI", width=300)
        self.boton_buscar = ft.ElevatedButton("Buscar", on_click=self.buscar_pacientes)
        self.boton_buscar_todos = ft.ElevatedButton("Ver todos los pacientes", on_click=self.ver_todos)
        self.lista_resultados = ft.Column(scroll=ft.ScrollMode.AUTO)
        self.titulo = ft.Text("Historial de pacientes", size=24, weight="bold")

        self.page.add(
            ft.Stack([
                ft.Container(
                    ft.Column([
                        ft.TextButton("← Volver al menú", on_click=self.volver_menu),
                        self.cargar_logo(),
                        self.titulo,
                        ft.Row([self.search_input, self.boton_buscar, self.boton_buscar_todos]),
                        self.lista_resultados
                    ],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.START),
                    expand=True,
                    alignment=ft.alignment.top_center,
                    padding=20
                )
            ])
        )
        self.page.update()

        self.todos_pacientes = []
        self.obtener_dnis()
        self.mostrando_todos = False

    def obtener_dnis(self):
        self.todos_pacientes = [doc.id for doc in db.collection("pacientes").list_documents()]

    def buscar_pacientes(self, e=None):
        filtro = self.search_input.value.strip()
        if not filtro:
            return

        self.mostrando_todos = False
        self.lista_resultados.controls.clear()
        for dni in self.todos_pacientes:
            if dni.startswith(filtro):
                self.lista_resultados.controls.append(self.crear_fila_paciente(dni))
        self.page.update()

    def ver_todos(self, e=None):
        if self.mostrando_todos:
            return
        self.mostrando_todos = True
        self.lista_resultados.controls.clear()
        for dni in self.todos_pacientes:
            self.lista_resultados.controls.append(self.crear_fila_paciente(dni))
        self.page.update()

    def crear_fila_paciente(self, dni):
        registros = db.collection("pacientes").document(dni).collection("registros").stream()
        registros_ordenados = sorted(registros, key=lambda d: d.id, reverse=True)

        filas = []
        for registro in registros_ordenados:
            datos = registro.to_dict()
            fecha = registro.id
            estado = "Diagnosticado" if "diagnostico" in datos else "Pendiente de diagnóstico"
            color_estado = "green" if estado == "Diagnosticado" else "orange"

            botones = []
            if self.archivo_existe(dni, fecha, f"{dni}_{fecha}_reporte.pdf"):
                botones.append(
                    ft.ElevatedButton("Descargar reporte", on_click=lambda e, d=dni, f=fecha: self.descargar_archivo(d, f, f"{d}_{f}_reporte.pdf"))
                )
            else:
                botones.append(ft.Text("Reporte no disponible", size=12, italic=True))

            if estado == "Diagnosticado":
                if self.archivo_existe(dni, fecha, f"{dni}_{fecha}_diagnostico.pdf"):
                    botones.append(
                        ft.ElevatedButton("Descargar diagnóstico", on_click=lambda e, d=dni, f=fecha: self.descargar_archivo(d, f, f"{d}_{f}_diagnostico.pdf"))
                    )
                else:
                    botones.append(ft.Text("Diagnóstico no disponible", size=12, italic=True))
            else:
                botones.append(ft.Text("Pendiente de diagnóstico", size=12, italic=True))
                if self.rol == "MED":
                    botones.append(
                        ft.ElevatedButton("Añadir diagnóstico", on_click=lambda e, d=dni, f=fecha: self.abrir_dialogo_diagnostico(d, f))
                    )

            filas.append(
                ft.Container(
                    ft.Column([
                        ft.Text(f"Fecha: {fecha}", weight="bold"),
                        ft.Text(f"Estado: {estado}", color=color_estado),
                        ft.Row(botones, spacing=10)
                    ], spacing=5),
                    bgcolor=ft.colors.GREY_100,
                    padding=10,
                    border_radius=10
                )
            )

        return ft.Container(
            ft.Column([
                ft.Text(f"DNI: {dni}", size=18, weight="bold"),
                *filas
            ],
            spacing=10),
            border=ft.border.all(1, ft.colors.GREY),
            padding=10,
            margin=10
        )

    def abrir_dialogo_diagnostico(self, dni, fecha):
        from Registrar_Diagnostico import Registrar_Diagnostico
        Registrar_Diagnostico(self.page, dni, fecha, self.usuario, self.rol).mostrar()

    def cerrar_dialogo(self):
        self.page.dialog.open = False
        self.page.update()

    def guardar_diagnostico(self, dni, fecha, texto):
        try:
            db.collection("pacientes").document(dni).collection("registros").document(fecha).update({
                "diagnostico": texto
            })
            print(f"[INFO] Diagnóstico guardado para {dni} ({fecha})")
            self.ver_todos()
        except Exception as err:
            print(f"[ERROR] No se pudo guardar el diagnóstico: {err}")

    def archivo_existe(self, dni, fecha, archivo_nombre):
        try:
            return bucket.blob(f"pacientes/{dni}/{fecha}/{archivo_nombre}").exists()
        except Exception as err:
            print(f"[ERROR] Verificación de existencia falló: {err}")
            return False

    def descargar_archivo(self, dni, fecha, archivo_nombre):
        from flet import FilePicker
        picker = FilePicker()
        self.page.overlay.append(picker)
        self.page.update()

        def cuando_selecciona_destino(e):
            if not picker.result or not picker.result.path:
                return
            destino = picker.result.path
            blob = bucket.blob(f"pacientes/{dni}/{fecha}/{archivo_nombre}")
            try:
                blob.download_to_filename(destino)
                print(f"[DESCARGADO] {destino}")
                self.page.snack_bar = ft.SnackBar(ft.Text(f"{archivo_nombre} descargado en {destino}"))
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as err:
                print(f"[ERROR] No se pudo descargar {archivo_nombre}: {err}")

        picker.on_result = cuando_selecciona_destino
        picker.save_file(dialog_title="Guardar archivo como", file_name=archivo_nombre)

    def volver_menu(self, e):
        from Menu_Principal import Menu_Principal
        Menu_Principal(self.page, self.usuario, self.rol).mostrar()