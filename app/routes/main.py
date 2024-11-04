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

@main.route('/procesar_historia_bruto/<string:atencion_id>', methods=['GET', 'POST'])
@login_required
def procesar_historia_bruto(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    form = ProcesarHistoriaBrutoForm()
    if form.validate_on_submit():
        texto_bruto = form.historia_bruto.data
        historia_actualizada = procesar_historia(paciente.historia or '', texto_bruto)
        paciente.historia = historia_actualizada.text
        db.session.commit()
        flash('Historia procesada y actualizada.', 'success')
        return redirect(url_for('main.detalle_atencion', atencion_id=atencion_id))

    return render_template('procesar_historia_bruto.html', form=form, atencion=atencion, paciente=paciente)

@main.route('/procesar_detalle_bruto/<string:atencion_id>', methods=['GET', 'POST'])
@login_required
def procesar_detalle_bruto(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    paciente = atencion.paciente

    form = ProcesarDetalleBrutoForm()
    if form.validate_on_submit():
        texto_bruto = form.detalle_bruto.data
        detalle_actualizado = procesar_detalle_atencion(
            paciente.historia or '', atencion.detalle or '', texto_bruto)
        atencion.detalle = detalle_actualizado.text
        db.session.commit()
        flash('Detalle de atención procesado y actualizado.', 'success')
        return redirect(url_for('main.detalle_atencion', atencion_id=atencion_id))

    return render_template('procesar_detalle_bruto.html', form=form, atencion=atencion, paciente=paciente)

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
