from Base_App import Base_App
import flet as ft
from firebase_config import db, bucket

class Ver_Historial(Base_App):
    def mostrar(self):
        self.limpiar()

        self.search_input = ft.TextField(label="Buscar DNI", width=300)
        self.boton_buscar = ft.ElevatedButton("Buscar", on_click=self.buscar_pacientes)
        self.lista_resultados = ft.Column(scroll=ft.ScrollMode.AUTO)
        self.titulo = ft.Text("Historial de pacientes", size=24, weight="bold")

        self.page.add(
            ft.Container(
                ft.Column([
                    self.cargar_logo(),
                    self.titulo,
                    ft.Row([self.search_input, self.boton_buscar]),
                    ft.ElevatedButton("Ver todos los pacientes", on_click=self.ver_todos),
                    self.lista_resultados
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.START),
                expand=True,
                alignment=ft.alignment.top_center,
                padding=20
            )
        )
        self.page.update()

        self.todos_pacientes = []
        self.obtener_dnis()

    def obtener_dnis(self):
        # Aquí listamos todos los DNIs (IDs de documentos dentro de "pacientes")
        self.todos_pacientes = [doc.id for doc in db.collection("pacientes").list_documents()]

    def buscar_pacientes(self, e=None):
        filtro = self.search_input.value.strip()
        if not filtro:
            return

        self.lista_resultados.controls.clear()
        for dni in self.todos_pacientes:
            if dni.startswith(filtro):
                self.lista_resultados.controls.append(self.crear_fila_paciente(dni))
        self.page.update()

    def ver_todos(self, e=None):
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

            botones = [
                ft.ElevatedButton("Descargar reporte IA", on_click=lambda e, d=dni, f=fecha: self.descargar_archivo(d, f, f"{dni}_{f}_reporte.pdf")),
            ]

            if estado == "Diagnosticado":
                botones.append(
                    ft.ElevatedButton("Descargar diagnóstico", on_click=lambda e, d=dni, f=fecha: self.descargar_archivo(d, f, "diagnostico.pdf"))
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

    def descargar_archivo(self, dni, fecha, archivo_nombre):
        blob = bucket.blob(f"pacientes/{dni}/{fecha}/{archivo_nombre}")
        destino = f"{dni}_{fecha}_{archivo_nombre}"
        try:
            blob.download_to_filename(destino)
            print(f"[DESCARGADO] {destino}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"{archivo_nombre} descargado"))
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as err:
            print(f"[ERROR] No se pudo descargar {archivo_nombre}: {err}")