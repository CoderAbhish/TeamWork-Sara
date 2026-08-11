import bcrypt
from flask import request
from flask_jwt_extended import create_access_token, jwt_required
from flask_restful import Resource

from auth import current_user
from db import db
from models import UserSara


def _user_payload(user):
    return {
        'recordId': user.recordId,
        'username': user.username,
        'emailId': user.emailId,
        'role': user.role,
        'isApproved': user.isApproved,
    }


def _issue_token(user):
    access_token = create_access_token(
        identity=str(user.recordId),
        additional_claims={'role': user.role, 'username': user.username},
    )
    return {'access_token': access_token, 'user': _user_payload(user)}


class LoginResource(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        identifier = (data.get('username') or '').strip()
        password = data.get('password') or ''

        if not identifier or not password:
            return {'error': 'username and password are required'}, 400

        user = UserSara.query.filter(
            (UserSara.username == identifier) | (UserSara.emailId == identifier)
        ).first()

        valid_password = user is not None and bcrypt.checkpw(
            password.encode('utf-8'), user.passwordHash.encode('utf-8')
        )
        if not user or not user.isActive or not valid_password:
            return {'error': 'invalid credentials'}, 401

        if not user.isAdmin and not user.isApproved:
            return {
                'error': 'pending_approval',
                'message': 'Your registration is pending admin approval. Please check back soon.',
            }, 403

        return _issue_token(user)


class RegisterResource(Resource):
    """Self-registration for team members.

    Admin accounts are seeded (see `flask seed-admin`), not self-served,
    so this always creates a non-admin (teamMember) user.
    """

    def post(self):
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        email_id = (data.get('emailId') or '').strip()
        password = data.get('password') or ''
        contact_number = (data.get('contactNumber') or '').strip() or None
        alternate_number = (data.get('alternateNumber') or '').strip() or None

        if not username or not email_id or not password:
            return {'error': 'username, emailId and password are required'}, 400
        if len(password) < 8:
            return {'error': 'password must be at least 8 characters'}, 400

        exists = UserSara.query.filter(
            (UserSara.username == username) | (UserSara.emailId == email_id)
        ).first()
        if exists:
            return {'error': 'username or email is already registered'}, 409

        user = UserSara(
            username=username,
            emailId=email_id,
            passwordHash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            contactNumber=contact_number,
            alternateNumber=alternate_number,
            isAdmin=False,
            isActive=True,
            isApproved=False,
        )
        db.session.add(user)
        db.session.commit()

        return {
            'status': 'pending_approval',
            'message': 'Registration submitted. An admin will review your account before you can sign in.',
        }, 201


class MeResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        user = current_user()
        if not user:
            return {'error': 'user not found'}, 404
        return {'user': _user_payload(user)}
