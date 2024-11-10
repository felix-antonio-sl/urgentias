# Estructura y Código del Proyecto urgentias

## Árbol del proyecto
```plaintext
├── app
│   ├── __init__.py
│   ├── forms.py
│   ├── models.py
│   ├── prompts
│   │   ├── procesar_detalle_atencion.txt
│   │   ├── procesar_historia.txt
│   │   └── procesar_texto_no_estructurado.txt
│   ├── routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── main.py
│   ├── static
│   │   └── css
│   │       └── styles.css
│   ├── templates
│   │   ├── 404.html
│   │   ├── 500.html
│   │   ├── atenciones.html
│   │   ├── base.html
│   │   ├── detalle_atencion.html
│   │   ├── login.html
│   │   ├── macros.html
│   │   ├── register.html
│   │   └── ver_reporte.html
│   └── utils.py
├── config
│   └── config.py
└── manage.py
```

### __init__.py

```py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config.config import DevelopmentConfig
import logging
from logging.handlers import RotatingFileHandler
import os
import ell
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from markupsafe import Markup, escape


# Definición del filtro nl2br
def nl2br(value):
    return Markup("<br>".join(escape(value).split("\n")))


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

from .models import User, Paciente, Atencion


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configuración para aceptar tokens CSRF en los encabezados
    app.config["WTF_CSRF_HEADERS"] = ["X-CSRFToken"]

    # Inicialización de ell
    ell.init(
        store="./ell_storage",
        autocommit=True,
        verbose=True,
        lazy_versioning=True,
        default_api_params={"temperature": 0.0},
    )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    csrf.init_app(app)

    # Registrar el filtro nl2br
    app.jinja_env.filters["nl2br"] = nl2br

    from .routes.main import main as main_bp

    app.register_blueprint(main_bp)

    from .routes.auth import auth as auth_bp

    app.register_blueprint(auth_bp)

    from .routes.main import register_error_handlers

    register_error_handlers(app)

    if not app.debug and not app.testing:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/urgentias.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Urgentias startup")

    return app
```

### forms.py

```py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class ActualizarHistoriaForm(FlaskForm):
    historia = TextAreaField("Puede editar este texto", validators=[DataRequired()])
    submit = SubmitField("Actualizar")


class ActualizarDetalleForm(FlaskForm):
    detalle = TextAreaField("Puede editar este texto", validators=[DataRequired()])
    submit = SubmitField("Actualizar")


class ProcesarHistoriaBrutoForm(FlaskForm):
    historia_bruto = TextAreaField("Ingrese texto", validators=[DataRequired()])
    submit = SubmitField("Procesar")


class ProcesarDetalleBrutoForm(FlaskForm):
    detalle_bruto = TextAreaField("Ingrese texto", validators=[DataRequired()])
    submit = SubmitField("Procesar")


class LoginForm(FlaskForm):
    email = StringField("Correo Electrónico", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    remember = BooleanField("Recordarme")
    submit = SubmitField("Iniciar Sesión")


class RegisterForm(FlaskForm):
    email = StringField("Correo Electrónico", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirmar Contraseña", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Registrarse")


class ProcesarTextoNoEstructuradoForm(FlaskForm):
    texto = TextAreaField("Ingrese Texto", validators=[DataRequired()])
    submit = SubmitField("Procesar")


class CerrarAtencionForm(FlaskForm):
    submit = SubmitField("Cerrar")
```

### models.py

```py
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
```

### procesar_detalle_atencion.txt

```txt
Usted es un especialista en medicina de urgencias y emergencias y en documentación clínica. Su tarea es elaborar un registro en tiempo real del proceso de atención de un paciente en un servicio de urgencias, basándose en la información proporcionada y siguiendo los principios de documentación en medicina de emergencia.

Se le proporcionará la siguiente información:

<historia>
{historia_paciente}
</historia>

<atencion_actual>
{detalle_actual}
</atencion_actual>

<nuevo_texto_atencion>
{texto_bruto}
</nuevo_texto_atencion>

Utilice esta información para generar un registro incremental del proceso de atención, siguiendo estos principios y guías:

A. Principios fundamentales de la documentación en medicina de emergencia:
1. Reconocimiento y manejo inmediato de condiciones que amenazan la vida
2. Enfoque sistemático
3. Estratificación dinámica del riesgo

Basándose en estos principios y en la información proporcionada, genere un registro incremental del proceso de atención. Asegúrese de:

1. Utilizar español médico chileno conciso. La redacción debe ser simple, clara, directa. Sin marcas markdown. solo texto plano. Tratar de presentar textos fluidos
2. Seguir un orden cronológico en la documentación.
3. Enfocarse en los aspectos más críticos y relevantes de la atención del paciente.
4. Incluir todas las evaluaciones, intervenciones y decisiones clínicas importantes.
5. Documentar cualquier cambio significativo en el estado del paciente.
6. Usa abreviaciones médicas reconocidas y universales
7. Evita justificaciones, interpretaciones y recomendaciones
```

### procesar_historia.txt

```txt
Historia actual:
{historia_actual}

Nuevo texto en bruto:
{texto_bruto}

Por favor, genera una historia clínica actualizada y coherente.
```

### procesar_texto_no_estructurado.txt

