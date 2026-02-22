import json
import logging
import re
import shutil
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple

from config_mejorado import Config


LOGGER_NAME = "podoscopio"
SETTINGS_FILE = Path("config_usuario.json")


def setup_logging() -> logging.Logger:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "app.log"

    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    logger.info("Logger inicializado")
    return logger


def backup_database(max_copias: int = 7) -> Path | None:
    db_path = Path(Config.DB_NAME)
    if not db_path.exists():
        return None

    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)

    backup_name = f"{db_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{db_path.suffix}"
    backup_path = backup_dir / backup_name
    shutil.copy2(db_path, backup_path)

    backups = sorted(backup_dir.glob(f"{db_path.stem}_*{db_path.suffix}"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[max_copias:]:
        old.unlink(missing_ok=True)

    return backup_path


def normalize_patient_name(name: str) -> str:
    compact = " ".join((name or "").strip().split())
    return compact.title()


def validate_email(email: str) -> Tuple[bool, str]:
    email = (email or "").strip()
    if not email:
        return True, ""
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return True, ""
    return False, "Email inválido. Ejemplo: nombre@dominio.com"


def validate_phone(phone: str) -> Tuple[bool, str]:
    phone = (phone or "").strip()
    if not phone:
        return True, ""
    if re.match(r"^[0-9+()\-\s]{6,20}$", phone):
        return True, ""
    return False, "Teléfono inválido. Use solo números y símbolos +()-"


def get_temp_dir(subdir: str | None = None) -> Path:
    base = Path("temp")
    if subdir:
        base = base / subdir
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_temp_file_path(prefix: str, suffix: str = ".png", subdir: str | None = None) -> Path:
    d = get_temp_dir(subdir)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    return d / f"{prefix}_{ts}{suffix}"


def mover_temporales_raiz_a_temp() -> int:
    """Mueve archivos temporales viejos de la raíz a temp/legacy para ordenar el proyecto."""
    legacy = get_temp_dir("legacy")
    movidos = 0
    for pat in ("scan_*.png", "temp_unida_*.png", "temp_mapa_view_*.png"):
        for f in Path('.').glob(pat):
            if f.is_file():
                dest = legacy / f.name
                try:
                    f.replace(dest)
                    movidos += 1
                except Exception:
                    pass
    return movidos


def limpiar_temporales(max_horas: int = 24) -> int:
    """Borra temporales antiguos dentro de temp/ para evitar acumulación en disco."""
    base = get_temp_dir()
    limite = datetime.now() - timedelta(hours=max_horas)
    eliminados = 0

    for sub in ("scans", "legacy"):
        d = base / sub
        if not d.exists():
            continue
        for pat in ("*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff"):
            for f in d.glob(pat):
                try:
                    if datetime.fromtimestamp(f.stat().st_mtime) < limite:
                        f.unlink(missing_ok=True)
                        eliminados += 1
                except Exception:
                    pass
    return eliminados


def load_runtime_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_runtime_setting(key: str, value):
    data = load_runtime_settings()
    data[key] = value
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalizar_modo_calibracion(modo: str | None) -> str:
    modo_txt = (modo or "").strip().lower()
    if "tinta" in modo_txt:
        return "tinta"
    return "digital"


def get_calibracion_correccion_por_modo(modo: str | None, fallback: float) -> float:
    """Obtiene el factor guardado para el modo dado; si no existe devuelve fallback."""
    data = load_runtime_settings()
    clave = f"calibracion_correccion_pxmm_{_normalizar_modo_calibracion(modo)}"
    v = data.get(clave)
    if isinstance(v, (int, float)):
        return max(0.50, min(1.30, float(v)))
    return max(0.50, min(1.30, float(fallback)))


def save_calibracion_correccion_por_modo(modo: str | None, valor: float):
    clave = f"calibracion_correccion_pxmm_{_normalizar_modo_calibracion(modo)}"
    save_runtime_setting(clave, max(0.50, min(1.30, float(valor))))


def apply_runtime_config_overrides() -> None:
    data = load_runtime_settings()
    v = data.get("calibracion_correccion_pxmm")
    if isinstance(v, (int, float)):
        Config.CALIBRACION_CORRECCION_PXMM = max(0.50, min(1.30, float(v)))
