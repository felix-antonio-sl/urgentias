from flask import Blueprint, render_template, redirect, url_for, flash, request
from ..forms import LoginForm, RegisterForm
from ..models import User
from .. import db
from flask_login import login_user, logout_user, current_user, login_required

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Inicio de sesión exitoso.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.lista_atenciones'))
        else:
            flash('Correo o contraseña incorrectos.', 'error')
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('El correo electrónico ya está registrado.', 'error')
        else:
            user = User(email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registro exitoso. Puedes iniciar sesión ahora.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('main.lista_atenciones'))
