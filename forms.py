from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm
class FilterForm(FlaskForm):
    name = StringField("Café name")
    location = StringField("Location")
    sockets = BooleanField("Sockets")
    toilet = BooleanField("Toilet")
    wifi = BooleanField("Wifi")
    calls = BooleanField("Calls")
    filter = SubmitField("Filter")
    reset = SubmitField("Remove Filter")  # , render_kw={"style": "float:right;"})  # problems on smaller resolutions


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit comment")
