# Estructura y código del proyecto urgentias

## Árbol del proyecto

            - urgentias/
                - manage.py
                - requirements.txt
                - app/
                    - utils.py
                    - models.py
                    - forms.py
                    - __init__.py
                    - static/
                        - css/
                            - styles.css
                    - templates/
                        - 404.html
                        - atenciones.html
                        - login.html
                        - register.html
                        - 500.html
                        - base.html
                        - crear_atencion.html
                        - detalle_atencion.html
                    - routes/
                        - auth.py
                        - main.py
                        - __init__.py
                - config/
                    - config.py


## Archivos y su contenido

### manage.py

```
from flask.cli import FlaskGroup
from app import create_app, db

app = create_app()
cli = FlaskGroup(create_app=create_app)

if __name__ == '__main__':
    cli()

```

---

### requirements.txt

```
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
gunicorn
Jinja2==3.1.4
openai==1.53.0
psutil==5.9.8
python-dotenv==1.0.1
SQLAlchemy==2.0.36
WTForms==3.2.1

```

---

### app/utils.py

```
import ell
import os
from dotenv import load_dotenv

load_dotenv()

@ell.complex(model="gpt-4o")
def procesar_historia(historia_actual: str, texto_bruto: str) -> str:
    return f"""
Historia actual:
{historia_actual}

Nuevo texto en bruto:
{texto_bruto}

Por favor, genera una historia clínica actualizada y coherente.
"""

@ell.complex(model="gpt-4o")
def procesar_detalle_atencion(historia_paciente: str, detalle_actual: str, texto_bruto: str) -> str:
    return f"""
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

Presente su registro incremental dentro de etiquetas <registro_atencion>.
"""

```

---

### app/models.py

```
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

```

---

### app/forms.py

```
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

```

---

### app/__init__.py

```
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

```

---

### app/static/css/styles.css

```
/* Estilos personalizados para Urgentias */

/* Variables de colores */
:root {
    --primary-color: #00B2A9;  /* Teal */
    --secondary-color: #4B0082; /* Indigo */
    --accent-color: #FFD700;    /* Gold */
    --text-color: #000000;      /* Black */
    --background-color: #FFFFFF;/* White */
    --highlight-color: #C71585; /* Medium Violet Red */
}

/* Aplicar el fondo blanco */
body {
    background-color: var(--background-color);
    color: var(--text-color);
}

/* Estilos del encabezado */
header {
    background-color: var(--primary-color);
}

header h1 {
    color: var(--background-color);
}

header nav a {
    color: var(--background-color);
}

header nav a:hover {
    color: var(--accent-color);
}

/* Estilos de botones */
.btn-primary {
    background-color: var(--secondary-color);
    border-color: var(--secondary-color);
}

.btn-primary:hover {
    background-color: var(--highlight-color);
    border-color: var(--highlight-color);
}

.btn-secondary {
    background-color: var(--accent-color);
    border-color: var(--accent-color);
    color: var(--text-color);
}

.btn-secondary:hover {
    background-color: var(--highlight-color);
    border-color: var(--highlight-color);
    color: var(--background-color);
}

/* Estilos de enlaces */
a {
    color: var(--secondary-color);
}

a:hover {
    color: var(--highlight-color);
}

/* Estilos de pie de página */
footer {
    background-color: var(--primary-color);
    color: var(--background-color);
}

/* Estilos de tablas */
.table thead {
    background-color: var(--primary-color);
    color: var(--background-color);
}

.table tbody tr:hover {
    background-color: var(--accent-color);
}

/* Estilos de formularios */
.form-label {
    color: var(--text-color);
}

.form-control {
    border-color: var(--secondary-color);
}

.form-control:focus {
    border-color: var(--highlight-color);
    box-shadow: 0 0 0 0.2rem rgba(199, 21, 133, 0.25);
}

/* Estilos de alertas */
.alert-success {
    background-color: var(--accent-color);
    color: var(--text-color);
    border-color: var(--accent-color);
}

.alert-danger {
    background-color: var(--highlight-color);
    color: var(--background-color);
    border-color: var(--highlight-color);
}

/* Estilos de modales */
.modal-content {
    background-color: var(--background-color);
    color: var(--text-color);
}

.modal-header {
    border-bottom-color: var(--secondary-color);
}

.modal-footer {
    border-top-color: var(--secondary-color);
}
```

