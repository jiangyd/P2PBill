import random
import uuid
import hmac
from hashlib import sha1
import base64
from datetime import datetime
import requests
import urllib.parse
from app import app


# class B(object):
#     def __init__(self,a,b):
#         self.a=a
#         self.b=b
#     def c(self,x):
#         print("aaa")
#         return x
# b=B("a","b")
# b.c("x")

def get_secret():
    data = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz234567', 16))
    return data



class SendMailByAli(object):
    def __init__(self):
        self.access_keyid=app.config["access_keyid"]
        self.access_secret=app.config["access_secret"]

    def __replace(self,str):
        data = str.replace("+", "%20")
        data = data.replace("*", "%2A")
        data = data.replace("%7E", '~')
        return data
    def __encry(self,secret,data):
        hash_value=hmac.new((secret + "&").encode("utf-8"),
                            data.encode("utf-8"), sha1).digest().strip()
        return base64.b64encode(hash_value).decode("utf-8")

    def __utcnow(self):
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def __nonce(self):
        """获取数据uuid"""
        return str(uuid.uuid4())
    def params(self,subject,toaddress,htmlbody=None,textbody=None):
        utctime=self.__utcnow()
        Nonce=self.__nonce()
        params = {"Action": "SingleSendMail",
                  "AccountName": "admin@testwd.cn",
                  "ReplyToAddress": "true",
                  "AddressType": "1",
                  "ToAddress": toaddress,
                  "FromAlias": "P2PBill",
                  "Subject": subject,
                  "Format": "JSON",
                  "AccessKeyId":self.access_keyid ,
                  "Timestamp": utctime,
                  "SignatureMethod": "HMAC-SHA1",
                  "SignatureVersion": "1.0",
                  "SignatureNonce": Nonce,
                  "Version": "2015-11-23", }
        if htmlbody is not None:
            params["HtmlBody"]=htmlbody
        if textbody is not None:
            params["TextBody"]=textbody
        sort_params = {}
        for key in sorted(params):
            sort_params[key] = params[key]
        return sort_params
    def send_mail(self,subject,toaddress,htmlbody=None,textbody=None):
        params_data=self.params(subject=subject,toaddress=toaddress,htmlbody=htmlbody,textbody=textbody)
        data=urllib.parse.urlencode(params_data)
        StringToSign="GET&%2F&" + self.__replace(requests.utils.quote(data,safe=""))
        Signature=self.__encry(self.access_secret,StringToSign)
        params_data["Signature"]=Signature
        url="https://dm.aliyuncs.com/?" +urllib.parse.urlencode(params_data)
        res=requests.get(url,verify=False)
        return {"code":res.status_code,"msg":res.text}







    # return '&'.join([k + "=" + str(params[k])  for k in sorted(params)])




