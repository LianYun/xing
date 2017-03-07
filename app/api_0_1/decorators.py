# _*_ coding: utf-8 _*_

from functools import wraps
from flask import g
from .errors import forbidden
from ..models import Permission

def permission_required(permission):
	def decorator(f):
		@wraps(f)
		def decorated_function(*args, **kwargs):
			if not g.current_user.can(permission):
				return forbidden("Insufficient permissions")
			return f(*args, **kwargs)
		return decorated_function
	return decorator
    
def not_anonymous(f):
    return permission_required(Permission.FOLLOW)(f)