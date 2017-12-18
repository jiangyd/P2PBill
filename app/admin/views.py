from . import admin
from .vericode import veri_code
from io import BytesIO
from flask import render_template, redirect, url_for, session, request, jsonify, flash, Response
from .forms import LoginForm, UserForm, BankCardForm, RegisterForm, ForgetPwdForm, RePwdForm
from app.models import User, Loginlog, BankCard, P2P, UserP2P, Invest, BillFlow, ForGetPwd
from functools import wraps
from app import app
from app.ext import db, restful
from flask_restful import Resource, reqparse, fields, marshal_with
from app.config import htmlbody, config
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy.sql import func
import json
from .util import get_secret, SendMailByAli
from .cus_validation import BankCardVerify
import onetimepass as totp
from flask import g, make_response
import time
import uuid
import os
import hashlib
import math

from flask_httpauth import HTTPTokenAuth
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

auth = HTTPTokenAuth(scheme='Bearer')
serializer = Serializer(app.config["SECRET_KEY"], expires_in=1800)


def create_token(data):
    """生成token"""
    token = serializer.dumps(data)
    return token.decode("utf-8")


@auth.verify_token
def verify_token(token):
    """验证token"""
    g.user = User.query.filter_by(token=token).first()
    return g.user is not None


def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("username", None) or not session.get("userid", None):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)

    return decorated_function


class LoginApi(Resource):
    """登录接口"""

    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('username', type=str, required=True, location=['json'])
        parse.add_argument('password', type=str, required=True, location=['json'])
        args = parse.parse_args()
        user = User.query.filter_by(username=args.username).first()
        if not user or not user.check_pwd(args.password):
            res = make_response(jsonify({"code": 1, "msg": "用户或密码错误"}))
            return res
        else:
            token = create_token({"username": user.username, "password": user.password})
            user.token = token
            db.session.add(user)
            db.session.commit()
            res = make_response(jsonify({"code": 0, "msg": "", "data": {"username": user.username,
                                                                        "nickname": user.nickname,
                                                                        "email": user.email,
                                                                        "phone": user.phone,
                                                                        "face": user.face,
                                                                        "mfa_status": user.mfa_status,
                                                                        "token": token}}))
            return res


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
            session["username"] = form.data["username"]
            if user.mfa_status:
                return render_template("verify_code.html")
            session["userid"] = user.id
            log = Loginlog(user.id, request.remote_addr)
            db.session.add(log)
            db.session.commit()
            return redirect(url_for("admin.index"))
    return render_template("login.html", form=form, error=error)


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


class BankCardApi(Resource):
    decorators = [auth.login_required]
    def get(self):
        verify = BankCardVerify()
        parse = reqparse.RequestParser()
        parse.add_argument('id', type=verify.id_exist, required=True, location=['args'])
        args = parse.parse_args()
        bankcard = BankCard.query.filter_by(user_id=g.user.id, id=args.id).first()

        return jsonify({"code": 0, "msg": "","data":{"id":bankcard.id,"name":bankcard.name,"card":bankcard.card}})

    def post(self):
        verify = BankCardVerify()
        parse = reqparse.RequestParser()
        parse.add_argument('name', type=verify.name, required=True, location=['json'])
        parse.add_argument('card', type=verify.card, required=True, location=['json'])
        args = parse.parse_args()
        bankcard = BankCard(name=args.name, card=args.card, user_id=g.user.id)
        db.session.add(bankcard)
        db.session.commit()
        return jsonify({"code": 0, "msg": ""})

    def put(self):
        verify = BankCardVerify()
        parse = reqparse.RequestParser()
        parse.add_argument('id', type=verify.id_exist, required=True, location=['json'])
        parse.add_argument('name', type=verify.name, required=True, location=['json'])
        # 设置银行卡id
        verify.cardid = parse.parse_args().id
        parse.add_argument('card', type=verify.card, required=True, location=['json'])
        args = parse.parse_args()
        bankcard = BankCard.query.filter_by(id=args.id).first()
        if bankcard.user_id != g.user.id:
            return jsonify({"code": 1, "msg": "无权限修改"})
        bankcard.name = args.name
        bankcard.card = args.card
        db.session.add(bankcard)
        db.session.commit()
        return jsonify({"code": 0, "msg": ""})

    def delete(self):
        verify = BankCardVerify()
        parse = reqparse.RequestParser()
        parse.add_argument('id', type=verify.id_exist, required=True, location=['json'])
        args = parse.parse_args()
        bankcard = BankCard.query.filter_by(id=args.id).first()
        if bankcard.user_id != g.user.id:
            return jsonify({"code": 1, "msg": "无权限删除"})
        db.session.delete(bankcard)
        db.session.commit()
        return jsonify({"code": 0, "msg": "删除成功"})




