from . import admin

from flask import render_template, redirect, url_for, session, request, jsonify, flash
from .forms import LoginForm, UserForm, BankCardForm, RegisterForm
from app.models import User, Loginlog, BankCard, P2P, UserP2P, Invest, BillFlow
from functools import wraps
from app import db, app
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy.sql import func
import json

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


@admin.route("/logout", methods=["GET"])
@admin_login_req
def logout():
    session.pop("userid")
    session.pop("login")
    return redirect(url_for("admin.login"))


@admin.route("/modifypwd", methods=["POST"])
@admin_login_req
def modifypwd():
    oldpwd = request.form.get("oldpwd")
    newpwd = request.form.get("newpwd")
    repwd = request.form.get("repwd")
    id = int(session.get("userid"))
    user = User.query.filter_by(id=id).first()
    if user.check_pwd(oldpwd):
        if newpwd == repwd:
            user.set_pwd(newpwd)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("admin.logout"))
    return redirect(url_for("admin.index"))


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


# 添加投资记录
@admin.route("/invest/add", methods=["GET", "POST"])
@admin_login_req
def addinvest():
    if request.method == "GET":
        p2ps = P2P.query.all()
        return render_template("addinvest.html", p2ps=p2ps)
    if request.method == "POST":
        p2p_id = request.form.get("p2p_id")
        profit = request.form.get("profit")
        money = request.form.get("money")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        lucre = request.form.get("lucre")
        invest = Invest(p2p_id=p2p_id, user_id=int(session.get("userid")), profit=profit, money=money,
                        start_time=start_time, end_time=end_time, lucre=lucre)
        db.session.add(invest)
        db.session.commit()
        return redirect(url_for("admin.invest", page=1))


# 删除投资记录
@admin.route("/invest/del", methods=["GET"])
@admin_login_req
def delinvest():
    id = int(request.args.get("id"))
    invest = Invest.query.filter_by(id=id).first()
    print(invest)
    db.session.delete(invest)
    db.session.commit()
    return redirect(url_for("admin.invest", page=1))


@admin.route("/invest/done", methods=["GET"])
@admin_login_req
def doneinvest():
    id = int(request.args.get("id"))
    invest = Invest.query.filter_by(id=id).first()
    if invest.status != 1:
        flash("当前投资还未到期")
        return redirect(url_for("admin.invest", page=1))
    # 只有投资状态为到期才能确认
    invest.status = 2
    db.session.add(invest)
    db.session.commit()
    return redirect(url_for("admin.invest", page=1))


# 资金流水
@admin.route("/billflow/<int:page>", methods=["GET"])
@admin_login_req
def billflow(page=None):
    if page is None:
        page = 1
    page_data = BillFlow.query.filter_by(user_id=int(session.get("userid"))).paginate(page=page, per_page=10)
    return render_template("billflow.html", billflowpage=True, page_data=page_data)


# 添加资金流水
@admin.route("/billflow/add", methods=["GET", "POST"])
@admin_login_req
def addbillflow():
    if request.method == "GET":
        p2ps = P2P.query.all()
        banks = BankCard.query.filter_by(user_id=int(session.get("userid")))
        return render_template("addbillflow.html", banks=banks, p2ps=p2ps)
    if request.method == "POST":
        p2p_id = request.form.get("p2p_id")
        card_id = request.form.get("card_id")
        money = request.form.get("money")
        type = request.form.get("type")
        billflow = BillFlow(p2p_id=p2p_id, card_id=card_id, money=int(money), type=int(type),
                            user_id=session.get("userid"))
        db.session.add(billflow)
        db.session.commit()
        return redirect(url_for("admin.billflow", page=1))


# 完成资金流水
@admin.route("/billflow/done", methods=["GET"])
@admin_login_req
def donebillflow():
    if request.method == "GET":
        id = int(request.args.get("id"))
        billflow = BillFlow.query.filter_by(id=id).first()
        billflow.status = 1
        billflow.donetime = datetime.now()
        db.session.add(billflow)
        db.session.commit()
        return redirect(url_for("admin.billflow", page=1))


# 删除资金流水
@admin.route("/billflow/del", methods=["GET"])
@admin_login_req
def delbillflow():
    if request.method == "GET":
        id = int(request.args.get("id"))
        billflow = BillFlow.query.filter_by(id=id).first()
        db.session.delete(billflow)
        db.session.commit()
        return redirect(url_for("admin.billflow", page=1))


# 用户平台
@admin.route("/userp2p/<int:page>", methods=["GET"])
@admin_login_req
def userp2p(page=None):
    if page is None:
        page = 1
    page_data = UserP2P.query.filter_by(user_id=int(session.get("userid"))).order_by(UserP2P.id).paginate(page=page,
                                                                                                          per_page=10)
    return render_template("userp2p.html", userp2ppage=True, page_data=page_data)


@admin.route("/userp2p/add", methods=["GET", "POST"])
@admin_login_req
def adduserp2p():
    if request.method == "GET":
        banks = BankCard.query.all()
        p2ps = P2P.query.all()
        return render_template("adduserp2p.html", p2ps=p2ps, banks=banks)
    if request.method == "POST":
        p2p_id = request.form.get("p2p_id")
        account = request.form.get("account")
        password = request.form.get("password")
        phone = request.form.get("phone")
        card_id = request.form.get("card_id")
        userp2p = UserP2P(p2p_id=p2p_id, user_id=int(session.get("userid")), account=account, password=password,
                          card_id=card_id, phone=phone)
        db.session.add(userp2p)
        db.session.commit()
        return redirect(url_for("admin.userp2p", page=1))


