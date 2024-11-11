# Estructura y Código del Proyecto urgentias

## Árbol del proyecto
```plaintext
└── app
    ├── __init__.py
    ├── routes
    │   └── main.py
    ├── static
    │   └── css
    │       └── styles.css
    └── templates
        ├── 404.html
        ├── 500.html
        ├── base.html
        ├── detalle_atencion_view.html
        ├── footer.html
        ├── lista_atenciones_view.html
        ├── login.html
        ├── macros.html
        ├── navbar.html
        ├── register.html
        └── ver_reporte_view.html
```

### __init__.py

```py
# app/__init__.py
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
from datetime import datetime, timezone


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

    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now(timezone.utc).year}

    return app
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
    agregar_nuevos_antecedentes_ia,
    agregar_novedades_atencion_ia,
    extraer_datos_inicio_paciente_ia,
    generar_reporte_atencion_ia,  # Importación de la función consolidada
    generar_asistencia_medica_ia,  # Importamos la nueva función unificada
)
from ..forms import (
    HistoriaMedicaForm,
    ProgresoAtencionForm,
    NuevosAntecedentesForm,
    NovedadesAtencionForm,
    DatosInicioPacienteForm,
    CierreAtencionForm,
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


@main.route("/")
@login_required
def lista_atenciones_route():
    atenciones = (
        Atencion.query.filter_by(activa=True).order_by(Atencion.creado_en.desc()).all()
    )
    form_cierre_atencion = CierreAtencionForm()
    form_datos_inicio_paciente = DatosInicioPacienteForm()
    return render_template(
        "lista_atenciones_view.html",
        atenciones=atenciones,
        form_cierre_atencion=form_cierre_atencion,
        form_datos_inicio_paciente=form_datos_inicio_paciente,
    )


@main.route("/detalle_atencion_route/<string:atencion_id>", methods=["GET", "POST"])
@login_required
def detalle_atencion_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    form_historia_medica = HistoriaMedicaForm(prefix="historia")
    form_progreso_atencion = ProgresoAtencionForm(prefix="detalle")
    form_nuevos_antecedentes = NuevosAntecedentesForm(prefix="procesar_historia_modal")
    form_novedades_atencion = NovedadesAtencionForm(prefix="procesar_detalle_modal")

    if form_historia_medica.validate_on_submit() and form_historia_medica.submit.data:
        paciente.historia = form_historia_medica.historia_medica_text.data
        db.session.commit()
        try:
            guardar_db_asistencia_medica(atencion)
            flash("Historia y datos AI actualizados correctamente.", "success")
        except Exception as e:
            logger.error(f"Error al actualizar información AI: {e}")
            flash(
                "Historia actualizada. La información AI no está disponible temporalmente.",
                "warning",
            )
        return redirect(url_for("main.detalle_atencion_route", atencion_id=atencion_id))

    elif (
        form_progreso_atencion.validate_on_submit()
        and form_progreso_atencion.submit.data
    ):
        atencion.detalle = form_progreso_atencion.progreso_atencion_text.data
        db.session.commit()
        try:
            guardar_db_asistencia_medica(atencion)
            flash(
                "Detalle de atención y datos AI actualizados correctamente.", "success"
            )
        except Exception as e:
            logger.error(f"Error al actualizar información AI: {e}")
            flash(
                "Detalle actualizado. La información AI no está disponible temporalmente.",
                "warning",
            )
        return redirect(url_for("main.detalle_atencion_route", atencion_id=atencion_id))

    if request.method == "GET":
        form_historia_medica.historia_medica_text.data = paciente.historia
        form_progreso_atencion.progreso_atencion_text.data = atencion.detalle

    return render_template(
        "detalle_atencion_view.html",
        atencion=atencion,
        paciente=paciente,
        form_historia_medica=form_historia_medica,
        form_progreso_atencion=form_progreso_atencion,
        form_nuevos_antecedentes=form_nuevos_antecedentes,
        form_novedades_atencion=form_novedades_atencion,
    )


@main.route("/nuevos_antecedentes_route/<string:atencion_id>", methods=["POST"])
@login_required
def nuevos_antecedentes_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    # Añadir el prefijo al formulario
    form_nuevos_antecedentes = NuevosAntecedentesForm(prefix="procesar_historia_modal")
    if form_nuevos_antecedentes.validate_on_submit():
        nuevos_antecedentes_raw = (
            form_nuevos_antecedentes.nuevos_antecedentes_raw_text.data
        )
        historia_actualizada = agregar_nuevos_antecedentes_ia(
            paciente.historia or "", nuevos_antecedentes_raw
        )
        paciente.historia = historia_actualizada.text
        db.session.commit()
        flash("Historia procesada y actualizada.", "success")
    else:
        # Agregar registro de errores para depuración
        current_app.logger.error(
            f"Errores del formulario: {form_nuevos_antecedentes.errors}"
        )
        flash("Error al procesar la historia.", "error")

    return redirect(url_for("main.detalle_atencion_route", atencion_id=atencion_id))


@main.route("/novedades_atencion_route/<string:atencion_id>", methods=["POST"])
@login_required
def novedades_atencion_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    # Añadir el prefijo al formulario
    form_novedades_atencion = NovedadesAtencionForm(prefix="procesar_detalle_modal")
    if form_novedades_atencion.validate_on_submit():
        novedades_atencion_raw = (
            form_novedades_atencion.novedades_atencion_raw_text.data
        )
        progreso_atencion_actualizado = agregar_novedades_atencion_ia(
            paciente.historia or "", atencion.detalle or "", novedades_atencion_raw
        )
        atencion.detalle = progreso_atencion_actualizado.text
        db.session.commit()
        flash("Detalle de atención procesado y actualizado.", "success")
    else:
        # Agregar registro de errores para depuración
        current_app.logger.error(
            f"Errores del formulario: {form_novedades_atencion.errors}"
        )
        flash("Error al procesar el detalle de atención.", "error")

    return redirect(url_for("main.detalle_atencion_route", atencion_id=atencion_id))


@main.route("/extraccion_datos_inicio_paciente_route", methods=["POST"])
@login_required
def extraccion_datos_inicio_paciente_route():
    data = request.get_json()
    texto = data.get("texto")

    if not texto:
        return jsonify({"error": "Texto no proporcionado"}), 400

    try:
        resultado = extraer_datos_inicio_paciente_ia(texto)
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


@main.route("/cierre_atencion_route/<string:atencion_id>", methods=["POST"])
@login_required
def cierre_atencion_route(atencion_id):
    form = CierreAtencionForm()
    if form.validate_on_submit():
        atencion = Atencion.query.get_or_404(atencion_id)
        atencion.activa = False
        atencion.cerrada_en = datetime.utcnow()
        db.session.commit()
        flash("Atención cerrada exitosamente.", "success")
    else:
        flash("Error al cerrar la atención.", "error")
    return redirect(url_for("main.lista_atenciones_route"))


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


@main.route(
    "/generar_reporte/<string:atencion_id>/<string:tipo_reporte>", methods=["GET"]
)
@login_required
def generacion_reporte_route(atencion_id, tipo_reporte):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    # Validar el tipo de reporte
    valid_report_types = ["alta_ambulatoria", "hospitalizacion", "interconsulta"]
    if tipo_reporte not in valid_report_types:
        flash("Tipo de reporte no válido.", "danger")
        return redirect(url_for("main.lista_atenciones_route"))

    # Obtener los datos necesarios
    historia_conocida = paciente.historia or ""
    atencion_en_curso = atencion.detalle or ""

    try:
        # Llamar a la nueva función consolidada para generar el reporte
        reporte_message = generar_reporte_atencion_ia(
            historia_conocida, atencion_en_curso, tipo_reporte
        )

        # Obtener el texto del reporte desde el mensaje de ell
        reporte_text = reporte_message.text

        # Determinar el título del reporte basado en el tipo
        titulos = {
            "alta_ambulatoria": "Reporte de Alta Ambulatoria",
            "hospitalizacion": "Solicitud de Hospitalización",
            "interconsulta": "Reporte de Interconsulta",
        }
        titulo = titulos.get(tipo_reporte, "Reporte Médico")

        # Renderizar la plantilla con el reporte
        return render_template(
            "ver_reporte_view.html",
            titulo=titulo,
            reporte=reporte_text,
            atencion=atencion,
        )
    except Exception as e:
        logger.error(f"Error al generar el reporte: {e}")
        flash("Ocurrió un error al generar el reporte.", "danger")
        return redirect(url_for("main.lista_atenciones_route"))


# Funciones auxiliares


def guardar_db_asistencia_medica(atencion):
    paciente = atencion.paciente

    logger.info(f"Actualizando información AI para Atención ID: {atencion.id}")

    # Generación de información AI unificada
    try:
        asistencia_msg = generar_asistencia_medica_ia(
            paciente.historia or "", atencion.detalle or ""
        )
    except Exception as e:
        logger.error(f"Error al llamar a la función generar_asistencia_medica: {e}")
        raise

    # Asignación de los resultados parseados
    try:
        atencion.diagnostico_diferencial = "\n".join(
            asistencia_msg.parsed.diagnostico_diferencial
        )
        atencion.manejo_sugerido = asistencia_msg.parsed.manejo_sugerido
        atencion.proxima_accion = asistencia_msg.parsed.proxima_accion
        atencion.alertas = "\n".join(asistencia_msg.parsed.alertas)
    except AttributeError as e:
        logger.error(f"Error al asignar los resultados de asistencia AI: {e}")
        raise

    atencion.actualizado_en = datetime.now(timezone.utc)
    db.session.commit()
    logger.info(f"Información AI actualizada para Atención ID: {atencion.id}")


def obtener_sintesis(detalle, longitud=25):
    """Obtiene una síntesis breve del detalle de la atención."""
    return (
        detalle[:longitud] + "..."
        if detalle and len(detalle) > longitud
        else detalle or "Sin detalle"
    )


def extraer_json(respuesta):
    match = re.search(r"```json(.*?)```", respuesta, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        return json_str
    else:
        raise ValueError("No se encontró un bloque JSON en la respuesta.")
```

