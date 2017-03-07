# _*_ coding: utf-8 _*_

from flask_wtf import Form
from wtforms import StringField, SelectField, TextAreaField, SelectMultipleField,\
    DateTimeField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, URL
from datetime import datetime
from flask.ext.pagedown.fields import PageDownField

__author__ = "movecloud.me"


class Conference(Form):
    title = StringField("Conference Tilte", validators = [DataRequired()])
    city = SelectField("City", choices=[("1","AA"), ("2", "BB")])
    description = PageDownField("Conference description")
    topics = SelectMultipleField("Topics", choices = [("1", "DD"), ("2", "EE"), ("3", "VV")])
    start_time = DateTimeField("Start Time (%Y-%m-%d %H:%M:%S)", format="%Y-%m-%d %H:%M", default=datetime.utcnow(), id="datetimepicker")
    end_time = DateTimeField("End Time (%Y-%m-%d %H:%M:%S)", format="%Y-%m-%d %H:%M", default=datetime.utcnow())
    max_attendees = IntegerField("Max Attendees", default=0)
    submit = SubmitField("Publish")

class EditProfile(Form):
    nickname = StringField("Nick Name", validators = [DataRequired()])
    about_me = PageDownField("About Me")
    address = StringField("Address")
    portrait_addr = StringField("Portrait_addr", validators = [URL()])
    
    submit = SubmitField("Save Changes")
    
class EditProfileAdmin(Form):
    email = StringField("Email Address", validators = [DataRequired(), Email()])
    nickname = StringField("Nick Name", validators = [DataRequired()])
    about_me = PageDownField("About Me")
    address = StringField("Address")
    
    submit = SubmitField("Save Changes")

class CommentForm(Form):
    body = PageDownField("Comment")
    submit = SubmitField("Submit")