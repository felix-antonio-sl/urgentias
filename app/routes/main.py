# app/routes/main.py

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from app import db
from app.models import Atencion
from app.forms import (
    HistoriaMedicaForm,
    NuevosAntecedentesForm,
    ProgresoAtencionForm,
    NovedadesAtencionForm,
    GenerarReporteForm,
    CierreAtencionForm
)

main_bp = Blueprint('main', __name__)

# Ruta principal de detalle de atención
@main_bp.route('/atencion/<int:atencion_id>', methods=['GET'])
@login_required
def detalle_atencion_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    return render_template('detalle_atencion_view.html', atencion=atencion)

# Historia Clínica
@main_bp.route('/atencion/<int:atencion_id>/historia_clinica', methods=['GET'])
@login_required
def historia_clinica_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    form_historia_medica = HistoriaMedicaForm()
    form_historia_medica.historia_medica_text.data = atencion.historia_clinica
    return render_template('partials/historia_clinica.html', atencion=atencion, form_historia_medica=form_historia_medica)

@main_bp.route('/atencion/<int:atencion_id>/actualizar_historia_clinica', methods=['POST'])
@login_required
def actualizar_historia_clinica_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    form_historia_medica = HistoriaMedicaForm()
    if form_historia_medica.validate_on_submit():
        atencion.historia_clinica = form_historia_medica.historia_medica_text.data
        db.session.commit()
        if request.headers.get('HX-Request'):
            flash('Historia clínica actualizada exitosamente.', 'success')
            return render_template('partials/historia_clinica.html', atencion=atencion, form_historia_medica=form_historia_medica)
        else:
            flash('Historia clínica actualizada exitosamente.', 'success')
            return redirect(url_for('main.detalle_atencion_route', atencion_id=atencion.id))
    else:
        return render_template('partials/historia_clinica.html', atencion=atencion, form_historia_medica=form_historia_medica)

# Atención Actual
@main_bp.route('/atencion/<int:atencion_id>/atencion_actual', methods=['GET'])
@login_required
def atencion_actual_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    form_progreso_atencion = ProgresoAtencionForm()
    form_progreso_atencion.progreso_atencion_text.data = atencion.progreso_atencion
    return render_template('partials/atencion_actual.html', atencion=atencion, form_progreso_atencion=form_progreso_atencion)

@main_bp.route('/atencion/<int:atencion_id>/actualizar_atencion_actual', methods=['POST'])
@login_required
def actualizar_atencion_actual_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    form_progreso_atencion = ProgresoAtencionForm()
    if form_progreso_atencion.validate_on_submit():
        atencion.progreso_atencion = form_progreso_atencion.progreso_atencion_text.data
        db.session.commit()
        if request.headers.get('HX-Request'):
            flash('Atención actual actualizada exitosamente.', 'success')
            return render_template('partials/atencion_actual.html', atencion=atencion, form_progreso_atencion=form_progreso_atencion)
        else:
            flash('Atención actual actualizada exitosamente.', 'success')
            return redirect(url_for('main.detalle_atencion_route', atencion_id=atencion.id))
    else:
        return render_template('partials/atencion_actual.html', atencion=atencion, form_progreso_atencion=form_progreso_atencion)

# Asistencia IA
@main_bp.route('/atencion/<int:atencion_id>/asistencia_ia', methods=['GET'])
@login_required
def asistencia_ia_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    return render_template('partials/asistencia_ia.html', atencion=atencion)

# Agregar Antecedentes
@main_bp.route('/atencion/<int:atencion_id>/agregar_antecedentes_modal', methods=['GET'])
@login_required
def agregar_antecedentes_modal_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    form_nuevos_antecedentes = NuevosAntecedentesForm()
    return render_template('partials/agregar_antecedentes_modal.html', atencion=atencion, form_nuevos_antecedentes=form_nuevos_antecedentes)

@main_bp.route('/atencion/<int:atencion_id>/agregar_antecedentes', methods=['POST'])
@login_required
def agregar_antecedentes_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    form_nuevos_antecedentes = NuevosAntecedentesForm()
    if form_nuevos_antecedentes.validate_on_submit():
        nuevos_antecedentes = form_nuevos_antecedentes.nuevos_antecedentes_raw_text.data
        # Supongamos que los antecedentes se agregan al campo 'antecedentes' de la atención
        atencion.antecedentes = (atencion.antecedentes or "") + "\n" + nuevos_antecedentes
        db.session.commit()
        if request.headers.get('HX-Request'):
            flash('Antecedentes agregados exitosamente.', 'success')
            # Retornar la sección de Historia Clínica actualizada
            form_historia_medica = HistoriaMedicaForm()
            form_historia_medica.historia_medica_text.data = atencion.historia_clinica
            return render_template('partials/historia_clinica.html', atencion=atencion, form_historia_medica=form_historia_medica)
        else:
            flash('Antecedentes agregados exitosamente.', 'success')
            return redirect(url_for('main.detalle_atencion_route', atencion_id=atencion.id))
    else:
        return render_template('partials/agregar_antecedentes_modal.html', atencion=atencion, form_nuevos_antecedentes=form_nuevos_antecedentes)

