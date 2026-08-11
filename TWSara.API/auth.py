import os
from datetime import timedelta
from functools import wraps

from flask_jwt_extended import JWTManager, get_jwt, get_jwt_identity, jwt_required

jwt = JWTManager()


def init_jwt(app):
    app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
    jwt.init_app(app)


def current_user():
    """The UserSara row for the caller of the current JWT-authenticated request."""
    from models import UserSara

    return UserSara.query.get(int(get_jwt_identity()))


def role_required(*roles):
    """Restrict a route to callers whose JWT 'role' claim is in `roles`."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            if get_jwt().get('role') not in roles:
                return {'error': 'forbidden'}, 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
