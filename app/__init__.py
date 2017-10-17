from flask import Flask,render_template

import os

from flask_sqlalchemy import SQLAlchemy

app=Flask(__name__)
app.config["SECRET_KEY" ]='you-will-never-guess'
app.config["SQLALCHEMY_DATABASE_URI"]="mysql+pymysql://root:123456@192.168.56.102:3377/p2pbill"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=True

#头像保存位置
UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)),"static/uploads")
app.config['UPLOAD_FOLDER'] =UPLOAD_FOLDER
db=SQLAlchemy(app)

from app.admin import admin as admin_blueprint
app.register_blueprint(admin_blueprint,url_prefix="/admin")