@admin.route("/userp2p/modify", methods=["GET", "POST"])
@admin_login_req
def modifyuserp2p():
    if request.method == "GET":
        banks = BankCard.query.all()
        p2ps = P2P.query.all()
        id = int(request.args.get("id"))
        userp2p = UserP2P.query.filter_by(id=id).first()
        return render_template("modifyuserp2p.html", userp2p=userp2p, banks=banks, p2ps=p2ps)
    if request.method == "POST":
        id = int(request.form.get("id"))
        p2p_id = request.form.get("p2p_id")
        card_id = request.form.get("card_id")
        account = request.form.get("account")
        password = request.form.get("password")
        phone = request.form.get("phone")
        userp2p = UserP2P.query.filter_by(id=id).first()
        userp2p.p2p_id = p2p_id
        userp2p.card_id = card_id
        userp2p.account = account
        userp2p.password = password
        userp2p.phone = phone
        db.session.add(userp2p)
        db.session.commit()
        return redirect(url_for("admin.userp2p", page=1))


@admin.route("/userp2p/del", methods=["GET"])
@admin_login_req
def deluserp2p():
    if request.method == "GET":
        id = int(request.args.get("id"))
        userp2p = UserP2P.query.filter_by(id=id).first()
        db.session.delete(userp2p)
        db.session.commit()
        return redirect(url_for("admin.userp2p", page=1))


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
        p2p = P2P.query.filter_by(id=id).first()
        p2p.name = name
        p2p.url = url
        p2p.funds_deposit = True if funds_deposit else False
        p2p.risk_deposit = True if risk_deposit else False
        db.session.add(p2p)
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
    return redirect(url_for("admin.p2p", page=1))


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


# 供ajax调用局部更新页面
@admin.route("/userinfo", methods=["GET"])
@admin_login_req
def userinfo():
    id = session.get("userid")
    user = User.query.filter_by(id=int(id)).first()
    return jsonify(user.to_json())


# 登录日志
@admin.route("/loginlog/<int:page>", methods=["GET"])
@admin_login_req
def loginlog(page=None):
    if page is None:
        page = 1
    page_data = Loginlog.query.filter_by(user_id=int(session.get("userid"))).order_by(Loginlog.addtime.desc()).paginate(
        page=page, per_page=10)
    return render_template("loginlog.html", loginlogpage=True, page_data=page_data)


# 注册
@admin.route("/register", methods=["GET", "POST"])
def register():
    error = None
    form = RegisterForm()
    if request.method == "POST":
        if form.validate_on_submit():
            username = request.form.get("username")
            nickname = request.form.get("nickname")
            email = request.form.get("email")
            password = request.form.get("password")
            phone = request.form.get("phone")
            verify_code = request.form.get("verify_code")
            user = User(username=username, nickname=nickname, email=email, phone=phone, password=password)
            db.session.add(user)
            db.session.commit()
            session["userid"] = user.id
            session["login"] = user.username
            return redirect(url_for("admin.index"))
    return render_template("register.html", form=form, error=error)


@admin.route("/overview", methods=["GET"])
@admin_login_req
def overview():
    if request.method == "GET":
        userid = int(session.get("userid"))
        overview = {}
        # 投资中金额，最大年利率,待收益,投资中的平台数去重复
        investinfo = db.session.query(func.sum(Invest.money).label("investment_money"),
                                      func.max(Invest.profit).label("investment_max_profit"),
                                      func.sum(Invest.lucre).label("investment_lucre"),
                                      func.count(func.distinct(Invest.id)).label("count_p2p")).filter_by(user_id=userid,
                                                                                                         status=0).first()
        # 7天内即将到期
        count_expire = db.session.query(func.count(Invest.id).label("expiring_invest")).filter(Invest.user_id == userid,
                                                                                               Invest.status == 0,
                                                                                               Invest.end_time >= (
                                                                                               datetime.now() - timedelta(
                                                                                                   days=7))).first()
        # 投资已到期，需要确认
        expire_invest = db.session.query(func.count(Invest.id).label("expire_invest")).filter(Invest.user_id == userid,
                                                                                              Invest.status == 1,
                                                                                              Invest.end_time >= datetime.now()).first()
        # 提现，充值金额
        in_money = db.session.query(func.sum(BillFlow.money).label("in_money")).filter_by(user_id=userid, status=1,
                                                                                          type=0).first()
        out_money = db.session.query(func.sum(BillFlow.money).label("out_money")).filter_by(user_id=userid, status=1,
                                                                                            type=1).first()
        # 最近登录时间，ip
        loginfo = db.session.query(Loginlog.ip, Loginlog.addtime).filter_by(user_id=userid).order_by(
            Loginlog.id.desc()).first()
        print(in_money.in_money)
        overview["last_login_ip"] = loginfo.ip
        overview["last_login_time"] = str(loginfo.addtime)
        overview["in_money"] = float(in_money.in_money)
        overview["out_money"] = float(out_money.out_money)
        overview["investment_money"] = float(investinfo.investment_money)
        overview["investment_max_profit"] = float(investinfo.investment_max_profit)
        overview["investment_lucre"] = float(investinfo.investment_lucre)
        overview["count_p2p"] = int(investinfo.count_p2p)
        overview["expiring_invest"] =int(count_expire.expiring_invest)
        overview["expire_invest"] = int(expire_invest.expire_invest)
        return jsonify(overview)


@admin.route("/investpercentage")
@admin_login_req
def investpercentage():
    overview={}
    data=[]

    items=db.session.query(func.sum(Invest.money), Invest.p2p_id, P2P.name).filter(Invest.p2p_id == P2P.id,Invest.status==0).group_by(
            Invest.p2p_id).all()
    for i in items:
        item={}
        item["sum_money"]=float(i[0])
        item["p2p_id"]=int(i[1])
        item["p2p_name"]=str(i[2])
        data.append(item)
    overview["percentage"] =data
    return jsonify(overview)

