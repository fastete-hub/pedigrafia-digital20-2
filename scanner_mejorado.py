"""
Scanner Mejorado - Podoscopio Pro v3.0
Soporta múltiples métodos de escaneo:
1. WIA (Windows Image Acquisition) - Escáneres USB tradicionales
2. TWAIN - Compatible con más escáneres (incluye WiFi)
3. Selección Manual - Permite cargar imágenes ya escaneadas
"""

import os
from datetime import datetime
from tkinter import messagebox, filedialog

class Scanner:
    """
    Clase mejorada para escaneo con múltiples métodos de captura
    """
    
    # Método preferido (se puede cambiar)
    METODO_PREFERIDO = "manual"  # Opciones: "wia", "twain", "manual"
    
    @staticmethod
    def _get_temp_dir():
        """Crea y devuelve la ruta de la carpeta para escaneos temporales, manteniendo la carpeta principal limpia."""
        temp_dir = os.path.join(os.getcwd(), "scans_temporales")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return temp_dir

    @staticmethod
    def disponible():
        """
        Verifica si hay escáneres disponibles
        Retorna True si al menos un método está disponible
        """
        # Siempre retornamos True porque el método manual siempre funciona
        return True
    
    @staticmethod
    def escanear():
        """
        Método principal de escaneo con selección automática del mejor método
        """
        # Intentar método preferido primero
        if Scanner.METODO_PREFERIDO == "wia":
            resultado = Scanner.escanear_wia()
            if resultado:
                return resultado
        elif Scanner.METODO_PREFERIDO == "twain":
            resultado = Scanner.escanear_twain()
            if resultado:
                return resultado
        
        # Si falla o es manual, usar método manual
        return Scanner.escanear_manual()
    
    @staticmethod
    def escanear_wia():
        """
        Método WIA - Solo para escáneres USB reconocidos por Windows
        """
        try:
            import win32com.client
            
            mgr = win32com.client.Dispatch("WIA.DeviceManager")
            if mgr.DeviceInfos.Count == 0:
                return None
            
            # Conexión al dispositivo
            device = mgr.DeviceInfos(1).Connect()
            item = device.Items(1)
            
            # CONFIGURACIÓN TÉCNICA
            # 6146: 1=Color
            item.Properties("6146").Value = 1 
            # 6147: Resolución 300 DPI
            item.Properties("6147").Value = 300
            item.Properties("6148").Value = 300
            
            dialog = win32com.client.Dispatch("WIA.CommonDialog")
            img = dialog.ShowAcquireImage(1, 1, 65536, "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}", False, True)
            
            if img:
                temp_dir = Scanner._get_temp_dir()
                path = os.path.abspath(os.path.join(temp_dir, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
                img.SaveFile(path)
                return path
        except Exception as e:
            print(f"Error WIA: {e}")
            return None
    
    @staticmethod
    def escanear_twain():
        """
        Método TWAIN - Compatible con más escáneres incluidos WiFi
        Requiere: pip install python-twain (opcional)
        """
        try:
            import twain
            
            # Inicializar TWAIN
            sm = twain.SourceManager(0)
            
            # Intentar obtener el escáner predeterminado
            try:
                ss = sm.OpenSource()
            except:
                # Si no hay predeterminado, mostrar selector
                ss = sm.SelectSource()
            
            if not ss:
                return None
            
            # Configurar escaneo
            ss.SetCapability(twain.ICAP_PIXELTYPE, twain.TWPT_RGB)
            ss.SetCapability(twain.ICAP_XRESOLUTION, 300)
            ss.SetCapability(twain.ICAP_YRESOLUTION, 300)
            
            # Realizar escaneo
            ss.RequestAcquire(0, 0)
            rv = ss.XferImageNatively()
            
            if rv:
                (handle, count) = rv
                temp_dir = Scanner._get_temp_dir()
                bmp_path = os.path.abspath(os.path.join(temp_dir, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bmp"))
                png_path = os.path.abspath(os.path.join(temp_dir, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
                
                twain.DIBToBMFile(handle, bmp_path)
                
                # Convertir BMP a PNG
                from PIL import Image
                img = Image.open(bmp_path)
                img.save(png_path)
                
                # Eliminar BMP temporal
                os.remove(bmp_path)
                
                return png_path
        except ImportError:
            print("python-twain no está instalado. Use: pip install python-twain")
            return None
        except Exception as e:
            print(f"Error TWAIN: {e}")
            return None
    
    @staticmethod
    def escanear_manual():
        """
        Método Manual - Permite seleccionar un archivo ya escaneado
        Útil para:
        - Escáneres WiFi que tienen su propio software
        - Imágenes ya guardadas
        - Compatibilidad universal
        """
        try:
            # Mostrar mensaje informativo
            respuesta = messagebox.askyesno(
                "Escaneo Manual",
                "¿Desea seleccionar una imagen ya escaneada?\n\n"
                "Presione SÍ para seleccionar un archivo,\n"
                "o presione NO para cancelar."
            )
            
            if not respuesta:
                return None
            
            # Abrir diálogo de selección de archivo
            archivo = filedialog.askopenfilename(
                title="Seleccionar imagen escaneada",
                filetypes=[
                    ("Imágenes", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                    ("PNG", "*.png"),
                    ("JPEG", "*.jpg *.jpeg"),
                    ("BMP", "*.bmp"),
                    ("TIFF", "*.tiff *.tif"),
                    ("Todos", "*.*")
                ]
            )
            
            if archivo and os.path.exists(archivo):
                return archivo
            else:
                return None
                
        except Exception as e:
            print(f"Error en escaneo manual: {e}")
            return None
    
    @staticmethod
    def escanear_con_canon():
        """
        Método específico para Canon - Usa el software IJ Scan Utility
        """
        try:
            # Mostrar instrucciones
            messagebox.showinfo(
                "Escaneo con Canon",
                "Por favor:\n\n"
                "1. Abra el software 'IJ Scan Utility' de Canon\n"
                "2. Escanee la imagen\n"
                "3. Guarde el archivo\n"
                "4. Luego seleccione el archivo guardado\n\n"
                "Presione OK cuando esté listo para seleccionar el archivo."
            )
            
            # Llamar al método manual para seleccionar
            return Scanner.escanear_manual()
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    @staticmethod
    def configurar_metodo_preferido():
        """
        Permite al usuario configurar el método de escaneo preferido
        """
        from tkinter import Tk, Toplevel, Label, Button, StringVar, Radiobutton
        
        # Crear ventana de configuración
        ventana = Toplevel()
        ventana.title("Configurar Método de Escaneo")
        ventana.geometry("450x350")
        ventana.resizable(False, False)
        
        Label(
            ventana,
            text="Seleccione el método de escaneo preferido:",
            font=("Segoe UI", 12, "bold"),
            pady=20
        ).pack()
        
        metodo_var = StringVar(value=Scanner.METODO_PREFERIDO)
        
        # Opción WIA
        frame_wia = Label(ventana, text="", pady=10)
        frame_wia.pack(fill="x", padx=30)
        
        Radiobutton(
            frame_wia,
            text="WIA - Escáneres USB tradicionales",
            variable=metodo_var,
            value="wia",
            font=("Segoe UI", 10)
        ).pack(anchor="w")
        Label(
            frame_wia,
            text="(Solo escáneres reconocidos por Windows)",
            font=("Segoe UI", 8),
            fg="gray"
        ).pack(anchor="w", padx=25)
        
        # Opción TWAIN
        frame_twain = Label(ventana, text="", pady=10)
        frame_twain.pack(fill="x", padx=30)
        
        Radiobutton(
            frame_twain,
            text="TWAIN - Mayor compatibilidad",
            variable=metodo_var,
            value="twain",
            font=("Segoe UI", 10)
        ).pack(anchor="w")
        Label(
            frame_twain,
            text="(Incluye escáneres WiFi - Requiere python-twain)",
            font=("Segoe UI", 8),
            fg="gray"
        ).pack(anchor="w", padx=25)
        
        # Opción Manual (Recomendada)
        frame_manual = Label(ventana, text="", pady=10)
        frame_manual.pack(fill="x", padx=30)
        
        Radiobutton(
            frame_manual,
            text="MANUAL - Selección de archivos (RECOMENDADO)",
            variable=metodo_var,
            value="manual",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")
        Label(
            frame_manual,
            text="(Use el software de su escáner y luego seleccione el archivo)",
            font=("Segoe UI", 8),
            fg="gray"
        ).pack(anchor="w", padx=25)
        
        def guardar():
            Scanner.METODO_PREFERIDO = metodo_var.get()
            messagebox.showinfo(
                "Guardado",
                f"Método configurado: {Scanner.METODO_PREFERIDO.upper()}"
            )
            ventana.destroy()
        
        Button(
            ventana,
            text="Guardar Configuración",
            command=guardar,
            font=("Segoe UI", 11),
            bg="#10b981",
            fg="white",
            padx=20,
            pady=10
        ).pack(pady=20)
        
        ventana.transient()
        ventana.grab_set()
        ventana.wait_window()


# Clase auxiliar para facilitar el uso
class ScannerHelper:
    """
    Clase auxiliar con métodos simplificados
    """
    
    @staticmethod
    def escanear_con_instrucciones():
        """
        Guía paso a paso para escanear
        """
        instrucciones = """
CÓMO ESCANEAR CON TU CANON G3100:

OPCIÓN 1 - Usando el Software Canon (RECOMENDADO):
1. Abre "IJ Scan Utility" (buscalo en el menú inicio)
2. Selecciona tu Canon G3100 WiFi
3. Haz clic en "Escanear"
4. Guarda la imagen en una carpeta conocida
5. Luego usa el botón "📂 CARGAR" en el programa

OPCIÓN 2 - Desde el Escáner:
1. En el panel del escáner, presiona "Scan"
2. Selecciona "Escanear a PC"
3. La imagen se guardará automáticamente
4. Busca la imagen y cárgala con "📂 CARGAR"

OPCIÓN 3 - Desde la App Canon (Móvil):
1. Usa la app "Canon PRINT" en tu celular
2. Escanea y guarda en tu teléfono
3. Transfiere la imagen a la PC
4. Cárgala con "📂 CARGAR"

Presione OK para continuar...
"""
        
        messagebox.showinfo("Instrucciones de Escaneo", instrucciones)
        
        # Después de mostrar instrucciones, permitir seleccionar archivo
        return Scanner.escanear_manual()