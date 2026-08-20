from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from auth import current_user, role_required
from controllers.lead_controller import _validate_assignee
from db import db
from models import CustProject, LeadTransferRequest, utcnow


def _transfer_payload(t):
    return {
        'recordId': t.recordId,
        'custProjectId': t.custProjectId,
        'leadName': t.lead.customer.leadName if t.lead else None,
        'fromUserId': t.fromUserId,
        'fromUsername': t.fromUser.username if t.fromUser else None,
        'toUserId': t.toUserId,
        'toUsername': t.toUser.username if t.toUser else None,
        'comment': t.comment,
        'status': t.status,
        'requestedOn': t.requestedOn.isoformat() if t.requestedOn else None,
        'reviewedByUsername': t.reviewedBy.username if t.reviewedBy else None,
        'reviewedOn': t.reviewedOn.isoformat() if t.reviewedOn else None,
        'reviewComment': t.reviewComment,
    }


class LeadTransferRequestListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        me = current_user()
        query = LeadTransferRequest.query
        if me.role == 'teamMember':
            query = query.filter_by(fromUserId=me.recordId)
        elif request.args.get('status'):
            query = query.filter_by(status=request.args['status'])

        items = query.order_by(LeadTransferRequest.requestedOn.desc()).all()
        return {'items': [_transfer_payload(t) for t in items]}

    def post(self):
        me = current_user()
        if me.role != 'teamMember':
            return {'error': 'only team members can request a lead transfer'}, 403

        data = request.get_json(silent=True) or {}
        cust_project_id = data.get('custProjectId')
        to_user_id = data.get('toUserId')
        comment = (data.get('comment') or '').strip()

        if not cust_project_id or not to_user_id or not comment:
            return {'error': 'custProjectId, toUserId and comment are required'}, 400

        lead = CustProject.query.get(cust_project_id)
        if not lead:
            return {'error': 'lead not found'}, 404
        if lead.assignedToUserId != me.recordId:
            return {'error': 'you can only transfer leads currently assigned to you'}, 403
        if to_user_id == me.recordId:
            return {'error': 'toUserId must be a different team member'}, 400

        assignee_error = _validate_assignee(to_user_id)
        if assignee_error:
            return {'error': assignee_error}, 400

        existing_pending = LeadTransferRequest.query.filter_by(
            custProjectId=cust_project_id, status='pending'
        ).first()
        if existing_pending:
            return {'error': 'a transfer request is already pending for this lead'}, 409

        transfer = LeadTransferRequest(
            custProjectId=cust_project_id,
            fromUserId=me.recordId,
            toUserId=to_user_id,
            comment=comment,
        )
        db.session.add(transfer)
        db.session.commit()
        return {'transferRequest': _transfer_payload(transfer)}, 201


class LeadTransferApproveResource(Resource):
    method_decorators = [role_required('admin')]

    def post(self, transfer_id):
        transfer = LeadTransferRequest.query.get(transfer_id)
        if not transfer:
            return {'error': 'transfer request not found'}, 404
        if transfer.status != 'pending':
            return {'error': f'transfer request already {transfer.status}'}, 409

        me = current_user()
        transfer.lead.assignedToUserId = transfer.toUserId
        transfer.lead.modifiedBy = me.recordId
        transfer.status = 'approved'
        transfer.reviewedByUserId = me.recordId
        transfer.reviewedOn = utcnow()
        db.session.commit()
        return {'transferRequest': _transfer_payload(transfer)}


class LeadTransferRejectResource(Resource):
    method_decorators = [role_required('admin')]

    def post(self, transfer_id):
        transfer = LeadTransferRequest.query.get(transfer_id)
        if not transfer:
            return {'error': 'transfer request not found'}, 404
        if transfer.status != 'pending':
            return {'error': f'transfer request already {transfer.status}'}, 409

        data = request.get_json(silent=True) or {}
        me = current_user()
        transfer.status = 'rejected'
        transfer.reviewedByUserId = me.recordId
        transfer.reviewedOn = utcnow()
        transfer.reviewComment = (data.get('reviewComment') or '').strip() or None
        db.session.commit()
        return {'transferRequest': _transfer_payload(transfer)}
