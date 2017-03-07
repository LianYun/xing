# _*_ coding: utf-8 _*_

"""
本部分定义应用的所有数据库对象。
"""
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, url_for
import datetime
from markdown import markdown
import bleach

from . import db, login_manager

ALL_ALLOWED_TAGS = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', \
                    'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', \
                    'h4', 'h5', 'h6', 'h7', 'p']
class Permission:
    """
    权限管理：
    
    0b00000001: 关注
    0b00000010: 评论
    0b00000100: 写文章
    0b00001000: 管理他人的评论
    0b00010000: 管理员权限
    """
    FOLLOW = 0x01
    COMMIT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMITS = 0x08
    ADMINISTER = 0x08
    
class Follow(db.Model):
    __tablename__ = "follows"
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    time_stamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Attendor(db.Model):
    __tablename__ = "attendors"
    attendee_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    atconference_id = db.Column(db.Integer, db.ForeignKey('conferences.id'), primary_key=True)
    time_stamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class User(UserMixin, db.Model):
    """
    用户表
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    nickname = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    address = db.Column(db.String(128))
    about_me = db.Column(db.Text)
    about_me_html = db.Column(db.Text)
    join_time = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    confirmed = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    conferences = db.relationship("Conference", backref="organizer", lazy='dynamic')
    comments = db.relationship("Comment", backref="author", lazy="dynamic")
    portrait_addr = db.Column(db.String(128))
    
    followed = db.relationship("Follow", 
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref("follower", lazy="joined"),
                               lazy="dynamic",
                               cascade='all, delete-orphan')
                               
    followers = db.relationship("Follow", 
                               foreign_keys=[Follow.followed_id],
                               backref=db.backref("followed", lazy="joined"),
                               lazy="dynamic",
                               cascade='all, delete-orphan')
                               
    atconferences = db.relationship("Attendor", 
                               foreign_keys=[Attendor.attendee_id],
                               backref=db.backref("attendee", lazy="joined"),
                               lazy="dynamic",
                               cascade="all, delete-orphan")
                               
                               # user.atconferences[k].attendee 是其自身
    

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config["XING_ADMIN"]:
                self.role = Role.query.filter_by(permissions = 0xff).first()
            else:
                self.role = Role.query.filter_by(default=True).first()
    
    def to_json(self):
        json_user = {
            "id": self.id,
            "url": url_for("api.get_user", id=self.id, _external=True),
            "nickname": self.nickname,
            "email": self.email,
            "address": self.address,
            "about_me": self.about_me,
            "join_time": self.join_time,
            "last_seen": self.last_seen,
            "confirmed": self.confirmed,
            "portrait_addr": self.portrait_addr,
            "conferences": url_for("api.get_user_conferences", id = self.id, _external=True),
            "conferences_count": self.conferences.count()
        }
        return json_user
        
    
    def attend(self, conference):
        if (not self.is_attend(conference)):
            a = Attendor(attendee = self, atconference = conference)
            db.session.add(a)
    
    def unattend(self, conference):
        a = self.atconferences.filter_by(atconference_id=conference.id).first()
        if a:
            db.session.delete(a)
        
    def is_attend(self, conference):
        return self.atconferences.filter_by(atconference_id=conference.id).first() is not None
    
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(follower_id=user.id).first()
        if f:
            db.session.delete(f)
    
    @property    
    def followers_conferences(self):
        return Conference.query.join(Follow, \
            Follow.followed_id == Conference.organizer_id).filter(\
                Follow.follower_id == self.id)
    
    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None
    
    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None
    
    def ping(self):
        """
        刷新用户的访问时间
        """
        self.last_seen = datetime.datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def can(self, permission):
        """
        Verify this user's role.
        If this user has permission required, return true, vise vese.
        """
        return (self.role is not None) and \
            ((self.role.permissions & permission) == permission)

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    @property
    def passwd(self):
        raise AttributeError("Password is not a readable attribute")

    @passwd.setter
    def passwd(self, passwd):
        self.password_hash = generate_password_hash(passwd)
        
    @property
    def portrait(self):
        if self.portrait_addr:
            return self.portrait_addr
        else:
            return "https://avatars3.githubusercontent.com/u/3695283?v=3&u=9269932cb4ce7e9b4976b62b2abcfe27f5b6f0a6&s=140"
    
    @portrait.setter
    def portrait(self, pt):
        self.portrait_addr = pt

    def verify_passwd(self, passwd):
        return check_password_hash(self.password_hash, passwd)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):

        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get("confirm") == self.id:
            self.confirmed = True
            db.session.add(self)
            db.session.commit()
            return True
        return False
    
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})
    
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')
    
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])
        
    @staticmethod
    def on_change_about_me(target, value, oldvalue, initiator):
        target.about_me_html = bleach.linkify(bleach.clean(markdown(value, \
                                output_format="html"), tags=ALL_ALLOWED_TAGS, \
                                strip=True))
                                
    
    @staticmethod
    def generate_fake(count=100):
        """
        说明：
        conferences留给Conference在fake时生成。
        comments留给Comment在fake时生成
        atconferences留给conference的fake来实现
        """
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        
        import forgery_py
        seed()
        role_count = Role.query.count()
        
        
        u = User(
            email = "lianyun08@126.com",
            nickname = "admin",
            passwd = "12",
            confirmed = True,
            address = forgery_py.address.street_address(),
            about_me = "administrator",
            portrait_addr = "https://avatars3.githubusercontent.com/u/3695283?v=3&s=260"
        )
        
        db.session.add(u)
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        
        for i in xrange(count):
            jt = forgery_py.date.date()
            delta_time = datetime.timedelta(days=randint(1, 10))
            
            lt = jt + delta_time
            r = Role.query.offset(randint(0, role_count - 1)).first()
            user_count = User.query.count()
            u = User(
                email = forgery_py.internet.email_address(),
                nickname = forgery_py.name.full_name(),
                passwd = forgery_py.lorem_ipsum.word(),
                confirmed = True,
                address = forgery_py.address.street_address(),
                about_me = forgery_py.forgery.currency.description(),
                join_time = jt,
                last_seen = lt,
                role = r,
                portrait_addr = "http://www.ttoou.com/qqtouxiang/allimg/120918/co12091Q01643-6-lp.jpg"
            )
            
            db.session.add(u)
            
             
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        
        user_count = User.query.count()
            
        for i in xrange(count):
            u = User.query.offset(i).first()
            
            followed_n = randint(0, 20)
            for j in xrange(followed_n):
                fu = User.query.offset(randint(0, user_count - 1)).first()
                if fu.id == u.id:
                    continue
                u.follow(fu)
                
                

    def __str__(self):
        return "<User %s>" % self.nickname
    
        
    __repr__ = __str__

db.event.listen(User.about_me, 'set', User.on_change_about_me)

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return True

login_manager.anonymous_user = AnonymousUser

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship("User", backref="role", lazy="dynamic")

    def to_json(self):
        json_role = {
            "id": self.id,
            "name": self.name
        }
        
        return json_role

    @staticmethod
    def insert_roles():
        roles = {
            "User" : (Permission.FOLLOW |
                      Permission.COMMIT |
                      Permission.WRITE_ARTICLES, True),
            "Moderator" : ( Permission.FOLLOW |
                            Permission.COMMIT |
                            Permission.WRITE_ARTICLES |
                            Permission.MODERATE_COMMITS, False),
            "Administrator" : (0xff, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __str__(self):
        return "<Role %s>" % self.name

    __repr__ = __str__

class City(db.Model):
    __tablename__ = "cities"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    conferences = db.relationship("Conference", backref="city", lazy="dynamic")
    
    def to_json(self):
        json_city = {
            "id": self.id,
            "name": self.name
        }
        return json_city
    
    @staticmethod
    def insert_cities():
        cities = {
            "default": "anywhere", 
            "xi_an": "Xi An",
            "bei_jing": "Bei Jing",
            "shang_hai": "Shang Hai"
        }
        for (value, name) in cities.items():
            city = City.query.filter_by(name=name).first()
            if city is None:
                city = City(name=name)
                db.session.add(city)
        db.session.commit()
    
    def __str__(self):
        return "<City %s>" % self.name
    
        
    __repr__ = __str__
            
    
class Topic(db.Model):
    __tablename__ = "topics"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    
    def to_json(self):
        json_topic = {
            "id": self.id,
            "name": self.name
        }
        return json_topic
    
    @staticmethod
    def insert_topics():
        topics = {
            "programming": "Programming",
            "web": "Web",
            "movie": "Movie",
            "health": "Health"
        }
        for (value, name) in topics.items():
            topic = Topic.query.filter_by(name=name).first()
            if topic is None:
                topic = Topic(name=name)
                db.session.add(topic)
        db.session.commit()
    
    def __str__(self):
        return "<Topic %s>" % self.name
        
    __repr__ = __str__


add_topics = db.Table('add_topics', \
                        db.Column("conference_id", db.Integer, db.ForeignKey("conferences.id")),
                        db.Column("topic_id", db.Integer, db.ForeignKey("topics.id")))

class Conference(db.Model):
    __tablename__ = "conferences"
    id = db.Column(db.Integer, primary_key=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    title = db.Column(db.String(128), index=True, nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    topics = db.relationship("Topic", secondary=add_topics, backref=db.backref("conferences", lazy="dynamic"), lazy="dynamic")
    description = db.Column(db.Text)
    description_html = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    max_attendees = db.Column(db.Integer)
    time_stamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    comments = db.relationship("Comment", backref="conference", lazy="dynamic")
    
    attendees = db.relationship("Attendor", 
                               foreign_keys=[Attendor.atconference_id],
                               backref=db.backref("atconference", lazy="joined"),
                               lazy="dynamic",
                               cascade="all, delete-orphan")
                               # 注意会议的attendees[k].atconference是其自身

    def to_json(self):
        json_conference = {
            "id": self.id,
            "url": url_for("api.get_conference", id = self.id, _external=True),
            "title": self.title,
            "city": url_for("api.get_city", id = self.city_id, _external=True),
            "topics": url_for("api.get_conference_topics", id = self.id, _external=True),
            "description": self.description,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "max_attendees": self.max_attendees,
            "time_stamp": self.time_stamp,
            "attendees": url_for("api.get_conference_attendees", id = self.id, _external=True),
            "attendees_count": self.attendees.count(),
            "comments": url_for("api.get_conference_comments", id = self.id, _external=True),
            "comments_count": self.comments.count()
        }
        return json_conference
        
    def __str__(self):
        return "<Conference %s>" % self.title
    
    __repr__ = __str__
    
    @staticmethod
    def on_change_description(target, value, oldvalue, initiator):
        target.description_html = bleach.linkify(bleach.clean(markdown(value, \
                                output_format="html"), tags=ALL_ALLOWED_TAGS, \
                                strip=True))

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        
        seed()
        user_count = User.query.count()
        city_count = City.query.count()
        topic_count = Topic.query.count()
        delta_time = datetime.timedelta(days=1)
        
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            c = City.query.offset(randint(0, city_count - 1)).first()
            t = forgery_py.lorem_ipsum.title()
            tps = []
            for ii in xrange(randint(0, topic_count-1)):
                tps.append(Topic.query.offset(randint(0, topic_count-1)).first())
            stime = forgery_py.date.date(True)
            etime = stime + delta_time
            des = forgery_py.forgery.basic.text(at_least=15, at_most=50, digits=True, spaces=True, punctuation=False)
            max_attendees = randint(5, 25)
            attendees = [User.query.offset(randint(0, user_count-1)).first() for i in xrange(randint(0,max_attendees))]
            time_stamp = forgery_py.date.date(True)
            
            conference = Conference(
                organizer = u,
                city = c,
                title = t,
                description = des,
                start_time = stime,
                end_time = etime,
                max_attendees = max_attendees,
                time_stamp = time_stamp
            )
            
            for t in tps:
                conference.topics.append(t)
                
            for u in attendees:
                u.attend(conference)
            
            db.session.add(conference)
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            
db.event.listen(Conference.description, 'set', Conference.on_change_description)

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    time_stamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    conference_id = db.Column(db.Integer, db.ForeignKey("conferences.id"))
    
    def to_json(self):
        json_comment = {
            "id": self.id,
            "body": self.body,
            "time_stamp": self.time_stamp,
            "author": url_for("api.get_user", id=self.author_id, _external=True),
            "conference": url_for("api.get_conference", id=self.conference_id, _external=True)
        }
        return json_comment
    
    @staticmethod
    def on_change_body(target, value, oldvalue, initiator):
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format="html"),\
                tags=ALL_ALLOWED_TAGS, strip=True))
                
    @staticmethod
    def generate_fake(count=550):
        from random import seed, randint
        import forgery_py
        
        seed()
        user_count = User.query.count()
        conference_count = Conference.query.count()
        for i in xrange(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            conf = Conference.query.offset(randint(0, conference_count-1)).first()
            
            c = Comment(
                body = forgery_py.forgery.basic.text(at_least=10, at_most=25),
                time_stamp = forgery_py.forgery.date.date(),
                disabled = False,
                author = u,
                conference = conf
            )
            db.session.add(c)
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        

db.event.listen(Comment.body, 'set', Comment.on_change_body)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