---

### app/templates/404.html

```
{% extends "base.html" %}

{% block title %}Página No Encontrada{% endblock %}

{% block content %}
<h2>404 - Página No Encontrada</h2>
<p>Lo sentimos, la página que buscas no existe.</p>
<a href="{{ url_for('main.lista_atenciones') }}">Volver al inicio</a>
{% endblock %}

```

---

### app/templates/atenciones.html

```
{% extends "base.html" %}
{% block title %}Lista de Atenciones{% endblock %}
{% block content %}
<h2>Lista de Atenciones</h2>
<table class="table table-bordered">
    <thead class="thead-light">
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
```

---

### app/templates/login.html

```
{% extends "base.html" %}

{% block title %}Iniciar Sesión{% endblock %}

{% block content %}
<div class="container">
    <h2>Iniciar Sesión</h2>
    <form method="POST" action="{{ url_for('auth.login') }}">
        {{ form.hidden_tag() }}
        <div class="mb-3">
            {{ form.email.label(class="form-label") }}
            {{ form.email(class="form-control") }}
            {% for error in form.email.errors %}
                <div class="text-danger">[{{ error }}]</div>
            {% endfor %}
        </div>
        <div class="mb-3">
            {{ form.password.label(class="form-label") }}
            {{ form.password(class="form-control") }}
            {% for error in form.password.errors %}
                <div class="text-danger">[{{ error }}]</div>
            {% endfor %}
        </div>
        <div class="mb-3 form-check">
            {{ form.remember(class="form-check-input") }}
            {{ form.remember.label(class="form-check-label") }}
        </div>
        <div>
            {{ form.submit(class="btn btn-primary") }}
        </div>
    </form>
    <p class="mt-3">¿No tienes una cuenta? <a href="{{ url_for('auth.register') }}">Regístrate aquí</a>.</p>
</div>
{% endblock %}
```

---

### app/templates/register.html

```
{% extends "base.html" %}

{% block title %}Registrarse{% endblock %}

{% block content %}
<div class="container">
    <h2>Registrarse</h2>
    <form method="POST" action="{{ url_for('auth.register') }}">
        {{ form.hidden_tag() }}
        <div class="mb-3">
            {{ form.email.label(class="form-label") }}
            {{ form.email(class="form-control") }}
            {% for error in form.email.errors %}
                <div class="text-danger">[{{ error }}]</div>
            {% endfor %}
        </div>
        <div class="mb-3">
            {{ form.password.label(class="form-label") }}
            {{ form.password(class="form-control") }}
            {% for error in form.password.errors %}
                <div class="text-danger">[{{ error }}]</div>
            {% endfor %}
        </div>
        <div class="mb-3">
            {{ form.confirm_password.label(class="form-label") }}
            {{ form.confirm_password(class="form-control") }}
            {% for error in form.confirm_password.errors %}
                <div class="text-danger">[{{ error }}]</div>
            {% endfor %}
        </div>
        <div>
            {{ form.submit(class="btn btn-primary") }}
        </div>
    </form>
    <p class="mt-3">¿Ya tienes una cuenta? <a href="{{ url_for('auth.login') }}">Inicia sesión aquí</a>.</p>
</div>
{% endblock %}
```

---

### app/templates/500.html

```
{% extends "base.html" %}

{% block title %}Error Interno del Servidor{% endblock %}

{% block content %}
<h2>¡Vaya! Algo salió mal.</h2>
<p>Estamos trabajando para solucionar este problema. Por favor, inténtalo de nuevo más tarde.</p>
{% endblock %}

```

---

### app/templates/base.html

