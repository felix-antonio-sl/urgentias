from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class HistoriaMedicaForm(FlaskForm):
    historia_medica_text = TextAreaField(
        "Puede editar este texto", validators=[DataRequired()]
    )
    submit = SubmitField("Actualizar")


class ProgresoAtencionForm(FlaskForm):
    progreso_atencion_text = TextAreaField(
        "Puede editar este texto", validators=[DataRequired()]
    )
    submit = SubmitField("Actualizar")


class NuevosAntecedentesForm(FlaskForm):
    nuevos_antecedentes_raw_text = TextAreaField(
        "Ingrese texto", validators=[DataRequired()]
    )
    submit = SubmitField("Procesar")


class NovedadesAtencionForm(FlaskForm):
    novedades_atencion_raw_text = TextAreaField(
        "Ingrese texto", validators=[DataRequired()]
    )
    submit = SubmitField("Procesar")


class LoginForm(FlaskForm):
    email = StringField("Correo Electrónico", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
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
        "Ingrese texto", validators=[DataRequired()]
    )
    submit = SubmitField("Procesar")


class CierreAtencionForm(FlaskForm):
    submit = SubmitField("Cerrar")
