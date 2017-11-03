from .models import Invest
from app import app,db
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.admin.util import SendMailByAli
from flask_apscheduler import APScheduler


#到期投资
def expire_invest(num):
    data=db.session.query(func.count(Invest.id).label("expiring_invest")).filter(
    Invest.status == 0,
    Invest.end_time == (
        datetime.now() - timedelta(
            days=num))).all()
    # 发邮件提醒投资人，投资到期
    for item in data:
        print(item)
    # SendMailByAli.send_mail(toaddress=, htmlbody="", )
    return data

JOBS = [
    {
        'id': 'createschuler_job',
        'func': expire_invest,
        'args': 7,
        'trigger': 'interval',
        'seconds': 5
    }
]


app.config["JOBS"]=JOBS
scheduler=APScheduler()
scheduler.init_app(app)
scheduler.start()