### styles.css

```css
/* Estilos personalizados para Urgentias */

/* Sobrescribir variables de Bootstrap */
:root {
  --bs-body-bg: #ffffff;
  --bs-body-color: #000000;
  --bs-primary: #3D0066; /* Morado oscuro */
  --bs-secondary: #00B2A9; /* Turquesa */
  --bs-success: #00B2A9;
  --bs-danger: #C71585; /* Rosa intenso */
  --bs-warning: #FDC500; /* Amarillo */
  --bs-info: #3D0066;
  --bs-light: #f8f9fa;
  --bs-dark: #000000;
  --bs-link-color: #3D0066;

  /* Tipografía */
  --bs-font-sans-serif: 'Roboto', sans-serif;
  --bs-font-size-base: 1rem;
  --bs-font-size-lg: 1.25rem;
  --bs-font-size-sm: 0.875rem;
  --bs-heading-font-family: 'Montserrat', sans-serif;
}

body {
  font-family: var(--bs-font-sans-serif);
  font-size: var(--bs-font-size-base);
  line-height: 1.6;
  color: var(--bs-body-color);
}

h1,
h2,
h3,
h4,
h5,
h6 {
  font-family: var(--bs-heading-font-family);
  font-weight: 700;
  color: var(--bs-primary);
}

p {
  margin-bottom: 1rem;
}

.container {
  max-width: 960px;
}

.navbar-brand,
.nav-link {
  font-family: var(--bs-heading-font-family);
  font-weight: 600;
}

.btn {
  font-weight: 600;
  padding: 0.75rem 1.25rem;
  border-radius: 0;
}

.table {
  margin-bottom: 2rem;
}

.table th {
  font-weight: 700;
  color: var(--bs-primary);
}

.form-control {
  padding: 0.75rem 1rem;
  border-radius: 0;
}

.form-control:focus {
  border-color: var(--bs-primary);
  box-shadow: none;
}

.footer {
  background-color: #ffffff; /* Fondo blanco */
  color: #000000;            /* Texto negro */
  padding: 2rem 0;
  border-top: 1px solid #eaeaea; /* Línea superior suave */
  box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1); /* Sombra sutil */
}

.footer p {
  margin: 0;
  font-size: 1rem; /* Asegura legibilidad */
  font-weight: 400; /* Peso de fuente regular */
}

/* Espaciado adicional */
.mt-4 {
  margin-top: 2rem !important;
}

.mb-4 {
  margin-bottom: 2rem !important;
}

.pt-4 {
  padding-top: 2rem !important;
}

.pb-4 {
  padding-bottom: 2rem !important;
}

/* Estilos para resaltar información AI */
.text-highlight {
  background-color: #FDC500;
  font-weight: bold;
  color: #000000;
}

.text-danger {
  color: var(--bs-danger);
  font-weight: bold;
}

/* Estilos para los formularios */
.form-label {
  font-weight: 600;
}

.modal-content {
  border-radius: 0;
}

.modal-header {
  background-color: var(--bs-primary);
  color: #ffffff;
}

.modal-footer {
  border-top: none;
}

/* Mejorar la legibilidad de los encabezados */
h1 {
  font-size: 2.5rem;
  margin-bottom: 1.5rem;
}

h2 {
  font-size: 2rem;
  margin-bottom: 1.2rem;
}

h3 {
  font-size: 1.75rem;
  margin-bottom: 1rem;
}

/* Aumentar el espacio entre párrafos y secciones */
section {
  padding: 2rem 0;
}

/* Mejorar la apariencia de los formularios */
.form-control {
  font-size: 1rem;
}

.form-label {
  margin-bottom: 0.5rem;
}

/* Ajustar botones para mayor claridad */
.btn {
  font-size: 1rem;
}

/* Espaciado en tablas */
.table th,
.table td {
  padding: 1rem;
}

/* Mejorar el aspecto de los modales */
.modal-header h5 {
  font-size: 1.5rem;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  padding: 1rem;
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
  <a href="{{ url_for('main.lista_atenciones_route') }}" class="btn btn-primary">Volver al inicio</a>
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

### base.html

```html
<!doctype html>
<html lang="es">

