# _*_ coding:utf-8 _*_

"""
Flask app config package.
Configration of xing conference
"""

import os
import random
import string

__author__ = "movecloud.me"

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Basic configration of app.
    """
    XING_CITIES = ["Xian", "Beijing", "Shanghai", "Shengzhen"]
    SECRET_KEY = os.environ.get("SECRET_KEY") or "adad m fciereqfdskj sdfsdipredmfsljf"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    MAIL_SERVER = "smtp.126.com"
    MAIL_PORT = 994
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    
    XING_MAIL_SUBJECT_PREFIX = "[Xing]"
    XING_MAIL_SENDER = "Xing Admin <lianyun08@126.com>"
    XING_ADMIN = "lianyun08@126.com"
    
    XING_CONFERENCES_PER_PAGE = 20
    XING_PROFILE_CONFERENCES_PER_PAGE = 5
    XING_COMMENTS_PER_PAGE = 5
    
    XING_FOLLOWS_PER_PAGE = 10
    
    SSL_DISABLE = True

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """
    Extends from Config class.
    Configration for development environment.
    """
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 将错误信息发送给管理员
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, "MAIL_USERNAME", None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, "MAIL_USE_SSL", None):
                secure = ()
        
        mail_handler = SMTPHandler(
            mailhost = (cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr = cls.XING_MAIL_SENDER,
            toaddrs = [cls.XING_ADMIN],
            subject = cls.XING_MAIL_SUBJECT_PREFIX + " Application Error!",
            credentials = credentials,
            secure = secure
        )
        mail_handler.setLevel(logging.ERROR)
        
        app.logger.addHandler(mail_handler)

class HerokuConfig(ProductionConfig):

    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # handle proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)
        
        # 输出到stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)  

class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)
        
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'heroku': HerokuConfig,
    'unix': UnixConfig
}
