from .models import Invest, User
from app.ext import db
from sqlalchemy.sql import func
from datetime import datetime, timedelta


# 到期投资
def expire_invest(num):
    with db.app.app_context():
        data = Invest.query.filter(Invest.status == 0,func.DATE_FORMAT(Invest.start_time,'%Y-%m-%d') == (datetime.now() - timedelta(days=num)).strftime("%Y-%m-%d")).all()
        print(data)
        # 发邮件提醒投资人，投资到期
        for item in data:
            print(item)
            # SendMailByAli.send_mail(toaddress=, htmlbody="", )
        return data


JOBS = [
    {
        'id': 'createschuler_job',
        'func': expire_invest,
        'args': (7,),
        'trigger': 'interval',
        'seconds': 50000
    }
]
