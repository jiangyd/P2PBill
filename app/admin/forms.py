from flask_wtf import FlaskForm,csrf,RecaptchaField
from flask_wtf.file import FileField,FileRequired,FileAllowed

from wtforms import StringField,PasswordField

from wtforms.validators import DataRequired,ValidationError,Regexp

from app.models import User

class LoginForm(FlaskForm):
    username=StringField(validators=[DataRequired("请输入用户名")])
    password=PasswordField(validators=[DataRequired("请输入密码")])


class UserForm(FlaskForm):
    username = StringField(label="用户名",validators=[DataRequired("请输入用户名")])
    nickname = StringField(label="昵称",validators=[DataRequired("请输入昵称")])
    email = StringField(label="邮箱",validators=[DataRequired("请输入邮箱")])
    phone = StringField(label="手机",validators=[DataRequired("请输入手机")])
    face = FileField(label="头像",validators=[ FileAllowed(['jpg', 'png','jpeg','gif'], 'Images only!')])

class BankCardForm(FlaskForm):
    name=StringField(label="开户行",validators=[DataRequired("请输入开户行")])
    card=StringField(label="银行卡号",validators=[DataRequired("请输入银行卡号")])

class ForgetPwdForm(FlaskForm):
    email=StringField(label="邮箱",validators=[DataRequired("请输入邮箱")])
    recaptcha=RecaptchaField()



class RegisterForm(FlaskForm):
    username=StringField(label="用户名", validators=[DataRequired("请输入用户名")])
    nickname = StringField(label="昵称", validators=[DataRequired("请输入昵称")])
    password=PasswordField(label="密码",validators=[DataRequired("请输入密码")])
    email = StringField(label="邮箱", validators=[DataRequired("请输入邮箱")])
    phone = StringField(label="手机", validators=[DataRequired("请输入手机"),Regexp("1[34578]\\d{9}",message="手机号格式错误")])
    verify_code=StringField(label="验证码",validators=[DataRequired("请输入验证码")])
    def validate_username(self,field):
        username=field.data
        user=User.query.filter_by(username=username).first()
        if user:
            raise ValidationError("用户已存在")
    def validate_phone(self,field):
        phone = field.data
        user = User.query.filter_by(phone=phone).first()
        if user:
            raise ValidationError("手机号已存在")
    def validate_email(self,field):
        email = field.data
        user = User.query.filter_by(email=email).first()
        if user:
            raise ValidationError("邮箱已存在")

