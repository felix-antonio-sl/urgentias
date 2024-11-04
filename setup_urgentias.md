```bash
#!/bin/bash

# Script para configurar y ejecutar la aplicación Flask "Urgentias"

# Salir inmediatamente si un comando falla
set -e

# Crear directorio del proyecto
mkdir urgentias
cd urgentias

# Crear un entorno virtual
python3 -m venv venv

# Activar el entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Crear requirements.txt
cat << EOF > requirements.txt
alembic==1.13.3
anthropic==0.37.1
blinker==1.8.2
email_validator==2.2.0
ell-ai==0.0.14
Flask==3.0.3
Flask-Login==0.6.3
Flask-Migrate==4.0.7
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.2
greenlet==3.1.1
Jinja2==3.1.4
openai==1.53.0
psutil==5.9.8
python-dotenv==1.0.1
SQLAlchemy==2.0.36
WTForms==3.2.1
EOF

# Instalar dependencias
pip install -r requirements.txt

# Crear estructura del proyecto
mkdir -p app/static/css app/templates app/routes config

# Crear manage.py
cat << 'EOF' > manage.py
from flask.cli import FlaskGroup
from app import create_app, db

app = create_app()
cli = FlaskGroup(create_app=create_app)

if __name__ == '__main__':
    cli()
EOF

# Crear app/__init__.py
cat << 'EOF' > app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config.config import DevelopmentConfig
import logging
from logging.handlers import RotatingFileHandler
import os
import ell
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

from .models import User, Paciente, Atencion

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    ell.init(store='./logdir', verbose=True, autocommit=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from .routes.main import main as main_bp
    app.register_blueprint(main_bp)

    from .routes.auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    from .routes.main import register_error_handlers
    register_error_handlers(app)

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/urgentias.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Urgentias startup')

    return app
EOF

# Crear app/models.py
cat << 'EOF' > app/models.py
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
EOF

# Crear app/forms.py
cat << 'EOF' > app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class CrearAtencionForm(FlaskForm):
    run = StringField('RUN del Paciente', validators=[DataRequired(), Length(max=12)])
    submit = SubmitField('Crear Atención')

class ActualizarHistoriaForm(FlaskForm):
    historia = TextAreaField('Historia Clínica', validators=[DataRequired()])
    submit = SubmitField('Actualizar Historia')

class ActualizarDetalleForm(FlaskForm):
    detalle = TextAreaField('Detalle de Atención Actual', validators=[DataRequired()])
    submit = SubmitField('Actualizar Atención Actual')

class ProcesarHistoriaBrutoForm(FlaskForm):
    historia_bruto = TextAreaField('Historia en Bruto', validators=[DataRequired()])
    submit = SubmitField('Procesar Historia en Bruto')

class ProcesarDetalleBrutoForm(FlaskForm):
    detalle_bruto = TextAreaField('Detalle de Atención en Bruto', validators=[DataRequired()])
    submit = SubmitField('Procesar Atención Actual en Bruto')

class LoginForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')
EOF

# Crear app/utils.py
cat << 'EOF' > app/utils.py
import ell
import os
from dotenv import load_dotenv

load_dotenv()

@ell.complex(model="gpt-4o-mini")
def procesar_historia(historia_actual: str, texto_bruto: str) -> str:
    return f"""
Historia actual:
{historia_actual}

Nuevo texto en bruto:
{texto_bruto}

Por favor, genera una historia clínica actualizada y coherente.
"""

@ell.complex(model="gpt-4o-mini")
def procesar_detalle_atencion(historia_paciente: str, detalle_actual: str, texto_bruto: str) -> str:
    return f"""
Historia del paciente:
{historia_paciente}

Detalle actual de la atención:
{detalle_actual}

Nuevo texto en bruto:
{texto_bruto}

Por favor, genera un detalle de atención actualizado y coherente.
"""
EOF

# Crear app/static/css/styles.css
mkdir -p app/static/css
cat << 'EOF' > app/static/css/styles.css
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
}

header {
    background-color: #4CAF50;
    padding: 10px 20px;
    color: white;
}

header h1 {
    margin: 0;
    display: inline-block;
}

nav {
    display: inline-block;
    float: right;
}

nav a {
    color: white;
    margin-left: 15px;
    text-decoration: none;
}

nav a:hover {
    text-decoration: underline;
}

main {
    padding: 20px;
}

footer {
    background-color: #f1f1f1;
    padding: 10px 20px;
    text-align: center;
}

.flashes {
    list-style-type: none;
    padding: 0;
}

.flashes li {
    padding: 10px;
    margin-bottom: 10px;
}

.flashes .success {
    background-color: #d4edda;
    color: #155724;
}

.flashes .error {
    background-color: #f8d7da;
    color: #721c24;
}

.flashes .warning {
    background-color: #fff3cd;
    color: #856404;
}

form div {
    margin-bottom: 10px;
}

form input[type="text"],
form input[type="password"],
form textarea {
    width: 100%;
    padding: 8px;
    box-sizing: border-box;
}

form input[type="submit"] {
    padding: 10px 20px;
    background-color: #4CAF50;
    border: none;
    color: white;
    cursor: pointer;
}

form input[type="submit"]:hover {
    background-color: #45a049;
}
EOF

# Crear app/templates/base.html
mkdir -p app/templates
cat << 'EOF' > app/templates/base.html
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>{% block title %}Urgentias{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>
<body>
    <header>
        <h1>Urgentias</h1>
        <nav>
            <a href="{{ url_for('main.lista_atenciones') }}">Atenciones</a>
            {% if current_user.is_authenticated %}
                <a href="{{ url_for('main.crear_atencion') }}">Crear Atención</a>
                <span>Bienvenido, {{ current_user.email }}</span>
                <a href="{{ url_for('auth.logout') }}">Cerrar Sesión</a>
            {% else %}
                <a href="{{ url_for('auth.login') }}">Iniciar Sesión</a>
                <a href="{{ url_for('auth.register') }}">Registrarse</a>
            {% endif %}
        </nav>
    </header>
    <main>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <ul class="flashes">
              {% for category, message in messages %}
                <li class="{{ category }}">{{ message }}</li>
              {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </main>
    <footer>
        <p>&copy; 2024 Urgentias</p>
    </footer>
</body>
</html>
EOF

# Crear app/templates/crear_atencion.html
cat << 'EOF' > app/templates/crear_atencion.html
{% extends "base.html" %}
{% block title %}Crear Nueva Atención{% endblock %}
{% block content %}
<h2>Crear Nueva Atención</h2>
<form method="post" action="{{ url_for('main.crear_atencion') }}">
    {{ form.hidden_tag() }}
    <div>
        {{ form.run.label }}<br>
        {{ form.run(size=32) }}<br>
        {% for error in form.run.errors %}
            <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </div>
    <br>
    <div>
        {{ form.submit() }}
    </div>
</form>
{% endblock %}
EOF

# Crear app/templates/atenciones.html
cat << 'EOF' > app/templates/atenciones.html
{% extends "base.html" %}
{% block title %}Lista de Atenciones{% endblock %}
{% block content %}
<h2>Lista de Atenciones</h2>
<table border="1" cellpadding="5" cellspacing="0">
    <thead>
        <tr>
            <th>ID</th>
            <th>Paciente RUN</th>
            <th>Creado En</th>
            <th>Acciones</th>
        </tr>
    </thead>
    <tbody>
        {% for atencion in atenciones %}
        <tr>
            <td>{{ atencion.id }}</td>
            <td>{{ atencion.paciente.run }}</td>
            <td>{{ atencion.creado_en }}</td>
            <td><a href="{{ url_for('main.detalle_atencion', atencion_id=atencion.id) }}">Ver Detalle</a></td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
EOF

# Crear app/templates/login.html
cat << 'EOF' > app/templates/login.html
{% extends "base.html" %}

{% block title %}Iniciar Sesión{% endblock %}

{% block content %}
<h2>Iniciar Sesión</h2>
<form method="POST" action="{{ url_for('auth.login') }}">
    {{ form.hidden_tag() }}
    <div>
        {{ form.email.label }}<br>
        {{ form.email(size=32) }}<br>
        {% for error in form.email.errors %}
            <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </div>
    <div>
        {{ form.password.label }}<br>
        {{ form.password(size=32) }}<br>
        {% for error in form.password.errors %}
            <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </div>
    <div>
        {{ form.remember() }} {{ form.remember.label }}
    </div>
    <div>
        {{ form.submit() }}
    </div>
</form>
<p>¿No tienes una cuenta? <a href="{{ url_for('auth.register') }}">Regístrate aquí</a>.</p>
{% endblock %}
EOF

# Crear app/templates/register.html
cat << 'EOF' > app/templates/register.html
{% extends "base.html" %}

{% block title %}Registrarse{% endblock %}

{% block content %}
<h2>Registrarse</h2>
<form method="POST" action="{{ url_for('auth.register') }}">
    {{ form.hidden_tag() }}
    <div>
        {{ form.email.label }}<br>
        {{ form.email(size=32) }}<br>
        {% for error in form.email.errors %}
            <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </div>
    <div>
        {{ form.password.label }}<br>
        {{ form.password(size=32) }}<br>
        {% for error in form.password.errors %}
            <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </div>
    <div>
        {{ form.confirm_password.label }}<br>
        {{ form.confirm_password(size=32) }}<br>
        {% for error in form.confirm_password.errors %}
            <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </div>
    <div>
        {{ form.submit() }}
    </div>
</form>
<p>¿Ya tienes una cuenta? <a href="{{ url_for('auth.login') }}">Inicia sesión aquí</a>.</p>
{% endblock %}
EOF

# Crear app/templates/detalle_atencion.html
cat << 'EOF' > app/templates/detalle_atencion.html
{% extends "base.html" %}

{% block title %}Detalle de Atención{% endblock %}

{% block content %}
<h2>Detalle de Atención</h2>

<h3>Paciente: {{ paciente.run }}</h3>

<!-- Formulario para actualizar la Historia Clínica -->
<h4>Actualizar Historia Clínica</h4>
<form method="POST" action="{{ url_for('main.detalle_atencion', atencion_id=atencion.id) }}">
    {{ form_historia.hidden_tag() }}
    <div>
        {{ form_historia.historia.label }}<br>
        {{ form_historia.historia(rows=5) }}<br>
        {% for error in form_historia.historia.errors %}
            <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </div>
    <div>
        {{ form_historia.submit() }}
    </div>
</form>

<hr>

<!-- Formulario para actualizar el Detalle de Atención Actual -->
<h4>Actualizar Detalle de Atención Actual</h4>
<form method="POST" action="{{ url_for('main.detalle_atencion', atencion_id=atencion.id) }}">
    {{ form_detalle.hidden_tag() }}
    <div>
        {{ form_detalle.detalle.label }}<br>
        {{ form_detalle.detalle(rows=5) }}<br>
        {% for error in form_detalle.detalle.errors %}
            <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </div>
    <div>
        {{ form_detalle.submit() }}
    </div>
</form>

<hr>

<!-- Formulario para procesar Historia en Bruto -->
<h4>Procesar Historia en Bruto</h4>
<form method="POST" action="{{ url_for('main.detalle_atencion', atencion_id=atencion.id) }}">
    {{ form_procesar_historia.hidden_tag() }}
    <div>
        {{ form_procesar_historia.historia_bruto.label }}<br>
        {{ form_procesar_historia.historia_bruto(rows=5) }}<br>
        {% for error in form_procesar_historia.historia_bruto.errors %}
            <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </div>
    <div>
        {{ form_procesar_historia.submit() }}
    </div>
</form>

<hr>

<!-- Formulario para procesar Detalle de Atención en Bruto -->
<h4>Procesar Detalle de Atención en Bruto</h4>
<form method="POST" action="{{ url_for('main.detalle_atencion', atencion_id=atencion.id) }}">
    {{ form_procesar_detalle.hidden_tag() }}
    <div>
        {{ form_procesar_detalle.detalle_bruto.label }}<br>
        {{ form_procesar_detalle.detalle_bruto(rows=5) }}<br>
        {% for error in form_procesar_detalle.detalle_bruto.errors %}
            <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </div>
    <div>
        {{ form_procesar_detalle.submit() }}
    </div>
</form>

{% endblock %}
EOF

# Crear app/templates/404.html
cat << 'EOF' > app/templates/404.html
{% extends "base.html" %}

{% block title %}Página No Encontrada{% endblock %}

{% block content %}
<h2>404 - Página No Encontrada</h2>
<p>Lo sentimos, la página que buscas no existe.</p>
<a href="{{ url_for('main.lista_atenciones') }}">Volver al inicio</a>
{% endblock %}
EOF

# Crear app/templates/500.html
cat << 'EOF' > app/templates/500.html
{% extends "base.html" %}

{% block title %}Error Interno del Servidor{% endblock %}

{% block content %}
<h2>¡Vaya! Algo salió mal.</h2>
<p>Estamos trabajando para solucionar este problema. Por favor, inténtalo de nuevo más tarde.</p>
{% endblock %}
EOF

# Crear app/routes/__init__.py
touch app/routes/__init__.py

# Crear app/routes/main.py
cat << 'EOF' > app/routes/main.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from .. import db
from ..models import Paciente, Atencion
from ..utils import procesar_historia, procesar_detalle_atencion
from ..forms import (
    CrearAtencionForm,
    ActualizarHistoriaForm,
    ActualizarDetalleForm,
    ProcesarHistoriaBrutoForm,
    ProcesarDetalleBrutoForm
)
from flask_login import login_required

main = Blueprint('main', __name__)

@main.route('/')
def lista_atenciones():
    atenciones = Atencion.query.order_by(Atencion.creado_en.desc()).all()
    return render_template('atenciones.html', atenciones=atenciones)

@main.route('/crear_atencion', methods=['GET', 'POST'])
@login_required
def crear_atencion():
    form = CrearAtencionForm()
    if form.validate_on_submit():
        run = form.run.data
        paciente = Paciente.query.filter_by(run=run).first()
        if not paciente:
            paciente = Paciente(run=run)
            db.session.add(paciente)
            db.session.commit()
        atencion = Atencion(paciente_id=paciente.id)
        db.session.add(atencion)
        db.session.commit()
        flash('Atención creada exitosamente.', 'success')
        return redirect(url_for('main.lista_atenciones'))
    return render_template('crear_atencion.html', form=form)

@main.route('/detalle_atencion/<string:atencion_id>', methods=['GET', 'POST'])
@login_required
def detalle_atencion(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    form_historia = ActualizarHistoriaForm(prefix='historia')
    form_detalle = ActualizarDetalleForm(prefix='detalle')
    form_procesar_historia = ProcesarHistoriaBrutoForm(prefix='procesar_historia')
    form_procesar_detalle = ProcesarDetalleBrutoForm(prefix='procesar_detalle')

    if form_historia.validate_on_submit() and form_historia.submit.data:
        paciente.historia = form_historia.historia.data
        db.session.commit()
        flash('Historia actualizada correctamente.', 'success')
        return redirect(url_for('main.detalle_atencion', atencion_id=atencion_id))
    elif form_detalle.validate_on_submit() and form_detalle.submit.data:
        atencion.detalle = form_detalle.detalle.data
        db.session.commit()
        flash('Detalle de atención actualizado correctamente.', 'success')
        return redirect(url_for('main.detalle_atencion', atencion_id=atencion_id))
    elif form_procesar_historia.validate_on_submit() and form_procesar_historia.submit.data:
        texto_bruto = form_procesar_historia.historia_bruto.data
        historia_actualizada = procesar_historia(paciente.historia or '', texto_bruto)
        paciente.historia = historia_actualizada.text
        db.session.commit()
        flash('Historia procesada y actualizada.', 'success')
        return redirect(url_for('main.detalle_atencion', atencion_id=atencion_id))
    elif form_procesar_detalle.validate_on_submit() and form_procesar_detalle.submit.data:
        texto_bruto = form_procesar_detalle.detalle_bruto.data
        detalle_actualizado = procesar_detalle_atencion(
            paciente.historia or '', atencion.detalle or '', texto_bruto)
        atencion.detalle = detalle_actualizado.text
        db.session.commit()
        flash('Detalle de atención procesado y actualizado.', 'success')
        return redirect(url_for('main.detalle_atencion', atencion_id=atencion_id))

    if request.method == 'GET':
        form_historia.historia.data = paciente.historia
        form_detalle.detalle.data = atencion.detalle

    return render_template(
        'detalle_atencion.html',
        atencion=atencion,
        paciente=paciente,
        form_historia=form_historia,
        form_detalle=form_detalle,
        form_procesar_historia=form_procesar_historia,
        form_procesar_detalle=form_procesar_detalle
    )

def register_error_handlers(app):
    from flask import render_template

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403
EOF

# Crear app/routes/auth.py
cat << 'EOF' > app/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from ..forms import LoginForm, RegisterForm
from ..models import User
from .. import db
from flask_login import login_user, logout_user, current_user, login_required

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Inicio de sesión exitoso.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.lista_atenciones'))
        else:
            flash('Correo o contraseña incorrectos.', 'error')
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('El correo electrónico ya está registrado.', 'error')
        else:
            user = User(email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registro exitoso. Puedes iniciar sesión ahora.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('main.lista_atenciones'))
EOF

# Crear config/config.py
mkdir -p config
cat << 'EOF' > config/config.py
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, '..', 'urgentias.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    SENTRY_DSN = os.getenv('SENTRY_DSN')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
EOF

# Crear .env
cat << 'EOF' > .env
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
DATABASE_URL=sqlite:///urgentias.db
EOF

# Inicializar la base de datos
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

echo "Configuración completa. Ahora puedes ejecutar la aplicación con: flask run --host=0.0.0.0"
````

---

## Integración de Gunicorn y Nginx en la Aplicación Flask “Urgentias”

### Arquitectura del Despliegue

#### Componentes Principales

 • Flask: Framework web ligero para Python, utilizado para desarrollar la lógica de la aplicación “Urgentias”.
 • Gunicorn: Servidor WSGI de Python, encargado de ejecutar la aplicación Flask y gestionar múltiples procesos de trabajo para manejar solicitudes concurrentes.
 • Nginx: Servidor web de alto rendimiento y proxy inverso, utilizado para manejar solicitudes HTTP/HTTPS, servir contenido estático y gestionar la terminación SSL.
 • Certbot (Let’s Encrypt): Herramienta para la obtención y renovación automática de certificados SSL gratuitos.

###  Diagrama de Arquitectura

Cliente (Navegador)
        |
        | HTTPS (puerto 443)
        v
      Nginx
        |
        | Proxy Pass (Socket Unix)
        v
     Gunicorn
        |
        | WSGI
        v
Aplicación Flask "Urgentias"

### Implementación Detallada

### Configuración del Entorno Virtual

Para aislar las dependencias de la aplicación y asegurar un entorno limpio, se utilizó un entorno virtual creado con virtualenv.

python3 -m venv /home/fx/urgentias/venv
source /home/fx/urgentias/venv/bin/activate
pip install --upgrade pip setuptools
pip install gunicorn
deactivate

### Configuración de Gunicorn

#### Archivo de Servicio de Systemd

Se creó un archivo de servicio para gestionar Gunicorn como un servicio de sistema, lo que permite su inicio automático al arrancar el servidor y su reinicio en caso de fallos.

Ruta: /etc/systemd/system/urgentias.service

[Unit]
Description=Gunicorn instance to serve urgentias
After=network.target

[Service]
User=fx
Group=www-data
WorkingDirectory=/home/fx/urgentias
Environment="PATH=/home/fx/urgentias/venv/bin"
ExecStart=/home/fx/urgentias/venv/bin/gunicorn --workers 3 --bind unix:/home/fx/urgentias/urgentias.sock manage:app

[Install]
WantedBy=multi-user.target

Explicación de Parámetros:

 • User y Group: Ejecutar Gunicorn bajo el usuario fx y el grupo www-data para mejorar la seguridad.
 • WorkingDirectory: Directorio raíz de la aplicación Flask.
 • Environment: Ruta al entorno virtual para asegurar que Gunicorn utiliza las dependencias correctas.
 • ExecStart: Comando para iniciar Gunicorn, especificando el número de trabajadores y el socket Unix para la comunicación con Nginx.

#### Gestión del Servicio

sudo systemctl daemon-reload
sudo systemctl start urgentias
sudo systemctl enable urgentias
sudo systemctl status urgentias

### Configuración de Nginx como Proxy Inverso

#### Archivo de Configuración de Nginx

Se creó un archivo de configuración específico para la aplicación “Urgentias”, definiendo cómo Nginx manejará las solicitudes entrantes y las direccionará a Gunicorn.

Ruta: /etc/nginx/sites-available/urgentias

server {
    listen 80;
    server_name urgentias.com <www.urgentias.com>;

    location /static/ {
        alias /home/fx/urgentias/app/static/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/fx/urgentias/urgentias.sock;
    }
}

#### Habilitación del Sitio en Nginx

sudo ln -s /etc/nginx/sites-available/urgentias /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

### Implementación de Certificados SSL con Certbot

Para asegurar la comunicación entre los clientes y el servidor, se implementaron certificados SSL utilizando Certbot y Let’s Encrypt.

#### Instalación de Certbot

sudo apt update
sudo apt install -y certbot python3-certbot-nginx

#### Obtención y Configuración Automática de Certificados

sudo certbot --nginx -d urgentias.com -d <www.urgentias.com> --non-interactive --agree-tos -m <felixsanhueza@me.com>

#### Renovación Automática de Certificados

Certbot configura automáticamente tareas de renovación. Se verificó la correcta configuración mediante una simulación:

sudo certbot renew --dry-run
