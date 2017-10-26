import random
import uuid
import hmac
from hashlib import sha1
import base64
from datetime import datetime
# import urllib
import requests


def get_secret():
    data = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz234567', 16))
    return data


def replacestr(str):
    data = str.replace("+", "%20")
    data = data.replace("*", "%2A")
    data = data.replace("%7E", '~')
    return data


def hash_value(secret, data):
    hashdata = hmac.new((secret + "&").encode("utf-8"), data.encode("utf-8"), sha1).digest().strip()
    return base64.b64encode(hashdata)


def get_utc_now():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def get_params(subject, emailaddress, accesskeyid, HtmlBody=None, TextBody=None):
    utctime = get_utc_now()
    nonce = uuid.uuid4()
    params = {"Action": "SingleSendMail",
              "AccountName": "admin@testwd.cn",
              "ReplyToAddress": True,
              "AddressType": 1,
              "ToAddress": emailaddress,
              "FromAlias": "P2PBill",
              "Subject": subject,
              "Format": "JSON",
              "Version": "2015-11-23",
              "AccessKeyId": accesskeyid,
              "Timestamp": utctime,
              "SignatureMethod": "HMAC-SHA1",
              "SignatureVersion": "1.0",
              "SignatureNonce": nonce}
    return ''.join([k + "=" + str(params[k]) + "&" for k in sorted(params)])


paran = get_params("测试", "jiangyd@jiagouyun.com", "LTAIVF29fBCXjmYC", TextBody="adsfdf")
print(paran)
data = replacestr(paran)
endata = requests.utils.quote(data)
print(endata)
StringToSign = "GET" + "&" + requests.utils.quote("/", safe="") + "&" + endata

v = hash_value("i9IkzpKWCuSwK808iNR6awWREjsvU4", StringToSign)
print(v)
url = "https://dm.aliyuncs.com/?" + data + "Signature=" + v.decode("utf-8")
print(url)
res = requests.get(url)
print(res.status_code, res.text)
