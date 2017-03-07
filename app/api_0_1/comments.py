from flask import jsonify

from . import api
from ..models import User, Comment, Conference


@api.route("/comments/<int:id>", methods=["GET"])
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())

    