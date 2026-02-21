class Config:
    # Directorios
    BASE_DIR = "pacientes"
    DB_NAME = "podoscopio.db"
    
    # Ventana
    WINDOW_SIZE = "1400x900"
    MIN_WINDOW_SIZE = "1200x700"
    
    # Temas
    THEME_MODE = "light"  # "light" o "dark"
    THEME_COLOR = "blue"
    
    # Paleta de colores - LIGHT MODE
    LIGHT_COLORS = {
        'primary': '#1e40af',
        'primary_hover': '#1e3a8a',
        'secondary': '#06b6d4',
        'accent': '#8b5cf6',
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'bg_primary': '#ffffff',
        'bg_secondary': '#f8fafc',
        'bg_tertiary': '#f1f5f9',
        'text_primary': '#0f172a',
        'text_secondary': '#64748b',
        'border': '#e2e8f0',
        'gradient_start': '#1e40af',
        'gradient_end': '#06b6d4',
    }
    
    # Paleta de colores - DARK MODE
    DARK_COLORS = {
        'primary': '#3b82f6',
        'primary_hover': '#60a5fa',
        'secondary': '#22d3ee',
        'accent': '#a78bfa',
        'success': '#34d399',
        'warning': '#fbbf24',
        'error': '#f87171',
        'bg_primary': '#0f172a',
        'bg_secondary': '#1e293b',
        'bg_tertiary': '#334155',
        'text_primary': '#f1f5f9',
        'text_secondary': '#94a3b8',
        'border': '#475569',
        'gradient_start': '#1e40af',
        'gradient_end': '#7c3aed',
    }
    
    # 🎨 Paletas de mapa de calor (solo 4)
    HEATMAP_COLORMAPS = {
        "Turbo": 20,       # ← Predeterminada
        "Hot": 11,
        "Inferno": 14,
        "Viridis": 16
    }
    
    # Tipografía
    FONT_FAMILY = "Segoe UI"
    FONT_SIZES = {
        'title': 32,
        'subtitle': 24,
        'heading': 18,
        'body': 14,
        'small': 12,
        'tiny': 10,
    }
    
    # Espaciado
    PADDING = {
        'xs': 5,
        'sm': 10,
        'md': 20,
        'lg': 30,
        'xl': 40,
    }
    
    # Radios de esquinas
    CORNER_RADIUS = {
        'sm': 8,
        'md': 12,
        'lg': 16,
        'xl': 20,
    }
    
    # Análisis
    TIPOS_MEDICION = [
        "Largo Total",
        "Ancho Metatarso",
        "Ancho Istmo",
        "Ancho Talón",
        "Ángulo Hallux",
        "Custom"
    ]
    
    LADOS_PIE = ["IZQ", "DER"]
    
    # Configuración de análisis
    UMBRAL_PRESION_MIN = 15
    UMBRAL_PRESION_MAX = 200
    UMBRAL_TINTA_MIN = 25
    HEATMAP_SMOOTH_SIGMA = 5.5
    HEATMAP_POST_BLUR_SIGMA = 2.2
    HEATMAP_MEDIAN_KERNEL = 5
    HEATMAP_PEAK_CLIP_PERCENTILE = 99.2

    # Escáner
    SCANNER_MAX_REINTENTOS = 3
    SCANNER_ESPERA_REINTENTO_S = 1.0

    # Procesamiento automático
    AUTO_ABRIR_EDITOR_ESCANEO = False

    # Homogeneidad de mapa de calor por modo
    HEATMAP_HOMOGENEIDAD_DIGITAL_MEDIAN = 7
    HEATMAP_HOMOGENEIDAD_DIGITAL_GAUSS = 11
    HEATMAP_HOMOGENEIDAD_TINTA_MEDIAN = 5
    HEATMAP_HOMOGENEIDAD_TINTA_GAUSS = 9

    # Control de calidad de captura
    CALIDAD_CAPTURA_AREA_MIN_MM2 = 5000
    CALIDAD_CAPTURA_DESBALANCE_MAX = 80

    # Corrección empírica de calibración automática (si mide 5cm como 4cm, usar 0.80)
    CALIBRACION_CORRECCION_PXMM = 0.80

    @classmethod
    def get_colors(cls):
        return cls.DARK_COLORS if cls.THEME_MODE == "dark" else cls.LIGHT_COLORS
    
    @classmethod
    def toggle_theme(cls):
        cls.THEME_MODE = "dark" if cls.THEME_MODE == "light" else "light"
        return cls.THEME_MODE