```
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>{% block title %}Urgentias{% endblock %}</title>
    <!-- Bootstrap CSS -->
    <!-- Utilizando Bootstrap 5 -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <!-- Tu archivo CSS personalizado -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>
<body>
    <header class="py-2">
        <div class="container d-flex justify-content-between align-items-center">
            <h1 class="h3 mb-0">Urgentias</h1>
            <nav>
                <a class="me-3" href="{{ url_for('main.lista_atenciones') }}">Atenciones</a>
                {% if current_user.is_authenticated %}
                    <a class="me-3" href="{{ url_for('main.crear_atencion') }}">Crear Atención</a>
                    <span>Bienvenido, {{ current_user.email }}</span>
                    <a class="ms-3" href="{{ url_for('auth.logout') }}">Cerrar Sesión</a>
                {% else %}
                    <a class="me-3" href="{{ url_for('auth.login') }}">Iniciar Sesión</a>
                    <a href="{{ url_for('auth.register') }}">Registrarse</a>
                {% endif %}
            </nav>
        </div>
    </header>
    <main class="container my-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <div class="mt-3">
              {% for category, message in messages %}
                <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show" role="alert">
                  {{ message }}
                  <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
                </div>
              {% endfor %}
            </div>
          {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </main>
    <footer class="py-3">
        <div class="container text-center">
            <p class="mb-0">&copy; 2024 Urgentias</p>
        </div>
    </footer>
    
    <!-- Bootstrap JS y sus dependencias -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

---

### app/templates/crear_atencion.html

```
{% extends "base.html" %}
{% block title %}Crear Nueva Atención{% endblock %}
{% block content %}
<div class="container">
    <h2>Crear Nueva Atención</h2>
    <form method="post" action="{{ url_for('main.crear_atencion') }}">
        {{ form.hidden_tag() }}
        <div class="mb-3">
            {{ form.run.label(class="form-label") }}
            {{ form.run(class="form-control") }}
            {% for error in form.run.errors %}
                <div class="text-danger">[{{ error }}]</div>
            {% endfor %}
        </div>
        <div>
            {{ form.submit(class="btn btn-primary") }}
        </div>
    </form>
</div>
{% endblock %}
```

---

### app/templates/detalle_atencion.html

```
{% extends "base.html" %}

{% block title %}Detalle de Atención{% endblock %}

{% block content %}
<div class="container mt-4">
    <h2>Detalle de Atención</h2>

    <h3>Paciente: {{ paciente.run }}</h3>

    <div class="row">
        <!-- Columna de Actualizar Historia Clínica -->
        <div class="col-md-6">
            <h4>Actualizar Historia Clínica</h4>
            <form method="POST" action="{{ url_for('main.detalle_atencion', atencion_id=atencion.id) }}">
                {{ form_historia.hidden_tag() }}
                <div class="mb-3">
                    {{ form_historia.historia.label(class="form-label") }}
                    {{ form_historia.historia(class="form-control", rows=10) }}
                    {% for error in form_historia.historia.errors %}
                        <div class="text-danger">[{{ error }}]</div>
                    {% endfor %}
                </div>
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
            <h4>Actualizar Detalle de Atención Actual</h4>
            <form method="POST" action="{{ url_for('main.detalle_atencion', atencion_id=atencion.id) }}">
                {{ form_detalle.hidden_tag() }}
                <div class="mb-3">
                    {{ form_detalle.detalle.label(class="form-label") }}
                    {{ form_detalle.detalle(class="form-control", rows=10) }}
                    {% for error in form_detalle.detalle.errors %}
                        <div class="text-danger">[{{ error }}]</div>
                    {% endfor %}
                </div>
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

    <!-- Modales -->
    <!-- Modal de Historia en Bruto -->
    <div class="modal fade" id="historiaBrutoModal" tabindex="-1" aria-labelledby="historiaBrutoModalLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <form method="POST" action="{{ url_for('main.procesar_historia_bruto_modal', atencion_id=atencion.id) }}">
            {{ form_procesar_historia.hidden_tag() }}
            <div class="modal-header">
              <h5 class="modal-title" id="historiaBrutoModalLabel">Procesar Historia en Bruto</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                {{ form_procesar_historia.historia_bruto.label(class="form-label") }}
                {{ form_procesar_historia.historia_bruto(class="form-control", rows=5) }}
                {% for error in form_procesar_historia.historia_bruto.errors %}
                    <div class="text-danger">[{{ error }}]</div>
                {% endfor %}
              </div>
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
    <div class="modal fade" id="detalleBrutoModal" tabindex="-1" aria-labelledby="detalleBrutoModalLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <form method="POST" action="{{ url_for('main.procesar_detalle_bruto_modal', atencion_id=atencion.id) }}">
            {{ form_procesar_detalle.hidden_tag() }}
            <div class="modal-header">
              <h5 class="modal-title" id="detalleBrutoModalLabel">Procesar Detalle de Atención en Bruto</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                {{ form_procesar_detalle.detalle_bruto.label(class="form-label") }}
                {{ form_procesar_detalle.detalle_bruto(class="form-control", rows=5) }}
                {% for error in form_procesar_detalle.detalle_bruto.errors %}
                    <div class="text-danger">[{{ error }}]</div>
                {% endfor %}
              </div>
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
    // Como estamos usando Bootstrap 5, necesitamos ajustar el código JavaScript
    document.addEventListener('DOMContentLoaded', function() {
        // Indicador de carga para el modal de Historia en Bruto
        const historiaBrutoForm = document.querySelector('#historiaBrutoModal form');
        historiaBrutoForm.addEventListener('submit', function() {
            const modal = bootstrap.Modal.getInstance(document.querySelector('#historiaBrutoModal'));
            modal._element.querySelectorAll('button').forEach(button => button.disabled = true);
            modal._element.querySelector('.modal-footer .btn-primary').textContent = 'Procesando...';
        });

        // Indicador de carga para el modal de Detalle de Atención en Bruto
        const detalleBrutoForm = document.querySelector('#detalleBrutoModal form');
        detalleBrutoForm.addEventListener('submit', function() {
            const modal = bootstrap.Modal.getInstance(document.querySelector('#detalleBrutoModal'));
            modal._element.querySelectorAll('button').forEach(button => button.disabled = true);
            modal._element.querySelector('.modal-footer .btn-primary').textContent = 'Procesando...';
        });
    });