```txt
Usted es un asistente que extrae información médica de texto no estructurado.

Por favor, extraiga y devuelva los siguientes datos en formato JSON:
- run: RUN del paciente. Independientemente del formato en que es extraido, la salida debe ser siempre en formato '12345678-9' (el digito verificador puede ser la letra k minuscula también)
- nombre: Nombre completo del paciente.
- fecha_nacimiento: Fecha de nacimiento en formato dd/mm/aaaa.

Si algún dato no está presente, coloque 'N/A' en su lugar.

Texto:
{texto_bruto}
```

### __init__.py

```py

```

### auth.py

```py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from ..forms import LoginForm, RegisterForm
from ..models import User
from .. import db
from flask_login import login_user, logout_user, current_user, login_required

auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Inicio de sesión exitoso.", "success")
            next_page = request.args.get("next")
            return (
                redirect(next_page)
                if next_page
                else redirect(url_for("main.lista_atenciones"))
            )
        else:
            flash("Correo o contraseña incorrectos.", "error")
    return render_template("login.html", form=form)


@auth.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("El correo electrónico ya está registrado.", "error")
        else:
            user = User(email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Registro exitoso. Puedes iniciar sesión ahora.", "success")
            return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for("main.lista_atenciones"))
```

### main.py

```py
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    send_file,
    current_app,
)
from .. import db
from ..models import Paciente, Atencion
from ..utils import (
    procesar_historia,
    procesar_detalle_atencion,
    procesar_texto_no_estructurado,
    generar_diagnostico_diferencial,
    generar_manejo_sugerido,
    generar_proxima_accion,
    generar_alertas,
    generar_reporte_alta_ambulatoria,
    generar_reporte_hospitalizacion,
    generar_reporte_interconsulta,
)
from ..forms import (
    ActualizarHistoriaForm,
    ActualizarDetalleForm,
    ProcesarHistoriaBrutoForm,
    ProcesarDetalleBrutoForm,
    ProcesarTextoNoEstructuradoForm,
    CerrarAtencionForm,
)

from flask_login import login_required, current_user
from datetime import datetime
import json
import re
from io import BytesIO
import logging
from datetime import datetime, timezone  # Importar timezone

main = Blueprint("main", __name__)

# Configuración de logging
logger = logging.getLogger(__name__)


def obtener_sintesis(detalle, longitud=25):
    """Obtiene una síntesis breve del detalle de la atención."""
    return (
        detalle[:longitud] + "..."
        if detalle and len(detalle) > longitud
        else detalle or "Sin detalle"
    )


@main.route("/")
@login_required
def lista_atenciones():
    atenciones = (
        Atencion.query.filter_by(activa=True).order_by(Atencion.creado_en.desc()).all()
    )
    form_cerrar = CerrarAtencionForm()
    form_procesar_texto = ProcesarTextoNoEstructuradoForm()
    return render_template(
        "atenciones.html",
        atenciones=atenciones,
        form_cerrar=form_cerrar,
        form_procesar_texto=form_procesar_texto,
    )


@main.route("/detalle_atencion/<string:atencion_id>", methods=["GET", "POST"])
@login_required
def detalle_atencion(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    form_historia = ActualizarHistoriaForm(prefix="historia")
    form_detalle = ActualizarDetalleForm(prefix="detalle")
    form_procesar_historia = ProcesarHistoriaBrutoForm(prefix="procesar_historia_modal")
    form_procesar_detalle = ProcesarDetalleBrutoForm(prefix="procesar_detalle_modal")

    if form_historia.validate_on_submit() and form_historia.submit.data:
        paciente.historia = form_historia.historia.data
        db.session.commit()
        try:
            actualizar_informacion_ai(atencion)
            flash("Historia y datos AI actualizados correctamente.", "success")
        except Exception as e:
            logger.error(f"Error al actualizar información AI: {e}")
            flash(
                "Historia actualizada. La información AI no está disponible temporalmente.",
                "warning",
            )
        return redirect(url_for("main.detalle_atencion", atencion_id=atencion_id))

    elif form_detalle.validate_on_submit() and form_detalle.submit.data:
        atencion.detalle = form_detalle.detalle.data
        db.session.commit()
        try:
            actualizar_informacion_ai(atencion)
            flash(
                "Detalle de atención y datos AI actualizados correctamente.", "success"
            )
        except Exception as e:
            logger.error(f"Error al actualizar información AI: {e}")
            flash(
                "Detalle actualizado. La información AI no está disponible temporalmente.",
                "warning",
            )
        return redirect(url_for("main.detalle_atencion", atencion_id=atencion_id))

    if request.method == "GET":
        form_historia.historia.data = paciente.historia
        form_detalle.detalle.data = atencion.detalle

    return render_template(
        "detalle_atencion.html",
        atencion=atencion,
        paciente=paciente,
        form_historia=form_historia,
        form_detalle=form_detalle,
        form_procesar_historia=form_procesar_historia,
        form_procesar_detalle=form_procesar_detalle,
    )


def actualizar_informacion_ai(atencion):
    paciente = atencion.paciente

    logger.info(f"Actualizando información AI para Atención ID: {atencion.id}")

    # Generación de información AI
    try:
        diagnostico_msg = generar_diagnostico_diferencial(
            paciente.historia or "", atencion.detalle or ""
        )
        manejo_msg = generar_manejo_sugerido(
            paciente.historia or "", atencion.detalle or ""
        )
        accion_msg = generar_proxima_accion(
            paciente.historia or "", atencion.detalle or ""
        )
        alertas_msg = generar_alertas(paciente.historia or "", atencion.detalle or "")
    except Exception as e:
        logger.error(f"Error al llamar a las funciones AI: {e}")
        raise

    # Asignación de los resultados parseados
    try:
        atencion.diagnostico_diferencial = "\n".join(
            diagnostico_msg.parsed.diagnosticos
        )
        atencion.manejo_sugerido = manejo_msg.parsed.manejo
        atencion.proxima_accion = accion_msg.parsed.accion
        atencion.alertas = "\n".join(alertas_msg.parsed.alertas)
    except AttributeError as e:
        logger.error(f"Error al asignar los resultados AI: {e}")
        raise

    atencion.actualizado_en = datetime.now(timezone.utc)  # Actualizado
    db.session.commit()
    logger.info(f"Información AI actualizada para Atención ID: {atencion.id}")


@main.route("/procesar_historia_bruto_modal/<string:atencion_id>", methods=["POST"])
@login_required
def procesar_historia_bruto_modal(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    # Añadir el prefijo al formulario
    form_procesar_historia = ProcesarHistoriaBrutoForm(prefix="procesar_historia_modal")
    if form_procesar_historia.validate_on_submit():
        texto_bruto = form_procesar_historia.historia_bruto.data
        historia_actualizada = procesar_historia(paciente.historia or "", texto_bruto)
        paciente.historia = historia_actualizada.text
        db.session.commit()
        flash("Historia procesada y actualizada.", "success")
    else:
        # Agregar registro de errores para depuración
        current_app.logger.error(
            f"Errores del formulario: {form_procesar_historia.errors}"
        )
        flash("Error al procesar la historia.", "error")

    return redirect(url_for("main.detalle_atencion", atencion_id=atencion_id))


@main.route("/procesar_detalle_bruto_modal/<string:atencion_id>", methods=["POST"])
@login_required
def procesar_detalle_bruto_modal(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    # Añadir el prefijo al formulario
    form_procesar_detalle = ProcesarDetalleBrutoForm(prefix="procesar_detalle_modal")
    if form_procesar_detalle.validate_on_submit():
        texto_bruto = form_procesar_detalle.detalle_bruto.data
        detalle_actualizado = procesar_detalle_atencion(
            paciente.historia or "", atencion.detalle or "", texto_bruto
        )
        atencion.detalle = detalle_actualizado.text
        db.session.commit()
        flash("Detalle de atención procesado y actualizado.", "success")
    else:
        # Agregar registro de errores para depuración
        current_app.logger.error(
            f"Errores del formulario: {form_procesar_detalle.errors}"
        )
        flash("Error al procesar el detalle de atención.", "error")

    return redirect(url_for("main.detalle_atencion", atencion_id=atencion_id))


@main.route("/procesar_texto", methods=["POST"])
@login_required
def procesar_texto():
    data = request.get_json()
    texto = data.get("texto")

    if not texto:
        return jsonify({"error": "Texto no proporcionado"}), 400

    try:
        resultado = procesar_texto_no_estructurado(texto)
        current_app.logger.debug(
            f"Resultado de procesar_texto_no_estructurado: {resultado}"
        )

        json_str = extraer_json(resultado.text)
        datos = json.loads(json_str)
        run = datos.get("run")
        nombre = datos.get("nombre")
        fecha_nacimiento = datos.get("fecha_nacimiento")
    except ValueError as e:
        current_app.logger.error(f"Error al extraer JSON: {e}")
        return jsonify({"error": "Error al interpretar la respuesta del modelo."}), 500
    except json.JSONDecodeError as e:
        current_app.logger.error(f"Error al decodificar JSON: {e}")
        current_app.logger.debug(f"Contenido de JSON: {json_str}")
        return jsonify({"error": "Error al interpretar la respuesta del modelo."}), 500
    except Exception as e:
        current_app.logger.error(f"Error inesperado: {e}")
        return jsonify({"error": "Error interno del servidor."}), 500

    if not run or not Paciente.validar_run(run):
        return jsonify({"error": "RUN no válido o no encontrado."}), 400

    if fecha_nacimiento and fecha_nacimiento != "N/A":
        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%d/%m/%Y").date()
        except ValueError:
            return jsonify({"error": "Formato de fecha de nacimiento inválido."}), 400
    else:
        fecha_nacimiento = None

    paciente = Paciente.query.filter_by(run=run).first()
    if not paciente:
        paciente = Paciente(run=run, nombre=nombre, fecha_nacimiento=fecha_nacimiento)
        db.session.add(paciente)
        db.session.commit()

    atencion = Atencion(paciente_id=paciente.id)
    db.session.add(atencion)
    db.session.commit()

    return jsonify({"message": "Atención creada exitosamente."}), 200


def extraer_json(respuesta):
    match = re.search(r"```json(.*?)```", respuesta, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        return json_str
    else:
        raise ValueError("No se encontró un bloque JSON en la respuesta.")


@main.route("/cerrar_atencion/<string:atencion_id>", methods=["POST"])
@login_required
def cerrar_atencion(atencion_id):
    form = CerrarAtencionForm()
    if form.validate_on_submit():
        atencion = Atencion.query.get_or_404(atencion_id)
        atencion.activa = False
        atencion.cerrada_en = datetime.utcnow()
        db.session.commit()
        flash("Atención cerrada exitosamente.", "success")
    else:
        flash("Error al cerrar la atención.", "error")
    return redirect(url_for("main.lista_atenciones"))


def register_error_handlers(app):
    from flask import render_template

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("403.html"), 403


@main.route("/generar_reporte/<string:atencion_id>/<string:tipo_reporte>")
@login_required
def generar_reporte(atencion_id, tipo_reporte):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    # Obtener los datos necesarios
    historia_paciente = paciente.historia or ""
    detalle_atencion = atencion.detalle or ""

    # Generar el reporte según el tipo
    if tipo_reporte == "alta_ambulatoria":
        reporte = generar_reporte_alta_ambulatoria(historia_paciente, detalle_atencion)
        titulo = "Reporte de Alta Ambulatoria"
    elif tipo_reporte == "hospitalizacion":
        reporte = generar_reporte_hospitalizacion(historia_paciente, detalle_atencion)
        titulo = "Solicitud de Hospitalización"
    elif tipo_reporte == "interconsulta":
        reporte = generar_reporte_interconsulta(historia_paciente, detalle_atencion)
        titulo = "Reporte de Interconsulta"
    else:
        flash("Tipo de reporte no válido.", "danger")
        return redirect(url_for("main.lista_atenciones"))

    # Renderizar la plantilla con el reporte
    return render_template(
        "ver_reporte.html", titulo=titulo, reporte=reporte, atencion=atencion
    )
```

