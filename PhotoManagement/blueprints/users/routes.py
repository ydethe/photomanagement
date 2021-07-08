import time

from flask import (
    render_template,
    request,
    flash,
    redirect,
    url_for,
)
from flask_login import login_user, logout_user
from werkzeug.urls import url_parse

from . import users_bp
from .forms import LoginForm
from ...User import User


@users_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.objects(email=form.email.data).get()
        if not user or not user.isCorrectPassword(form.password.data):
            flash("Please check your login details and try again.")
            return redirect(
                url_for(".login")
            )  # if the user doesn't exist or password is wrong, reload the page
        else:
            login_user(user)
            next_page = request.args.get("next")
            if not next_page or url_parse(next_page).netloc != "":
                next_page = url_for("photo.photo_defaults")
            return redirect(next_page)

    return render_template("login.html", form=form)


@users_bp.route("/logout", methods=["GET"])
def logout():
    logout_user()

    return redirect(url_for(".login"))
