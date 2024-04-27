import sqlalchemy as sa

from app import db
from app.models import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError


class LoginForm(FlaskForm):
    username = StringField("Email or Username", description="Your email or username", validators=[DataRequired()])
    password = PasswordField("Password", description="Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    firstname = StringField("First Name", validators=[DataRequired()], description="Your firstname",)
    lastname = StringField("Last Name", validators=[DataRequired()], description="Your lastname",)
    username = StringField("Username", validators=[DataRequired()], description="Pick your username",)
    email = StringField("Email", validators=[DataRequired(), Email()], description="Your email address",)
    organization = StringField("Organization", validators=[DataRequired()], description="Organization name",) 
    password = PasswordField("Password", validators=[DataRequired()], description="Choose a password",)
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")], description="Retype your password",
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        query = sa.select(User).where(User.username == username.data)
        user = db.session.scalar(
            query
        )  # returns None if no user is found, or the first user if there is one
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        query = sa.select(User).where(User.email == email.data)
        user = db.session.scalar(
            query
        )  # returns None if no user is found, or the first user if there is one
        if user is not None:
            raise ValidationError(
                "Email already taken, please use a different one to register."
            )
