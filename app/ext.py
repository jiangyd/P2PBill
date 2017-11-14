from flask_sqlalchemy import SQLAlchemy

from flask_apscheduler import APScheduler

from flask_restful import Api

db=SQLAlchemy()

scheduler=APScheduler()

restful_api=Api()

