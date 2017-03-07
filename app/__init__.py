# _*_ coding: utf-8 _*_

"""
本部分是应用程序的主体部分。

定义应用运行时的所有插件，并且创建应用对象，并且在应用对象上注册相关的蓝本。

"""
from flask import Flask

from config import config

# bootstrap
from flask.ext.bootstrap import Bootstrap
bootstrap = Bootstrap()

# ORM
from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy()

# Login
from flask.ext.login import LoginManager
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "auth.login"

# email
from flask.ext.mail import Mail
mail = Mail()

# Markdown
from flask.ext.pagedown import PageDown
pagedown = PageDown()

# Moment
from flask.ext.moment import Moment
moment = Moment()


def create_app(config_name):
    """
    创建应用，定义应用的配置，并且初始化应用的运行插件，最后将蓝本注册到应用。
    """
    app = Flask(__name__)
    
    # 配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 插件
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    pagedown.init_app(app)
    moment.init_app(app)
    
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        sslify = SSLify(app)

    # 蓝本
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    from .api_0_1 import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix="/api/v0.1")

    return app