# 添加银行卡
@admin.route("/bankcard/add", methods=["GET"])
def addbank():
    return render_template("addbankcard.html")


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





# 登录日志
@admin.route("/loginlog/<int:page>", methods=["GET"])
@admin_login_req
def loginlog(page=None):
    if page is None:
        page = 1
    page_data = Loginlog.query.filter_by(user_id=int(session.get("userid"))).order_by(Loginlog.addtime.desc()).paginate(
        page=page, per_page=10)
    return render_template("loginlog.html", loginlogpage=True, page_data=page_data)


class LogoutApi(Resource):
    """登出接口"""
    decorators = [auth.login_required]

    def get(self):
        g.user.token = ""
        db.session.add(g.user)
        db.session.commit()
        return jsonify({"code": 0, "msg": "", "data": []})


class GetUserInfoApi(Resource):
    """获取用户信息"""
    decorators = [auth.login_required]

    def get(self):
        # 判断用户头像是否为空
        face = g.user.face if g.user.face else "face.jpg"
        return jsonify({"code": 0, "msg": "",
                        "data": {"username": g.user.username, "nickname": g.user.nickname, "user_id": g.user.id,
                                 "face": url_for(".static", _external=True, filename="uploads/" + face),
                                 "mfa_status": g.user.mfa_status, "email": g.user.email,
                                 "phone": g.user.phone}})


class LoginLogApi(Resource):
    """获取登录日志接口"""
    decorators = [auth.login_required]
    resource_fields = {'num_result': fields.Integer,
                       "objects": fields.List(fields.Nested({
                           'id': fields.Integer,
                           # 'user': fields.Nested({"username":fields.String}),
                           "username": fields.String,
                           'ip': fields.String,
                           'mfa_status': fields.Boolean,
                           'addtime': fields.String})),
                       "page": fields.Integer,
                       "total_page": fields.Integer
                       }

    @marshal_with(resource_fields, envelope='loginlog_resource')
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('page_index', type=int, required=True, location=['args'])
        args = parse.parse_args()
        login = Loginlog.query.filter_by(user_id=g.user.id).order_by(Loginlog.addtime.desc()).paginate(
            page=args.page_index, per_page=10)
        for i in range(len(login.items)):
            login.items[i].username = login.items[i].user.username
        return {"num_result": login.total, "objects": login.items, "page": login.page, "total_page": login.pages}


class BankListApi(Resource):
    """银行卡管理"""
    decorators = [auth.login_required]
    resource_fields = {"code":fields.Integer,'num_result': fields.Integer,
                       "objects": fields.List(fields.Nested({
                           'id': fields.Integer,
                           # 'user': fields.Nested({"username":fields.String}),
                           "username": fields.String,
                           'name': fields.String,
                           'card': fields.String})),
                       "page": fields.Integer,
                       "total_page": fields.Integer
                       }

    @marshal_with(resource_fields)
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('page_index', type=int, required=False, location=['args'])
        args = parse.parse_args()
        if args.page_index is None:

            bank = BankCard.query.filter_by(user_id=g.user.id).order_by(BankCard.id.desc()).paginate()
        else:
            bank = BankCard.query.filter_by(user_id=g.user.id).order_by(BankCard.id.desc()).paginate(
                page=args.page_index,
                per_page=10)
        for i in range(len(bank.items)):
            bank.items[i].username = bank.items[i].user.username
        return {"code":0,"num_result": bank.total, "objects": bank.items, "page": bank.page, "total_page": bank.pages}


