from flask import session
from wtforms.validators import ValidationError

class CaptchaError(object):
    """验证码验证"""
    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if session.get("captcha").lower()!=field.data.lower():
            raise ValidationError(self.message)