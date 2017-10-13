from flask_wtf import FlaskForm,csrf

from wtforms import StringField,PasswordField

from wtforms.validators import DataRequired,ValidationError

class LoginForm(FlaskForm):
    username=StringField(validators=[DataRequired()])
    password=PasswordField(validators=[DataRequired()])
