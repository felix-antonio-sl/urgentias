from . import db
from datetime import datetime, timezone
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run = db.Column(db.String(12), unique=True, nullable=False)
    historia = db.Column(db.Text, nullable=True)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    atenciones = db.relationship('Atencion', backref='paciente', lazy=True)

class Atencion(db.Model):
    __tablename__ = 'atenciones'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    paciente_id = db.Column(db.String, db.ForeignKey('pacientes.id'), nullable=False)
    detalle = db.Column(db.Text, nullable=True)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)
