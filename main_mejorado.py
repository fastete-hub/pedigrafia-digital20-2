import customtkinter as ctk
import tkinter as tk 
from tkinter import messagebox, filedialog, simpledialog
import os, shutil, math, json
from datetime import datetime
import logging
from PIL import Image, ImageTk, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('Agg')

from config_mejorado import Config
from database import Database
from analysis_mejorado import ImageAnalyzer
from scanner import Scanner
from app_utils import (
    setup_logging, backup_database, get_temp_file_path, mover_temporales_raiz_a_temp,
    limpiar_temporales, apply_runtime_config_overrides, save_runtime_setting
)
from services.patient_service import PatientService
from services.report_service import ReportService
from services.analysis_service import AnalysisService
from services.alert_service import AlertService

ctk.set_appearance_mode(Config.THEME_MODE)
ctk.set_default_color_theme(Config.THEME_COLOR)

class ModernButton(ctk.CTkButton):
    """Botón con efectos hover mejorados"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.original_fg = kwargs.get('fg_color', Config.get_colors()['primary'])
        
    def on_enter(self, e):
        self.configure(cursor="hand2")
        
    def on_leave(self, e):
        self.configure(cursor="")

class PodoscopioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.logger = setup_logging()
        apply_runtime_config_overrides()
        self._migrar_temporales_raiz()
        self._limpiar_temporales_inicio()
        self.title("Podoscopio Pro v3.0 - Sistema Avanzado de Análisis Podológico")
        self.geometry(Config.WINDOW_SIZE)
        self.minsize(1200, 700)
        self.state("zoomed")
        
        self.colors = Config.get_colors()
        self.configure(fg_color=self.colors['bg_secondary'])
        
        # Variables de estado
        self.db = Database()
        self._backup_startup()
        self.paciente_actual = None
        self.estudio_id_edicion = None 
        self.path_original_temp = None
        self.path_mapa_temp = None
        self.modo_visualizacion = "Original"
        self.modo_captura = "Digital"
        self.pixels_por_cm = None
        self.lines_data = []
        self.drawing_start = None
        self.current_line_id = None
        self.img_tk_cache = None
        
        # Nuevas variables para zoom y pan
        self.zoom_level = 1.0
        self.pan_start = None
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        
        # Configuración de mapa de calor
        self.colormap_actual = "Turbo"
        self.intensidad_calor = 1.0
        self.suavizado_activo = True
        
        # Estadísticas de análisis
        self.stats_presion = {}
        
        # Frame principal
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.mostrar_inicio()

    def _migrar_temporales_raiz(self):
        try:
            movidos = mover_temporales_raiz_a_temp()
            if movidos:
                self.logger.info("Se movieron %s temporales desde raíz a temp/legacy", movidos)
        except Exception:
            self.logger.exception("No se pudieron organizar temporales de raíz")


    def _limpiar_temporales_inicio(self):
        try:
            eliminados = limpiar_temporales(max_horas=24)
            if eliminados:
                self.logger.info("Se limpiaron %s temporales antiguos al iniciar", eliminados)
        except Exception:
            self.logger.exception("No se pudieron limpiar temporales al iniciar")

    def _backup_startup(self):
        try:
            backup = backup_database()
            if backup:
                self.logger.info("Backup inicial creado: %s", backup)
        except Exception:
            self.logger.exception("No se pudo crear backup inicial")

    def on_close(self):
        try:
            backup = backup_database()
            if backup:
                self.logger.info("Backup de cierre creado: %s", backup)
        except Exception:
            self.logger.exception("No se pudo crear backup al cerrar")

        try:
            self.db.close()
        except Exception:
            self.logger.exception("No se pudo cerrar la base de datos al salir")
        self.destroy()

    def _abrir_en_sistema(self, ruta, tipo="ruta"):
        """Abre una ruta en el sistema operativo y muestra fallback amigable."""
        try:
            os.startfile(ruta)
            return True
        except Exception:
            import subprocess
            try:
                subprocess.Popen(['xdg-open', ruta])
                return True
            except Exception:
                self.logger.exception("No se pudo abrir %s en el sistema: %s", tipo, ruta)
                messagebox.showinfo("Info", f"No se pudo abrir automáticamente. {tipo.capitalize()}:\n{ruta}")
                return False

    def crear_backup_manual(self):
        """Genera un backup de la base y ofrece abrir la carpeta."""
        try:
            backup = backup_database()
            if backup:
                self.logger.info("Backup manual creado: %s", backup)
                abrir = messagebox.askyesno("Backup creado", f"Se creó un backup en:\n{backup}\n\n¿Desea abrir la carpeta?")
                if abrir:
                    self._abrir_en_sistema(str(backup.parent), tipo="carpeta de backups")
            else:
                messagebox.showwarning("Backup", "No se encontró la base de datos para respaldar.")
        except Exception:
            self.logger.exception("Error creando backup manual")
            messagebox.showerror("Error", "No se pudo crear el backup. Revise permisos de carpeta.")

    def limpiar_temporales_manual(self):
        try:
            eliminados = limpiar_temporales(max_horas=0)
            messagebox.showinfo("Temporales", f"Se eliminaron {eliminados} archivos temporales.")
            self.logger.info("Limpieza manual de temporales: %s eliminados", eliminados)
        except Exception:
            self.logger.exception("Error limpiando temporales manualmente")
            messagebox.showerror("Error", "No se pudieron limpiar los temporales.")

    def limpiar_ui(self):
        """Limpia todos los widgets del frame principal"""
        for w in self.main_frame.winfo_children():
            w.destroy()

    def crear_gradiente_header(self, master, texto, altura=180):
        """Crea un header con gradiente visual"""
        header = ctk.CTkFrame(master, height=altura, corner_radius=0, fg_color=self.colors['primary'])
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Título con sombra
        titulo_frame = ctk.CTkFrame(header, fg_color="transparent")
        titulo_frame.pack(expand=True)
        
        ctk.CTkLabel(
            titulo_frame, 
            text=texto,
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['title'], "bold"),
            text_color="white"
        ).pack(pady=20)
        
        # Subtítulo
        ctk.CTkLabel(
            titulo_frame,
            text="Sistema Profesional de Análisis Biomecánico",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['small']),
            text_color=self.colors['secondary']
        ).pack()
        
        return header

    def mostrar_inicio(self):
        """Pantalla de inicio mejorada con estadísticas visuales"""
        self.limpiar_ui()
        self.estudio_id_edicion = None
        
        # Header con gradiente
        self.crear_gradiente_header(self.main_frame, "PODOSCOPIO PRO")
        
        # Estadísticas en cards modernas
        stats_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_container.pack(pady=50)
        
        pacientes, estudios = self.db.contar_stats()
        
        # Cards de estadísticas
        self.crear_stat_card_moderna(stats_container, "Pacientes Registrados", pacientes, "👥", 0)
        self.crear_stat_card_moderna(stats_container, "Estudios Realizados", estudios, "📊", 1)
        self.crear_stat_card_moderna(stats_container, "Análisis Hoy", self.obtener_estudios_hoy(), "🕐", 2)
        
        # Botones principales con diseño moderno
        btn_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_container.pack(pady=40)
        
        ModernButton(
            btn_container,
            text="➕  NUEVO PACIENTE",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['heading'], "bold"),
            height=70,
            width=320,
            corner_radius=Config.CORNER_RADIUS['lg'],
            fg_color=self.colors['primary'],
            hover_color=self.colors['primary_hover'],
            command=self.nuevo_paciente
        ).pack(side="left", padx=15)
        
        ModernButton(
            btn_container,
            text="🔍  BUSCAR PACIENTE",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['heading'], "bold"),
            height=70,
            width=320,
            corner_radius=Config.CORNER_RADIUS['lg'],
            fg_color=self.colors['bg_primary'],
            text_color=self.colors['primary'],
            border_width=3,
            border_color=self.colors['primary'],
            hover_color=self.colors['bg_tertiary'],
            command=self.buscar_paciente
        ).pack(side="left", padx=15)
        
        ModernButton(
            btn_container,
            text="⚙️  CONFIGURACIÓN",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['heading'], "bold"),
            height=70,
            width=320,
            corner_radius=Config.CORNER_RADIUS['lg'],
            fg_color=self.colors['secondary'],
            hover_color="#0891b2",
            command=self.mostrar_configuracion
        ).pack(side="left", padx=15)
        
        # Footer con versión
        footer = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=50)
        footer.pack(side="bottom", fill="x", pady=20)
        ctk.CTkLabel(
            footer,
            text="Versión 3.0 | Desarrollado con IA avanzada",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['small']),
            text_color=self.colors['text_secondary']
        ).pack()

    def crear_stat_card_moderna(self, master, titulo, valor, icono, columna):
        """Crea una tarjeta de estadística moderna con iconos y animación"""
        card = ctk.CTkFrame(
            master,
            width=280,
            height=160,
            corner_radius=Config.CORNER_RADIUS['lg'],
            fg_color=self.colors['bg_primary'],
            border_width=2,
            border_color=self.colors['border']
        )
        card.grid(row=0, column=columna, padx=20)
        card.pack_propagate(False)
        
        # Icono grande
        ctk.CTkLabel(
            card,
            text=icono,
            font=(Config.FONT_FAMILY, 40)
        ).pack(pady=(25, 5))
        
        # Valor
        ctk.CTkLabel(
            card,
            text=str(valor),
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['title'], "bold"),
            text_color=self.colors['primary']
        ).pack()
        
        # Título
        ctk.CTkLabel(
            card,
            text=titulo,
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['small']),
            text_color=self.colors['text_secondary']
        ).pack(pady=(0, 10))
        
        # Efecto hover
        card.bind("<Enter>", lambda e: card.configure(border_color=self.colors['primary']))
        card.bind("<Leave>", lambda e: card.configure(border_color=self.colors['border']))

    def obtener_estudios_hoy(self):
        """Obtiene el número de estudios realizados hoy"""
        try:
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            cursor = self.db.cursor
            result = cursor.execute(
                "SELECT COUNT(*) FROM informes WHERE fecha = ?", 
                (fecha_hoy,)
            ).fetchone()
            return result[0] if result else 0
        except Exception:
            self.logger.exception("Error obteniendo cantidad de estudios del día")
            return 0

    def mostrar_configuracion(self):
        """Muestra panel de configuración con opciones de tema y análisis"""
        self.limpiar_ui()
        
        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color=self.colors['primary'], height=100, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ModernButton(
            header,
            text="← Volver",
            width=120,
            fg_color="transparent",
            hover_color=self.colors['primary_hover'],
            command=self.mostrar_inicio
        ).pack(side="left", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="⚙️ CONFIGURACIÓN",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['subtitle'], "bold"),
            text_color="white"
        ).pack(side="left", padx=20)
        
        # Panel de configuración
        config_container = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color="transparent"
        )
        config_container.pack(fill="both", expand=True, padx=50, pady=30)
        
        # Sección: Tema
        self.crear_seccion_config(config_container, "🎨 Apariencia")
        
        tema_frame = ctk.CTkFrame(config_container, fg_color=self.colors['bg_primary'], corner_radius=12)
        tema_frame.pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(
            tema_frame,
            text="Tema de la aplicación:",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body'], "bold")
        ).pack(side="left", padx=20, pady=15)
        
        def cambiar_tema():
            nuevo_tema = Config.toggle_theme()
            messagebox.showinfo(
                "Reinicio necesario",
                "Los cambios de tema se aplicarán al reiniciar la aplicación."
            )
        
        ModernButton(
            tema_frame,
            text=f"Cambiar a tema {'Oscuro' if Config.THEME_MODE == 'light' else 'Claro'}",
            command=cambiar_tema,
            width=200
        ).pack(side="right", padx=20, pady=10)
        
        # Sección: Análisis
        self.crear_seccion_config(config_container, "🔬 Configuración de Análisis")
        
        analisis_frame = ctk.CTkFrame(config_container, fg_color=self.colors['bg_primary'], corner_radius=12)
        analisis_frame.pack(fill="x", pady=10, padx=20, ipady=15)
        
        # Opciones de análisis (placeholder para futuras opciones)
        ctk.CTkLabel(
            analisis_frame,
            text="Las opciones avanzadas de análisis están disponibles durante el estudio.",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body']),
            text_color=self.colors['text_secondary']
        ).pack(padx=20, pady=15)

        # Sección: Calibración
        self.crear_seccion_config(config_container, "⚖️ Calibración automática")

        calib_frame = ctk.CTkFrame(config_container, fg_color=self.colors['bg_primary'], corner_radius=12)
        calib_frame.pack(fill="x", pady=10, padx=20, ipady=10)

        self.lbl_calib = ctk.CTkLabel(
            calib_frame,
            text=f"Factor de corrección actual: {Config.CALIBRACION_CORRECCION_PXMM:.2f}",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body'], "bold"),
            text_color=self.colors['text_primary']
        )
        self.lbl_calib.pack(anchor="w", padx=20, pady=(12, 6))

        ctk.CTkLabel(
            calib_frame,
            text="Si 5 cm se miden como 4 cm, usar 0.80. Ajuste fino en pasos de 0.05.",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['small']),
            text_color=self.colors['text_secondary']
        ).pack(anchor="w", padx=20, pady=(0, 8))

        def ajustar_calibracion(delta):
            Config.CALIBRACION_CORRECCION_PXMM = max(0.50, min(1.30, Config.CALIBRACION_CORRECCION_PXMM + delta))
            save_runtime_setting("calibracion_correccion_pxmm", Config.CALIBRACION_CORRECCION_PXMM)
            self.lbl_calib.configure(text=f"Factor de corrección actual: {Config.CALIBRACION_CORRECCION_PXMM:.2f}")

        btns_calib = ctk.CTkFrame(calib_frame, fg_color="transparent")
        btns_calib.pack(anchor="w", padx=20, pady=(0, 12))

        ModernButton(btns_calib, text="- 0.05", width=90, command=lambda: ajustar_calibracion(-0.05)).pack(side="left", padx=(0, 8))
        ModernButton(btns_calib, text="+ 0.05", width=90, command=lambda: ajustar_calibracion(0.05)).pack(side="left", padx=8)

        # Sección: Mantenimiento
        self.crear_seccion_config(config_container, "🛠️ Mantenimiento")

        mantenimiento_frame = ctk.CTkFrame(config_container, fg_color=self.colors['bg_primary'], corner_radius=12)
        mantenimiento_frame.pack(fill="x", pady=10, padx=20, ipady=10)

        ctk.CTkLabel(
            mantenimiento_frame,
            text="Herramientas rápidas de soporte y respaldo:",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body']),
            text_color=self.colors['text_secondary']
        ).pack(anchor="w", padx=20, pady=(10, 5))

        botones_frame = ctk.CTkFrame(mantenimiento_frame, fg_color="transparent")
        botones_frame.pack(fill="x", padx=20, pady=(0, 10))

        ModernButton(
            botones_frame,
            text="💾 Crear backup ahora",
            command=self.crear_backup_manual,
            fg_color=self.colors['success'],
            hover_color="#059669",
            width=220
        ).pack(side="left", padx=(0, 10), pady=8)

        ModernButton(
            botones_frame,
            text="📂 Abrir logs",
            command=lambda: self._abrir_en_sistema(os.path.abspath("logs"), tipo="carpeta de logs"),
            width=180
        ).pack(side="left", padx=10, pady=8)

        ModernButton(
            botones_frame,
            text="📁 Abrir backups",
            command=lambda: self._abrir_en_sistema(os.path.abspath("backups"), tipo="carpeta de backups"),
            width=180
        ).pack(side="left", padx=10, pady=8)

        ModernButton(
            botones_frame,
            text="🧹 Limpiar temporales",
            command=self.limpiar_temporales_manual,
            width=200
        ).pack(side="left", padx=10, pady=8)

    def crear_seccion_config(self, master, titulo):
        """Crea un título de sección en configuración"""
        ctk.CTkLabel(
            master,
            text=titulo,
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['heading'], "bold"),
            text_color=self.colors['text_primary']
        ).pack(anchor="w", padx=20, pady=(20, 10))

    def nuevo_paciente(self):
        """Formulario mejorado para nuevo paciente"""
        self.limpiar_ui()
        
        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color=self.colors['primary'], height=90, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ModernButton(
            header,
            text="← Volver",
            width=120,
            fg_color="transparent",
            hover_color=self.colors['primary_hover'],
            command=self.mostrar_inicio
        ).pack(side="left", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="NUEVO PACIENTE",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['subtitle'], "bold"),
            text_color="white"
        ).pack(side="left", padx=20)
        
        # Contenedor con scroll para formularios largos
        scroll_container = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color="transparent"
        )
        scroll_container.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Formulario con mejor diseño
        form_container = ctk.CTkFrame(
            scroll_container,
            fg_color="transparent"
        )
        form_container.pack(pady=20)
        
        form = ctk.CTkFrame(
            form_container,
            fg_color=self.colors['bg_primary'],
            corner_radius=Config.CORNER_RADIUS['lg'],
            border_width=2,
            border_color=self.colors['border']
        )
        form.pack(padx=40, pady=20, ipadx=50, ipady=30)
        
        # Campos del formulario con mejor estilo
        campos = [
            ("Nombre Completo *", "entry"),
            ("Edad", "dropdown", [str(i) for i in range(1, 100)]),
            ("Obra Social", "entry"),
            ("Talle del pie (mm)", "dropdown", [str(i) for i in range(100, 351, 5)]),
            ("Teléfono", "entry"),
            ("Email", "entry"),
        ]
        
        self.form_entries = {}
        
        for idx, campo in enumerate(campos):
            nombre = campo[0]
            tipo = campo[1]
            
            # Label
            ctk.CTkLabel(
                form,
                text=nombre,
                font=(Config.FONT_FAMILY, Config.FONT_SIZES['body'], "bold"),
                text_color=self.colors['text_primary']
            ).grid(row=idx, column=0, padx=25, pady=15, sticky="e")
            
            # Campo
            if tipo == "entry":
                widget = ctk.CTkEntry(
                    form,
                    width=350,
                    height=40,
                    corner_radius=Config.CORNER_RADIUS['sm'],
                    border_width=2,
                    border_color=self.colors['border']
                )
            else:  # dropdown
                valores = campo[2]
                widget = ctk.CTkOptionMenu(
                    form,
                    width=350,
                    height=40,
                    values=valores,
                    corner_radius=Config.CORNER_RADIUS['sm'],
                    fg_color=self.colors['bg_secondary'],
                    button_color=self.colors['border'],
                    button_hover_color=self.colors['primary']
                )
                if nombre.startswith("Edad"):
                    widget.set("30")
                elif nombre.startswith("Talle"):
                    widget.set("250")
            
            widget.grid(row=idx, column=1, padx=25, pady=15)
            
            # Guardar referencia
            key = nombre.split()[0].lower()
            self.form_entries[key] = widget
        
        # Botón de guardar
        def guardar_paciente():
            edad = self.form_entries['edad'].get()
            obra_social = self.form_entries['obra'].get()
            email = self.form_entries['email'].get()
            telefono = self.form_entries['teléfono'].get()
            talle = self.form_entries['talle'].get()

            try:
                datos_paciente = PatientService.validar_y_normalizar(
                    self.form_entries['nombre'].get(), edad, obra_social, email, telefono, talle
                )
            except ValueError as e:
                messagebox.showerror("Datos inválidos", str(e))
                return

            pid = self.db.insertar_paciente(
                datos_paciente['nombre'],
                datos_paciente['edad'],
                datos_paciente['obra_social'],
                datos_paciente['email'],
                datos_paciente['telefono'],
                datos_paciente['talle'],
            )
            messagebox.showinfo("Éxito", f"Paciente '{datos_paciente['nombre']}' registrado correctamente")
            self.logger.info("Paciente registrado: id=%s nombre=%s", pid, datos_paciente['nombre'])
            self.seleccionar_paciente(pid)

        ModernButton(
            form_container,
            text="💾  GUARDAR PACIENTE",
            height=60,
            width=400,
            corner_radius=Config.CORNER_RADIUS['md'],
            fg_color=self.colors['success'],
            hover_color="#059669",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['heading'], "bold"),
            command=guardar_paciente
        ).pack(pady=30)

    def buscar_paciente(self):
        """Pantalla de búsqueda de pacientes mejorada"""
        self.limpiar_ui()
        
        # Variable de búsqueda
        search_var = tk.StringVar()
        
        # Header de búsqueda
        header = ctk.CTkFrame(
            self.main_frame,
            fg_color=self.colors['bg_primary'],
            height=110,
            corner_radius=0
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ModernButton(
            header,
            text="←",
            width=60,
            height=40,
            corner_radius=Config.CORNER_RADIUS['sm'],
            command=self.mostrar_inicio
        ).pack(side="left", padx=20, pady=30)
        
        # Barra de búsqueda mejorada
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.pack(side="left", padx=20, pady=30, fill="x", expand=True)
        
        ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=(Config.FONT_FAMILY, 20)
        ).pack(side="left", padx=5)
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Buscar por nombre del paciente...",
            width=600,
            height=50,
            corner_radius=Config.CORNER_RADIUS['xl'],
            border_width=2,
            border_color=self.colors['primary'],
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body']),
            textvariable=search_var
        )
        search_entry.pack(side="left", padx=10)
        search_entry.focus()
        
        # Contador de resultados
        contador_label = ctk.CTkLabel(
            header,
            text="",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body']),
            text_color=self.colors['text_secondary']
        )
        contador_label.pack(side="right", padx=30)
        
        # Área de resultados con scroll
        scroll_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True, padx=60, pady=30)
        
        def cargar_resultados(*args):
            # Limpiar resultados anteriores
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            
            # Buscar pacientes
            query = search_var.get()
            pacientes = self.db.buscar_pacientes(query)
            
            # Actualizar contador
            contador_label.configure(
                text=f"{len(pacientes)} paciente{'s' if len(pacientes) != 1 else ''} encontrado{'s' if len(pacientes) != 1 else ''}"
            )
            
            # Mostrar resultados
            if not pacientes:
                ctk.CTkLabel(
                    scroll_frame,
                    text="No se encontraron pacientes",
                    font=(Config.FONT_FAMILY, Config.FONT_SIZES['heading']),
                    text_color=self.colors['text_secondary']
                ).pack(pady=100)
            else:
                for paciente in pacientes:
                    self.crear_tarjeta_paciente(scroll_frame, paciente)
        
        # Vincular búsqueda en tiempo real
        search_var.trace_add("write", cargar_resultados)
        cargar_resultados()

    def crear_tarjeta_paciente(self, master, paciente):
        """Crea una tarjeta moderna para cada paciente en búsqueda"""
        card = ctk.CTkFrame(
            master,
            fg_color=self.colors['bg_primary'],
            corner_radius=Config.CORNER_RADIUS['md'],
            border_width=2,
            border_color=self.colors['border']
        )
        card.pack(fill="x", pady=8, padx=10)
        
        # Contenido de la tarjeta
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="x", padx=25, pady=20)
        
        # Icono de paciente
        ctk.CTkLabel(
            content_frame,
            text="👤",
            font=(Config.FONT_FAMILY, 30)
        ).pack(side="left", padx=(0, 15))
        
        # Información del paciente
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        # Nombre
        ctk.CTkLabel(
            info_frame,
            text=paciente[1].upper(),
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['heading'], "bold"),
            text_color=self.colors['text_primary'],
            anchor="w"
        ).pack(anchor="w")
        
        # Detalles
        detalles = []
        if paciente[2]:  # Edad
            detalles.append(f"{paciente[2]} años")
        if paciente[3]:  # Obra social
            detalles.append(paciente[3])
        
        if detalles:
            ctk.CTkLabel(
                info_frame,
                text=" | ".join(detalles),
                font=(Config.FONT_FAMILY, Config.FONT_SIZES['small']),
                text_color=self.colors['text_secondary'],
                anchor="w"
            ).pack(anchor="w", pady=(5, 0))
        
        # Botón de abrir
        ModernButton(
            content_frame,
            text="ABRIR FICHA →",
            width=150,
            height=40,
            corner_radius=Config.CORNER_RADIUS['sm'],
            fg_color=self.colors['primary'],
            hover_color=self.colors['primary_hover'],
            command=lambda: self.seleccionar_paciente(paciente[0])
        ).pack(side="right")
        
        # Efecto hover en la tarjeta
        def on_enter(e):
            card.configure(border_color=self.colors['primary'])
        
        def on_leave(e):
            card.configure(border_color=self.colors['border'])
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

    def seleccionar_paciente(self, paciente_id):
        """Muestra la ficha completa del paciente con sus estudios"""
        self.limpiar_ui()
        self.paciente_actual = self.db.obtener_paciente_real(paciente_id)
        self.estudio_id_edicion = None
        
        estudios = self.db.listar_informes_paciente(paciente_id)
        
        # Header del paciente
        header = ctk.CTkFrame(
            self.main_frame,
            fg_color=self.colors['primary'],
            height=130,
            corner_radius=0
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Botón volver
        ModernButton(
            header,
            text="← Inicio",
            width=100,
            fg_color="transparent",
            hover_color=self.colors['primary_hover'],
            command=self.mostrar_inicio
        ).pack(side="left", padx=20, pady=20)
        
        # Info del paciente en header
        info_frame = ctk.CTkFrame(header, fg_color="transparent")
        info_frame.pack(side="left", padx=20, pady=20)
        
        ctk.CTkLabel(
            info_frame,
            text=self.paciente_actual[1],
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['subtitle'], "bold"),
            text_color="white"
        ).pack(anchor="w")
        
        detalles_pac = []
        if self.paciente_actual[2]:  # Edad
            detalles_pac.append(f"{self.paciente_actual[2]} años")
        if self.paciente_actual[3]:  # Obra Social
            detalles_pac.append(f"OS: {self.paciente_actual[3]}")
        if self.paciente_actual[6]:  # Talle
            detalles_pac.append(f"Talle: {self.paciente_actual[6]}mm")
        
        if detalles_pac:
            ctk.CTkLabel(
                info_frame,
                text=" • ".join(detalles_pac),
                font=(Config.FONT_FAMILY, Config.FONT_SIZES['body']),
                text_color=self.colors['secondary']
            ).pack(anchor="w", pady=(5, 0))
        
        # Botón eliminar paciente
        ModernButton(
            header,
            text="🗑️ Eliminar",
            width=120,
            fg_color=self.colors['error'],
            hover_color="#dc2626",
            command=lambda: self.borrar_paciente(paciente_id)
        ).pack(side="right", padx=20, pady=20)
        
        # Contenido principal - División en paneles
        main_content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Panel izquierdo - Lista de estudios
        left_panel = ctk.CTkFrame(
            main_content,
            fg_color=self.colors['bg_primary'],
            corner_radius=Config.CORNER_RADIUS['lg'],
            border_width=2,
            border_color=self.colors['border']
        )
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        # Título del panel
        title_frame = ctk.CTkFrame(left_panel, fg_color=self.colors['bg_tertiary'], corner_radius=0)
        title_frame.pack(fill="x", padx=2, pady=2)
        
        ctk.CTkLabel(
            title_frame,
            text="📊 HISTORIAL DE ESTUDIOS",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['heading'], "bold"),
            text_color=self.colors['text_primary']
        ).pack(pady=15)
        
        # Lista scrolleable de estudios
        estudios_scroll = ctk.CTkScrollableFrame(
            left_panel,
            fg_color="transparent"
        )
        estudios_scroll.pack(fill="both", expand=True, padx=15, pady=15)
        
        if not estudios:
            # Sin estudios
            empty_frame = ctk.CTkFrame(estudios_scroll, fg_color="transparent")
            empty_frame.pack(expand=True, pady=80)
            
            ctk.CTkLabel(
                empty_frame,
                text="📋",
                font=(Config.FONT_FAMILY, 50)
            ).pack()
            
            ctk.CTkLabel(
                empty_frame,
                text="No hay estudios registrados",
                font=(Config.FONT_FAMILY, Config.FONT_SIZES['heading']),
                text_color=self.colors['text_secondary']
            ).pack(pady=10)
        else:
            # Mostrar estudios
            for estudio in reversed(estudios):  # Más recientes primero
                self.crear_tarjeta_estudio(estudios_scroll, estudio)
        
        # Panel derecho - Acciones rápidas
        right_panel = ctk.CTkFrame(
            main_content,
            width=320,
            fg_color=self.colors['bg_primary'],
            corner_radius=Config.CORNER_RADIUS['lg'],
            border_width=2,
            border_color=self.colors['border']
        )
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)
        
        # Título
        ctk.CTkLabel(
            right_panel,
            text="⚡ ACCIONES RÁPIDAS",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body'], "bold"),
            text_color=self.colors['text_primary']
        ).pack(pady=20)
        
        # Botón nuevo estudio
        ModernButton(
            right_panel,
            text="➕ NUEVO ESTUDIO",
            height=70,
            corner_radius=Config.CORNER_RADIUS['md'],
            fg_color=self.colors['success'],
            hover_color="#059669",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body'], "bold"),
            command=self.pantalla_nuevo_estudio
        ).pack(fill="x", padx=20, pady=10)
        
        # Botón abrir carpeta del paciente
        ModernButton(
            right_panel,
            text="📁 ABRIR CARPETA",
            height=50,
            corner_radius=Config.CORNER_RADIUS['md'],
            fg_color=self.colors['secondary'],
            hover_color="#0891b2",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body']),
            command=lambda: self.abrir_carpeta_paciente(self.paciente_actual)
        ).pack(fill="x", padx=20, pady=10)
        
        if len(estudios) >= 2:
            ModernButton(
                right_panel,
                text="📉 COMPARAR ÚLTIMOS 2",
                height=50,
                corner_radius=Config.CORNER_RADIUS['md'],
                fg_color=self.colors['accent'],
                hover_color="#7c3aed",
                font=(Config.FONT_FAMILY, Config.FONT_SIZES['body']),
                command=self.mostrar_comparacion_paciente
            ).pack(fill="x", padx=20, pady=10)

        # Estadísticas del paciente
        if estudios:
            stats_frame = ctk.CTkFrame(
                right_panel,
                fg_color=self.colors['bg_tertiary'],
                corner_radius=Config.CORNER_RADIUS['md']
            )
            stats_frame.pack(fill="x", padx=20, pady=20)
            
            ctk.CTkLabel(
                stats_frame,
                text="📈 Resumen",
                font=(Config.FONT_FAMILY, Config.FONT_SIZES['body'], "bold")
            ).pack(pady=(15, 10))
            
            ctk.CTkLabel(
                stats_frame,
                text=f"Total de estudios: {len(estudios)}",
                font=(Config.FONT_FAMILY, Config.FONT_SIZES['small']),
                text_color=self.colors['text_secondary']
            ).pack(pady=5)
            
            # Fecha del último estudio
            ultimo_estudio = estudios[-1]
            ctk.CTkLabel(
                stats_frame,
                text=f"Último estudio: {ultimo_estudio[1]}",
                font=(Config.FONT_FAMILY, Config.FONT_SIZES['small']),
                text_color=self.colors['text_secondary']
            ).pack(pady=(5, 8), padx=10)

            try:
                inf_ult = self.db.obtener_informe(ultimo_estudio[0])
                alertas_ult = AlertService.desde_mediciones_json(inf_ult[6] if inf_ult else None)
                sem = AlertService.resumen_semaforo(alertas_ult)
                ctk.CTkLabel(
                    stats_frame,
                    text=f"Semáforo: {sem['nivel']}",
                    font=(Config.FONT_FAMILY, Config.FONT_SIZES['small'], "bold"),
                    text_color=sem['color']
                ).pack(pady=(2, 2), padx=10)
                ctk.CTkLabel(
                    stats_frame,
                    text=sem['mensaje'],
                    font=(Config.FONT_FAMILY, Config.FONT_SIZES['tiny']),
                    text_color=self.colors['text_secondary']
                ).pack(pady=(0, 15), padx=10)
            except Exception:
                pass

    def mostrar_comparacion_paciente(self):
        """Muestra comparación textual entre los dos últimos estudios del paciente."""
        try:
            resumen = AnalysisService.comparar_ultimos_dos_estudios(self.db, self.paciente_actual[0])
            messagebox.showinfo("Comparación de estudios", resumen)
        except ValueError as e:
            messagebox.showwarning("Comparación", str(e))
        except Exception:
            self.logger.exception("Error comparando estudios de paciente id=%s", self.paciente_actual[0])
            messagebox.showerror("Error", "No se pudo generar la comparación de estudios.")

    def crear_tarjeta_estudio(self, master, estudio):
        """Crea una tarjeta para cada estudio en el historial"""
        estudio_id, fecha, imagen_path = estudio
        
        card = ctk.CTkFrame(
            master,
            fg_color=self.colors['bg_secondary'],
            corner_radius=Config.CORNER_RADIUS['md'],
            border_width=1,
            border_color=self.colors['border']
        )
        card.pack(fill="x", pady=8, padx=5)

        # Barra de estado visual
        accent_bar = ctk.CTkFrame(card, width=10, corner_radius=8, fg_color=self.colors['border'])
        accent_bar.pack(side="left", fill="y", padx=(6, 0), pady=6)
        
        # Contenido
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=14, pady=15)
        
        # Fecha e icono
        left_info = ctk.CTkFrame(content, fg_color="transparent")
        left_info.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            left_info,
            text=f"📅 {fecha}",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body'], "bold"),
            text_color=self.colors['text_primary']
        ).pack(anchor="w")

        try:
            inf_est = self.db.obtener_informe(estudio_id)
            alertas_est = AlertService.desde_mediciones_json(inf_est[6] if inf_est else None)
            sem_est = AlertService.resumen_semaforo(alertas_est)
            accent_bar.configure(fg_color=sem_est['color'])
            ctk.CTkLabel(
                left_info,
                text=f"Semáforo estudio: {sem_est['nivel']}",
                font=(Config.FONT_FAMILY, Config.FONT_SIZES['tiny'], "bold"),
                text_color=sem_est['color']
            ).pack(anchor="w", pady=(2, 0))
        except Exception:
            pass
        
        # Botones de acción
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ModernButton(
            btn_frame,
            text="👁️ Ver",
            width=80,
            height=35,
            corner_radius=Config.CORNER_RADIUS['sm'],
            fg_color=self.colors['secondary'],
            command=lambda: self.reabrir_estudio(estudio_id)
        ).pack(side="left", padx=3)
        
        ModernButton(
            btn_frame,
            text="📄 PDF",
            width=80,
            height=35,
            corner_radius=Config.CORNER_RADIUS['sm'],
            fg_color=self.colors['error'],
            command=lambda: self.exportar_pdf_directo(estudio_id)
        ).pack(side="left", padx=3)

        ModernButton(
            btn_frame,
            text="🗑️",
            width=45,
            height=35,
            corner_radius=Config.CORNER_RADIUS['sm'],
            fg_color="#b91c1c",
            hover_color="#991b1b",
            command=lambda: self.borrar_estudio(estudio_id)
        ).pack(side="left", padx=3)

    def borrar_estudio(self, estudio_id):
        """Elimina un estudio puntual del paciente actual."""
        if not messagebox.askyesno("Eliminar estudio", "¿Desea eliminar este estudio? Esta acción no se puede deshacer."):
            return
        try:
            informe = self.db.obtener_informe(estudio_id)
            self.db.eliminar_informe(estudio_id)
            if informe and informe[3] and os.path.exists(informe[3]):
                try:
                    os.remove(informe[3])
                except Exception:
                    pass
                mapa = informe[3].replace("_original.png", "_mapa_calor.png")
                if os.path.exists(mapa):
                    try:
                        os.remove(mapa)
                    except Exception:
                        pass
            messagebox.showinfo("Éxito", "Estudio eliminado correctamente")
            self.seleccionar_paciente(self.paciente_actual[0])
        except Exception as e:
            self.logger.exception("Error eliminando estudio id=%s", estudio_id)
            messagebox.showerror("Error", f"No se pudo eliminar el estudio: {e}")

    def reabrir_estudio(self, estudio_id):
        """Abre un estudio existente para visualización/edición"""
        informe = self.db.obtener_informe(estudio_id)
        if not informe:
            messagebox.showerror("Error", "No se pudo cargar el estudio")
            return

        self.estudio_id_edicion = estudio_id
        self.pantalla_nuevo_estudio()

        # Cargar imagen si existe
        img_path = informe[3]
        if os.path.exists(img_path):
            self.path_original_temp = img_path

            # Regenerar mapa de calor
            try:
                _, mapa_img, self.stats_presion = ImageAnalyzer.analizar_imagen(
                    img_path,
                    modo=self.modo_captura,
                    colormap_name=self.colormap_actual,
                    intensidad=self.intensidad_calor,
                    suavizado=self.suavizado_activo
                )
                self.path_mapa_temp = str(get_temp_file_path("temp_mapa_view", ".png"))
                mapa_img.save(self.path_mapa_temp)
                self.mostrar_imagen_canvas(self.path_original_temp)
            except Exception as e:
                messagebox.showerror("Error", f"Error procesando imagen: {e}")

        # Cargar observaciones y recomendaciones
        self.obs_text.delete("0.0", "end")
        if informe[4]:
            self.obs_text.insert("0.0", informe[4])

        self.plan_text.delete("0.0", "end")
        if informe[5]:
            self.plan_text.insert("0.0", informe[5])

        # Cargar mediciones si existen
        if informe[6]:
            try:
                mediciones = json.loads(informe[6])
                # Aquí podrías reconstruir las líneas en el canvas si lo deseas
            except Exception:
                pass


    def pantalla_nuevo_estudio(self):
        """Pantalla principal de análisis con herramientas avanzadas"""
        self.limpiar_ui()
        # --- INICIALIZAR COLORMAP FIJO ---
        if not hasattr(self, "colormap_actual"):
            self.colormap_actual = "Turbo"
        
        # Reiniciar variables de zoom/pan
        self.zoom_level = 1.0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        
        # Header con herramientas
        header = ctk.CTkFrame(
            self.main_frame,
            fg_color=self.colors['primary'],
            height=90,
            corner_radius=0
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Botón volver
        ModernButton(
            header,
            text="← VOLVER",
            width=110,
            fg_color="transparent",
            border_width=2,
            border_color="white",
            hover_color=self.colors['primary_hover'],
            command=lambda: self.seleccionar_paciente(self.paciente_actual[0])
        ).pack(side="left", padx=20, pady=20)
        
        # Controles de medición
        medicion_frame = ctk.CTkFrame(header, fg_color="transparent")
        medicion_frame.pack(side="left", padx=20, pady=15)
        
        # Selector de lado
        self.lado_pie = ctk.StringVar(value="IZQ")
        
        ctk.CTkLabel(
            medicion_frame,
            text="Lado:",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['small']),
            text_color="white"
        ).pack(side="left", padx=(0, 5))
        
        for lado in Config.LADOS_PIE:
            ctk.CTkRadioButton(
                medicion_frame,
                text=lado,
                variable=self.lado_pie,
                value=lado,
                text_color="white",
                fg_color=self.colors['secondary'],
                hover_color=self.colors['secondary']
            ).pack(side="left", padx=5)
        
        # Selector de tipo de medición
        ctk.CTkLabel(
            medicion_frame,
            text="Medición:",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['small']),
            text_color="white"
        ).pack(side="left", padx=(20, 5))
        
        self.tipo_medida = ctk.StringVar(value="Largo Total")
        tipo_menu = ctk.CTkOptionMenu(
            medicion_frame,
            variable=self.tipo_medida,
            values=Config.TIPOS_MEDICION,
            width=180,
            fg_color=self.colors['bg_primary'],
            text_color=self.colors['text_primary'],
            button_color=self.colors['secondary']
        )
        tipo_menu.pack(side="left", padx=5)
        
        # Selector de unidad (visualización)
        ctk.CTkLabel(
            medicion_frame,
            text="Unidad:",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['small']),
            text_color="white"
        ).pack(side="left", padx=(20, 5))

        self.unidad_medida = ctk.StringVar(value="cm")
        unidad_menu = ctk.CTkOptionMenu(
            medicion_frame,
            variable=self.unidad_medida,
            values=["mm", "cm"],
            width=80,
            fg_color=self.colors['bg_primary'],
            text_color=self.colors['text_primary'],
            button_color=self.colors['secondary']
        )
        unidad_menu.pack(side="left", padx=5)

        # Botones de acción
        action_frame = ctk.CTkFrame(header, fg_color="transparent")
        action_frame.pack(side="right", padx=20, pady=15)
        
        ModernButton(
            action_frame,
            text="↩ Deshacer",
            width=100,
            height=35,
            fg_color="transparent",
            border_width=2,
            border_color="white",
            command=self.borrar_ultima_medicion
        ).pack(side="left", padx=5)
        
        ModernButton(
            action_frame,
            text="🎯 Calibrar",
            width=110,
            height=35,
            fg_color=self.colors['secondary'],
            command=self.calibrar_escala_manual
        ).pack(side="left", padx=5)

        ModernButton(
            action_frame,
            text="📐 Analizar",
            width=120,
            height=35,
            fg_color=self.colors['warning'],
            hover_color="#d97706",
            command=self.calcular_diagnostico
        ).pack(side="left", padx=5)
        
        # Contenedor principal
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=15)
        
        # ===== PANEL IZQUIERDO - CANVAS DE ANÁLISIS =====
        self.left_panel = ctk.CTkFrame(
            content,
            fg_color=self.colors['bg_primary'],
            corner_radius=Config.CORNER_RADIUS['lg']
        )
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        # Toolbar del canvas
        toolbar = ctk.CTkFrame(
            self.left_panel,
            height=70,
            fg_color=self.colors['bg_tertiary'],
            corner_radius=0
        )
        toolbar.pack(side="top", fill="x")
        
        # Selector de modo de captura
        self.selector_modo = ctk.CTkSegmentedButton(
            toolbar,
            values=["Digital", "Tinta (Papel)"],
            command=lambda v: setattr(self, 'modo_captura', v),
            fg_color=self.colors['bg_secondary'],
            selected_color=self.colors['primary'],
            selected_hover_color=self.colors['primary_hover']
        )
        self.selector_modo.set("Digital")
        self.selector_modo.pack(side="left", padx=15, pady=15)
        
        # Botones de carga
        ModernButton(
            toolbar,
            text="📂 Cargar",
            width=110,
            height=40,
            fg_color=self.colors['secondary'],
            command=self.cargar_imagenes_manual
        ).pack(side="left", padx=5)
        
        ModernButton(
            toolbar,
            text="⚡ Escanear",
            width=130,
            height=40,
            fg_color=self.colors['warning'],
            hover_color="#d97706",
            command=self.escanear_pies
        ).pack(side="left", padx=5)
        
        # Selector de visualización
        self.selector_vista = ctk.CTkSegmentedButton(
            toolbar,
            values=["Original", "Mapa de Calor"],
            command=self.cambiar_visualizacion,
            fg_color=self.colors['bg_secondary'],
            selected_color=self.colors['accent'],
            selected_hover_color="#7c3aed"
        )
        self.selector_vista.set("Original")
        self.selector_vista.pack(side="left", padx=20)
        
        # Controles de zoom
        zoom_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        zoom_frame.pack(side="right", padx=15)
        
        ModernButton(
            zoom_frame,
            text="🔍+",
            width=45,
            height=40,
            command=self.zoom_in
        ).pack(side="left", padx=2)
        
        ModernButton(
            zoom_frame,
            text="🔍-",
            width=45,
            height=40,
            command=self.zoom_out
        ).pack(side="left", padx=2)
        
        ModernButton(
            zoom_frame,
            text="⟲",
            width=45,
            height=40,
            command=self.reset_zoom
        ).pack(side="left", padx=2)
        
        # Canvas principal
        self.canvas = tk.Canvas(
            self.left_panel,
            bg=self.colors['bg_secondary'],
            highlightthickness=0,
            cursor="crosshair"
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Bindings del canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.do_pan)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel_zoom)
        
        # ===== PANEL DERECHO - PANEL DE CONTROL =====
        self.right_panel = ctk.CTkFrame(
            content,
            width=380,
            fg_color=self.colors['bg_primary'],
            corner_radius=Config.CORNER_RADIUS['lg']
        )
        self.right_panel.pack(side="right", fill="y")
        self.right_panel.pack_propagate(False)
        
        # Scroll para el panel derecho
        right_scroll = ctk.CTkScrollableFrame(
            self.right_panel,
            fg_color="transparent"
        )
        right_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # ===== SECCIÓN: CONFIGURACIÓN DE MAPA DE CALOR =====
        self.crear_seccion_panel(right_scroll, "🎨 CONFIGURACIÓN DE ANÁLISIS")
        
        config_frame = ctk.CTkFrame(
            right_scroll,
            fg_color=self.colors['bg_tertiary'],
            corner_radius=Config.CORNER_RADIUS['md']
        )
        config_frame.pack(fill="x", padx=15, pady=10)
        
        # Slider de intensidad
        ctk.CTkLabel(
            config_frame,
            text="Intensidad:",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['small'], "bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.intensidad_slider = ctk.CTkSlider(
            config_frame,
            from_=0.5,
            to=2.0,
            number_of_steps=30,
            command=self.cambiar_intensidad,
            button_color=self.colors['primary'],
            button_hover_color=self.colors['primary_hover']
        )
        self.intensidad_slider.set(1.0)
        self.intensidad_slider.pack(fill="x", padx=15, pady=5)
        
        self.intensidad_label = ctk.CTkLabel(
            config_frame,
            text="1.0x",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['tiny'])
        )
        self.intensidad_label.pack(pady=(0, 15))
        
        # Suavizado
        self.suavizado_var = ctk.BooleanVar(value=True)
        suavizado_check = ctk.CTkCheckBox(
            config_frame,
            text="Aplicar suavizado (reduce ruido)",
            variable=self.suavizado_var,
            command=self.toggle_suavizado,
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['small'])
        )
        suavizado_check.pack(anchor="w", padx=15, pady=(5, 15))
        
        # ===== SECCIÓN: ESTADÍSTICAS DE PRESIÓN =====
        self.crear_seccion_panel(right_scroll, "📊 ESTADÍSTICAS DE PRESIÓN")
        
        self.stats_frame = ctk.CTkFrame(
            right_scroll,
            fg_color=self.colors['bg_tertiary'],
            corner_radius=Config.CORNER_RADIUS['md']
        )
        self.stats_frame.pack(fill="x", padx=15, pady=10)
        
        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text="Cargue una imagen para ver estadísticas",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['small']),
            text_color=self.colors['text_secondary']
        )
        self.stats_label.pack(pady=20)
        
        # ===== SECCIÓN: OBSERVACIONES =====
        self.crear_seccion_panel(right_scroll, "📝 OBSERVACIONES PROFESIONALES")
        
        self.obs_text = ctk.CTkTextbox(
            right_scroll,
            height=180,
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body']),
            corner_radius=Config.CORNER_RADIUS['sm']
        )
        self.obs_text.pack(fill="x", padx=15, pady=10)
        
        # ===== SECCIÓN: RECOMENDACIONES =====
        self.crear_seccion_panel(right_scroll, "💡 RECOMENDACIONES DE TRATAMIENTO")
        
        self.plan_text = ctk.CTkTextbox(
            right_scroll,
            height=140,
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body']),
            corner_radius=Config.CORNER_RADIUS['sm']
        )
        self.plan_text.pack(fill="x", padx=15, pady=10)
        
        # ===== BOTONES DE ACCIÓN =====
        action_container = ctk.CTkFrame(right_scroll, fg_color="transparent")
        action_container.pack(fill="x", padx=15, pady=20)
        
        btn_texto = "💾 ACTUALIZAR ESTUDIO" if self.estudio_id_edicion else "💾 GUARDAR ESTUDIO"
        
        ModernButton(
            action_container,
            text=btn_texto,
            height=55,
            corner_radius=Config.CORNER_RADIUS['md'],
            fg_color=self.colors['success'],
            hover_color="#059669",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body'], "bold"),
            command=self.guardar_estudio
        ).pack(fill="x", pady=5)
        
        ModernButton(
            action_container,
            text="❌ CANCELAR",
            height=45,
            corner_radius=Config.CORNER_RADIUS['md'],
            fg_color="transparent",
            text_color=self.colors['error'],
            border_width=2,
            border_color=self.colors['error'],
            hover_color=self.colors['bg_tertiary'],
            command=lambda: self.seleccionar_paciente(self.paciente_actual[0])
        ).pack(fill="x", pady=5)

    def crear_seccion_panel(self, master, titulo):
        """Crea un título de sección en el panel derecho"""
        ctk.CTkLabel(
            master,
            text=titulo,
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['body'], "bold"),
            text_color=self.colors['text_primary']
        ).pack(anchor="w", padx=15, pady=(15, 5))

    # ===== TRANSFORMACIONES CANVAS <-> IMAGEN =====

    def _get_image_transform(self):
        """Devuelve (scale_total, center_x, center_y) de la imagen actual en canvas."""
        if not hasattr(self, 'img_original_size') or self.img_original_size is None:
            return None
        w_canvas = self.left_panel.winfo_width()
        h_canvas = self.left_panel.winfo_height() - 70
        img_w, img_h = self.img_original_size
        scale_base = min(w_canvas / img_w, h_canvas / img_h)
        scale_total = scale_base * self.zoom_level
        center_x = w_canvas // 2 + self.canvas_offset_x
        center_y = h_canvas // 2 + self.canvas_offset_y
        return scale_total, center_x, center_y

    def _canvas_to_image(self, x, y):
        t = self._get_image_transform()
        if t is None:
            return None, None
        scale_total, cx, cy = t
        img_w, img_h = self.img_original_size
        ix = (x - cx) / scale_total + (img_w / 2.0)
        iy = (y - cy) / scale_total + (img_h / 2.0)
        return ix, iy

    def _image_to_canvas(self, ix, iy):
        t = self._get_image_transform()
        if t is None:
            return None, None
        scale_total, cx, cy = t
        img_w, img_h = self.img_original_size
        x = (ix - (img_w / 2.0)) * scale_total + cx
        y = (iy - (img_h / 2.0)) * scale_total + cy
        return x, y

    def _redibujar_mediciones(self):
        """Redibuja las mediciones ancladas a la imagen tras zoom/pan."""
        if not hasattr(self, 'lines_data'):
            return

        for m in self.lines_data:
            if 'x1_img' not in m:
                continue
            x1, y1 = self._image_to_canvas(m['x1_img'], m['y1_img'])
            x2, y2 = self._image_to_canvas(m['x2_img'], m['y2_img'])
            if None in (x1, y1, x2, y2):
                continue

            self.canvas.coords(m['id'], x1, y1, x2, y2)
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            padding = 60
            self.canvas.coords(m['bg_id'], mx - padding, my - 15, mx + padding, my + 15)
            self.canvas.coords(m['txt_id'], mx, my)

    # ===== FUNCIONES DE ZOOM Y PAN =====
    
    def zoom_in(self):
        """Aumenta el zoom"""
        self.zoom_level = min(self.zoom_level * 1.2, 5.0)
        self.actualizar_canvas_zoom()
    
    def zoom_out(self):
        """Disminuye el zoom"""
        self.zoom_level = max(self.zoom_level / 1.2, 0.5)
        self.actualizar_canvas_zoom()
    
    def reset_zoom(self):
        """Resetea el zoom y posición"""
        self.zoom_level = 1.0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        if self.path_original_temp:
            self.mostrar_imagen_canvas(self.path_original_temp, mantener=True)
    
    def on_mousewheel_zoom(self, event):
        """Zoom con la rueda del mouse"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def start_pan(self, event):
        """Inicia el paneo con botón derecho"""
        self.pan_start = (event.x, event.y)
    
    def do_pan(self, event):
        """Realiza el paneo"""
        if self.pan_start and self.path_original_temp:
            dx = event.x - self.pan_start[0]
            dy = event.y - self.pan_start[1]
            self.canvas_offset_x += dx
            self.canvas_offset_y += dy
            self.pan_start = (event.x, event.y)
            self.actualizar_canvas_zoom()
    
    def actualizar_canvas_zoom(self):
        """Actualiza el canvas con el nivel de zoom actual"""
        if self.path_original_temp:
            path = self.path_original_temp if self.modo_visualizacion == "Original" else self.path_mapa_temp
            self.mostrar_imagen_canvas(path, mantener=True)

    # ===== FUNCIONES DE VISUALIZACIÓN =====
    
    def cambiar_visualizacion(self, modo):
        """Cambia entre vista original y mapa de calor"""
        self.modo_visualizacion = modo
        if self.path_original_temp:
            path = self.path_original_temp if modo == "Original" else self.path_mapa_temp
            self.mostrar_imagen_canvas(path, mantener=True)
    
    def cambiar_intensidad(self, valor):
        """Cambia la intensidad del mapa de calor"""
        self.intensidad_calor = float(valor)
        self.intensidad_label.configure(text=f"{valor:.1f}x")
        self.reprocesar_imagen()
    
    def toggle_suavizado(self):
        """Activa/desactiva el suavizado"""
        self.suavizado_activo = self.suavizado_var.get()
        self.reprocesar_imagen()
    
    def reprocesar_imagen(self):
        """Reprocesa la imagen con los nuevos parámetros"""
        if not self.path_original_temp:
            return
        
        try:
            _, mapa_img, self.stats_presion = ImageAnalyzer.analizar_imagen(
                self.path_original_temp,
                modo=self.modo_captura,
                colormap_name=self.colormap_actual,
                intensidad=self.intensidad_calor,
                suavizado=self.suavizado_activo
            )
            
            self.path_mapa_temp = str(get_temp_file_path("temp_mapa_view", ".png"))
            mapa_img.save(self.path_mapa_temp)
            
            if self.modo_visualizacion == "Mapa de Calor":
                self.mostrar_imagen_canvas(self.path_mapa_temp, mantener=True)
            
            self.actualizar_estadisticas()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando imagen: {e}")

    def mostrar_imagen_canvas(self, path, mantener=False):
        """Muestra una imagen en el canvas con soporte para zoom"""
        try:
            img = Image.open(path)
            self.left_panel.update()
            
            w_canvas = self.left_panel.winfo_width()
            h_canvas = self.left_panel.winfo_height() - 70  # Restar toolbar
            
            # Guardar tamaño original de imagen para transformar coordenadas de medición
            self.img_original_size = (img.width, img.height)
            
            # Calcular factor de escala base
            self.scale_factor_base = min(w_canvas / img.width, h_canvas / img.height)
            
            # Aplicar zoom
            scale_total = self.scale_factor_base * self.zoom_level
            
            new_w = int(img.width * scale_total)
            new_h = int(img.height * scale_total)
            
            # Redimensionar imagen
            img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self.img_tk_cache = ImageTk.PhotoImage(img_resized)
            
            center_x = w_canvas // 2 + self.canvas_offset_x
            center_y = h_canvas // 2 + self.canvas_offset_y

            if mantener and self.canvas.find_withtag("img_bg"):
                # Actualizar imagen existente y su posición
                self.canvas.itemconfig("img_bg", image=self.img_tk_cache)
                self.canvas.coords("img_bg", center_x, center_y)
                self._redibujar_mediciones()
            else:
                # Crear nueva imagen
                self.canvas.delete("all")
                self.canvas.create_image(
                    center_x, center_y,
                    image=self.img_tk_cache,
                    anchor="center",
                    tags="img_bg"
                )
                self.lines_data = []
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen: {e}")

    def actualizar_estadisticas(self):
        """Actualiza el panel de estadísticas con los datos de presión corregidos"""
        if not self.stats_presion:
            return
        
        # Limpiar frame de stats
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        # Obtener datos del análisis
        area_mm2 = self.stats_presion.get('area_contacto_mm2', 0)
        area_cm2 = area_mm2 / 100
        dist = self.stats_presion.get('distribucion', {'anterior': 0, 'media': 0, 'posterior': 0})
        calidad_nivel = self.stats_presion.get('calidad_nivel', 'N/D')
        calidad_alertas = self.stats_presion.get('calidad_alertas', [])
        alertas_txt = "\n".join([f"- {a}" for a in calidad_alertas]) if calidad_alertas else "Sin alertas"

        stats_text = f"""
ESTADÍSTICAS DE PRESIÓN:
━━━━━━━━━━━━━━━━━━━━━━━
Presión Media: {self.stats_presion.get('presion_media', 0):.1f}
Presión Máxima: {self.stats_presion.get('presion_max', 0):.1f}
Área de Contacto: {area_cm2:.1f} cm²

CALIDAD DE CAPTURA: {calidad_nivel}
{alertas_txt}

DISTRIBUCIÓN POR ZONAS:
━━━━━━━━━━━━━━━━━━━━━━━
Anterior (dedos): {dist.get('anterior', 0):.1f}%
Media (arco): {dist.get('media', 0):.1f}%
Posterior (talón): {dist.get('posterior', 0):.1f}%
"""
        
        ctk.CTkLabel(
            self.stats_frame,
            text=stats_text,
            font=(Config.FONT_FAMILY, 13),
            text_color=self.colors['text_primary'],
            justify="left"
        ).pack(padx=15, pady=15, anchor="w")

    def _get_pixels_por_mm_actual(self):
        """Devuelve la escala activa (manual si existe, si no automática)."""
        if self.manual_pixels_por_mm and self.manual_pixels_por_mm > 0:
            return self.manual_pixels_por_mm
        if hasattr(self, 'stats_presion') and 'pixels_por_mm' in self.stats_presion:
            return self.stats_presion['pixels_por_mm']
        return None

    def calibrar_escala_manual(self):
        """Calibra la escala usando la última línea dibujada sobre una referencia conocida."""
        if not self.lines_data:
            messagebox.showwarning(
                "Calibración",
                "Primero dibuje una línea sobre una referencia conocida (regla/marca)."
            )
            return

        ultima = self.lines_data[-1]
        dist_px_ref = ultima.get('dist_px')
        if not dist_px_ref or dist_px_ref <= 0:
            messagebox.showwarning("Calibración", "No se pudo obtener la distancia de referencia.")
            return

        valor_mm = simpledialog.askfloat(
            "Calibración manual",
            "Ingrese la longitud REAL de la línea en milímetros (mm):",
            minvalue=1.0,
            maxvalue=1000.0
        )
        if valor_mm is None:
            return

        self.manual_pixels_por_mm = dist_px_ref / valor_mm
        if not hasattr(self, 'stats_presion'):
            self.stats_presion = {}
        self.stats_presion['pixels_por_mm'] = self.manual_pixels_por_mm

        messagebox.showinfo(
            "Calibración",
            f"Escala calibrada: {self.manual_pixels_por_mm:.2f} px/mm\n"
            f"(Referencia: {valor_mm:.1f} mm)"
        )



    # ===== FUNCIONES DE MEDICIÓN EN CANVAS =====
    
    def on_canvas_click(self, event):
        """Maneja el click en el canvas para iniciar una medición"""
        if not self.path_original_temp:
            return
            
        self.drawing_start = (event.x, event.y)
        tipo = self.tipo_medida.get()
        
        colores = {
            "Largo Total": "#eab308",
            "Ancho Metatarso": "#f97316",
            "Ancho Istmo": "#06b6d4",
            "Ancho Talón": "#8b5cf6",
            "Ángulo Hallux": "#ef4444",
            "Custom": "#10b981"
        }
        
        color = colores.get(tipo, "#64748b")
        
        self.current_line_id = self.canvas.create_line(
            event.x, event.y, event.x, event.y,
            fill=color,
            width=4,
            tags="medicion"
        )
    
    def on_canvas_drag(self, event):
        """Actualiza la línea mientras se arrastra"""
        if self.current_line_id:
            self.canvas.coords(
                self.current_line_id,
                self.drawing_start[0], self.drawing_start[1],
                event.x, event.y
            )
    
    def on_canvas_release(self, event):
        """Finaliza la medición y muestra el resultado EN CENTÍMETROS"""
        if not self.current_line_id:
            return
        
        x1, y1 = self.drawing_start
        x2, y2 = event.x, event.y
        
        # Transformar a coordenadas de imagen (ancladas al escaneo)
        x1_img, y1_img = self._canvas_to_image(x1, y1)
        x2_img, y2_img = self._canvas_to_image(x2, y2)
        if None in (x1_img, y1_img, x2_img, y2_img):
            self.canvas.delete(self.current_line_id)
            self.current_line_id = None
            return

        # Distancia en píxeles de imagen (independiente del zoom)
        dist_px = math.sqrt((x2_img - x1_img)**2 + (y2_img - y1_img)**2)
        
        # Si la línea es muy corta, descartarla
        if dist_px < 10:
            self.canvas.delete(self.current_line_id)
            self.current_line_id = None
            return
        
        # Obtener datos de la medición
        tipo = self.tipo_medida.get()
        lado = self.lado_pie.get()
        
        # Calcular valor calibrado y mostrar según unidad seleccionada
        pixels_por_mm = self._get_pixels_por_mm_actual()
        if pixels_por_mm:
            valor_mm = dist_px / pixels_por_mm
            unidad = self.unidad_medida.get() if hasattr(self, 'unidad_medida') else 'cm'
            if unidad == "mm":
                texto = f"{tipo}: {valor_mm:.1f} mm"
            else:
                valor_cm = valor_mm / 10.0
                texto = f"{tipo}: {valor_cm:.2f} cm"
        else:
            # Fallback si no hay calibración
            valor_mm = None
            texto = f"{tipo}: {int(dist_px)} px (sin calibrar)"
        
        # Posición del texto (punto medio)
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        
        # Crear fondo para el texto
        padding = 60
        bg_rect = self.canvas.create_rectangle(
            mx - padding, my - 15,
            mx + padding, my + 15,
            fill="black",
            outline="",
            tags="medicion_bg"
        )
        
        # Crear texto
        txt_id = self.canvas.create_text(
            mx, my,
            text=texto,
            fill="white",
            font=(Config.FONT_FAMILY, Config.FONT_SIZES['small'], "bold"),
            tags="medicion_txt"
        )
        
        # Guardar datos de la medición
        self.lines_data.append({
            'id': self.current_line_id,
            'txt_id': txt_id,
            'bg_id': bg_rect,
            'tipo': tipo,
            'lado': lado,
            'dist_px': dist_px,
            'valor_mm': valor_mm,  # Nota: se conserva la clave histórica por compatibilidad
            'x1_img': x1_img,
            'y1_img': y1_img,
            'x2_img': x2_img,
            'y2_img': y2_img	
        })
        
        self.current_line_id = None
    
    def borrar_ultima_medicion(self):
        """Elimina la última medición realizada"""
        if self.lines_data:
            medicion = self.lines_data.pop()
            self.canvas.delete(medicion['id'])
            self.canvas.delete(medicion['txt_id'])
            self.canvas.delete(medicion['bg_id'])

    # ===== FUNCIONES DE CARGA Y ESCANEO =====
    
    def cargar_imagenes_manual(self):
        """Carga dos imágenes manualmente para análisis"""
        # Cargar imagen izquierda
        img_izq = filedialog.askopenfilename(
            title="Seleccionar imagen del pie IZQUIERDO",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp"), ("Todos", "*.*")]
        )
        
        if not img_izq:
            return
        
        # Cargar imagen derecha
        img_der = filedialog.askopenfilename(
            title="Seleccionar imagen del pie DERECHO",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp"), ("Todos", "*.*")]
        )
        
        if not img_der:
            return
        
        self.procesar_imagenes(img_izq, img_der)
    
    def escanear_pies(self):
        """Escanea ambos pies usando el escáner"""
        try:
            # Escanear pie izquierdo
            messagebox.showinfo(
                "Escanear",
                "Coloque el PIE IZQUIERDO en el escáner y presione OK"
            )
            img_izq, intentos_izq = Scanner.escanear_con_reintentos()
            
            if not img_izq:
                self.logger.error("Fallo de escaneo: pie izquierdo tras %s intentos", intentos_izq)
                messagebox.showerror("Error de escaneo", f"No se pudo escanear el pie izquierdo tras {intentos_izq} intentos. Verifique conexión del escáner e intente nuevamente.")
                return
            
            # Escanear pie derecho
            messagebox.showinfo(
                "Escanear",
                "Coloque el PIE DERECHO en el escáner y presione OK"
            )
            img_der, intentos_der = Scanner.escanear_con_reintentos()
            
            if not img_der:
                self.logger.error("Fallo de escaneo: pie derecho tras %s intentos", intentos_der)
                messagebox.showerror("Error de escaneo", f"No se pudo escanear el pie derecho tras {intentos_der} intentos. Verifique conexión del escáner e intente nuevamente.")
                return
            
            self.logger.info("Escaneo exitoso: pie izq en %s intento(s), pie der en %s intento(s)", intentos_izq, intentos_der)
            self.procesar_imagenes(img_izq, img_der)
            
        except Exception as e:
            self.logger.exception("Error durante escaneo")
            messagebox.showerror("Error", f"Error durante el escaneo: {e}")
    
    def procesar_imagenes(self, img_izq, img_der):
        """Procesa y une las dos imágenes de los pies"""
        try:
            # Reiniciar calibración manual para el nuevo estudio/captura
            self.manual_pixels_por_mm = None

            # Crear archivo temporal para imagen unida
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_unida = str(get_temp_file_path("temp_unida", ".png"))

            # Unir imágenes
            if ImageAnalyzer.unir_imagenes(img_izq, img_der, temp_unida):

                # Analizar imagen
                img_original, img_mapa, self.stats_presion = ImageAnalyzer.analizar_imagen(
                    temp_unida,
                    modo=self.modo_captura,
                    colormap_name=self.colormap_actual,
                    intensidad=self.intensidad_calor,
                    suavizado=self.suavizado_activo
                )

                # CORRECCIÓN CRÍTICA:
                # Guardar la imagen ORIGINAL procesada (con fondo blanco)
                self.path_original_temp = temp_unida  # Esta es la imagen original
                
                # Guardar el mapa de calor
                self.path_mapa_temp = str(get_temp_file_path("temp_mapa_view", ".png"))
                img_mapa.save(self.path_mapa_temp)
                
                # Guardar también la imagen original procesada (con fondo blanco)
                img_original.save(self.path_original_temp)

                # Mostrar imagen según modo de visualización
                if self.modo_visualizacion == "Original":
                    self.mostrar_imagen_canvas(self.path_original_temp)
                else:
                    self.mostrar_imagen_canvas(self.path_mapa_temp)
                
                # Actualizar estadísticas
                self.actualizar_estadisticas()

        except Exception as e:
            self.logger.exception("Error procesando imágenes")
            messagebox.showerror("Error", f"Error procesando imagen: {e}")

    def _evaluar_calidad_captura(self):
        """Evalúa calidad mínima de captura antes de guardar estudio."""
        issues = []
        area_mm2 = (self.stats_presion or {}).get('area_contacto_mm2', 0)
        if area_mm2 < Config.CALIDAD_CAPTURA_AREA_MIN_MM2:
            issues.append(f"Área de contacto baja: {area_mm2/100:.1f} cm²")

        dist = (self.stats_presion or {}).get('distribucion', {})
        vals = [dist.get('anterior', 0), dist.get('media', 0), dist.get('posterior', 0)]
        if max(vals) - min(vals) > Config.CALIDAD_CAPTURA_DESBALANCE_MAX:
            issues.append("Distribución muy irregular (posible captura defectuosa)")

        return issues

    # ===== FUNCIONES DE ANÁLISIS =====
    
    def calcular_diagnostico(self):
        """Calcula el diagnóstico basado en las mediciones calibradas"""
        if not self._get_pixels_por_mm_actual():
            messagebox.showwarning(
                "Aviso", 
                "Las mediciones ya están calibradas automáticamente.\n"
                "Puede realizar mediciones directamente."
            )
            return
        
        # Analizar mediciones
        resultado = "\n━━━━━━━ ANÁLISIS PODOLÓGICO ━━━━━━━\n\n"
        
        for lado in ["IZQ", "DER"]:
            resultado += f"═══ PIE {lado} ═══\n"
            
            # Obtener mediciones del lado (etiquetadas en cm)
            ancho_meta = next(
                (m['valor_mm'] for m in self.lines_data 
                if m['lado'] == lado and m['tipo'] == "Ancho Metatarso" and m['valor_mm']),
                None
            )
            
            ancho_istmo = next(
                (m['valor_mm'] for m in self.lines_data 
                if m['lado'] == lado and m['tipo'] == "Ancho Istmo" and m['valor_mm']),
                None
            )
            
            if ancho_meta and ancho_istmo:
                # Calcular índice del arco
                ratio = ancho_istmo / ancho_meta
                
                # Clasificar tipo de pie
                if 0.30 <= ratio <= 0.38:
                    tipo_pie = "NORMAL"
                    recomendacion = "Pie con arco normal. Mantener cuidados habituales."
                elif ratio < 0.30:
                    tipo_pie = "CAVO"
                    recomendacion = "Pie cavo detectado. Considerar plantillas con soporte."
                else:
                    tipo_pie = "PLANO"
                    recomendacion = "Pie plano detectado. Considerar plantillas correctivas."
                
                unidad = self.unidad_medida.get() if hasattr(self, 'unidad_medida') else 'cm'
                if unidad == "mm":
                    resultado += f"Ancho Metatarso: {ancho_meta:.1f} mm\n"
                    resultado += f"Ancho Istmo: {ancho_istmo:.1f} mm\n"
                else:
                    resultado += f"Ancho Metatarso: {ancho_meta/10.0:.2f} cm\n"
                    resultado += f"Ancho Istmo: {ancho_istmo/10.0:.2f} cm\n"
                resultado += f"Índice del Arco: {ratio:.3f}\n"
                resultado += f"Tipo de Pie: {tipo_pie}\n"
                resultado += f"→ {recomendacion}\n\n"
            else:
                resultado += "⚠ Faltan mediciones para análisis completo\n\n"
        
        alertas = AlertService.generar_alertas_mediciones(self.lines_data)
        if alertas:
            resultado += "\n═══ ALERTAS AUTOMÁTICAS ═══\n"
            for a in alertas:
                resultado += f"• {a}\n"

        # Añadir al cuadro de observaciones
        self.obs_text.insert("end", resultado)
        
        messagebox.showinfo("Análisis Completado", "El análisis ha sido añadido a las observaciones")

    # ===== FUNCIONES DE GUARDADO =====
    
    def guardar_estudio(self):
        """Guarda o actualiza el estudio actual"""
        if not self.path_original_temp:
            messagebox.showwarning("Aviso", "Debe cargar imágenes antes de guardar")
            return

        issues_calidad = self._evaluar_calidad_captura()
        if issues_calidad:
            detalle = "\n".join(f"• {i}" for i in issues_calidad)
            recapturar = messagebox.askyesno("Control de calidad", f"Se detectaron posibles problemas de captura:\n\n{detalle}\n\n¿Desea recapturar antes de guardar?")
            if recapturar:
                motivo = simpledialog.askstring("Motivo de recaptura", "Ingrese motivo de recaptura (opcional):")
                self.logger.info("Recaptura solicitada para paciente id=%s. Motivo=%s", self.paciente_actual[0] if self.paciente_actual else None, motivo or "(sin motivo)")
                return
        
        # Recopilar datos
        datos = {
            "obs_profesional": self.obs_text.get("0.0", "end").strip(),
            "recomendacion_plantilla": self.plan_text.get("0.0", "end").strip(),
            "mediciones": json.dumps([
                {
                    'tipo': m['tipo'],
                    'lado': m['lado'],
                    'valor_mm': m['valor_mm'],  # Compatibilidad con estudios previos
                    'dist_px': m['dist_px']
                }
                for m in self.lines_data
            ])
        }
        
        if self.estudio_id_edicion:
            # Actualizar estudio existente
            self.db.actualizar_informe(self.estudio_id_edicion, datos)
            messagebox.showinfo("Éxito", "Estudio actualizado correctamente")
        else:
            # Crear nuevo estudio
            paciente = self.paciente_actual
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            timestamp = datetime.now().strftime("%H%M%S")
            
            # Crear estructura de carpetas mejorada
            # Formato: pacientes/Apellido_Nombre/YYYY-MM-DD/
            nombre_paciente = paciente[1].replace(' ', '_')
            carpeta_paciente = os.path.join(
                Config.BASE_DIR,
                nombre_paciente  # Nombre del paciente como carpeta principal
            )
            carpeta_estudio = os.path.join(carpeta_paciente, fecha_hoy)  # Fecha del estudio
            
            # Crear carpetas si no existen
            os.makedirs(carpeta_estudio, exist_ok=True)
            
            # Nombres de archivo más descriptivos
            nombre_base = f"Estudio_{fecha_hoy}_{timestamp}"
            path_destino_orig = os.path.join(carpeta_estudio, f"{nombre_base}_original.png")
            path_destino_mapa = os.path.join(carpeta_estudio, f"{nombre_base}_mapa_calor.png")
            
            # Copiar archivos de imágenes
            shutil.copy(self.path_original_temp, path_destino_orig)
            shutil.copy(self.path_mapa_temp, path_destino_mapa)

            # Limpiar temporales para evitar acumulación en disco
            for tmp in (self.path_original_temp, self.path_mapa_temp):
                try:
                    if tmp and os.path.exists(tmp) and os.path.abspath(tmp).startswith(os.path.abspath("temp")):
                        os.remove(tmp)
                except Exception:
                    pass
            
            # Guardar en base de datos
            datos.update({
                "paciente_id": paciente[0],
                "fecha": fecha_hoy,
                "imagen": path_destino_orig
            })
            
            self.db.insertar_informe(datos)
            
            # Preguntar si desea abrir la carpeta
            resultado = messagebox.askyesno(
                "Estudio Guardado",
                f"✅ Estudio guardado correctamente en:\n{carpeta_estudio}\n\n¿Desea abrir la carpeta?"
            )
            
            if resultado:
                # Abrir la carpeta del estudio
                try:
                    os.startfile(carpeta_estudio)
                except:
                    # Para sistemas no Windows
                    import subprocess
                    try:
                        subprocess.Popen(['xdg-open', carpeta_estudio])
                    except:
                        messagebox.showinfo("Info", f"Carpeta guardada en:\n{carpeta_estudio}")
        
        # Volver a la ficha del paciente
        self.seleccionar_paciente(self.paciente_actual[0])

    def exportar_pdf_directo(self, estudio_id):
        """Exporta un estudio a PDF y lo guarda en la carpeta del paciente"""
        informe = self.db.obtener_informe(estudio_id)
        
        if not informe:
            messagebox.showerror("Error", "No se pudo cargar el estudio")
            return
        
        # Obtener ruta de la imagen para determinar la carpeta del estudio
        imagen_path = informe[3]
        carpeta_estudio = os.path.dirname(imagen_path)
        
        # Nombre sugerido del PDF
        fecha_estudio = informe[1]
        nombre_paciente = self.paciente_actual[1].replace(' ', '_')
        nombre_pdf_sugerido = f"Informe_{nombre_paciente}_{fecha_estudio}.pdf"
        
        # Sugerir guardar en la carpeta del estudio
        ruta_pdf_sugerida = os.path.join(carpeta_estudio, nombre_pdf_sugerido)
        
        # Pedir ubicación de guardado (con ruta sugerida)
        ruta_pdf = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")],
            initialfile=nombre_pdf_sugerido,
            initialdir=carpeta_estudio,
            title="Guardar informe PDF"
        )
        
        if not ruta_pdf:
            return
        
        try:
            if ReportService.generar_pdf(self.paciente_actual, informe, ruta_pdf):
                respuesta = messagebox.askyesno(
                    "PDF Generado",
                    f"✅ PDF guardado en:\n{ruta_pdf}\n\n¿Desea abrirlo?"
                )
                
                if respuesta:
                    try:
                        os.startfile(ruta_pdf)
                    except:
                        # Para sistemas no Windows
                        import subprocess
                        try:
                            subprocess.Popen(['xdg-open', ruta_pdf])
                        except:
                            messagebox.showinfo("Info", f"PDF guardado en:\n{ruta_pdf}")
            else:
                messagebox.showerror("Error", "No se pudo generar el PDF")
                
        except Exception as e:
            self.logger.exception("Error exportando PDF")
            messagebox.showerror("Error", f"Error generando PDF: {e}")

    def borrar_paciente(self, paciente_id):
        """Elimina un paciente y todos sus estudios"""
        confirmacion = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar al paciente {self.paciente_actual[1]} y todos sus estudios?\n\nEsta acción no se puede deshacer."
        )
        
        if confirmacion:
            try:
                self.db.eliminar_paciente(paciente_id)
                messagebox.showinfo("Éxito", "Paciente eliminado correctamente")
                self.mostrar_inicio()
            except Exception as e:
                self.logger.exception("Error eliminando paciente id=%s", paciente_id)
                messagebox.showerror("Error", f"Error eliminando paciente: {e}")
    
    def abrir_carpeta_paciente(self, paciente):
        """Abre la carpeta del paciente en el explorador de archivos"""
        nombre_paciente = paciente[1].replace(' ', '_')
        carpeta_paciente = os.path.join(Config.BASE_DIR, nombre_paciente)
        
        # Crear carpeta si no existe
        if not os.path.exists(carpeta_paciente):
            os.makedirs(carpeta_paciente, exist_ok=True)
            messagebox.showinfo(
                "Carpeta Creada",
                f"Se ha creado la carpeta del paciente en:\n{carpeta_paciente}"
            )
        
        # Abrir carpeta
        try:
            os.startfile(carpeta_paciente)
        except:
            # Para sistemas no Windows
            import subprocess
            try:
                subprocess.Popen(['xdg-open', carpeta_paciente])
            except:
                messagebox.showinfo("Info", f"Carpeta del paciente:\n{carpeta_paciente}")


if __name__ == "__main__":
    app = PodoscopioApp()
    app.mainloop()
