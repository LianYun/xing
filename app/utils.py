# _*_ coding: utf-8 _*_

import functools
from flask import abort
from flask.ext.login import current_user

from .models import Permission

def permission_required(permission):
    def decorator(func):
        @functools.wraps(func)
        def helper(*args, **kwargs):
            if (not current_user.can(permission)):
                abort(403)
            return func(*args, **kwargs)
        return helper
    return decorator

def admin_required(func):
    return permission_required(Permission.ADMINISTER)(func)