<head>
  <meta charset="utf-8">
  <title>{% block title %}Urgentias{% endblock %}</title>
  {% import 'macros.html' as macros %}
  
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700&family=Roboto:wght@400;500&display=swap" rel="stylesheet">
  
  <!-- Bootstrap CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  
  <!-- Bootstrap Icons -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
  
  <!-- CSS Personalizado -->
  <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>

<body>
  {% include 'navbar.html' %}
  <main class="container my-4">
    {% with messages = get_flashed_messages(with_categories=true) %}
    {{ macros.render_alerts(messages) }}
    {% endwith %}
    {% block content %}{% endblock %}
  </main>
  {% include 'footer.html' %}
  
  <!-- Bootstrap JS y dependencias -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  {% block scripts %}{% endblock %}
</body>

</html>
```

### detalle_atencion_view.html

```html
{% extends "base.html" %}
{% import 'macros.html' as macros %}
{% block title %}Detalle de Atención{% endblock %}
{% block content %}
<div class="container mt-4">
  <h1 class="mb-5">Atención Actual</h1>
  <div class="row mb-5">
    <div class="col-md-4">
      <h5>RUN</h5>
      <p>{{ paciente.run }}</p>
    </div>
    <div class="col-md-4">
      <h5>Nombre</h5>
      <p>{{ paciente.nombre or 'N/A' }}</p>
    </div>
    <div class="col-md-4">
      <h5>Edad</h5>
      <p>
        {% if paciente.edad %}
        {{ paciente.edad }} años
        {% else %}
        N/A
        {% endif %}
      </p>
    </div>
  </div>
  <!-- Pestañas -->
  <ul class="nav nav-tabs mb-4" id="detalleAtencionTabs" role="tablist">
    <li class="nav-item" role="presentation">
      <button class="nav-link active" id="historia-tab" data-bs-toggle="tab" data-bs-target="#historia" type="button"
        role="tab" aria-controls="historia" aria-selected="true">Historia Clínica</button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="atencion-tab" data-bs-toggle="tab" data-bs-target="#atencion" type="button"
        role="tab" aria-controls="atencion" aria-selected="false">Atención Actual</button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="ai-tab" data-bs-toggle="tab" data-bs-target="#ai" type="button" role="tab"
        aria-controls="ai" aria-selected="false">Asistencia AI</button>
    </li>
  </ul>
  <div class="tab-content" id="detalleAtencionTabsContent">
    <!-- Historia Clínica -->
    <div class="tab-pane fade show active" id="historia" role="tabpanel" aria-labelledby="historia-tab">
      <form method="POST" action="{{ url_for('main.detalle_atencion_route', atencion_id=atencion.id) }}">
        {{ form_historia_medica.hidden_tag() }}
        {{ macros.render_form_field(
        form_historia_medica.historia_medica_text,
        attrs={'id': 'historiaClinica', 'rows': 10}
        ) }}
        <div class="d-flex">
          {{ form_historia_medica.submit(class="btn btn-primary me-2") }}
          <!-- Botón para abrir el modal de Historia en Bruto -->
          <button type="button" class="btn btn-secondary" data-bs-toggle="modal" data-bs-target="#historiaBrutoModal">
            <i class="bi bi-arrow-repeat"></i> Procesar
          </button>
        </div>
      </form>
    </div>
    <!-- Atención Actual -->
    <div class="tab-pane fade" id="atencion" role="tabpanel" aria-labelledby="atencion-tab">
      <form method="POST" action="{{ url_for('main.detalle_atencion_route', atencion_id=atencion.id) }}">
        {{ form_progreso_atencion.hidden_tag() }}
        {{ macros.render_form_field(
        form_progreso_atencion.progreso_atencion_text,
        attrs={'id': 'detalleAtencion', 'rows': 10}
        ) }}
        <div class="d-flex">
          {{ form_progreso_atencion.submit(class="btn btn-primary me-2") }}
          <!-- Botón para abrir el modal de Detalle de Atención en Bruto -->
          <button type="button" class="btn btn-secondary" data-bs-toggle="modal" data-bs-target="#detalleBrutoModal">
            <i class="bi bi-arrow-repeat"></i> Procesar
          </button>
        </div>
      </form>
    </div>
    <!-- Asistencia AI -->
    <div class="tab-pane fade" id="ai" role="tabpanel" aria-labelledby="ai-tab">
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
          <p class="text-highlight">
            {{ atencion.proxima_accion or "Información no disponible" }}
          </p>
        </div>
        <div class="col-md-6">
          <h4>Alertas de Amenazas o Riesgos</h4>
          <p class="text-danger">
            {{ atencion.alertas or "Información no disponible" }}
          </p>
        </div>
      </div>
    </div>
  </div>
  <!-- Modales -->
  <!-- Modal de Historia en Bruto -->
  <div class="modal fade" id="historiaBrutoModal" tabindex="-1" aria-labelledby="historiaBrutoModalLabel"
    aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <form method="POST" action="{{ url_for('main.nuevos_antecedentes_route', atencion_id=atencion.id) }}">
          {{ form_nuevos_antecedentes.hidden_tag() }}
          <div class="modal-header">
            <h5 class="modal-title" id="historiaBrutoModalLabel">Procesar Historia en Bruto</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
          </div>
          <div class="modal-body">
            {{ macros.render_form_field(
            form_nuevos_antecedentes.nuevos_antecedentes_raw_text,
            attrs={'id': 'historiaBruto', 'rows': 5}
            ) }}
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            {{ form_nuevos_antecedentes.submit(class="btn btn-primary") }}
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
        <form method="POST" action="{{ url_for('main.novedades_atencion_route', atencion_id=atencion.id) }}">
          {{ form_novedades_atencion.hidden_tag() }}
          <div class="modal-header">
            <h5 class="modal-title" id="detalleBrutoModalLabel">Procesar Detalle de Atención en Bruto</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
          </div>
          <div class="modal-body">
            {{ macros.render_form_field(
            form_novedades_atencion.novedades_atencion_raw_text,
            attrs={'id': 'detalleBruto', 'rows': 5}
            ) }}
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            {{ form_novedades_atencion.submit(class="btn btn-primary") }}
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}