### styles.css

```css
/* Estilos personalizados para Urgentias */

/* Variables de colores personalizados */
:root {
    --primary-color: #00B2A9;
    /* Teal */
    --secondary-color: #4B0082;
    /* Indigo */
    --accent-color: #FFD700;
    /* Gold */
    --highlight-color: #C71585;
    /* Medium Violet Red */

    /* Sobrescribir variables de Bootstrap */
    --bs-primary: var(--primary-color);
    --bs-secondary: var(--secondary-color);
    --bs-success: var(--accent-color);
    --bs-danger: var(--highlight-color);
    /* Puedes continuar sobrescribiendo otras variables según sea necesario */
}

/* Estilos para resaltar información AI */
.text-highlight {
    background-color: #ffffcc;
    /* Amarillo claro */
    font-weight: bold;
}

.text-danger {
    color: var(--bs-danger);
    /* Usando el color definido */
    font-weight: bold;
}
```

### 404.html

```html
{% extends "base.html" %}

{% block title %}Página No Encontrada{% endblock %}

{% block content %}
<div class="container text-center mt-5">
  <h2>404 - Página No Encontrada</h2>
  <p>Lo sentimos, la página que buscas no existe.</p>
  <a href="{{ url_for('main.lista_atenciones') }}" class="btn btn-primary">Volver al inicio</a>
</div>
{% endblock %}
```

