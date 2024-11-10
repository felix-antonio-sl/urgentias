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
    generar_reporte,  # Importación de la función consolidada
    generar_diagnostico_diferencial,
    generar_manejo_sugerido,
    generar_proxima_accion,
    generar_alertas,
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


@main.route(
    "/generar_reporte/<string:atencion_id>/<string:tipo_reporte>", methods=["GET"]
)
@login_required
def generar_reporte_route(atencion_id, tipo_reporte):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    # Validar el tipo de reporte
    valid_report_types = ["alta_ambulatoria", "hospitalizacion", "interconsulta"]
    if tipo_reporte not in valid_report_types:
        flash("Tipo de reporte no válido.", "danger")
        return redirect(url_for("main.lista_atenciones"))

    # Obtener los datos necesarios
    historia_paciente = paciente.historia or ""
    detalle_atencion = atencion.detalle or ""

    try:
        # Llamar a la nueva función consolidada para generar el reporte
        reporte_message = generar_reporte(
            historia_paciente, detalle_atencion, tipo_reporte
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
            "ver_reporte.html", titulo=titulo, reporte=reporte_text, atencion=atencion
        )
    except Exception as e:
        logger.error(f"Error al generar el reporte: {e}")
        flash("Ocurrió un error al generar el reporte.", "danger")
        return redirect(url_for("main.lista_atenciones"))
