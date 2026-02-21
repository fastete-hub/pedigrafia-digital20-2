import time

from config_mejorado import Config
from app_utils import get_temp_file_path


class Scanner:
    @staticmethod
    def _ruta_escaneo_unica(ext="png"):
        """Genera una ruta única para evitar sobrescribir escaneos consecutivos."""
        return str(get_temp_file_path("scan", f".{ext}", subdir="scans"))

    @staticmethod
    def _get_wia_device_manager():
        import win32com.client

        return win32com.client.Dispatch("WIA.DeviceManager")

    @staticmethod
    def disponible():
        try:
            mgr = Scanner._get_wia_device_manager()
            return mgr.DeviceInfos.Count > 0
        except Exception:
            return False

    @staticmethod
    def escanear():
        try:
            import win32com.client

            mgr = Scanner._get_wia_device_manager()
            if mgr.DeviceInfos.Count == 0:
                return None

            # Conexión al dispositivo
            device = mgr.DeviceInfos(1).Connect()
            item = device.Items(1)

            # CONFIGURACIÓN TÉCNICA
            # 6146: 1=Color (Mejor para capturar matices de tinta)
            item.Properties("6146").Value = 1
            # 6147/6148: Resolución (300 DPI es ideal para pedigrafía)
            item.Properties("6147").Value = 300
            item.Properties("6148").Value = 300

            dialog = win32com.client.Dispatch("WIA.CommonDialog")
            img = dialog.ShowAcquireImage(1, 1, 65536, "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}", False, True)

            if img:
                path = Scanner._ruta_escaneo_unica('png')
                img.SaveFile(path)
                return path
            return None
        except Exception:
            return None

    @staticmethod
    def escanear_con_reintentos(max_reintentos=None, espera_s=None):
        """Intenta escanear múltiples veces para tolerar fallos transitorios del dispositivo."""
        max_reintentos = Config.SCANNER_MAX_REINTENTOS if max_reintentos is None else max_reintentos
        espera_s = Config.SCANNER_ESPERA_REINTENTO_S if espera_s is None else espera_s

        for intento in range(1, max_reintentos + 1):
            path = Scanner.escanear()
            if path:
                return path, intento
            if intento < max_reintentos and espera_s > 0:
                time.sleep(espera_s)

        return None, max_reintentos