# Agregar Novedades
@main_bp.route('/atencion/<int:atencion_id>/agregar_novedades_modal', methods=['GET'])
@login_required
def agregar_novedades_modal_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    form_novedades_atencion = NovedadesAtencionForm()
    return render_template('partials/agregar_novedades_modal.html', atencion=atencion, form_novedades_atencion=form_novedades_atencion)

@main_bp.route('/atencion/<int:atencion_id>/agregar_novedades', methods=['POST'])
@login_required
def agregar_novedades_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    form_novedades_atencion = NovedadesAtencionForm()
    if form_novedades_atencion.validate_on_submit():
        novedades = form_novedades_atencion.novedades_atencion_raw_text.data
        # Supongamos que las novedades se agregan al campo 'novedades_atencion' de la atención
        atencion.novedades_atencion = (atencion.novedades_atencion or "") + "\n" + novedades
        db.session.commit()
        if request.headers.get('HX-Request'):
            flash('Novedades agregadas exitosamente.', 'success')
            # Retornar la sección de Atención Actual actualizada
            form_progreso_atencion = ProgresoAtencionForm()
            form_progreso_atencion.progreso_atencion_text.data = atencion.progreso_atencion
            return render_template('partials/atencion_actual.html', atencion=atencion, form_progreso_atencion=form_progreso_atencion)
        else:
            flash('Novedades agregadas exitosamente.', 'success')
            return redirect(url_for('main.detalle_atencion_route', atencion_id=atencion.id))
    else:
        return render_template('partials/agregar_novedades_modal.html', atencion=atencion, form_novedades_atencion=form_novedades_atencion)

# Generar Reporte Modal
@main_bp.route('/atencion/<int:atencion_id>/generar_reporte_modal', methods=['GET'])
@login_required
def generar_reporte_modal_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    tipos_reporte = ['alta_ambulatoria', 'hospitalizacion', 'interconsulta']
    form_generar_reporte = GenerarReporteForm()
    return render_template('partials/generar_reporte_modal.html', atencion=atencion, tipos_reporte=tipos_reporte, form_generar_reporte=form_generar_reporte)

@main_bp.route('/atencion/<int:atencion_id>/generar_reporte', methods=['POST'])
@login_required
def generar_reporte_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    form_generar_reporte = GenerarReporteForm()
    if form_generar_reporte.validate_on_submit():
        tipo_reporte = form_generar_reporte.tipo_reporte.data
        # Lógica para generar el reporte basado en tipo_reporte
        # Por ejemplo, generar un PDF o redirigir a una página de descarga
        # Aquí simplemente se simula la generación del reporte
        if request.headers.get('HX-Request'):
            return jsonify({'message': f'Reporte {tipo_reporte.replace("_", " ").capitalize()} generado exitosamente.'})
        else:
            flash(f'Reporte {tipo_reporte.replace("_", " ").capitalize()} generado exitosamente.', 'success')
            return redirect(url_for('main.detalle_atencion_route', atencion_id=atencion.id))
    else:
        return render_template('partials/generar_reporte_modal.html', atencion=atencion, tipos_reporte=tipos_reporte, form_generar_reporte=form_generar_reporte)

# Cerrar Atención Modal
@main_bp.route('/atencion/<int:atencion_id>/cerrar_atencion_modal', methods=['GET'])
@login_required
def cerrar_atencion_modal_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    form_cierre_atencion = CierreAtencionForm()
    return render_template('partials/cerrar_atencion_modal.html', atencion=atencion, form_cierre_atencion=form_cierre_atencion)

# Cerrar Atención
@main_bp.route('/atencion/<int:atencion_id>/cerrar', methods=['POST'])
@login_required
def cerrar_atencion_route(atencion_id):
    atencion = Atencion.query.get_or_404(atencion_id)
    form_cierre_atencion = CierreAtencionForm()
    if form_cierre_atencion.validate_on_submit():
        atencion.estado = 'cerrada'
        db.session.commit()
        if request.headers.get('HX-Request'):
            flash('Atención cerrada exitosamente.', 'success')
            return render_template('partials/atencion_cerrada.html', atencion=atencion)
        else:
            flash('Atención cerrada exitosamente.', 'success')
            return redirect(url_for('main.lista_atenciones_route'))
    else:
        return render_template('partials/cerrar_atencion_modal.html', atencion=atencion, form_cierre_atencion=form_cierre_atencion)