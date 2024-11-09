from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class ActualizarHistoriaForm(FlaskForm):
    historia = TextAreaField("Puede editar este texto", validators=[DataRequired()])
    submit = SubmitField("Actualizar")


class ActualizarDetalleForm(FlaskForm):
    detalle = TextAreaField("Puede editar este texto", validators=[DataRequired()])
    submit = SubmitField("Actualizar")


class ProcesarHistoriaBrutoForm(FlaskForm):
    historia_bruto = TextAreaField("Ingrese texto", validators=[DataRequired()])
    submit = SubmitField("Procesar")


class ProcesarDetalleBrutoForm(FlaskForm):
    detalle_bruto = TextAreaField("Ingrese texto", validators=[DataRequired()])
    submit = SubmitField("Procesar")


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


class ProcesarTextoNoEstructuradoForm(FlaskForm):
    texto = TextAreaField("Ingrese Texto", validators=[DataRequired()])
    submit = SubmitField("Procesar")


class CerrarAtencionForm(FlaskForm):
    submit = SubmitField("Cerrar")