### 500.html

```html
{% extends "base.html" %}

{% block title %}Error Interno del Servidor{% endblock %}

{% block content %}
<div class="container text-center mt-5">
  <h2>¡Vaya! Algo salió mal.</h2>
  <p>Estamos trabajando para solucionar este problema. Por favor, inténtalo de nuevo más tarde.</p>
</div>
{% endblock %}
```

### atenciones.html

```html
{% extends "base.html" %}
{% import 'macros.html' as macros %}
{% block title %}Lista de Atenciones{% endblock %}
{% block content %}
<h2 class="mb-4">Lista de Atenciones</h2>

<!-- Botón para abrir el modal de creación de atención con texto no estructurado -->
<button type="button" class="btn btn-primary mb-3" data-bs-toggle="modal" data-bs-target="#crearAtencionModal">
  Crear Atención con Texto No Estructurado
</button>

<!-- Modal para Ingreso de Texto No Estructurado -->
<div class="modal fade" id="crearAtencionModal" tabindex="-1" aria-labelledby="crearAtencionModalLabel"
  aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <form id="crearAtencionForm">
        <div class="modal-header">
          <h5 class="modal-title" id="crearAtencionModalLabel">Ingresar Detalles de la Atención</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
        </div>
        <div class="modal-body">
          {{ macros.render_form_field(form_procesar_texto.texto, attrs={'id': 'textoNoEstructurado', 'rows': 5,
          'placeholder': 'Ingrese el RUN, nombre y fecha de nacimiento'}) }}
          <div id="crearAtencionError" class="text-danger mt-2 d-none"></div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
          <button type="button" class="btn btn-primary" id="enviarTextoNoEstructurado">Enviar</button>
        </div>
      </form>
    </div>
  </div>
</div>

<table class="table table-bordered">
  <thead class="table-light">
    <tr>
      <th>Tiempo (hh:mm)</th>
      <th>RUN</th>
      <th>Nombre</th>
      <th>Edad</th>
      <th>Motivo</th>
      <th>Acciones</th>
    </tr>
  </thead>
  <tbody>
    {% for atencion in atenciones %}
    <tr>
      <td>{{ atencion.tiempo_desde_creacion }}</td>
      <td>{{ atencion.paciente.run }}</td>
      <td>{{ atencion.paciente.nombre or 'N/A' }}</td>
      <td>
        {% if atencion.paciente.edad %}
        {{ atencion.paciente.edad }} años
        {% else %}
        N/A
        {% endif %}
      </td>
      <td>
        <span data-bs-toggle="tooltip" title="{{ atencion.detalle }}">
          {{ atencion.obtener_sintesis(40) }}
        </span>
      </td>
      <td>
        <a href="{{ url_for('main.detalle_atencion', atencion_id=atencion.id) }}"
          class="btn btn-info btn-sm">Detalles</a>
        <!-- Botón para abrir el modal de selección de reporte -->
        <button type="button" class="btn btn-secondary btn-sm" data-bs-toggle="modal"
          data-bs-target="#seleccionarReporteModal" data-atencion-id="{{ atencion.id }}">
          Reporte
        </button>
        <form action="{{ url_for('main.cerrar_atencion', atencion_id=atencion.id) }}" method="POST"
          style="display:inline;">
          {{ form_cerrar.hidden_tag() }}
          {{ form_cerrar.submit(class="btn btn-danger btn-sm", onclick="return confirm('¿Está seguro de cerrar esta
          atención?');") }}
        </form>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
<!-- Modal de Selección de Tipo de Reporte -->
<div class="modal fade" id="seleccionarReporteModal" tabindex="-1" aria-labelledby="seleccionarReporteModalLabel"
  aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="seleccionarReporteModalLabel">Generar Reporte</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
      </div>
      <div class="modal-body">
        <p>Seleccione el tipo de reporte que desea generar:</p>
        <ul class="list-group">
          <li class="list-group-item">
            <a href="#" class="btn btn-link" data-report-type="alta_ambulatoria">Alta Ambulatoria</a>
          </li>
          <li class="list-group-item">
            <a href="#" class="btn btn-link" data-report-type="hospitalizacion">Hospitalización</a>
          </li>
          <li class="list-group-item">
            <a href="#" class="btn btn-link" data-report-type="interconsulta">Interconsulta</a>
          </li>
        </ul>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
      </div>
    </div>
  </div>
</div>

{% endblock %}


{% block scripts %}
<script>
  // Manejar el envío del formulario de Texto No Estructurado
  document.getElementById("enviarTextoNoEstructurado").addEventListener("click", function () {
    const texto = document.getElementById("textoNoEstructurado").value.trim();
    const errorDiv = document.getElementById("crearAtencionError");
    errorDiv.classList.add("d-none");
    errorDiv.textContent = "";

    if (!texto) {
      errorDiv.textContent = "El texto no puede estar vacío.";
      errorDiv.classList.remove("d-none");
      return;
    }

    fetch("{{ url_for('main.procesar_texto') }}", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": "{{ csrf_token() }}"
      },
      body: JSON.stringify({ texto })
    }).then(response => response.json().then(data => ({ status: response.status, body: data })))
      .then(result => {
        if (result.status === 200) {
          window.location.reload();
        } else {
          errorDiv.textContent = result.body.error || "Error al procesar el texto.";
          errorDiv.classList.remove("d-none");
        }
      })
      .catch(() => {
        errorDiv.textContent = "Error de comunicación con el servidor.";
        errorDiv.classList.remove("d-none");
      });
  });

  // Script para seleccionar el tipo de reporte y generar la URL
  let currentAtencionId = null;
  var seleccionarReporteModal = document.getElementById('seleccionarReporteModal');
  seleccionarReporteModal.addEventListener('show.bs.modal', function (event) {
    var button = event.relatedTarget;
    currentAtencionId = button.getAttribute('data-atencion-id');
  });

  var reportLinks = seleccionarReporteModal.querySelectorAll('[data-report-type]');
  reportLinks.forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      if (!currentAtencionId) {
        alert('Error: No se pudo obtener el ID de la atención.');
        return;
      }
      var tipoReporte = this.getAttribute('data-report-type');
      var url = "{{ url_for('main.generar_reporte', atencion_id='ATENCION_ID', tipo_reporte='TIPO_REPORTE') }}";
      url = url.replace('ATENCION_ID', currentAtencionId).replace('TIPO_REPORTE', tipoReporte);
      window.location.href = url;
    });
  });
</script>
{% endblock %}
```