class P2PListApi(Resource):
    """p2p平台list"""
    decorators = [auth.login_required]
    resource_fields = {'num_result': fields.Integer,
                       "objects": fields.List(fields.Nested({
                           'id': fields.Integer,
                           "name": fields.String,
                           'url': fields.String,
                           'funds_deposit': fields.Boolean,
                           'risk_deposit': fields.Boolean})),
                       "page": fields.Integer,
                       "total_page": fields.Integer,
                       "code": fields.Integer,
                       "msg": fields.String
                       }

    @marshal_with(resource_fields)
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('page_index', type=int, required=False, location=['args'])
        args = parse.parse_args()
        if args.page_index is None:
            p2p = P2P.query.filter_by().order_by(P2P.id.desc()).paginate()
        else:
            p2p = P2P.query.filter_by().order_by(P2P.id.desc()).paginate(page=args.page_index, per_page=10)
        return {"code": "0", "msg": "", "num_result": p2p.total, "objects": p2p.items, "page": p2p.page,
                "total_page": p2p.pages}


class MyP2PListApi(Resource):
    """我的平台"""
    decorators = [auth.login_required]

    resource_fields = {
        "code": fields.Integer,
        "msg": fields.String,
        "num_result": fields.Integer,
        "page": fields.Integer,
        "total_page": fields.Integer,
        "objects": fields.List(fields.Nested({
            'id': fields.Integer,
            "p2p_id": fields.String,
            "p2p_name": fields.String,
            'username': fields.String,
            'account': fields.String,
            'password': fields.String,
            "card_id": fields.Integer,
            "card_name": fields.String,
            "card_card": fields.String,
            "phone": fields.String
        }))
    }

    @marshal_with(resource_fields)
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('page_index', type=int, required=True, location=['args'])
        args = parse.parse_args()
        myp2p = UserP2P.query.filter_by(user_id=g.user.id).order_by(UserP2P.id.desc()).paginate(page=args.page_index,
                                                                                                per_page=10)
        for i in range(len(myp2p.items)):
            myp2p.items[i].username = myp2p.items[i].user.username
            myp2p.items[i].p2p_name = myp2p.items[i].p2p.name
            myp2p.items[i].card_name = myp2p.items[i].bankcard.name
            myp2p.items[i].card_card = myp2p.items[i].bankcard.card
        return {"code": 0, "msg": "", "num_result": myp2p.total, "objects": myp2p.items, "page": myp2p.page,
                "total_page": myp2p.pages}

class MyP2PApi(Resource):
    """我的p2p"""
    decorators = [auth.login_required]
    def post(self):
        parse=reqparse.RequestParser()
        parse.add_argument('p2p_id',type=int,required=True,location=['json'])
        parse.add_argument('account',type=str,required=True,location=['json'])
        parse.add_argument('password',type=str,required=True,location=['json'])
        parse.add_argument('card_id',type=int,required=True,location=['json'])
        parse.add_argument('phone',type=int,required=True,location=['json'])
        args=parse.parse_args()
        myp2p=UserP2P(user_id=g.user.id,p2p_id=args.p2p_id,account=args.account,password=args.password,card_id=args.card_id,phone=args.phone)
        db.session.add(myp2p)
        db.session.commit()
        return jsonify({"code":0,"msg":""})
    def put(self):
        parse = reqparse.RequestParser()
        parse.add_argument("id",type=int,required=True,location=['json'])
        parse.add_argument('p2p_id', type=int, required=True, location=['json'])
        parse.add_argument('account', type=str, required=True, location=['json'])
        parse.add_argument('password', type=str, required=True, location=['json'])
        parse.add_argument('card_id', type=int, required=True, location=['json'])
        parse.add_argument('phone', type=int, required=True, location=['json'])
        args = parse.parse_args()
        myp2p=UserP2P.query.filter_by(id=args.id).first()
        if myp2p.user_id!=g.user.id:
            return jsonify({"code":1,"msg":"无权限修改"})
        myp2p.p2p_id=args.p2p_id
        myp2p.account=args.account
        myp2p.password=args.password
        myp2p.phone=args.phone
        myp2p.card_id=args.card_id
        db.session.add(myp2p)
        db.session.commit()
        return jsonify({"code": 0, "msg": ""})
    def get(self):
        """查看我的p2p信息"""
        parse=reqparse.RequestParser()
        parse.add_argument("id", type=int, required=True, location=['args'])
        args = parse.parse_args()
        myp2p = UserP2P.query.filter_by(id=args.id).first()
        return jsonify({"code": 0, "msg": "","data":{"id":myp2p.id,"p2p_id":myp2p.p2p_id,"account":myp2p.account,"password":myp2p.password,"card_id":myp2p.card_id,"phone":myp2p.phone}})

    def delete(self):
        """删除我的p2p"""
        parse = reqparse.RequestParser()
        parse.add_argument("id", type=int, required=True, location=['args'])
        args = parse.parse_args()
        myp2p = UserP2P.query.filter_by(id=args.id).first()
        if myp2p.user_id!=g.user.id:
            return jsonify({"code":1,"msg":"无权限删除"})
        db.session.delete(myp2p)
        db.session.commit()
        return jsonify({"code":0,"msg":""})