{% block scripts %}
<script>
  // Inicializar pestañas
  var triggerTabList = [].slice.call(document.querySelectorAll('#detalleAtencionTabs button'))
  triggerTabList.forEach(function (triggerEl) {
    var tabTrigger = new bootstrap.Tab(triggerEl)
    triggerEl.addEventListener('click', function (event) {
      event.preventDefault()
      tabTrigger.show()
    })
  })
</script>
{% endblock %}
```

### footer.html

```html
<footer class="footer text-center">
  <div class="container">
    <p>&copy; {{ current_year }} Urgentias</p>
  </div>
</footer>
```

### lista_atenciones_view.html

```html
{% extends "base.html" %}
{% import 'macros.html' as macros %}
{% block title %}Lista de Atenciones{% endblock %}
{% block content %}
<h1 class="mb-4">Lista de Atenciones</h1>
<!-- Botón para abrir el modal de creación de atención -->
<button type="button" class="btn btn-primary mb-4" data-bs-toggle="modal" data-bs-target="#crearAtencionModal">
  <i class="bi bi-plus-circle"></i> Nueva Atención
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
          {{ macros.render_form_field(
          form_datos_inicio_paciente.datos_inicio_paciente_raw_text,
          attrs={
          'id': 'textoNoEstructurado',
          'rows': 5,
          'placeholder': 'Ingrese el RUN, nombre y fecha de nacimiento'
          }
          ) }}
          <div id="crearAtencionError" class="text-danger mt-2 d-none"></div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
          <button type="button" class="btn btn-primary" id="enviarTextoNoEstructurado">
            <i class="bi bi-send"></i> Enviar
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
<div class="table-responsive">
  <table class="table table-hover align-middle">
    <thead class="table-light">
      <tr>
        <th>Tiempo</th>
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
          <a href="{{ url_for('main.detalle_atencion_route', atencion_id=atencion.id) }}" class="btn btn-info btn-sm">
            <i class="bi bi-eye"></i> Detalles
          </a>
          <!-- Botón para abrir el modal de selección de reporte -->
          <button type="button" class="btn btn-secondary btn-sm" data-bs-toggle="modal"
            data-bs-target="#seleccionarReporteModal" data-atencion-id="{{ atencion.id }}">
            <i class="bi bi-file-earmark-text"></i> Reporte
          </button>
          <form action="{{ url_for('main.cierre_atencion_route', atencion_id=atencion.id) }}" method="POST"
            style="display:inline;">
            {{ form_cierre_atencion.hidden_tag() }}
            {{ form_cierre_atencion.submit(class="btn btn-danger btn-sm", onclick="return confirm('¿Está seguro de
            cerrar esta atención?');", value='Cerrar') }}
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
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
            <a href="#" class="btn btn-link" data-report-type="alta_ambulatoria">
              Alta Ambulatoria
            </a>
          </li>
          <li class="list-group-item">
            <a href="#" class="btn btn-link" data-report-type="hospitalizacion">
              Hospitalización
            </a>
          </li>
          <li class="list-group-item">
            <a href="#" class="btn btn-link" data-report-type="interconsulta">
              Interconsulta
            </a>
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
  // Inicializar tooltips
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
  })

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
    fetch("{{ url_for('main.extraccion_datos_inicio_paciente_route') }}", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": "{{ csrf_token() }}"
      },
      body: JSON.stringify({ texto })
    }).then(response => response.json()
      .then(data => ({ status: response.status, body: data })))
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
      var url = "{{ url_for('main.generacion_reporte_route', atencion_id='ATENCION_ID', tipo_reporte='TIPO_REPORTE') }}";
      url = url.replace('ATENCION_ID', currentAtencionId).replace('TIPO_REPORTE', tipoReporte);
      window.location.href = url;
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
<div class="container d-flex justify-content-center align-items-center" style="min-height: 80vh;">
  <div class="card shadow-sm" style="max-width: 400px; width: 100%;">
    <div class="card-body">
      <h2 class="card-title mb-4 text-center">Iniciar Sesión</h2>
      <form method="POST" action="{{ url_for('auth.login') }}">
        {{ form.hidden_tag() }}
        {{ macros.render_form_field(form.email) }}
        {{ macros.render_form_field(form.password) }}
        {{ macros.render_form_checkbox(form.remember) }}
        <div>
          {{ form.submit(class="btn btn-primary w-100") }}
        </div>
      </form>
      <p class="mt-3 text-center">¿No tienes una cuenta? <a href="{{ url_for('auth.register') }}">Regístrate aquí</a>.</p>
    </div>
  </div>
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
  <div class="invalid-feedback d-block">{{ error }}</div>
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
  <div class="invalid-feedback d-block">{{ error }}</div>
  {% endfor %}
  {% endif %}
