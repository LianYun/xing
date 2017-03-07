# _*_ coding: utf-8 _*_

from flask import jsonify, request, current_app, url_for, g

import json
from StringIO import StringIO

from . import api
from ..models import Conference, Permission, City, Topic
from .. import db

from errors import forbidden

from decorators import not_anonymous, permission_required

@api.route("/conferences")
def get_conferences():
	page = request.args.get("page", 1, type=int)
	pagination = Conference.query.paginate(
		page, per_page=current_app.config["XING_CONFERENCES_PER_PAGE"], 
		error_out=False
	)
	conferences = pagination.items
	page_prev = None
	if pagination.has_prev:
		page_prev = url_for("api.get_conferences", page=page-1, _external=True)
	page_next = None
	if pagination.has_next:
		page_next = url_for("api.get_conferences", page=page+1, _external=True)
	
	return jsonify({
		"conferences": [c.to_json() for c in conferences],
		"prev": page_prev,
		"next": page_next,
		"count": pagination.total
	})

@api.route("/conferences/<int:id>")
def get_conference(id):
	conference = Conference.query.get_or_404(id)
	return jsonify(conference.to_json())

@api.route("/conferences/<int:id>/topics")
def get_conference_topics(id):
	conference = Conference.query.get_or_404(id)
	# 如果没有找到会发生什么呢？ 如果使用filter_by查询，会抛出异常
	# 使用get_or_404后，会直接返回404错误
	return jsonify({"topics": [t.to_json() for t in conference.topics]})

@api.route("/conferences/<int:id>/city")
def get_city(id):
	conference = Conference.query.get_or_404(id)
	return jsonify(conference.city.to_json())
    
@api.route("/conferences/<int:id>/attendees")
@not_anonymous
def get_conference_attendees(id):
    conference = Conference.query.get_or_404(id)
    attendees = [atts.attendee for atts in conference.attendees]
    
    return jsonify({"attendees": [attendee.to_json() for attendee in attendees]})
    
    
@api.route("/conferences/<int:id>/comments", methods=["GET"])
def get_conference_comments(id):
    conference = Conference.query.get_or_404(id)
    return jsonify({"comments": [comment.to_json() for comment in conference.comments]})
    
def success(message):
    response = jsonify({'flag': 'suncess', 'message': message})
    response.status_code = 200
    return response

def failure(message):
    response = jsonify({'flag': 'failure', 'message': message})
    response.status_code = 200
    return response
    
@api.route("/conferences/new", methods = ["POST"])
@permission_required(Permission.WRITE_ARTICLES)
def new_conferences():
    """
    api 定义如下：
    {
        "title" : "...",
        "city" : "name",
        "description" : "...md...",
        "topics": ["name1", "name2"],
        "start_time" : "DATE",
        "end_time" : "DATE",
        "max_attendees": "<int:n>"
    }
    """
    conf_dict = request.json
    
    city_name = conf_dict.get("city") or "anywhere"
    
    city = City.query.filter_by(name=city_name).first()
    if city is None:
        city = City(name=city_name)
        db.session.add(city)       
    
    new_conference = Conference(
        organizer=g.current_user,
        title=conf_dict.get('title') or "no title",
        description=conf_dict.get('description') or "no description",
        city=city,
        max_attendees=conf_dict.get("max_attendees")
    )
    
    for tn in conf_dict.get("topics"):
        topic = Topic.query.filter_by(name=tn).first()
        if topic is None:
            topic = Topic(name=tn)
            db.session.add(topic)
        new_conference.topics.append(topic)   
    
    db.session.add(new_conference)
    
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return failure("database failed, please try again")
        
    print(new_conference)
    return success("new conference created!")
    