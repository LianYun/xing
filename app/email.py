# _*_ coding: utf-8 _*_

from threading import Thread
from flask import current_app, render_template
from flask.ext.mail import Message

from . import mail

def send_email(app, msg):
    """
    在应用上下文中发送邮件。
    """
    with app.app_context():
        mail.send(msg)

def send_async_email(to,  subject, template, **kwargs):
    """
    异步地发送邮件。
    """
    app = current_app._get_current_object()
    msg = Message(app.config['XING_MAIL_SUBJECT_PREFIX'] + " " + \
        subject, sender=app.config['XING_MAIL_SENDER'], recipients=[to])

    msg.body = render_template(template+".txt", **kwargs)
    msg.html = render_template(template+".html", **kwargs)
    thr = Thread(target=send_email, args=[app, msg])
    thr.start()
    return thr
