from app_utils import normalize_patient_name, validate_email, validate_phone


class PatientService:
    @staticmethod
    def validar_y_normalizar(nombre, edad, obra_social, email, telefono, talle):
        nombre_norm = normalize_patient_name(nombre)
        if not nombre_norm:
            raise ValueError("El nombre es obligatorio.")

        email_ok, email_msg = validate_email(email)
        if not email_ok:
            raise ValueError(email_msg)

        tel_ok, tel_msg = validate_phone(telefono)
        if not tel_ok:
            raise ValueError(tel_msg)

        return {
            "nombre": nombre_norm,
            "edad": str(edad),
            "obra_social": (obra_social or "").strip(),
            "email": (email or "").strip(),
            "telefono": (telefono or "").strip(),
            "talle": str(talle),
        }
