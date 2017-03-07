import unittest

from app.models import User, Permission, Role
from app import create_app, db

class UserModelsTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_passwd_setter(self):
        u = User(email="test@1.com", nickname="test", passwd="cat")
        self.assertTrue(u.password_hash is not None)

    def test_passwd_getter(self):
        u = User(email="test@1.com", nickname="test", passwd="cat")
        with self.assertRaises(AttributeError):
            u.passwd

    def test_passwd_verification(self):
        u = User(email="test@1.com", nickname="test", passwd = "cat")
        self.assertTrue(u.verify_passwd("cat"))
        self.assertFalse(u.verify_passwd("dog"))

    def test_passed_salts_are_random(self):
        u1 = User(email="test@1.com", nickname="test", passwd="cat")
        u2 = User(email="test@1.com", nickname="test", passwd="cat")
        self.assertTrue(u1.password_hash != u2.password_hash)

    def test_default_user_roles_permissions(self):
        u = User(email="ly@1.com", nickname="ly", passwd="cat")
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMIT))
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.MODERATE_COMMITS))
        self.assertFalse(u.can(Permission.ADMINISTER))

    def test_admin_user_roles_permissions(self):
        admin_role = Role.query.filter_by(permissions=0xff).first()
        u = User(email="ly@1.com", nickname="ly", passwd="cat", role=admin_role)
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMIT))
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertTrue(u.can(Permission.MODERATE_COMMITS))
        self.assertTrue(u.can(Permission.ADMINISTER))
