from flask import session
from wtforms.validators import ValidationError
from app.models import BankCard

class CaptchaError(object):
    """验证码验证"""
    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if session.get("captcha").lower()!=field.data.lower():
            raise ValidationError(self.message)


class BankCardVerify(object):
    def card(self,card_str,id=None):
        print(card_str,id)
        """银行卡号验证"""
        if len(card_str)==0:
            raise ValueError("银行卡号不能为空")

        if id is None:
            if BankCard.card_exist(card_str):
                raise ValueError("{} is exist".format(card_str))
        else:
            if BankCard.card_exist(card_str,cardid=id):
                raise ValueError("{} is exist".format(card_str))


        return card_str

    def name(self,name_str):
        """银行卡名称验证"""
        if len(name_str)==0:
            raise ValueError("银行卡名称不能为空")
        else:
            return name_str
    def id_exist(self,id_int):
        """ID 验证"""

        if id_int.isdigit():
            if BankCard.id_exist(id_int):
                if BankCard.id_exist(id_int):
                    return int(id_int)
            else:
                raise ValueError("{} is not exist".format(id_int))
        else:
            raise ValueError("type error must but int")