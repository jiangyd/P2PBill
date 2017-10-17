from . import admin

from flask import render_template, redirect, url_for, session, request
from .forms import LoginForm, UserForm, BankCardForm
from app.models import User, Loginlog, BankCard, P2P, UserP2P, Invest, BillFlow
from functools import wraps
from app import db, app
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import os


def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("login", None):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)

    return decorated_function


@admin.route("/login", methods=["GET", "POST"])
def login():
    error = None
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.data["username"]).first()
            if not user or not user.check_pwd(form.data["password"]):
                error = "用户名或密码错误"
                return render_template("login.html", form=form, error=error)
            session["login"] = form.data["username"]
            session["userid"] = user.id
            log = Loginlog(user.id, request.remote_addr)
            db.session.add(log)
            db.session.commit()
            return redirect(url_for("admin.index"))
    return render_template("login.html", form=form, error=error)


@admin.route("/index")
@admin_login_req
def index():
    return render_template("dashboard.html", dashboardpage=True)


# 投资记录
@admin.route("/invest/<int:page>", methods=["GET"])
@admin_login_req
def invest(page=None):
    if page is None:
        page = 1
    page_data = Invest.query.filter_by(user_id=int(session.get("userid"))).paginate(page=page, per_page=10)
    return render_template("invest.html", investpage=True, page_data=page_data)


# 资金流水
@admin.route("/billflow/<int:page>", methods=["GET"])
@admin_login_req
def billflow(page=None):
    if page is None:
        page = 1
    page_data = BillFlow.query.filter_by(user_id=int(session.get("userid"))).paginate(page=page, per_page=10)
    return render_template("billflow.html", billflowpage=True, page_data=page_data)


# 用户平台
@admin.route("/userp2p/<int:page>", methods=["GET"])
@admin_login_req
def userp2p(page=None):
    if page is None:
        page = 1
    page_data = UserP2P.query.order_by(UserP2P.id).paginate(page=page, per_page=10)
    return render_template("userp2p.html", userp2ppage=True, page_data=page_data)
@admin.route("/userp2p/add",methods=["GET","POST"])
@admin_login_req
def adduserp2p():
    if request.method=="GET":
        banks=BankCard.query.all()
        p2ps=P2P.query.all()
        return render_template("adduserp2p.html",p2ps=p2ps,banks=banks)
    if request.method=="POST":
        print("sfaddsfadadsfasdfdfasfa")
        p2p_id=request.form.get("p2p_id")
        account=request.form.get("account")
        password=request.form.get("password")
        phone=request.form.get("phone")
        card_id=request.form.get("card_id")
        print("p2p_id",p2p_id)
        print("card_id",card_id)
        userp2p=UserP2P(p2p_id=p2p_id,user_id=int(session.get("userid")),account=account,password=password,card_id=card_id,phone=phone)
        db.session.add(userp2p)
        db.session.commit()
        print("dsffs")
        return redirect(url_for("admin.userp2p",page=1))



# 平台信息
@admin.route("/p2p/<int:page>", methods=["GET"])
@admin_login_req
def p2p(page=None):
    if page is None:
        page = 1
    page_data = P2P.query.order_by(P2P.id).paginate(page=page, per_page=10)
    return render_template("p2p.html", p2ppage=True, page_data=page_data)


@admin.route("/p2p/add", methods=["POST"])
@admin_login_req
def addp2p():
    if request.method == "POST":
        p2p_name = request.form["p2p_name"]
        p2p_url = request.form["p2p_url"]
        risk = True if request.form.get("risk_deposit", None) else False
        funds = True if request.form.get("funds_deposit", None) else False
        if len(p2p_name) > 0 and len(p2p_url) > 0:
            p2p = P2P(name=p2p_name, url=p2p_url, funds_deposit=funds, risk_deposit=risk)
            db.session.add(p2p)
            db.session.commit()
            return redirect(url_for("admin.p2p", page=1))
    return redirect(url_for("admin.p2p", page=1))