### base.html

```html
<!doctype html>
<html lang="es">

<head>
  <meta charset="utf-8">
  <title>{% block title %}Urgentias{% endblock %}</title>
  {% import 'macros.html' as macros %}
  <!-- Bootstrap CSS -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <!-- Tu archivo CSS personalizado -->
  <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>

<body>
  <header class="py-2 bg-primary">
    <div class="container d-flex justify-content-between align-items-center">
      <h1 class="h3 mb-0 text-white">Urgentias</h1>
      <nav>
        <a class="me-3 text-white" href="{{ url_for('main.lista_atenciones') }}">Atenciones</a>
        {% if current_user.is_authenticated %}
        <span class="text-white">Bienvenido, {{ current_user.email }}</span>
        <a class="ms-3 text-white" href="{{ url_for('auth.logout') }}">Cerrar Sesión</a>
        {% else %}
        <a class="me-3 text-white" href="{{ url_for('auth.login') }}">Iniciar Sesión</a>
        <a class="text-white" href="{{ url_for('auth.register') }}">Registrarse</a>
        {% endif %}
      </nav>
    </div>
  </header>
  <main class="container my-4">
    {% with messages = get_flashed_messages(with_categories=true) %}
    {{ macros.render_alerts(messages) }}
    {% endwith %}
    {% block content %}{% endblock %}
  </main>
  <footer class="py-3 bg-primary">
    <div class="container text-center text-white">
      <p class="mb-0">&copy; 2024 Urgentias</p>
    </div>
  </footer>

  <!-- Bootstrap JS y sus dependencias -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

  {% block scripts %}
  <script>
    // Inicializar tooltips en todo el documento
    document.addEventListener('DOMContentLoaded', function () {
      var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
      var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
      })
    });
  </script>
  {% endblock %}
</body>

</html>
```

