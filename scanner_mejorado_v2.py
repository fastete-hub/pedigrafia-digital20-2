"""
Scanner Mejorado v2 - Podoscopio Pro v3.0
Detecta escáneres WiFi como Canon G3100
"""

import os
from datetime import datetime
from tkinter import messagebox, filedialog

class Scanner:
    """
    Scanner mejorado con soporte para:
    - WIA (escáneres USB)
    - WSD (escáneres WiFi en red)
    - TWAIN (compatibilidad extendida)
    - Selección manual de archivos
    """
    
    @staticmethod
    def disponible():
        """Verifica si hay escáneres disponibles"""
        # Intentar detectar con WIA
        if Scanner._check_wia():
            return True
        # Intentar detectar con WSD
        if Scanner._check_wsd():
            return True
        # Siempre hay método manual
        return True
    
    @staticmethod
    def _check_wia():
        """Verifica escáneres WIA (USB)"""
        try:
            import win32com.client
            mgr = win32com.client.Dispatch("WIA.DeviceManager")
            return mgr.DeviceInfos.Count > 0
        except:
            return False
    
    @staticmethod
    def _check_wsd():
        """Verifica escáneres WSD (WiFi)"""
        try:
            import win32com.client
            mgr = win32com.client.Dispatch("WIA.DeviceManager")
            # Buscar dispositivos WSD
            for i in range(1, mgr.DeviceInfos.Count + 1):
                device_info = mgr.DeviceInfos(i)
                # Los escáneres WiFi suelen tener "Network" o "WSD" en el nombre
                if "Network" in str(device_info) or "WSD" in str(device_info):
                    return True
            return False
        except:
            return False
    
    @staticmethod
    def listar_escaneres():
        """Lista todos los escáneres detectados"""
        escaneres = []
        
        try:
            import win32com.client
            mgr = win32com.client.Dispatch("WIA.DeviceManager")
            
            for i in range(1, mgr.DeviceInfos.Count + 1):
                device_info = mgr.DeviceInfos(i)
                try:
                    nombre = device_info.Properties("Name").Value
                    tipo = device_info.Properties("Type").Value
                    escaneres.append({
                        'index': i,
                        'nombre': nombre,
                        'tipo': tipo
                    })
                except:
                    escaneres.append({
                        'index': i,
                        'nombre': f"Escáner {i}",
                        'tipo': 'Desconocido'
                    })
        except:
            pass
        
        return escaneres
    
    @staticmethod
    def escanear():
        """
        Método principal de escaneo con detección inteligente
        """
        # Primero, listar escáneres disponibles
        escaneres = Scanner.listar_escaneres()
        
        if len(escaneres) == 0:
            # No hay escáneres detectados, ofrecer opciones
            return Scanner._mostrar_opciones_sin_escaner()
        elif len(escaneres) == 1:
            # Un solo escáner, usarlo directamente
            return Scanner._escanear_con_dispositivo(escaneres[0]['index'])
        else:
            # Múltiples escáneres, permitir elegir
            return Scanner._seleccionar_y_escanear(escaneres)
    
    @staticmethod
    def _mostrar_opciones_sin_escaner():
        """Muestra opciones cuando no se detecta escáner"""
        from tkinter import Tk, Toplevel, Label, Button
        
        ventana = Toplevel()
        ventana.title("Escáner no detectado")
        ventana.geometry("500x350")
        ventana.resizable(False, False)
        
        Label(
            ventana,
            text="⚠️ No se detectó ningún escáner",
            font=("Segoe UI", 14, "bold"),
            fg="#f59e0b"
        ).pack(pady=20)
        
        Label(
            ventana,
            text="Para escáneres WiFi como Canon G3100:",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=10)
        
        instrucciones = """
1. Abre el software de tu escáner (ej: IJ Scan Utility)
2. Escanea las imágenes y guárdalas
3. Usa el botón "📂 CARGAR" en el Podoscopio

O bien:

• Verifica que el escáner esté encendido
• Verifica la conexión WiFi/USB
• Reinstala los drivers del fabricante
        """
        
        Label(
            ventana,
            text=instrucciones,
            font=("Segoe UI", 10),
            justify="left"
        ).pack(pady=10)
        
        resultado = {"opcion": None}
        
        def usar_manual():
            resultado["opcion"] = "manual"
            ventana.destroy()
        
        def cancelar():
            resultado["opcion"] = "cancelar"
            ventana.destroy()
        
        Button(
            ventana,
            text="📂 Cargar Archivos Manualmente",
            command=usar_manual,
            font=("Segoe UI", 11),
            bg="#10b981",
            fg="white",
            padx=20,
            pady=10
        ).pack(pady=10)
        
        Button(
            ventana,
            text="Cancelar",
            command=cancelar,
            font=("Segoe UI", 10),
            bg="#ef4444",
            fg="white",
            padx=20,
            pady=5
        ).pack(pady=5)
        
        ventana.transient()
        ventana.grab_set()
        ventana.wait_window()
        
        if resultado["opcion"] == "manual":
            return Scanner.escanear_manual()
        else:
            return None
    
    @staticmethod
    def _seleccionar_y_escanear(escaneres):
        """Permite seleccionar entre múltiples escáneres"""
        from tkinter import Toplevel, Label, Button, Listbox, Scrollbar
        
        ventana = Toplevel()
        ventana.title("Seleccionar Escáner")
        ventana.geometry("450x400")
        
        Label(
            ventana,
            text="Seleccione el escáner a utilizar:",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=20)
        
        # Lista de escáneres
        frame_lista = Label(ventana)
        frame_lista.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")
        
        listbox = Listbox(
            frame_lista,
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set,
            height=10
        )
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        for escaner in escaneres:
            listbox.insert("end", f"{escaner['nombre']} ({escaner['tipo']})")
        
        listbox.select_set(0)
        
        resultado = {"index": None}
        
        def usar_seleccionado():
            seleccion = listbox.curselection()
            if seleccion:
                resultado["index"] = escaneres[seleccion[0]]['index']
            ventana.destroy()
        
        def cancelar():
            ventana.destroy()
        
        Button(
            ventana,
            text="Usar Este Escáner",
            command=usar_seleccionado,
            font=("Segoe UI", 11),
            bg="#10b981",
            fg="white",
            padx=20,
            pady=10
        ).pack(pady=10)
        
        Button(
            ventana,
            text="Cancelar",
            command=cancelar
        ).pack()
        
        ventana.transient()
        ventana.grab_set()
        ventana.wait_window()
        
        if resultado["index"]:
            return Scanner._escanear_con_dispositivo(resultado["index"])
        else:
            return None
    
    @staticmethod
    def _escanear_con_dispositivo(device_index):
        """Escanea con el dispositivo especificado"""
        try:
            import win32com.client
            
            mgr = win32com.client.Dispatch("WIA.DeviceManager")
            device = mgr.DeviceInfos(device_index).Connect()
            item = device.Items(1)
            
            # Configuración de escaneo
            try:
                item.Properties("6146").Value = 1  # Color
                item.Properties("6147").Value = 300  # DPI X
                item.Properties("6148").Value = 300  # DPI Y
            except:
                # Algunos escáneres no soportan estas propiedades
                pass
            
            # Intentar escaneo directo
            try:
                dialog = win32com.client.Dispatch("WIA.CommonDialog")
                img = dialog.ShowAcquireImage(1, 1, 65536, "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}", False, True)
                
                if img:
                    path = os.path.abspath(f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    img.SaveFile(path)
                    return path
            except:
                # Si falla el diálogo, intentar escaneo directo
                try:
                    img = item.Transfer("{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}")
                    path = os.path.abspath(f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    img.SaveFile(path)
                    return path
                except:
                    messagebox.showerror(
                        "Error",
                        "No se pudo escanear con este dispositivo.\n"
                        "Use el botón 'CARGAR' para seleccionar archivos."
                    )
                    return None
        except Exception as e:
            messagebox.showerror("Error", f"Error al escanear: {e}")
            return None
    
    @staticmethod
    def escanear_manual():
        """Método de selección manual de archivos"""
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
    
    @staticmethod
    def diagnosticar_escaneres():
        """
        Herramienta de diagnóstico para ver qué escáneres se detectan
        """
        print("\n=== DIAGNÓSTICO DE ESCÁNERES ===\n")
        
        # 1. Verificar WIA
        print("1. Verificando WIA (Windows Image Acquisition)...")
        try:
            import win32com.client
            mgr = win32com.client.Dispatch("WIA.DeviceManager")
            count = mgr.DeviceInfos.Count
            print(f"   ✓ WIA disponible: {count} dispositivo(s) detectado(s)\n")
            
            if count > 0:
                for i in range(1, count + 1):
                    try:
                        device = mgr.DeviceInfos(i)
                        nombre = device.Properties("Name").Value
                        tipo = device.Properties("Type").Value
                        print(f"   [{i}] {nombre} (Tipo: {tipo})")
                    except:
                        print(f"   [{i}] Dispositivo sin nombre")
        except Exception as e:
            print(f"   ✗ WIA no disponible: {e}\n")
        
        # 2. Verificar si puede listar
        print("\n2. Listando con función mejorada...")
        escaneres = Scanner.listar_escaneres()
        if escaneres:
            print(f"   ✓ {len(escaneres)} escáner(es) encontrado(s):")
            for e in escaneres:
                print(f"      - {e['nombre']}")
        else:
            print("   ✗ No se encontraron escáneres")
        
        print("\n=== FIN DEL DIAGNÓSTICO ===\n")