@admin.route("/p2p/modify", methods=["GET", "POST"])
@admin_login_req
def modifyp2p():
    if request.method == "GET":
        id = int(request.args.get("id"))
        p2p = P2P.query.filter_by(id=id).first()
    if request.method == "POST":
        id = int(request.form.get("id"))
        name = request.form.get("p2p_name")
        url = request.form.get("p2p_url")
        funds_deposit = request.form.get("funds_deposit")
        risk_deposit = request.form.get("risk_deposit")
        p2p = P2P.query.filter_by(id=id)
        p2p.name = name
        p2p.url = url
        p2p.funds_deposit = True if funds_deposit else False
        p2p.risk_deposit = True if risk_deposit else False
        db.session.add("p2p")
        db.session.commit()
        return redirect(url_for("admin.p2p", page=1))
    return render_template("modifyp2p.html", p2p=p2p)


@admin.route("/p2p/del", methods=["GET"])
@admin_login_req
def delp2p():
    id = request.args.get("id")
    p2p = P2P.query.filter_by(id=id).first()
    db.session.delete(p2p)
    db.session.commit()
    return redirect(url_for("admin.p2p",page=1))


# 银行卡信息
@admin.route("/bankcard/<int:page>", methods=["GET"])
@admin_login_req
def bankcard(page=None):
    if page is None:
        page = 1
    page_data = BankCard.query.filter_by(user_id=int(session.get("userid"))).paginate(page=page, per_page=10)
    return render_template("bankcard.html", bankcardpage=True, page_data=page_data)


# 添加银行卡
@admin.route("/bankcard/add", methods=["POST"])
@admin_login_req
def addbank():
    if request.method == "POST":
        bank_name = request.form["bank_name"]
        bank_card = request.form["bank_card"]
        if len(bank_name) > 0 and len(bank_card) > 0:
            bankcard = BankCard(name=bank_name, card=bank_card, user_id=int(session.get("userid")))
            db.session.add(bankcard)
            db.session.commit()
            return redirect(url_for("admin.bankcard", page=1))
    return redirect(url_for("admin.bankcard", page=1))


@admin.route("/bankcard/modify", methods=["GET", "POST"])
@admin_login_req
def modifybank():
    if request.method == "GET":
        id = int(request.args.get("id"))
        bank = BankCard.query.filter_by(id=id).first()
    if request.method == "POST":
        id = int(request.form["id"])
        name = request.form["bank_name"]
        card = request.form["bank_card"]
        bank = BankCard.query.filter_by(id=id).first()
        bank.name = name
        bank.card = card
        db.session.add(bank)
        db.session.commit()
        return redirect(url_for("admin.bankcard", page=1))
    return render_template("modifybank.html", bank=bank)


@admin.route("/bankcard/del", methods=["GET"])
@admin_login_req
def delbank():
    id = request.args.get("id")  # 银行卡id
    bankcard = BankCard.query.filter_by(id=int(id)).first()
    db.session.delete(bankcard)
    db.session.commit()
    return redirect(url_for("admin.bankcard", page=1))


# 用户信息
@admin.route("/user", methods=["GET", "POST"])
@admin_login_req
def user():
    form = UserForm()
    user = User.query.filter_by(username=session.get("login")).first()
    if request.method == "GET":
        form.username.data = user.username
        form.nickname.data = user.nickname
        form.email.data = user.email
        form.phone.data = user.phone
        form.face.data = user.face
    if form.validate_on_submit():
        f = form.face.data
        if f is not None:
            face_filename = secure_filename(f.filename)
            f.save(os.path.join(app.config["UPLOAD_FOLDER"], face_filename))
            user.face = face_filename
        user.nickname = form.nickname.data
        user.email = form.email.data
        user.phone = form.phone.data
        db.session.add(user)
        db.session.commit()
    return render_template("user.html", userpage=True, form=form, user=user)


# 登录日志
@admin.route("/loginlog/<int:page>", methods=["GET"])
@admin_login_req
def loginlog(page=None):
    if page is None:
        page = 1
    page_data = Loginlog.query.order_by(Loginlog.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("loginlog.html", loginlogpage=True, page_data=page_data)
