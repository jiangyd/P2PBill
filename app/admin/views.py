from . import admin

from flask import render_template,redirect,url_for,session,request
from .forms import LoginForm
from app.models import User
from functools import wraps


def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if not session.get("login",None):
            return redirect(url_for("admin.login"))
        return f(*args,**kwargs)
    return decorated_function


@admin.route("/login",methods=["GET","POST"])
def login():
    error=None
    form=LoginForm()
    if request.method=="POST":
        if form.validate_on_submit():
            user=User.query.filter_by(username=form.data["username"]).first()
            if not user or not user.check_pwd(form.data["password"]):
                error="用户名或密码错误"
                return render_template("login.html",form=form,error=error)
            session["login"]=form.data["username"]
            return redirect(url_for("admin.index"))
    return render_template("login.html",form=form,error=error)

