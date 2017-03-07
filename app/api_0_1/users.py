# _*_ coding: utf-8 _*_

from flask import jsonify

from . import api, auth
from ..models import User, Conference, Role

@api.route("/users/<int:id>")
def get_user(id):
	user = User.query.get_or_404(id)
	return  jsonify(user.to_json())
	

@api.route("/users/<int:id>/conferences")
def get_user_conferences(id):
	user = User.query.get_or_404(id)
	return jsonify({"conferences": [ c.to_json() for c in user.conferences]})


@api.route("/users/<int:id>/followed")
def get_user_followed(id):
    user = User.query.get_or_404(id)
    return jsonify({"followed": [f.followed.to_json() for f in user.followed]})

@api.route("/users/<int:id>/followers")
def get_user_followers(id):
    user = User.query.get_or_404(id)
    return jsonify({"followers": [f.follower.to_json() for f in user.followers]})
   