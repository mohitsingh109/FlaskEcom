from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length

# db = SQLAlchemy()
#
#
# class Customer(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(100), unique=True)
#     username = db.Column(db.String(100))
#     password_hash = db.Column(db.String(150))  # Store password hash
#     date_joined = db.Column(db.DateTime(), default=datetime.utcnow)
#
#     @property
#     def password(self):
#         raise AttributeError('Password is not a readable Attribute')
#
#     @password.setter
#     def password(self, password):
#         self.password_hash = generate_password_hash(password=password)
#
#     def verify_password(self, password):
#         return check_password_hash(self.password_hash, password=password)
#
#     def __str__(self):
#         return '<Customer %r>' % Customer.id


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()], render_kw={"placeholder": "Email"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')


class SignUpForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Length(max=100)
        ],
        render_kw={"placeholder": "Email"}
    )

    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=4, max=100)],
        render_kw={"placeholder": "Username"}
    )

    password1 = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=6, message="Password must be at least 6 characters long")
        ],
        render_kw={"placeholder": "Password"}
    )

    password2 = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password1', message="Passwords must match")
        ],
        render_kw={"placeholder": "Confirm Password"}
    )

    submit = SubmitField('Sign Up')