### detalle_atencion.html

```html
{% extends "base.html" %}
{% import 'macros.html' as macros %}

{% block title %}Detalle de Atención{% endblock %}

{% block content %}
<div class="container mt-4">
  <h2 class="mb-4">Atención Actual</h2>

  <div class="row mb-3">
    <div class="col-md-4"><strong>RUT:</strong> {{ paciente.run }}</div>
    <div class="col-md-4"><strong>Nombre:</strong> {{ paciente.nombre or 'N/A' }}</div>
    <div class="col-md-4"><strong>Edad:</strong>
      {% if paciente.edad %}
      {{ paciente.edad }} años
      {% else %}
      N/A
      {% endif %}
    </div>
  </div>

  <div class="row">
    <!-- Columna de Actualizar Historia Clínica -->
    <div class="col-md-6">
      <h4>Historia Clínica</h4>
      <form method="POST" action="{{ url_for('main.detalle_atencion', atencion_id=atencion.id) }}">
        {{ form_historia.hidden_tag() }}
        {{ macros.render_form_field(form_historia.historia, attrs={'rows': 10, 'id': 'historiaClinica'}) }}
        <div class="d-flex">
          {{ form_historia.submit(class="btn btn-primary me-2") }}
          <!-- Botón para abrir el modal de Historia en Bruto -->
          <button type="button" class="btn btn-secondary" data-bs-toggle="modal" data-bs-target="#historiaBrutoModal">
            Procesar
          </button>
        </div>
      </form>
    </div>

    <!-- Columna de Actualizar Detalle de Atención Actual -->
    <div class="col-md-6">
      <h4>Atención Actual</h4>
      <form method="POST" action="{{ url_for('main.detalle_atencion', atencion_id=atencion.id) }}">
        {{ form_detalle.hidden_tag() }}
        {{ macros.render_form_field(form_detalle.detalle, attrs={'rows': 10, 'id': 'detalleAtencion'}) }}
        <div class="d-flex">
          {{ form_detalle.submit(class="btn btn-primary me-2") }}
          <!-- Botón para abrir el modal de Detalle de Atención en Bruto -->
          <button type="button" class="btn btn-secondary" data-bs-toggle="modal" data-bs-target="#detalleBrutoModal">
            Procesar
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Secciones de Información Generada por AI -->
  <div class="row mt-4">
    <div class="col-md-6">
      <h4>Diagnóstico Diferencial</h4>
      <p>{{ atencion.diagnostico_diferencial or "Información no disponible" }}</p>
    </div>
    <div class="col-md-6">
      <h4>Manejo Sugerido</h4>
      <p>{{ atencion.manejo_sugerido or "Información no disponible" }}</p>
    </div>
  </div>
  <div class="row mt-4">
    <div class="col-md-6">
      <h4>Próxima Acción Más Importante</h4>
      <p class="text-highlight">{{ atencion.proxima_accion or "Información no disponible" }}</p>
    </div>
    <div class="col-md-6">
      <h4>Alertas de Amenazas o Riesgos</h4>
      <p class="text-danger">{{ atencion.alertas or "Información no disponible" }}</p>
    </div>
  </div>

  <!-- Modales -->
  <!-- Modal de Historia en Bruto -->
  <div class="modal fade" id="historiaBrutoModal" tabindex="-1" aria-labelledby="historiaBrutoModalLabel"
    aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <form method="POST" action="{{ url_for('main.procesar_historia_bruto_modal', atencion_id=atencion.id) }}">
          {{ form_procesar_historia.hidden_tag() }}
          <div class="modal-header">
            <h5 class="modal-title" id="historiaBrutoModalLabel">Procesar Historia en Bruto</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
          </div>
          <div class="modal-body">
            {{ macros.render_form_field(form_procesar_historia.historia_bruto, attrs={'id': 'historiaBruto', 'rows': 5})
            }}
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            {{ form_procesar_historia.submit(class="btn btn-primary") }}
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Modal de Detalle de Atención en Bruto -->
  <div class="modal fade" id="detalleBrutoModal" tabindex="-1" aria-labelledby="detalleBrutoModalLabel"
    aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <form method="POST" action="{{ url_for('main.procesar_detalle_bruto_modal', atencion_id=atencion.id) }}">
          {{ form_procesar_detalle.hidden_tag() }}
          <div class="modal-header">
            <h5 class="modal-title" id="detalleBrutoModalLabel">Procesar Detalle de Atención en Bruto</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
          </div>
          <div class="modal-body">
            {{ macros.render_form_field(form_procesar_detalle.detalle_bruto, attrs={'id': 'detalleBruto', 'rows': 5}) }}
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            {{ form_procesar_detalle.submit(class="btn btn-primary") }}
          </div>
        </form>
      </div>
    </div>
  </div>

</div>
{% endblock %}


{% block scripts %}
<script>
  // Manejar el envío del formulario de Texto No Estructurado
  document.getElementById("enviarTextoNoEstructurado").addEventListener("click", function () {
    const texto = document.getElementById("textoNoEstructurado").value.trim();
    const errorDiv = document.getElementById("crearAtencionError");
    errorDiv.style.display = "none";
    errorDiv.textContent = "";

    if (!texto) {
      errorDiv.textContent = "El texto no puede estar vacío.";
      errorDiv.style.display = "block";
      return;
    }

    fetch("{{ url_for('main.procesar_texto') }}", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": "{{ csrf_token() }}"
      },
      body: JSON.stringify({ texto })
    }).then(response => response.json().then(data => ({ status: response.status, body: data })))
      .then(result => {
        if (result.status === 200) {
          window.location.reload();
        } else {
          errorDiv.textContent = result.body.error || "Error al procesar el texto.";
          errorDiv.style.display = "block";
        }
      })
      .catch(() => {
        errorDiv.textContent = "Error de comunicación con el servidor.";
        errorDiv.style.display = "block";
      });
  });
</script>
{% endblock %}
```

