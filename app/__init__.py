from flask import Flask,render_template

from app.admin import admin as admin_blueprint


app=Flask(__name__)
app.config["SECRET_KEY" ]='you-will-never-guess'

app.register_blueprint(admin_blueprint,url_prefix="/admin")