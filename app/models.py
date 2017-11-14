# from flask import Flask

# from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timedelta
from werkzeug.security import generate_password_hash,check_password_hash
# from app import db
from app.ext import db
# #
# app=Flask(__name__)
# #
# app.config["SQLALCHEMY_DATABASE_URI"]="mysql+pymysql://root:123456@192.168.56.102:3377/p2pbill"
# db=SQLAlchemy(app)

#平台信息表
class P2P(db.Model):
    __tablename__="p2p"
    def __init__(self,name,url,funds_deposit,risk_deposit):
        self.name=name
        self.url=url
        self.funds_deposit=funds_deposit
        self.risk_deposit=risk_deposit
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(32),unique=True) #平台名称
    url=db.Column(db.String(255),unique=True) #平台URL
    funds_deposit=db.Column(db.Boolean,default=False) #资金存管
    risk_deposit=db.Column(db.Boolean,default=False)  #风险金存管
    invests=db.relationship('Invest',backref="p2p") #投资记录外键关联关系
    userp2ps=db.relationship('UserP2P',backref="p2p")#用户平台外键关联关系
    billflows=db.relationship("BillFlow",backref="p2p") #资金流水外键关联关系


#用户信息表
class User(db.Model):
    __tablename__="user"
    def __init__(self,username,password,nickname,email,phone):
        self.username=username
        self.password=self.set_pwd(password)
        self.nickname=nickname
        self.email=email
        self.phone=phone

    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(16),unique=True) #登录用户名
    password=db.Column(db.String(100)) #密码
    nickname=db.Column(db.String(32)) #昵称
    email=db.Column(db.String(32),unique=True) #邮箱
    phone=db.Column(db.String(11),unique=True) #手机
    face=db.Column(db.String(255)) #头像
    secret=db.Column(db.String(16)) #MFA密钥
    mfa_status=db.Column(db.Boolean,default=False) #用户mfa设置默认未开启
    loginlogs=db.relationship("Loginlog",backref="user")
    bankcards=db.relationship("BankCard",backref="user")
    invests = db.relationship("Invest", backref="user")
    userp2ps = db.relationship("UserP2P", backref="user")
    billflows = db.relationship("BillFlow", backref="user")
    def check_pwd(self,pwd):
        return check_password_hash(self.password,pwd)
    def set_pwd(self,pwd):
        self.password=generate_password_hash(pwd)
    def to_json(self):
        json_user={
            "id":self.id,
            "username":self.username,
            "nickname":self.nickname,
            "email":self.email,
            "phone":self.phone,
            "face":self.face,
        }
        return json_user


#投资记录表
class Invest(db.Model):
    __tablename__="Invest"
    def __init__(self,p2p_id,user_id,money,start_time,end_time,profit,lucre):
        self.p2p_id=p2p_id
        self.user_id=user_id
        self.money=money
        self.start_time=start_time
        self.end_time=end_time
        self.profit=profit
        self.lucre=lucre
    id=db.Column(db.Integer,primary_key=True)
    p2p_id=db.Column(db.Integer,db.ForeignKey('p2p.id')) #外键关联p2p
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    money=db.Column(db.Integer) #投资金额
    start_time=db.Column(db.DateTime)# 投资开始时间
    end_time=db.Column(db.DateTime)# 投资到期时间
    profit=db.Column(db.Integer) #年利润
    lucre=db.Column(db.Integer)  #收益
    status=db.Column(db.Integer,default=0) #0投资中,1已到期,2已完成

#用户平台关联表
class UserP2P(db.Model):
    __tablename__="userp2p"
    def __init__(self,p2p_id,user_id,account,password,card_id,phone):
        self.p2p_id=p2p_id
        self.user_id=user_id
        self.account=account
        self.password=password
        self.card_id=card_id
        self.phone=phone
    id=db.Column(db.Integer,primary_key=True)
    p2p_id=db.Column(db.Integer,db.ForeignKey("p2p.id")) #外键关联p2p
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    account=db.Column(db.String(16))  #平台帐户
    password=db.Column(db.String(100))#平台密码
    card_id=db.Column(db.Integer,db.ForeignKey('bankcard.id')) #银行卡号
    phone=db.Column(db.String(11)) #手机号


#资金流水记录表
class BillFlow(db.Model):
    __tablename__="billflow"
    def __init__(self,card_id,p2p_id,user_id,money,type):
        self.card_id=card_id
        self.p2p_id=p2p_id
        self.user_id=user_id
        self.money=money
        self.type=type
    id=db.Column(db.Integer,primary_key=True)
    card_id=db.Column(db.Integer,db.ForeignKey("bankcard.id"))
    p2p_id=db.Column(db.Integer,db.ForeignKey("p2p.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    money=db.Column(db.Integer) #金额
    status=db.Column(db.Integer,default=0) #0进行中,1已完成
    type=db.Column(db.Integer) #0 充值，1 提现
    addtime=db.Column(db.DateTime,default=datetime.now) #添加时间
    donetime=db.Column(db.DateTime) #完成时间

#银行卡管理
class BankCard(db.Model):
    __tablename__="bankcard"
    def __init__(self,name,card,user_id):
        self.name=name
        self.card=card
        self.user_id=user_id
    @classmethod
    def card_exist(cls,card):
        """验证卡号是否存在"""
        return BankCard.query.filter_by(card=card).first()
    @classmethod
    def id_exist(cls,id):
        """验证ID是否存在"""
        return BankCard.query.filter_by(id=id).first()
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(32)) #开户行
    card=db.Column(db.String(25),unique=True) #银行卡号
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    billflows=db.relationship('BillFlow',backref='bankcard')
    userp2ps=db.relationship('UserP2P',backref='bankcard')

#登录日志
class Loginlog(db.Model):
    __tablename__="loginlog"
    def __init__(self, user_id, ip):
        self.user_id=user_id
        self.ip=ip
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("user.id"))
    ip=db.Column(db.String(15))
    mfa_status=db.Column(db.Boolean,default=False) #这个状态要保存，所以不能从用户表读取
    addtime=db.Column(db.DateTime,default=datetime.now)

#找回密码
class ForGetPwd(db.Model):
    """
    用户可能存在多次找回密码操作，应该需要获取第一条数据验证
    用户可能通过一次找回密码链接，多次进行修改密码，应在第一次找回密码通过后，设置为已使用
    """
    __tablename__="forgetpwd"
    def __init__(self,email,token,addtime,expiretime):
        self.email=email
        self.token=token
        self.addtime=addtime
        self.expiretime=expiretime
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(32))
    token=db.Column(db.String(32))
    addtime=db.Column(db.DateTime,default=datetime.now)
    expiretime=db.Column(db.DateTime)
    use=db.Column(db.Boolean,default=False)




if __name__=="__main__":
    # pass
    db.create_all()
    user=User(username="admin",password=generate_password_hash("Qwe123123"),nickname="道可道",email="962584902@qq.com",phone="15821834763")
    db.session.add(user)
    db.session.commit()