</script>
{% endblock %}
```

---

### app/routes/auth.py

```
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

```

---

### app/routes/main.py

```
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
from flask_login import login_required, current_user

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
    form_procesar_historia = ProcesarHistoriaBrutoForm(prefix='procesar_historia_modal')
    form_procesar_detalle = ProcesarDetalleBrutoForm(prefix='procesar_detalle_modal')

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

# Nuevas rutas para manejar el procesamiento desde los modales

@main.route('/procesar_historia_bruto_modal/<string:atencion_id>', methods=['POST'])
@login_required
def procesar_historia_bruto_modal(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    # Añade el prefijo al instanciar el formulario
    form_procesar_historia = ProcesarHistoriaBrutoForm(prefix='procesar_historia_modal')
    if form_procesar_historia.validate_on_submit():
        texto_bruto = form_procesar_historia.historia_bruto.data
        historia_actualizada = procesar_historia(paciente.historia or '', texto_bruto)
        paciente.historia = historia_actualizada.text
        db.session.commit()
        flash('Historia procesada y actualizada.', 'success')
    else:
        for field, errors in form_procesar_historia.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form_procesar_historia, field).label.text}: {error}', 'danger')

    return redirect(url_for('main.detalle_atencion', atencion_id=atencion_id))

@main.route('/procesar_detalle_bruto_modal/<string:atencion_id>', methods=['POST'])
@login_required
def procesar_detalle_bruto_modal(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    # Añade el prefijo al instanciar el formulario
    form_procesar_detalle = ProcesarDetalleBrutoForm(prefix='procesar_detalle_modal')
    if form_procesar_detalle.validate_on_submit():
        texto_bruto = form_procesar_detalle.detalle_bruto.data
        detalle_actualizado = procesar_detalle_atencion(
            paciente.historia or '', atencion.detalle or '', texto_bruto)
        atencion.detalle = detalle_actualizado.text
        db.session.commit()
        flash('Detalle de atención procesado y actualizado.', 'success')
    else:
        for field, errors in form_procesar_detalle.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form_procesar_detalle, field).label.text}: {error}', 'danger')

    return redirect(url_for('main.detalle_atencion', atencion_id=atencion_id))

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

```

---

### app/routes/__init__.py

```

```

---

### config/config.py

```
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

```

---

