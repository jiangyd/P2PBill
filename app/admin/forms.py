from flask_wtf import FlaskForm,csrf
from flask_wtf.file import FileField,FileRequired,FileAllowed

from wtforms import StringField,PasswordField

from wtforms.validators import DataRequired,ValidationError

class LoginForm(FlaskForm):
    username=StringField(validators=[DataRequired()])
    password=PasswordField(validators=[DataRequired()])


class UserForm(FlaskForm):
    username = StringField(label="用户名",validators=[DataRequired()])
    nickname = StringField(label="昵称",validators=[DataRequired()])
    email = StringField(label="邮箱",validators=[DataRequired()])
    phone = StringField(label="手机",validators=[DataRequired()])
    face = FileField(label="头像",validators=[ FileAllowed(['jpg', 'png','jpeg','gif'], 'Images only!')])

class BankCardForm():
    name=StringField(label="开户行",validators=[DataRequired()])
    card=StringField(label="银行卡号",validators=[DataRequired()])


