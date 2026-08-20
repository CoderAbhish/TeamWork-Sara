from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from auth import current_user
from controllers.lead_controller import _owned_lead_or_none
from db import db
from models import SiteVisit


def _site_visit_payload(v):
    return {
        'recordId': v.recordId,
        'custProjectId': v.custProjectId,
        'scheduledOn': v.scheduledOn.isoformat() if v.scheduledOn else None,
        'status': v.status,
        'notes': v.notes,
    }


class SiteVisitListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self, lead_id):
        lead = _owned_lead_or_none(lead_id, current_user())
        if not lead:
            return {'error': 'lead not found'}, 404
        return {'items': [_site_visit_payload(v) for v in lead.siteVisits]}

    def post(self, lead_id):
        me = current_user()
        lead = _owned_lead_or_none(lead_id, me)
        if not lead:
            return {'error': 'lead not found'}, 404

        data = request.get_json(silent=True) or {}
        scheduled_on = data.get('scheduledOn')
        if not scheduled_on:
            return {'error': 'scheduledOn is required'}, 400

        visit = SiteVisit(
            custProjectId=lead_id,
            scheduledOn=scheduled_on,
            status=(data.get('status') or 'Scheduled').strip(),
            notes=(data.get('notes') or '').strip() or None,
            createdBy=me.recordId,
        )
        db.session.add(visit)
        db.session.commit()
        return {'siteVisit': _site_visit_payload(visit)}, 201


class SiteVisitResource(Resource):
    method_decorators = [jwt_required()]

    def _owned_or_none(self, visit_id, me):
        visit = SiteVisit.query.get(visit_id)
        if not visit:
            return None
        if not _owned_lead_or_none(visit.custProjectId, me):
            return None
        return visit

    def patch(self, visit_id):
        me = current_user()
        visit = self._owned_or_none(visit_id, me)
        if not visit:
            return {'error': 'site visit not found'}, 404

        data = request.get_json(silent=True) or {}
        if 'scheduledOn' in data:
            if not data['scheduledOn']:
                return {'error': 'scheduledOn cannot be empty'}, 400
            visit.scheduledOn = data['scheduledOn']
        if 'status' in data:
            status = (data.get('status') or '').strip()
            if not status:
                return {'error': 'status cannot be empty'}, 400
            visit.status = status
        if 'notes' in data:
            visit.notes = (data.get('notes') or '').strip() or None
        visit.modifiedBy = me.recordId

        db.session.commit()
        return {'siteVisit': _site_visit_payload(visit)}

    def delete(self, visit_id):
        me = current_user()
        visit = self._owned_or_none(visit_id, me)
        if not visit:
            return {'error': 'site visit not found'}, 404
        db.session.delete(visit)
        db.session.commit()
        return {}, 204
