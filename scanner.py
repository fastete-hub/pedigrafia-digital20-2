import win32com.client
import os
from datetime import datetime
import uuid

class Scanner:

    @staticmethod
    def _ruta_escaneo_unica(ext="png"):
        """Genera una ruta única para evitar sobrescribir escaneos consecutivos."""
        ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        token = uuid.uuid4().hex[:6]
        return os.path.abspath(f"scan_{ts}_{token}.{ext}")

    @staticmethod
    def disponible():
        try:
            mgr = win32com.client.Dispatch("WIA.DeviceManager")
            return mgr.DeviceInfos.Count > 0
        except: return False

    @staticmethod
    def escanear():
        try:
            mgr = win32com.client.Dispatch("WIA.DeviceManager")
            if mgr.DeviceInfos.Count == 0: return None
            
            # Conexión al dispositivo
            device = mgr.DeviceInfos(1).Connect()
            item = device.Items(1)
            
            # CONFIGURACIÓN TÉCNICA
            # 6146: 1=Color (Mejor para capturar matices de tinta)
            item.Properties("6146").Value = 1 
            # 6147: Resolución (300 DPI es ideal para pedigrafía)
            item.Properties("6147").Value = 300
            item.Properties("6148").Value = 300
            
            dialog = win32com.client.Dispatch("WIA.CommonDialog")
            img = dialog.ShowAcquireImage(1, 1, 65536, "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}", False, True)
            
            if img:
                path = Scanner._ruta_escaneo_unica('png')
                img.SaveFile(path)
                return path
        except: return None