</div>
{% endmacro %}

{% macro render_alerts(messages) %}
{% if messages %}
{% for category, message in messages %}
<div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show"
  role="alert">
  {{ message }}
  <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
</div>
{% endfor %}
{% endif %}
{% endmacro %}
```

### navbar.html

```html
<nav class="navbar navbar-expand-lg">
    <div class="container-fluid">
        <a class="navbar-brand" href="{{ url_for('main.lista_atenciones_route') }}">
            <i class="bi bi-house-door-fill"></i> Urgentias
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
            aria-controls="navbarNav" aria-expanded="false" aria-label="Alternar navegación">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav ms-auto">
                <!-- Enlace a la Lista de Atenciones -->
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('main.lista_atenciones_route') }}">
                        <i class="bi bi-list-task"></i> Atenciones
                    </a>
                </li>
                {% if current_user.is_authenticated %}
                <!-- Enlace para Cerrar Sesión -->
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('auth.logout') }}">
                        <i class="bi bi-box-arrow-right"></i> Cerrar Sesión
                    </a>
                </li>
                {% else %}
                <!-- Enlace para Iniciar Sesión -->
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('auth.login') }}">
                        <i class="bi bi-box-arrow-in-right"></i> Iniciar Sesión
                    </a>
                </li>
                <!-- Enlace para Registrarse -->
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('auth.register') }}">
                        <i class="bi bi-person-plus-fill"></i> Registrarse
                    </a>
                </li>
                {% endif %}
            </ul>
        </div>
    </div>
