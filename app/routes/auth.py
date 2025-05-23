from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from ..forms import LoginForm, RegisterForm
from ..models import User
from .. import db
from flask_login import login_user, logout_user, login_required
from ..extensions import supabase

auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        result = supabase.auth.sign_in_with_password(
            {"email": form.email.data, "password": form.password.data}
        )
        session = getattr(result, "session", None)
        if session:
            user = User.query.filter_by(email=form.email.data).first()
            if not user:
                user = User(email=form.email.data)
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
            login_user(user)
            flash("Inicio de sesión exitoso.", "success")
            next_page = request.args.get("next")
            resp = make_response(
                redirect(next_page) if next_page else redirect(url_for("main.lista_atenciones_route"))
            )
            resp.set_cookie("access_token", session.access_token, httponly=True)
            resp.set_cookie("refresh_token", session.refresh_token, httponly=True)
            return resp
        else:
            flash("Correo o contraseña incorrectos.", "error")
    return render_template("login.html", form=form)


@auth.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = supabase.auth.sign_up(
            {"email": form.email.data, "password": form.password.data}
        )
        if getattr(result, "user", None):
            existing_user = User.query.filter_by(email=form.email.data).first()
            if not existing_user:
                user = User(email=form.email.data)
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
            flash("Registro exitoso. Puedes iniciar sesión ahora.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Error al registrar el usuario.", "error")
    return render_template("register.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    resp = make_response(redirect(url_for("main.lista_atenciones_route")))
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    flash("Has cerrado sesión correctamente.", "success")
    return resp
