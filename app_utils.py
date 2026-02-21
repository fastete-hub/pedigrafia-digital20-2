import logging
import re
import shutil
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Tuple

from config_mejorado import Config


LOGGER_NAME = "podoscopio"


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
