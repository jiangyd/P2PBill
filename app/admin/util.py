import random
import uuid

def get_secret():
    data=''.join(random.sample('abcdefghijklmnopqrstuvwxyz234567',16))
    return data