class BillFlowListApi(Resource):
    """资金流水"""
    decorators = [auth.login_required]

    resource_fields = {
        "code": fields.Integer,
        "msg": fields.String,
        "num_result": fields.Integer,
        "page": fields.Integer,
        "total_page": fields.Integer,
        "objects": fields.List(fields.Nested({
            'id': fields.Integer,
            "p2p_id": fields.String,
            "p2p_name": fields.String,
            'username': fields.String,
            "money": fields.Float,
            "status": fields.Integer,
            "type": fields.Integer,
            "card_id": fields.Integer,
            "card_name": fields.String,
            "card_card": fields.String,
            "addtime": fields.String,
            "donetime": fields.String,
        }))
    }

    @marshal_with(resource_fields)
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('page_index', type=int, required=True, location=['args'])
        args = parse.parse_args()
        billflow = BillFlow.query.filter_by(user_id=g.user.id).order_by(BillFlow.addtime.desc()).paginate(
            page=args.page_index, per_page=10)
        for i in range(len(billflow.items)):
            billflow.items[i].username = billflow.items[i].user.username
            billflow.items[i].p2p_name = billflow.items[i].p2p.name
            billflow.items[i].card_name = billflow.items[i].bankcard.name
            billflow.items[i].card_card = billflow.items[i].bankcard.card
        return {"code": 0, "msg": "", "num_result": billflow.total, "objects": billflow.items, "page": billflow.page,
                "total_page": billflow.pages}


class InvestListApi(Resource):
    decorators = [auth.login_required]

    resource_fields = {
        "code": fields.Integer,
        "msg": fields.String,
        "num_result": fields.Integer,
        "page": fields.Integer,
        "total_page": fields.Integer,
        "objects": fields.List(fields.Nested({
            'id': fields.Integer,
            "p2p_id": fields.String,
            "p2p_name": fields.String,
            'username': fields.String,
            "money": fields.Float,
            "status": fields.Integer,
            "profit": fields.Integer,
            "lucre": fields.Integer,
            "start_time": fields.String,
            "end_time": fields.String,
        }))
    }

    @marshal_with(resource_fields)
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('page_index', type=int, required=True, location=['args'])
        args = parse.parse_args()
        investlist = Invest.query.filter_by(user_id=g.user.id).order_by(Invest.id.desc()).paginate(page=args.page_index,
                                                                                                   per_page=10)
        for i in range(len(investlist.items)):
            investlist.items[i].p2p_name = investlist.items[i].p2p.name
            investlist.items[i].username = investlist.items[i].user.username
        return {"code": 0, "msg": "", "num_result": investlist.total, "objects": investlist.items,
                "page": investlist.page, "total_page": investlist.pages}


