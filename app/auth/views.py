# _*_ coding: utf-8 _*_

from flask import render_template, redirect, flash, url_for, request, session
from flask.ext.login import login_user, logout_user, login_required, \
    current_user


from . import auth
from ..main import main
from ..models import User
from ..email import send_async_email
from .. import db
from forms import Login, Register

@auth.route("/login", methods=['GET', 'POST'])
def login():
    """
    用户登陆路由。
    """
    form = Login()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if u and u.verify_passwd(form.passwd.data):
            login_user(u, form.remember_me.data)
            flash("Logged in successfully.")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("main.index"))
        flash("Invalid username or password.")
    return render_template("auth/login.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    """
    用户退出。
    """
    logout_user()
    flash("You have been logged out!")
    return redirect(url_for("main.index"))


@auth.route("/register", methods=['GET', 'POST'])
def register():
    """
    用户注册的处理。
    """
    REGISTER_HTML_PATH = "auth/register.html"
    form = Register()
    if form.validate_on_submit():
        email = form.email.data
        nickname = form.nickname.data
        passwd = form.passwd.data
        confirm = form.confirm.data

        new_user = User(email=email, nickname=nickname, passwd=passwd)
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("Database Error!")
            return render_template(REGISTER_HTML_PATH, form=form)
        token = new_user.generate_confirmation_token()
        send_async_email(new_user.email, "Confirm Your Account", "auth/email/confirm",\
            user=new_user, token=token)  # to,  subject, template, **kwargs
        flash('A confirmation email has been sent to you by email.')
        session["nickname"] = nickname
        return redirect(url_for("main.index"))
    return render_template(REGISTER_HTML_PATH, form=form)

@auth.route("/confirm/<token>")
@login_required
def confirm(token):
    """
    确认用户。
    注意和重新发送确认邮件的路由之间的区别。
    """
    if not current_user.confirmed:
        if current_user.confirm(token):
            flash("You have confirmed your account!")
        else:
            flash("The confirmation link is invalid or has expired.")
    return redirect(url_for("main.index"))

@auth.before_app_request
def before_request():
    """
    注册了一个函数，在每次请求前验证用户信息。
    """
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
            and request.endpoint[:5] != "auth."\
            and request.endpoint != 'static':
            return redirect(url_for("auth.unconfirmed"))

@auth.route("/unconfirmed")
def unconfirmed():
    """
    弹出给未验证用户的界面。提醒未验证用户尽快验证。
    """
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for("main.index"))
    return render_template("auth/unconfirmed.html")

@auth.route('/confirm')
@login_required
def resend_confirmation():
    """
    用于重新发送确认邮件的路由。
    会在异步发送邮件后重定向到首页。
    """
    token = current_user.generate_confirmation_token()
    send_async_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))