</nav>
```

### register.html

```html
{% extends "base.html" %}
{% import 'macros.html' as macros %}
{% block title %}Registrarse{% endblock %}
{% block content %}
<div class="container d-flex justify-content-center align-items-center" style="min-height: 80vh;">
  <div class="card shadow-sm" style="max-width: 400px; width: 100%;">
    <div class="card-body">
      <h2 class="card-title mb-4 text-center">Registrarse</h2>
      <form method="POST" action="{{ url_for('auth.register') }}">
        {{ form.hidden_tag() }}
        {{ macros.render_form_field(form.email) }}
        {{ macros.render_form_field(form.password) }}
        {{ macros.render_form_field(form.confirm_password) }}
        <div>
          {{ form.submit(class="btn btn-primary w-100") }}
        </div>
      </form>
      <p class="mt-3 text-center">¿Ya tienes una cuenta? <a href="{{ url_for('auth.login') }}">Inicia sesión aquí</a>.</p>
    </div>
  </div>
</div>
{% endblock %}
```

### ver_reporte_view.html

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
  <div class="bg-light p-3 rounded">
    <p>{{ reporte | nl2br }}</p>
  </div>

  <div class="mt-4">
    <a href="{{ url_for('main.lista_atenciones_route') }}" class="btn btn-secondary me-2">
      <i class="bi bi-arrow-left"></i> Volver a la Lista de Atenciones
    </a>
    <a href="{{ url_for('main.detalle_atencion_route', atencion_id=atencion.id) }}" class="btn btn-primary">
      <i class="bi bi-eye"></i> Ver Detalle de Atención
    </a>
  </div>
</div>
{% endblock %}
```

