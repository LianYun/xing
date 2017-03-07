# _*_ coding: utf-8 _*_

"""
本部分时api蓝本。


"""
from flask.ext.httpauth import HTTPBasicAuth
from flask import Blueprint

api = Blueprint("api", __name__)

auth = HTTPBasicAuth()

from . import authentication, conferences, errors, users, comments