class InvestApi(Resource):
    """投资记录接口"""
    decorators = [auth.login_required]
    def post(self):
        """添加投资记录接口"""
        parse = reqparse.RequestParser()
        parse.add_argument('p2p_id', type=int, required=True, location=['json'])
        parse.add_argument('money', type=float, required=True, location=['json'])
        parse.add_argument('profit', type=float, required=True, location=['json'])
        parse.add_argument('start_time', type=str, required=True, location=['json'])
        parse.add_argument('end_time', type=str, required=True, location=['json'])
        parse.add_argument('lucre', type=float, required=True, location=['json'])
        args = parse.parse_args()
        invest=Invest(p2p_id=args.p2p_id,user_id=g.user.id,money=args.money,profit=args.profit,start_time=args.start_time,end_time=args.end_time,lucre=args.lucre)
        db.session.add(invest)
        db.session.commit()
        return jsonify({"code":0,"msg":""})
    def put(self):
        """修改投资记录接口"""
        parse = reqparse.RequestParser()
        parse.add_argument('id', type=int, required=True, location=['json'])
        parse.add_argument('p2p_id', type=int, required=True, location=['json'])
        parse.add_argument('money', type=float, required=True, location=['json'])
        parse.add_argument('profit', type=float, required=True, location=['json'])
        parse.add_argument('start_time', type=str, required=True, location=['json'])
        parse.add_argument('end_time', type=str, required=True, location=['json'])
        parse.add_argument('lucre', type=float, required=True, location=['json'])
        args = parse.parse_args()
        invest=Invest.query.filter_by(id=args.id).first()
        if invest.user_id!=g.user.id:
            return jsonify({"code":1,"msg":"无权限修改"})
        invest.p2p_id=args.p2p_id
        invest.money=args.money
        invest.profit=args.profit
        invest.start_time=args.start_time
        invest.end_time=args.end_time
        invest.lucre=args.lucre
        db.session.add(invest)
        db.session.commit()
        return jsonify({"code":0,"msg":""})

    def get(self):
        """获取投资记录详情接口"""
        parse=reqparse.RequestParser()
        parse.add_argument('id', type=int, required=True, location=['args'])
        args = parse.parse_args()
        invest=Invest.query.filter_by(id=args.id).first()
        if invest.user_id!=g.user.id:
            return jsonify({"code":1,"msg":"无权限查看"})
        return jsonify({"code":0,"msg":"","data":{"id":invest.id,"p2p_id":invest.p2p_id,"money":invest.money,"profit":invest.profit,"lucre":invest.lucre,"start_time":invest.start_time,"end_time":invest.end_time}})
    def delete(self):
        """删除投资记录接口"""
        parse=reqparse.RequestParser()
        parse.add_argument('id', type=int, required=True, location=['args'])
        args = parse.parse_args()
        invest=Invest.query.filter_by(id=args.id).first()
        if invest.user_id!=g.user.id:
            return jsonify({"code":1,"msg":"无权限删除"})
        db.session.delete(invest)
        db.session.commit()
        return jsonify({"code":0,"msg":""})


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
        overview["expiring_invest"] = int(count_expire.expiring_invest)
        overview["expire_invest"] = int(expire_invest.expire_invest)
        return jsonify(overview)


@admin.route("/investpercentage")
@admin_login_req
def investpercentage():
    overview = {}
    data = []

    items = db.session.query(func.sum(Invest.money), Invest.p2p_id, P2P.name).filter(Invest.p2p_id == P2P.id,
                                                                                     Invest.status == 0).group_by(
        Invest.p2p_id).all()
    for i in items:
        item = {}
        item["sum_money"] = float(i[0])
        item["p2p_id"] = int(i[1])
        item["p2p_name"] = str(i[2])
        data.append(item)
    overview["percentage"] = data
    return jsonify(overview)


@admin.route("/setmfa", methods=["GET", "POST"])
@admin_login_req
def setmfa():
    user = User.query.filter_by(username=session.get("username")).first()
    if request.method == "GET":
        if not user.mfa_status:
            user.secret = get_secret()
            db.session.add(user)
            db.session.commit()
            return render_template("mfa.html", secret=user.secret, nickname=user.nickname)
        else:
            return render_template("closemfa.html")
    if request.method == "POST":
        onecode = request.form.get("onecode")
        twocode = request.form.get("twocode")
        # 判断身份宝验证码是否正确
        if totp.valid_totp(token=twocode, secret=user.secret) and totp.valid_totp(token=onecode, secret=user.secret,
                                                                                  clock=int(time.time()) - 30):
            if user.mfa_status == False:
                user.mfa_status = True
            else:
                user.mfa_status = False
            db.session.add(user)
            db.session.commit()
            return redirect(request.referrer)
        else:
            print(onecode, twocode)
            return redirect(request.referrer)


@admin.route("/verify_maf_code", methods=["POST"])
def verify_mfa_code():
    if request.method == "POST":
        # 获取json数据
        code = json.loads(request.get_data())["code"].strip()
        user = User.query.filter_by(username=session.get("username")).first()
        if len(code) > 0:
            if totp.valid_totp(secret=user.secret, token=code):
                session["userid"] = user.id
                log = Loginlog(user.id, request.remote_addr)
                log.mfa_status = True
                db.session.add(log)
                db.session.commit()
                return jsonify({"code": 0, "msg": "登录成功", "redirect": url_for("admin.index")})
            else:
                return jsonify({"code": 1, "msg": "动态口令无效"})
        else:
            return jsonify({"code": 2, "msg": "动态口令必填"})


