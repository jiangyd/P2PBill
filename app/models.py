from flask import Flask

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash,check_password_hash

app=Flask(__name__)

db=SQLAlchemy(app)

#平台信息表
class P2P(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(32),unique=True) #平台名称
    url=db.Column(db.String(255),unique=True) #平台URL
    funds_deposit=db.Column(db.Boolean) #资金存管
    risk_deposit=db.Column(db.Boolean)  #风险金存管
    invests=db.relationship('Invest',backref="p2p") #投资记录外键关联关系
    userp2ps=db.relationship('UserP2P',backref="p2p")#用户平台外键关联关系

#用户信息表
class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(16)) #登录用户名
    password=db.Column(db.String(100)) #密码
    nickname=db.Column(db.String(32)) #昵称
    email=db.Column(db.String(32)) #邮箱
    phone=db.Column(db.String(11)) #手机
    face=db.Column(db.String(255)) #头像
    def check_pwd(self,pwd):
        return check_password_hash(self.password,pwd)


#投资记录表
class Invest(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    p2p_id=db.Column(db.Integer,db.ForeignKey('p2p.id')) #外键关联p2p
    money=db.Column(db.Integer) #投资金额
    start_time=db.Column(db.DateTime)# 投资开始时间
    end_time=db.Column(db.DateTime)# 投资到期时间
    days=db.Column(db.Integer) #投资周期天数,可以不用手动填写
    profit=db.Column(db.Integer) #年利润
    lucre=db.Column(db.Integer)  #收益
    status=db.Column(db.Integer,default=0) #0投资中,1已到期,2已完成

#用户平台关联表
class UserP2P(db.Model):
    __tablename__="userp2p"
    id=db.Column(db.Integer,primary_key=True)
    p2p_id=db.Column(db.Integer,db.ForeignKey("p2p.id")) #外键关联p2p
    account=db.Column(db.String(16))  #平台帐户
    password=db.Column(db.String(100))#平台密码
    card_id=db.Column(db.Integer,db.ForeignKey('bankcard.id')) #银行卡号
    phone=db.Column(db.String) #手机号


#资金流水记录表
class BillFlow(db.Model):
    __tablename__="billflow"
    id=db.Column(db.Integer,primary_key=True)
    card_id=db.Column(db.Integer,db.ForeignKey("bankcard.id"))
    money=db.Column(db.Integer)
    statu=db.Column(db.Integer,default=0) #0进行中,1已完成
    action=db.Column(db.Integer) #0 充值，1 提现

#银行卡管理
class BankCard(db.Model):
    __tablename__="bankcard"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(32)) #开户行
    card=db.Column(db.Integer) #银行卡号
    billflows=db.relationship('BillFlow',backref='bankcard')
    userp2ps=db.relationship('UserP2P',backref='bankcard')


