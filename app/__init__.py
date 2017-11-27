from flask import Flask,render_template
from app.crontab import JOBS

from app.ext import db,scheduler,restful,cors

import os




app=Flask(__name__)

app.config["SECRET_KEY" ]='you-will-never-guess'
app.config["SQLALCHEMY_DATABASE_URI"]="mysql+pymysql://root:123456@127.0.0.1:3306/p2pbill"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=True
app.config["SQLALCHEMY_ECHO"]=False

db.app=app
db.init_app(app)

#头像保存位置
UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)),"static/uploads")
app.config['UPLOAD_FOLDER'] =UPLOAD_FOLDER




app.config["JOBS"]=JOBS

scheduler.init_app(app)
scheduler.start()

from app.admin import admin as admin_blueprint
app.register_blueprint(admin_blueprint,url_prefix="/admin")
restful.init_app(app)

#解决跨域问题
cors.init_app(app,resources={r"/admin/*": {"origins": "*"}})

