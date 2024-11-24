# app/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class GenerarReporteForm(FlaskForm):
    tipo_reporte = SelectField(
        'Tipo de Reporte',
        choices=[
            ('alta_ambulatoria', 'Alta Ambulatoria'),
            ('hospitalizacion', 'Hospitalización'),
            ('interconsulta', 'Interconsulta')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Generar Reporte')

class HistoriaMedicaForm(FlaskForm):
    historia_medica_text = TextAreaField('Historia Clínica', validators=[DataRequired()])
    submit = SubmitField('Guardar')

class NuevosAntecedentesForm(FlaskForm):
    nuevos_antecedentes_raw_text = TextAreaField('Antecedentes', validators=[DataRequired()])
    submit = SubmitField('Agregar Antecedentes')

class ProgresoAtencionForm(FlaskForm):
    progreso_atencion_text = TextAreaField('Progreso de Atención', validators=[DataRequired()])
    submit = SubmitField('Actualizar Atención')

class NovedadesAtencionForm(FlaskForm):
    novedades_atencion_raw_text = TextAreaField('Novedades de Atención', validators=[DataRequired()])
    submit = SubmitField('Agregar Novedades')

class GenerarReporteForm(FlaskForm):
    tipo_reporte = SelectField(
        'Tipo de Reporte',
        choices=[
            ('alta_ambulatoria', 'Alta Ambulatoria'),
            ('hospitalizacion', 'Hospitalización'),
            ('interconsulta', 'Interconsulta')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Generar Reporte')

class CierreAtencionForm(FlaskForm):
    submit = SubmitField('Cerrar Atención')


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


class DatosInicioPacienteForm(FlaskForm):
    datos_inicio_paciente_raw_text = TextAreaField(
        "Ingrese Texto", validators=[DataRequired()]
    )
    submit = SubmitField("Procesar")

