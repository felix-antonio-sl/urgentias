from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from .. import db
from ..models import Paciente, Atencion
from ..utils import procesar_historia, procesar_detalle_atencion, procesar_texto_no_estructurado
from ..forms import (
    CrearAtencionForm,
    ActualizarHistoriaForm,
    ActualizarDetalleForm,
    ProcesarHistoriaBrutoForm,
    ProcesarDetalleBrutoForm,
    ProcesarTextoNoEstructuradoForm,  # Asegúrate de importar el formulario
    CerrarAtencionForm
)
from flask_login import login_required, current_user
from datetime import datetime
import json
import re
from io import BytesIO

main = Blueprint('main', __name__)

def obtener_sintesis(detalle, longitud=25):
    """Obtiene una síntesis breve del detalle de la atención."""
    return detalle[:longitud] + "..." if detalle and len(detalle) > longitud else detalle or "Sin detalle"

@main.route('/')
@login_required
def lista_atenciones():
    atenciones = Atencion.query.filter_by(activa=True).order_by(Atencion.creado_en.desc()).all()
    form_cerrar = CerrarAtencionForm()
    form_procesar_texto = ProcesarTextoNoEstructuradoForm()
    return render_template(
        'atenciones.html',
        atenciones=atenciones,
        form_cerrar=form_cerrar,
        form_procesar_texto=form_procesar_texto  # Pasa el formulario al template
    )



@main.route('/crear_atencion', methods=['GET', 'POST'])
@login_required
def crear_atencion():
    form = CrearAtencionForm()
    if form.validate_on_submit():
        run = form.run.data
        if not Paciente.validar_run(run):
            flash('RUN inválido. Por favor, verifica el formato.', 'error')
            return redirect(url_for('main.crear_atencion'))

        paciente = Paciente.query.filter_by(run=run).first()
        if not paciente:
            flash('Paciente no encontrado. Por favor, utiliza el modal para crear una atención con texto no estructurado.', 'error')
            return redirect(url_for('main.crear_atencion'))
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

@main.route('/procesar_historia_bruto_modal/<string:atencion_id>', methods=['POST'])
@login_required
def procesar_historia_bruto_modal(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    # Añadir el prefijo al formulario
    form_procesar_historia = ProcesarHistoriaBrutoForm(prefix='procesar_historia_modal')
    if form_procesar_historia.validate_on_submit():
        texto_bruto = form_procesar_historia.historia_bruto.data
        historia_actualizada = procesar_historia(paciente.historia or '', texto_bruto)
        paciente.historia = historia_actualizada.text
        db.session.commit()
        flash('Historia procesada y actualizada.', 'success')
    else:
        # Agregar registro de errores para depuración
        current_app.logger.error(f"Errores del formulario: {form_procesar_historia.errors}")
        flash('Error al procesar la historia.', 'error')

    return redirect(url_for('main.detalle_atencion', atencion_id=atencion_id))

@main.route('/procesar_detalle_bruto_modal/<string:atencion_id>', methods=['POST'])
@login_required
def procesar_detalle_bruto_modal(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    # Añadir el prefijo al formulario
    form_procesar_detalle = ProcesarDetalleBrutoForm(prefix='procesar_detalle_modal')
    if form_procesar_detalle.validate_on_submit():
        texto_bruto = form_procesar_detalle.detalle_bruto.data
        detalle_actualizado = procesar_detalle_atencion(
            paciente.historia or '', atencion.detalle or '', texto_bruto)
        atencion.detalle = detalle_actualizado.text
        db.session.commit()
        flash('Detalle de atención procesado y actualizado.', 'success')
    else:
        # Agregar registro de errores para depuración
        current_app.logger.error(f"Errores del formulario: {form_procesar_detalle.errors}")
        flash('Error al procesar el detalle de atención.', 'error')

    return redirect(url_for('main.detalle_atencion', atencion_id=atencion_id))

@main.route('/procesar_texto', methods=['POST'])
@login_required
def procesar_texto():
    data = request.get_json()
    texto = data.get("texto")

    if not texto:
        return jsonify({"error": "Texto no proporcionado"}), 400

    try:
        resultado = procesar_texto_no_estructurado(texto)
        current_app.logger.debug(f"Resultado de procesar_texto_no_estructurado: {resultado}")

        json_str = extraer_json(resultado.text)
        datos = json.loads(json_str)
        run = datos.get('run')
        nombre = datos.get('nombre')
        fecha_nacimiento = datos.get('fecha_nacimiento')
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

    if fecha_nacimiento and fecha_nacimiento != 'N/A':
        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%d/%m/%Y").date()
        except ValueError:
            return jsonify({"error": "Formato de fecha de nacimiento inválido."}), 400
    else:
        fecha_nacimiento = None

    paciente = Paciente.query.filter_by(run=run).first()
    if not paciente:
        if not nombre or not fecha_nacimiento:
            return jsonify({"error": "Falta nombre o fecha de nacimiento para crear un nuevo paciente."}), 400
        paciente = Paciente(run=run, nombre=nombre, fecha_nacimiento=fecha_nacimiento)
        db.session.add(paciente)
        db.session.commit()

    atencion = Atencion(paciente_id=paciente.id)
    db.session.add(atencion)
    db.session.commit()

    return jsonify({"message": "Atención creada exitosamente."}), 200

def extraer_json(respuesta):
    match = re.search(r'```json(.*?)```', respuesta, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        return json_str
    else:
        raise ValueError("No se encontró un bloque JSON en la respuesta.")

@main.route('/generar_reporte/<string:atencion_id>')
@login_required
def generar_reporte(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    pdf = BytesIO()
    pdf.write(b"%PDF-1.4\n%...")
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name='reporte.pdf', mimetype='application/pdf')

@main.route('/cerrar_atencion/<string:atencion_id>', methods=['POST'])
@login_required
def cerrar_atencion(atencion_id):
    form = CerrarAtencionForm()
    if form.validate_on_submit():
        atencion = Atencion.query.get_or_404(atencion_id)
        atencion.activa = False
        atencion.cerrada_en = datetime.utcnow()
        db.session.commit()
        flash('Atención cerrada exitosamente.', 'success')
    else:
        flash('Error al cerrar la atención.', 'error')
    return redirect(url_for('main.lista_atenciones'))

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
