# _*_ coding: utf-8 _*_

from flask import Blueprint

auth = Blueprint("auth", __name__)

from . import views
