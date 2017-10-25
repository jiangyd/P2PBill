import random
import uuid
import hmac
from hashlib import sha1
import base64
from datetime import datetime


def get_secret():
    data=''.join(random.sample('abcdefghijklmnopqrstuvwxyz234567',16))
    return data

def replacestr(str):
    data=str.replace("+","%20").replace("*","%2A").replace("%7E",'~')

def hash_value(secret,data):
    hashdata=hmac.new((secret+"&").encode("utf-8"),data.encode("utf-8"),sha1).digest().strip()
    return base64.b64encode(hashdata)


print(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

