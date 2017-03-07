#!/usr/bin/env python
# _*_ coding: utf-8 _*_

"""
Script for start, shell, test of this project.

lianyun @ 2015-12-29 XiAn
"""

# import system dependencies
import os

COV = None
if os.environ.get("FLASK_COVERAGE"):
    import coverage
    COV = coverage.coverage(branch=True, include="app/*")
    COV.start()
    

# import flask affixes
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

# import other object from this project
from app import create_app, db
from app.models import User, Role, Conference, City, Topic, Comment, Attendor


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)

migrate = Migrate(app, db)
manager.add_command("db", MigrateCommand)

def make_shell_context():
    """
    shell命令的上下文。
    """
    return dict(app=app, db=db, User=User, Role=Role, Conference=Conference, \
            City=City, Topic=Topic, Comment=Comment, Attendor=Attendor)

manager.add_command("shell", Shell(make_context=make_shell_context))

@manager.command
def test(coverage=False):
    """
    项目的测试命令！
    """
    if coverage and not os.environ.get("FLASK_COVERAGE"):
        import sys
        os.environ["FLASK_COVERAGE"] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    
    import unittest
    tests = unittest.TestLoader().discover("tests")
    unittest.TextTestRunner(verbosity=2).run(tests)
    
    if COV:
        COV.stop()
        COV.save()
        print("Coverage Summary:")
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print("HTML version: file://%s/index.html" % covdir)
        COV.erase()

@manager.command
def deploy():
    """运行部署任务"""
    from flask.ext.migrate import upgrade
    upgrade()
    Role.insert_roles()
    City.insert_cities()
    Topic.insert_topics()
    
@manager.command
def genfake():
    config = os.getenv('FLASK_CONFIG') or 'default'
    if config == 'default' or config == 'development':
        print("delete all files ...")
        db.drop_all()
        db.create_all()
        print("creating roles ...")
        Role.insert_roles()
        print("creating cities ...")
        City.insert_cities()
        print("creating topics ...")
        Topic.insert_topics()
        print("creating users ...")
        User.generate_fake()
        print("creating conferences ...")
        Conference.generate_fake()
        print("creating comments ...")
        Comment.generate_fake()
    

if __name__ == "__main__":
    #app.run("0.0.0.0", debug=True)
    manager.run()
