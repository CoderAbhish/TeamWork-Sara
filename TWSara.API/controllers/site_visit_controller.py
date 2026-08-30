from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from auth import current_user
from controllers.lead_controller import (
    _apply_lead_status,
    _lead_payload,
    _owned_lead_or_none,
    _status_id_by_name,
)
from db import db
from models import LeadComment, SiteVisit, utcnow

# Automatic status advances triggered by site-visit activity — these are the
# only transitions allowed out of that step, and only forward, never
# overriding a lead that's already moved further along (e.g. converted).
_STATUSES_THAT_ADVANCE_ON_SCHEDULE = {'New', 'Contacted'}
_STATUS_THAT_ADVANCES_ON_COMPLETE = 'Site Visit Scheduled'

# A visit's status only ever starts at Scheduled (set on creation, never
# chosen by the caller) and is then moved to exactly one of these by hand.
VISIT_STATUS_OPTIONS = {'Scheduled', 'Completed', 'Postponed', 'Preponed', 'No-show'}


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

        if not lead.isCustLeadRegistered:
            return {'error': 'the lead must be registered with the builder before a site visit can be scheduled'}, 400

        data = request.get_json(silent=True) or {}
        scheduled_on = data.get('scheduledOn')
        if not scheduled_on:
            return {'error': 'scheduledOn is required'}, 400

        visit = SiteVisit(
            custProjectId=lead_id,
            scheduledOn=scheduled_on,
            status='Scheduled',
            notes=(data.get('notes') or '').strip() or None,
            createdBy=me.recordId,
        )
        db.session.add(visit)

        current_status_name = lead.status.recordName if lead.status else None
        if current_status_name in _STATUSES_THAT_ADVANCE_ON_SCHEDULE:
            scheduled_status_id = _status_id_by_name('Site Visit Scheduled')
            if scheduled_status_id:
                _apply_lead_status(lead, scheduled_status_id)
                lead.modifiedBy = me.recordId

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
            if status not in VISIT_STATUS_OPTIONS:
                return {'error': f'status must be one of: {", ".join(sorted(VISIT_STATUS_OPTIONS))}'}, 400
            if status == 'Completed' and utcnow().date() < visit.scheduledOn.date():
                return {'error': 'this visit can only be marked completed on or after its scheduled date'}, 400
            visit.status = status
        if 'notes' in data:
            visit.notes = (data.get('notes') or '').strip() or None
        visit.modifiedBy = me.recordId

        if 'status' in data and visit.status == 'Completed':
            lead = visit.lead
            current_status_name = lead.status.recordName if lead.status else None
            if current_status_name == _STATUS_THAT_ADVANCES_ON_COMPLETE:
                negotiation_status_id = _status_id_by_name('Negotiation')
                if negotiation_status_id:
                    _apply_lead_status(lead, negotiation_status_id)
                    lead.modifiedBy = me.recordId

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


class SiteVisitRescheduleResource(Resource):
    """Rescheduling is deliberately its own action, not part of the generic
    PATCH: it's only allowed once the visit's status has been moved away
    from Scheduled (i.e. something was recorded about what happened — it
    was completed, postponed, preponed, or a no-show), always requires a
    comment (why is it moving?), and always pushes the lead's status back
    to Site Visit Scheduled, even if the lead had already progressed past
    it."""

    method_decorators = [jwt_required()]

    def post(self, visit_id):
        me = current_user()
        visit = SiteVisit.query.get(visit_id)
        if not visit or not _owned_lead_or_none(visit.custProjectId, me):
            return {'error': 'site visit not found'}, 404

        if visit.status == 'Scheduled':
            return {
                'error': 'update this visit\'s status before rescheduling it — '
                'reschedule is only available once something has been recorded about it'
            }, 400

        data = request.get_json(silent=True) or {}
        new_scheduled_on = data.get('scheduledOn')
        notes = (data.get('notes') or '').strip()
        if not new_scheduled_on:
            return {'error': 'scheduledOn is required'}, 400
        if not notes:
            return {'error': 'a comment is required when rescheduling a visit'}, 400

        visit.scheduledOn = new_scheduled_on
        visit.status = 'Scheduled'
        visit.notes = notes
        visit.modifiedBy = me.recordId

        lead = visit.lead
        scheduled_status_id = _status_id_by_name('Site Visit Scheduled')
        if scheduled_status_id:
            _apply_lead_status(lead, scheduled_status_id)
            lead.modifiedBy = me.recordId
        db.session.add(LeadComment(
            custProjectId=lead.recordId,
            authorUserId=me.recordId,
            commentText=f'Site visit rescheduled: {notes}',
        ))

        db.session.commit()
        return {'siteVisit': _site_visit_payload(visit), 'lead': _lead_payload(lead)}