@admin.route("/forgetpwd", methods=["GET", "POST"])
def forgetpwd():
    error = None
    form = ForgetPwdForm()
    if request.method == "POST":
        if form.validate_on_submit():
            email = request.form.get("email")
            user = User.query.filter_by(email=email).first()
            captcha_code = request.form.get("captcha")
            if captcha_code.lower() != session.get("captcha").lower():
                error = "验证码错误"
                return render_template("forgetpwd.html", error=error, form=form)
            if not user:
                error = "邮箱不存在"
                return render_template("forgetpwd.html", error=error, form=form)
            else:
                mail = SendMailByAli()
                m = hashlib.md5()
                m.update(str(uuid.uuid4()).encode("utf-8"))
                token = m.hexdigest()
                content = htmlbody.format(nickname=user.nickname, url="http://" + config["host"]["ip"] +
                                                                      ":" + config["host"]["port"]
                                                                      + url_for('admin.repwd', token=token))
                res = mail.send_mail(subject="找回密码", toaddress=email, htmlbody=content)
                # 如果多次找回密码，验证token的时候需要根据expire获取最新一条
                now = datetime.now()
                addtime = now.strftime("%Y-%m-%d %H:%M:%S")
                expiretime = (now + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
                forgetpwd = ForGetPwd(email=email, token=token, addtime=addtime, expiretime=expiretime)
                db.session.add(forgetpwd)
                db.session.commit()
                s = ForGetPwd.query.filter_by().order_by(ForGetPwd.expiretime.desc()).first()
                return jsonify(dict(res))
    return render_template("forgetpwd.html", error=error, form=form)


@admin.route("/repwd", methods=["GET", "POST"])
def repwd():
    error = None
    form = RePwdForm()
    token = None
    if request.method == "GET":
        token = request.args.get("token")
    if request.method == "POST":
        token = request.form.get("token")
        if form.validate_on_submit():
            forgetpwd = ForGetPwd.query.filter_by(token=token).first()
            password = request.form.get("password")
            if forgetpwd:
                if datetime.now() > datetime.strptime(str(forgetpwd.expiretime), "%Y-%m-%d %H:%M:%S") or forgetpwd.use:
                    error = "令牌已过期"
                else:
                    user = User.query.filter_by(email=forgetpwd.email).first()
                    user.set_pwd(password)
                    forgetpwd.use = True
                    db.session.add(forgetpwd)
                    db.session.add(user)
                    db.session.commit()
                    return redirect(url_for('admin.login'))
            else:
                error = "令牌无效"
    return render_template("repwd.html", token=token, form=form, error=error)


@admin.route("/captcha")
def captcha():
    f = BytesIO()
    code, image = veri_code()
    image.save(f, 'jpeg')
    session['captcha'] = code
    print(code)
    res = Response(f.getvalue(), mimetype="image/jpeg")
    res.headers['Access-Control-Allow-Origin'] = '*'
    return res


restful.add_resource(BankCardApi, '/admin/bankcard', endpoint='bankcard')
restful.add_resource(LoginApi, '/admin/logins', endpoint='logins')
restful.add_resource(LoginLogApi, '/admin/loginlogs', endpoint='loginlogs')
restful.add_resource(LogoutApi, '/admin/logout', endpoint='logout')
restful.add_resource(GetUserInfoApi, '/admin/userinfo', endpoint='userinfo')
restful.add_resource(BankListApi, '/admin/banklist', endpoint='banklist')
restful.add_resource(P2PListApi, '/admin/p2plist', endpoint='p2plist')
restful.add_resource(MyP2PListApi, '/admin/myp2plist', endpoint='myp2plist')
restful.add_resource(MyP2PApi,'/admin/myp2p')
restful.add_resource(BillFlowListApi, '/admin/billflowlist', endpoint='billflowlist')
restful.add_resource(InvestListApi, "/admin/investlist", endpoint="investlist")
restful.add_resource(InvestApi,"/admin/invest",endpoint="myinvest")