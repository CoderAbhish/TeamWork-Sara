from flask import request
from flask_restful import Resource

from auth import current_user, role_required
from controllers.lead_controller import _lead_payload
from db import db
from models import CustProject, UserSara


def _team_member_payload(user):
    return {
        'recordId': user.recordId,
        'username': user.username,
        'emailId': user.emailId,
        'contactNumber': user.contactNumber,
        'isActive': user.isActive,
        'isApproved': user.isApproved,
        'assignedLeadCount': CustProject.query.filter_by(assignedToUserId=user.recordId).count(),
    }


class TeamMemberListResource(Resource):
    method_decorators = [role_required('admin')]

    def get(self):
        members = (
            UserSara.query.filter_by(isAdmin=False).order_by(UserSara.username).all()
        )
        return {'items': [_team_member_payload(m) for m in members]}


class TeamMemberResource(Resource):
    method_decorators = [role_required('admin')]

    def get(self, user_id):
        member = UserSara.query.filter_by(recordId=user_id, isAdmin=False).first()
        if not member:
            return {'error': 'team member not found'}, 404
        return {'teamMember': _team_member_payload(member)}

    def patch(self, user_id):
        member = UserSara.query.filter_by(recordId=user_id, isAdmin=False).first()
        if not member:
            return {'error': 'team member not found'}, 404

        data = request.get_json(silent=True) or {}
        if 'isActive' in data:
            member.isActive = bool(data['isActive'])
        if 'isApproved' in data:
            member.isApproved = bool(data['isApproved'])
        member.modifiedBy = current_user().recordId

        db.session.commit()
        return {'teamMember': _team_member_payload(member)}


class TeamMemberLeadsResource(Resource):
    method_decorators = [role_required('admin')]

    def get(self, user_id):
        member = UserSara.query.filter_by(recordId=user_id, isAdmin=False).first()
        if not member:
            return {'error': 'team member not found'}, 404
        leads = CustProject.query.filter_by(assignedToUserId=user_id).order_by(
            CustProject.createdOn.desc()
        ).all()
        return {'items': [_lead_payload(lead) for lead in leads]}