### login.html

```html
{% extends "base.html" %}
{% import 'macros.html' as macros %}

{% block title %}Iniciar Sesión{% endblock %}

{% block content %}
<div class="container">
  <h2 class="mb-4">Iniciar Sesión</h2>
  <form method="POST" action="{{ url_for('auth.login') }}">
    {{ form.hidden_tag() }}
    {{ macros.render_form_field(form.email, attrs={'id': 'email'}) }}
    {{ macros.render_form_field(form.password, attrs={'id': 'password'}) }}
    {{ macros.render_form_checkbox(form.remember, attrs={'id': 'remember'}) }}
    <div>
      {{ form.submit(class="btn btn-primary") }}
    </div>
  </form>
  <p class="mt-3">¿No tienes una cuenta? <a href="{{ url_for('auth.register') }}">Regístrate aquí</a>.</p>
</div>
{% endblock %}
```

### macros.html

```html
{% macro render_form_field(field, attrs={}) %}
<div class="mb-3">
  {{ field.label(class="form-label") }}
  {{ field(class="form-control", **attrs) }}
  {% if field.errors %}
  {% for error in field.errors %}
  <div class="text-danger">{{ error }}</div>
  {% endfor %}
  {% endif %}
</div>
{% endmacro %}

{% macro render_form_checkbox(field, attrs={}) %}
<div class="mb-3 form-check">
  {{ field(class="form-check-input", **attrs) }}
  {{ field.label(class="form-check-label") }}
  {% if field.errors %}
  {% for error in field.errors %}
  <div class="text-danger">{{ error }}</div>
  {% endfor %}
  {% endif %}
</div>
{% endmacro %}

{% macro render_alerts(messages) %}
{% if messages %}
<div class="mt-3">
  {% for category, message in messages %}
  <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show"
    role="alert">
    {{ message }}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
  </div>
  {% endfor %}
</div>
{% endif %}
{% endmacro %}
```

### register.html

```html
{% extends "base.html" %}
{% import 'macros.html' as macros %}
{% block title %}Registrarse{% endblock %}

{% block content %}
<div class="container">
  <h2 class="mb-4">Registrarse</h2>
  <form method="POST" action="{{ url_for('auth.register') }}">
    {{ form.hidden_tag() }}
    {{ macros.render_form_field(form.email, attrs={'id': 'email'}) }}
    {{ macros.render_form_field(form.password, attrs={'id': 'password'}) }}
    {{ macros.render_form_field(form.confirm_password, attrs={'id': 'confirm_password'}) }}
    <div>
      {{ form.submit(class="btn btn-primary") }}
    </div>
  </form>
  <p class="mt-3">¿Ya tienes una cuenta? <a href="{{ url_for('auth.login') }}">Inicia sesión aquí</a>.</p>
</div>
{% endblock %}
```

### ver_reporte.html

```html
{% extends "base.html" %}
{% block title %}{{ titulo }}{% endblock %}

{% block content %}
<div class="container mt-4">
  <h2>{{ titulo }}</h2>

  <h3>Datos del Paciente</h3>
  <p><strong>Nombre:</strong> {{ atencion.paciente.nombre or 'N/A' }}</p>
  <p><strong>RUN:</strong> {{ atencion.paciente.run }}</p>
  <p><strong>Edad:</strong> {{ atencion.paciente.edad }} años</p>

  <h3>Reporte</h3>
  <p>{{ reporte | nl2br }}</p>

  <p>
    <a href="{{ url_for('main.lista_atenciones') }}" class="btn btn-primary">Volver a la Lista de Atenciones</a>
    <a href="{{ url_for('main.detalle_atencion', atencion_id=atencion.id) }}" class="btn btn-secondary">Volver a Detalle
      de Atención</a>
  </p>
</div>
{% endblock %}
```

### utils.py

