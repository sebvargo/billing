import sqlalchemy as sa


from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User
from flask import url_for, redirect, flash, render_template, request
from flask_login import current_user, login_user, logout_user
from urllib.parse import urlsplit


# ___________________________________________________________________________________________
@bp.route("/", methods=["GET", "POST"])
@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()

    # check for submission
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )
        if user is None:
            user = db.session.scalar(
                sa.select(User).where(User.email == form.username.data)
            )
        
        # if credentials are incorrect, redirect ot login page
        if user is None or not user.check_password(form.password.data):
            flash("Incorrect username or password. Please try again.", 'warning')
            return redirect(url_for("auth.login"))

        # if credentials are correct, log the user in
        login_user(user, remember=form.remember_me.data)
        user.get_token()
        db.session.commit()

        # redirect to the next page if it exists
        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("main.home")
            
        return redirect(next_page)
    return render_template("auth/login.html", title="Login", form=form)


# ___________________________________________________________________________________________
@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = RegistrationForm()
    # check for submission
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, firstname = form.firstname.data, lastname = form.lastname.data, organization = form.organization.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Welcome!", 'success')
        return redirect(url_for("auth.login"))

    
    return render_template("auth/register.html", title="Register", form=form)



# ___________________________________________________________________________________________
@bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        current_user.revoke_token()
    logout_user()
    db.session.commit()
    return redirect(url_for("auth.login"))
