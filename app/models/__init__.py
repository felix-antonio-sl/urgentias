from dataclasses import dataclass, field
from datetime import datetime, date, timezone
import re
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


def _parse_datetime(value):
    if isinstance(value, datetime) or value is None:
        return value
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _parse_date(value):
    if isinstance(value, date) or value is None:
        return value
    try:
        return date.fromisoformat(value)
    except Exception:
        return None


@dataclass
class Paciente:
    id: str | None = None
    nombre: str | None = None
    run: str | None = None
    fecha_nacimiento: date | None = None
    historia: str | None = None
    creado_en: datetime | None = None

    @property
    def edad(self):
        if self.fecha_nacimiento:
            hoy = date.today()
            return hoy.year - self.fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None

    @staticmethod
    def validar_run(run: str) -> bool:
        return bool(re.match(r"^\d{6,8}-[\dkK]$", run))

    @classmethod
    def from_dict(cls, data: dict) -> "Paciente":
        return cls(
            id=data.get("id"),
            nombre=data.get("nombre"),
            run=data.get("run"),
            fecha_nacimiento=_parse_date(data.get("fecha_nacimiento")),
            historia=data.get("historia"),
            creado_en=_parse_datetime(data.get("creado_en")),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "run": self.run,
            "fecha_nacimiento": self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            "historia": self.historia,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }


@dataclass
class Atencion:
    id: str | None = None
    paciente_id: str | None = None
    activa: bool = True
    detalle: str | None = None
    informe_final: str | None = None
    creado_en: datetime | None = None
    cerrada_en: datetime | None = None
    actualizado_en: datetime | None = None
    diagnostico_diferencial: str | None = None
    manejo_sugerido: str | None = None
    proxima_accion: str | None = None
    alertas: str | None = None

    @property
    def tiempo_desde_creacion(self):
        if not self.creado_en:
            return "00:00"
        ahora = datetime.now(timezone.utc)
        delta = ahora - self.creado_en
        horas, segundos = divmod(delta.total_seconds(), 3600)
        minutos = int((segundos % 3600) // 60)
        return f"{int(horas):02}:{minutos:02}"

    def obtener_sintesis(self, longitud=150):
        detalle = self.detalle or ""
        return detalle[:longitud] + "..." if len(detalle) > longitud else detalle or "Sin detalle"

    @classmethod
    def from_dict(cls, data: dict) -> "Atencion":
        return cls(
            id=data.get("id"),
            paciente_id=data.get("paciente_id"),
            activa=data.get("activa", True),
            detalle=data.get("detalle"),
            informe_final=data.get("informe_final"),
            creado_en=_parse_datetime(data.get("creado_en")),
            cerrada_en=_parse_datetime(data.get("cerrada_en")),
            actualizado_en=_parse_datetime(data.get("actualizado_en")),
            diagnostico_diferencial=data.get("diagnostico_diferencial"),
            manejo_sugerido=data.get("manejo_sugerido"),
            proxima_accion=data.get("proxima_accion"),
            alertas=data.get("alertas"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "activa": self.activa,
            "detalle": self.detalle,
            "informe_final": self.informe_final,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
            "cerrada_en": self.cerrada_en.isoformat() if self.cerrada_en else None,
            "actualizado_en": self.actualizado_en.isoformat() if self.actualizado_en else None,
            "diagnostico_diferencial": self.diagnostico_diferencial,
            "manejo_sugerido": self.manejo_sugerido,
            "proxima_accion": self.proxima_accion,
            "alertas": self.alertas,
        }


@dataclass
class User(UserMixin):
    id: int | None = None
    email: str | None = None
    password_hash: str | None = None
    created_at: datetime | None = None

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id) if self.id is not None else None

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            id=data.get("id"),
            email=data.get("email"),
            password_hash=data.get("password_hash"),
            created_at=_parse_datetime(data.get("created_at")),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
