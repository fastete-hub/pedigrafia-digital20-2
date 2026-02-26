import time


class WiiBalanceBoardService:
    VENDOR_ID = 0x057E
    PRODUCT_ID = 0x0306

    def __init__(self):
        self.hid = None
        self.device = None

    def available(self):
        try:
            import hid  # type: ignore
            self.hid = hid
            return True
        except Exception:
            return False

    def connect(self):
        if not self.available():
            return False, "Dependencia 'hid' no instalada (pip install hidapi)."
        try:
            devs = self.hid.enumerate(self.VENDOR_ID, self.PRODUCT_ID)
            if not devs:
                return False, "No se encontró Wii Balance Board conectada por Bluetooth/HID."
            path = devs[0].get("path")
            self.device = self.hid.device()
            self.device.open_path(path)
            self.device.set_nonblocking(1)
            return True, "Wii Balance Board conectada (modo experimental)."
        except Exception as e:
            return False, f"No se pudo conectar Wii Balance Board: {e}"

    @staticmethod
    def _parse_sensors(report):
        # Parse heurístico de 4 sensores 16-bit desde payload HID
        if not report or len(report) < 12:
            return None
        b = list(report)
        # intentar desde offsets comunes
        for off in (2, 4):
            if off + 8 <= len(b):
                vals = []
                for i in range(0, 8, 2):
                    vals.append((b[off + i] << 8) + b[off + i + 1])
                if max(vals) > 0:
                    return vals
        return None

    def capture_seconds(self, seconds=10.0, foot="IZQ"):
        if not self.device:
            return [], "Wii Balance Board no conectada"
        t0 = time.time()
        out = []
        while (time.time() - t0) < seconds:
            try:
                r = self.device.read(32)
            except Exception:
                r = None
            sensors = self._parse_sensors(r)
            if sensors:
                fz = float(sum(sensors))
                out.append((time.time() - t0, foot, fz))
            time.sleep(0.01)
        return out, "ok"

    def close(self):
        try:
            if self.device:
                self.device.close()
        except Exception:
            pass
        self.device = None
