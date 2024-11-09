from . import db
from datetime import datetime, date, timezone, timedelta
import uuid
import re
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Paciente(db.Model):
    __tablename__ = "pacientes"

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(100), nullable=True)
    run = db.Column(db.String(12), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    historia = db.Column(db.Text, nullable=True)
    creado_en = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )  # Actualizado

    atenciones = db.relationship("Atencion", backref="paciente", lazy=True)

    @property
    def edad(self):
        if self.fecha_nacimiento:
            hoy = date.today()
            return (
                hoy.year
                - self.fecha_nacimiento.year
                - (
                    (hoy.month, hoy.day)
                    < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
                )
            )
        else:
            return None

    @staticmethod
    def validar_run(run):
        return bool(re.match(r"^\d{6,8}-[\dkK]$", run))


class Atencion(db.Model):
    __tablename__ = "atenciones"

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    paciente_id = db.Column(db.String, db.ForeignKey("pacientes.id"), nullable=False)
    activa = db.Column(db.Boolean, default=True)
    detalle = db.Column(db.Text, nullable=True)
    informe_final = db.Column(db.Text, nullable=True)
    creado_en = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )  # Actualizado
    cerrada_en = db.Column(db.DateTime, nullable=True)
    actualizado_en = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),  # Actualizado
        onupdate=lambda: datetime.now(timezone.utc),  # Actualizado
    )

    # Campos generados por AI
    diagnostico_diferencial = db.Column(db.Text, nullable=True)
    manejo_sugerido = db.Column(db.Text, nullable=True)
    proxima_accion = db.Column(db.Text, nullable=True)
    alertas = db.Column(db.Text, nullable=True)

    @property
    def tiempo_desde_creacion(self):
        now = datetime.now(timezone.utc)
        creado_en = self.creado_en

        # Si creado_en es naive, asumimos que está en UTC y lo convertimos a aware
        if creado_en.tzinfo is None:
            creado_en = creado_en.replace(tzinfo=timezone.utc)

        delta = now - creado_en
        horas, segundos = divmod(delta.total_seconds(), 3600)
        minutos = int((segundos % 3600) // 60)
        return f"{int(horas):02}:{minutos:02}"

    def obtener_sintesis(self, longitud=150):
        detalle = self.detalle or ""
        return (
            detalle[:longitud] + "..."
            if len(detalle) > longitud
            else detalle or "Sin detalle"
        )


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )  # Actualizado

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)
