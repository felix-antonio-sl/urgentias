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

class ProcesarTextoNoEstructuradoForm(FlaskForm):
    texto = TextAreaField('Texto no estructurado', validators=[DataRequired()])
    submit = SubmitField('Procesar Atención')