```py
import os
import ell
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import logging

load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Definición de modelos de salida estructurados
class DiagnosticoDiferencial(BaseModel):
    diagnosticos: list[str] = Field(
        description="Lista de posibles diagnósticos diferenciales."
    )


class ManejoSugerido(BaseModel):
    manejo: str = Field(description="Recomendaciones de manejo clínico.")


class ProximaAccion(BaseModel):
    accion: str = Field(description="Próxima acción más importante a realizar.")


class Alertas(BaseModel):
    alertas: list[str] = Field(description="Lista de amenazas o riesgos identificados.")


# Funciones AI utilizando ell con mensajes estructurados
@ell.complex(model="gpt-4o-mini", response_format=DiagnosticoDiferencial)
def generar_diagnostico_diferencial(historia_paciente: str, detalle_atencion: str):
    """Eres un médico de emergencias experto en diagnóstico diferencial."""
    return [
        ell.user(
            f"""
Basándote en la siguiente información, proporciona una lista de posibles diagnósticos diferenciales:

Historia Clínica:
{historia_paciente}

Detalle de Atención:
{detalle_atencion}

Responde en formato JSON con el siguiente esquema:
{json.dumps(DiagnosticoDiferencial.model_json_schema(), indent=2)}
"""
        )
    ]


@ell.complex(model="gpt-4o-mini", response_format=ManejoSugerido)
def generar_manejo_sugerido(historia_paciente: str, detalle_atencion: str):
    """Eres un médico de emergencias experto en manejo clínico."""
    return [
        ell.user(
            f"""
Basándote en la siguiente información, proporciona recomendaciones de manejo alineadas con las guías actuales:

Historia Clínica:
{historia_paciente}

Detalle de Atención:
{detalle_atencion}

Responde en formato JSON con el siguiente esquema:
{json.dumps(ManejoSugerido.model_json_schema(), indent=2)}
"""
        )
    ]


@ell.complex(model="gpt-4o-mini", response_format=ProximaAccion)
def generar_proxima_accion(historia_paciente: str, detalle_atencion: str):
    """Eres un médico de emergencias priorizando acciones clínicas."""
    return [
        ell.user(
            f"""
Basándote en la siguiente información, indica la próxima acción más importante:

Historia Clínica:
{historia_paciente}

Detalle de Atención:
{detalle_atencion}

Responde en formato JSON con el siguiente esquema:
{json.dumps(ProximaAccion.model_json_schema(), indent=2)}
"""
        )
    ]


@ell.complex(model="gpt-4o-mini", response_format=Alertas)
def generar_alertas(historia_paciente: str, detalle_atencion: str):
    """Eres un médico de emergencias atento a posibles riesgos."""
    return [
        ell.user(
            f"""
Basándote en la siguiente información, proporciona una lista de posibles amenazas o riesgos:

Historia Clínica:
{historia_paciente}

Detalle de Atención:
{detalle_atencion}

Responde en formato JSON con el siguiente esquema:
{json.dumps(Alertas.model_json_schema(), indent=2)}
"""
        )
    ]


# Funciones auxiliares existentes
def load_prompt(filename):
    """Carga un prompt desde un archivo en el directorio prompts."""
    base_dir = os.path.dirname(__file__)
    prompt_path = os.path.join(base_dir, "prompts", filename)
    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()


@ell.complex(model="gpt-4o-mini")
def procesar_historia(historia_actual: str, texto_bruto: str):
    """Procesa la historia clínica actualizada."""
    prompt_template = load_prompt("procesar_historia.txt")
    prompt_content = prompt_template.format(
        historia_actual=historia_actual, texto_bruto=texto_bruto
    )
    return [ell.user(prompt_content)]


@ell.complex(model="gpt-4o-mini")
def procesar_detalle_atencion(
    historia_paciente: str, detalle_actual: str, texto_bruto: str
):
    """Procesa el detalle de atención del paciente."""
    prompt_template = load_prompt("procesar_detalle_atencion.txt")
    prompt_content = prompt_template.format(
        historia_paciente=historia_paciente,
        detalle_actual=detalle_actual,
        texto_bruto=texto_bruto,
    )
    return [ell.user(prompt_content)]


@ell.complex(model="gpt-4o-mini")
def procesar_texto_no_estructurado(texto_bruto: str):
    """Extrae información médica de texto no estructurado."""
    prompt_template = load_prompt("procesar_texto_no_estructurado.txt")
    prompt_content = prompt_template.format(texto_bruto=texto_bruto)
    return [ell.user(prompt_content)]


@ell.simple(model="gpt-4o-mini")
def generar_reporte_alta_ambulatoria(historia_paciente: str, detalle_atencion: str):
    """Genera un reporte de alta ambulatoria."""
    prompt = f"""
    Usted es un asistente médico que genera reportes de alta ambulatoria.

    Historia Clínica:
    {historia_paciente}

    Detalle de Atención:
    {detalle_atencion}

    Por favor, genere un reporte conciso y claro para el alta ambulatoria del paciente.
    """
    return prompt


@ell.simple(model="gpt-4o-mini")
def generar_reporte_hospitalizacion(historia_paciente: str, detalle_atencion: str):
    """Genera una solicitud de hospitalización."""
    prompt = f"""
    Usted es un asistente médico que genera solicitudes de hospitalización.

    Historia Clínica:
    {historia_paciente}

    Detalle de Atención:
    {detalle_atencion}

    Por favor, genere una solicitud de hospitalización detallada para el paciente.
    """
    return prompt


@ell.simple(model="gpt-4o-mini")
def generar_reporte_interconsulta(historia_paciente: str, detalle_atencion: str):
    """Genera un reporte de interconsulta a especialista."""
    prompt = f"""
    Usted es un asistente médico que genera reportes de interconsulta.

    Historia Clínica:
    {historia_paciente}

    Detalle de Atención:
    {detalle_atencion}

    Por favor, genere un reporte de interconsulta para derivar al paciente a un especialista.
    """
    return prompt
```

### config.py

```py
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, "..", ".env"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "..", "urgentias.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
```

### manage.py

```py
from flask.cli import FlaskGroup
from app import create_app, db

app = create_app()
cli = FlaskGroup(create_app=create_app)

if __name__ == "__main__":
    cli()
```

