# _*_ coding: utf-8 _*_

from datetime import datetime

from forms import *
import forms
from flask import render_template, url_for, redirect, flash, session, request, current_app
from flask.ext.login import login_required, current_user

from . import main
from ..models import User, Topic, City, Conference, Comment, Permission
from .. import db
from ..utils import admin_required, permission_required


@main.route('/', methods=['GET', 'POST'])
def index():
    """
    网站首页
    """
    nickname = session.get("nickname", None)
    if nickname:
        flash("Hello %s" % nickname)
    return render_template('index.html')

@main.route("/show_conference", methods=['GET', 'POST'])
def show_conference():
    """
    显示所有发布的会议
    """
    page = request.args.get("page", 1, type=int)
    pagination = Conference.query.order_by(Conference.time_stamp.desc()) \
                    .paginate(page, per_page=current_app.config["XING_CONFERENCES_PER_PAGE"], error_out=False)
    conferences = pagination.items
    return render_template('show_conference.html', conferences=conferences, pagination=pagination)

@main.route("/create_conference", methods=["GET", "POST"])
@login_required
def create_conference():
    """
    创建一个会议
    """
    form = forms.Conference()
    if form.validate_on_submit():

        title = form.title.data
        description = form.description.data
        city_id = form.city.data
        topic_ids = form.topics.data
        stime = form.start_time.data
        etime = form.end_time.data
        max_attendees = form.max_attendees.data
        time_stamp = datetime.utcnow()
        
        new_conf = Conference(
            organizer = current_user._get_current_object(),
            title = title,
            city = City.query.filter_by(id = city_id).first(),
            description = description,
            start_time = stime,
            end_time = etime,
            max_attendees = max_attendees,
            time_stamp = time_stamp
        )
        for topic_id in topic_ids:
            new_conf.topics.append(Topic.query.filter_by(id=topic_id).first())
        
        db.session.add(new_conf)
        db.session.commit()
        
        flash("New conference is created!")
        
        return redirect(url_for("main.index"))

    allowable_topics = [(topic.id, topic.name) for topic in Topic.query.all()]
    allowable_cities = [(city.id, city.name) for city in City.query.all()] 
    form.city.choices = allowable_cities
    form.topics.choices = allowable_topics
    
    return render_template('create_conference.html', form=form)

@main.route("/conference/<int:id>", methods=["GET", "POST"])
def conference(id):
    """
    显示对应id的会议的详细信息。
    """
    conference = Conference.query.filter_by(id=id).first()
    form = CommentForm()
    if form.validate_on_submit():
        if (form.body.data == ""):
            flash("You can't submit empty comment!")
        else:
            comment = Comment(body=form.body.data, \
                            author=current_user._get_current_object(), \
                            conference=conference)
            db.session.add(comment)
            flash("Your comment have been published!")
            return redirect(url_for("main.conference", id=conference.id, page=-1))
    
    page = request.args.get("page", 1, type=int)
    
    if (page == -1):
        page = (conference.comments.count()-1) / \
                current_app.config['XING_COMMENTS_PER_PAGE'] + 1
    pagination = conference.comments.order_by(Comment.time_stamp.asc()).paginate(page, \
                 per_page=current_app.config['XING_COMMENTS_PER_PAGE'], \
                 error_out=False)
    comments = pagination.items
    return render_template("conference_context.html", conference=conference, form=form, comments=comments, pagination=pagination)
    

@main.route("/profile/<int:id>", methods=["GET"])
@login_required
def profile(id):
    user = User.query.get_or_404(id)
    
    page = request.args.get("page", 1, type=int)
    pagination = user.conferences.paginate(page, \
        per_page=current_app.config["XING_PROFILE_CONFERENCES_PER_PAGE"], \
        error_out=False)
    return render_template("profile.html", user=user, \
        pagination=pagination, conferences=pagination.items)

@main.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile(): 
    form = EditProfile()
    if form.validate_on_submit():
        current_user.nickname = form.nickname.data
        current_user.about_me = form.about_me.data
        current_user.address = form.address.data
        current_user.portrait = form.portrait_addr.data
        db.session.add(current_user)
        flash("You profile has been updated!")
        return redirect(url_for("main.profile", id=current_user.id))
    form.nickname.data = current_user.nickname
    form.about_me.data = current_user.about_me
    form.address.data = current_user.address
    form.portrait_addr.data = current_user.portrait
    return render_template("edit_profile.html", form=form, user=current_user)

@main.route("/edit_profile/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdmin()
    
    if form.validate_on_submit():
        user.email = form.email.data
        user.nickname = form.nickname.data
        user.about_me = form.about_me.data
        user.address = form.address.data
        
        db.session.add(user)
        flash(user.nickname + "'s profile has been updated")
        return redirect(url_for("main.profile", id=user.id))
    form.email.data =  user.email
    form.nickname.data = user.nickname
    form.about_me.data = user.about_me
    form.address.data = user.address
    
    return render_template("edit_profile.html", form=form, user=user)
    
@main.route("/city/<int:id>", methods=["GET"])
def city_conferences(id):
    city = City.query.get_or_404(id)
    page = request.args.get("page", 1, type=int)
     
    pagination = Conference.query.filter_by(city=city).paginate(\
        page, per_page=current_app.config["XING_CONFERENCES_PER_PAGE"], error_out=False)
    
    return render_template("city_conferences.html", city=city, conferences=pagination.items, pagination=pagination)
    

@main.route("/follow/<int:id>")
@login_required
@permission_required(Permission.FOLLOW)
def follow(id):
    user = User.query.get_or_404(id)
    if (current_user.is_following(user)):
        flash("You are already following this user.")
        return redirect(url_for("main.profile", id=user.id))
    current_user.follow(user)
    flash("You are now following %s." % user.nickname)
    return redirect(url_for("main.profile", id=user.id))
    
@main.route("/unfollow/<int:id>")
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(id):
    user = User.query.get_or_404(id)
    if (not current_user.is_following(user)):
        flash("You are already unfollowing this user.")
        return redirect(url_for("main.profile", id=user.id))
    current_user.unfollow(user)
    flash("You are no long following %s now." % user.nickname)
    return redirect(url_for("main.profile", id=user.id))
    
@main.route("/followers/<int:id>")
@login_required
def followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    
    pagination = user.followers.paginate(page, \
        per_page=current_app.config["XING_FOLLOWS_PER_PAGE"], 
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.time_stamp} 
        for item in pagination.items]
    return render_template("follows.html", user=user, title="Followers of", 
        endpoint="main.followers", pagination=pagination, follows=follows)
    
@main.route("/followed_by/<int:id>")
@login_required
def followed_by(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    
    pagination = user.followed.paginate(page, \
        per_page=current_app.config["XING_FOLLOWS_PER_PAGE"], 
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.time_stamp} 
        for item in pagination.items]
    return render_template("follows.html", user=user, title="Followed by", 
        endpoint="main.followed_by", pagination=pagination, follows=follows)


@main.route("/followers_conferences/<int:id>")
@login_required   
def followers_conferences(id):
    query = current_user.followers_conferences
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Conference.time_stamp.desc()).paginate(
        page, per_page=current_app.config["XING_CONFERENCES_PER_PAGE"], error_out=False
    )
    conferences = pagination.items
    return render_template("followers_conferences.html", pagination=pagination, conferences=conferences)