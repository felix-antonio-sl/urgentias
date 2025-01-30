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
from app.extensions import db
from app.models import Paciente, Atencion
from app.utils.main import (
    agregar_nuevos_antecedentes_ia,
    agregar_novedades_atencion_ia,
    extraer_datos_inicio_paciente_ia,
    generar_reporte_atencion_ia,
    generar_asistencia_medica_ia,
)
from app.forms import (
    HistoriaMedicaForm,
    ProgresoAtencionForm,
    NuevosAntecedentesForm,
    NovedadesAtencionForm,
    DatosInicioPacienteForm,
    CierreAtencionForm,
)
from flask_login import login_required, current_user
from datetime import datetime, timezone
import json
import re
from io import BytesIO
import logging

main = Blueprint("main", __name__)
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
        flash("Historia actualizada correctamente.", "success")
        return redirect(url_for("main.detalle_atencion_route", atencion_id=atencion_id))

    elif form_progreso_atencion.validate_on_submit() and form_progreso_atencion.submit.data:
        atencion.detalle = form_progreso_atencion.progreso_atencion_text.data
        db.session.commit()
        flash("Detalle de atención actualizado correctamente.", "success")
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

    form_nuevos_antecedentes = NuevosAntecedentesForm(prefix="procesar_historia_modal")
    if form_nuevos_antecedentes.validate_on_submit():
        nuevos_antecedentes_raw = form_nuevos_antecedentes.nuevos_antecedentes_raw_text.data
        historia_actualizada = agregar_nuevos_antecedentes_ia(
            paciente.historia or "", nuevos_antecedentes_raw
        )
        paciente.historia = historia_actualizada.text
        db.session.commit()
        flash("Historia procesada y actualizada.", "success")
    else:
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

    form_novedades_atencion = NovedadesAtencionForm(prefix="procesar_detalle_modal")
    if form_novedades_atencion.validate_on_submit():
        novedades_atencion_raw = form_novedades_atencion.novedades_atencion_raw_text.data
        progreso_atencion_actualizado = agregar_novedades_atencion_ia(
            paciente.historia or "", atencion.detalle or "", novedades_atencion_raw
        )
        atencion.detalle = progreso_atencion_actualizado.text
        db.session.commit()
        flash("Detalle de atención procesado y actualizado.", "success")
    else:
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

@main.route("/generar_reporte/<string:atencion_id>/<string:tipo_reporte>", methods=["GET"])
@login_required
def generacion_reporte_route(atencion_id, tipo_reporte):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    valid_report_types = ["alta_ambulatoria", "hospitalizacion", "interconsulta"]
    if tipo_reporte not in valid_report_types:
        flash("Tipo de reporte no válido.", "danger")
        return redirect(url_for("main.lista_atenciones_route"))

    historia_conocida = paciente.historia or ""
    atencion_en_curso = atencion.detalle or ""

    try:
        reporte_message = generar_reporte_atencion_ia(
            historia_conocida, atencion_en_curso, tipo_reporte
        )
        reporte_text = reporte_message.text
        titulos = {
            "alta_ambulatoria": "Reporte de Alta Ambulatoria",
            "hospitalizacion": "Solicitud de Hospitalización",
            "interconsulta": "Reporte de Interconsulta",
        }
        titulo = titulos.get(tipo_reporte, "Reporte Médico")
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

def obtener_sintesis(detalle, longitud=25):
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
