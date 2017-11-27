from flask_sqlalchemy import SQLAlchemy

from flask_apscheduler import APScheduler

from flask_restful import Api

from flask_cors import CORS

cors=CORS()

db=SQLAlchemy()

scheduler=APScheduler()

restful=Api()

