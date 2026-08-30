"""Computed notifications — there's no background scheduler in this app, so
rather than generating notification rows ahead of time, every request just
recomputes what's currently true (follow-ups due soon, lapsed
registrations, unassigned leads, pending transfer requests) from live data.
NotificationDismissal is the only persisted piece: a per-user marker so a
reminder that's been seen doesn't keep resurfacing on the next poll.
"""

from datetime import timedelta

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from auth import current_user
from db import db
from models import CustProject, LeadTransferRequest, NotificationDismissal, utcnow

# Leads that are done, one way or another, don't need follow-up or
# registration nudges any more.
_DONE_STATUSES = {'Lost', 'Converted'}

# Ordered most-urgent-first: (key, "due within" window, human label). Only
# the single smallest window a lead currently falls inside is surfaced, so
# a lead escalates through "1 day" -> "6 hours" -> "30 minutes" as its
# follow-up approaches rather than showing all three at once.
_FOLLOW_UP_BUCKETS = [
    ('30m', timedelta(minutes=30), '30 minutes'),
    ('6h', timedelta(hours=6), '6 hours'),
    ('1d', timedelta(days=1), '1 day'),
]

_SEVERITY_ORDER = {'urgent': 0, 'warning': 1, 'info': 2}


def _dismissed_keys(user_id):
    rows = NotificationDismissal.query.filter_by(userId=user_id).all()
    return {r.notificationKey for r in rows}


def _leads_for(me, extra_filter):
    query = CustProject.query.filter(extra_filter)
    if me.role == 'teamMember':
        query = query.filter(CustProject.assignedToUserId == me.recordId)
    return [
        lead for lead in query.all()
        if not (lead.status and lead.status.recordName in _DONE_STATUSES)
    ]


def _follow_up_notifications(me, now):
    items = []
    for lead in _leads_for(me, CustProject.nextFollowUpOn.isnot(None)):
        delta = lead.nextFollowUpOn - now
        for bucket_key, max_delta, label in _FOLLOW_UP_BUCKETS:
            if delta <= max_delta:
                items.append({
                    'key': f'followup:{lead.recordId}:{bucket_key}',
                    'type': 'followUpReminder',
                    'severity': 'urgent' if bucket_key == '30m' else 'warning' if bucket_key == '6h' else 'info',
                    'title': 'Follow-up overdue' if delta.total_seconds() < 0 else f'Follow-up due in ~{label}',
                    'message': f'{lead.customer.leadName} — {lead.nextFollowUpOn.isoformat()}',
                    'leadId': lead.recordId,
                    'referenceOn': lead.nextFollowUpOn.isoformat(),
                })
                break
    return items


def _registration_expired_notifications(me, now):
    items = []
    for lead in _leads_for(
        me,
        db.and_(
            CustProject.isCustLeadRegistered.is_(True),
            CustProject.registrationExpiryDate.isnot(None),
            CustProject.registrationExpiryDate < now,
        ),
    ):
        items.append({
            'key': f'reg-expired:{lead.recordId}',
            'type': 'registrationExpired',
            'severity': 'warning',
            'title': 'Registration needs renewal',
            'message': f"{lead.customer.leadName}'s registration expired "
                       f"{lead.registrationExpiryDate.date().isoformat()}",
            'leadId': lead.recordId,
            'referenceOn': lead.registrationExpiryDate.isoformat(),
        })
    return items


def _unassigned_notification(me, now):
    if me.role != 'admin':
        return []
    count = CustProject.query.filter(CustProject.assignedToUserId.is_(None)).count()
    if not count:
        return []
    return [{
        'key': 'unassigned-count',
        'type': 'unassignedLeads',
        'severity': 'info',
        'title': 'Unassigned leads',
        'message': f'{count} lead(s) have no team member assigned',
        'leadId': None,
        'referenceOn': now.isoformat(),
    }]


def _transfer_request_notifications(me):
    if me.role != 'admin':
        return []
    items = []
    requests = (
        LeadTransferRequest.query.filter_by(status='pending')
        .order_by(LeadTransferRequest.requestedOn.desc())
        .all()
    )
    for t in requests:
        items.append({
            'key': f'transfer-request:{t.recordId}',
            'type': 'transferRequest',
            'severity': 'info',
            'title': 'Lead transfer requested',
            'message': f'{t.fromUser.username} wants to hand "{t.lead.customer.leadName}" to {t.toUser.username}',
            'leadId': t.custProjectId,
            'referenceOn': t.requestedOn.isoformat(),
        })
    return items


class NotificationListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        me = current_user()
        now = utcnow()
        items = (
            _follow_up_notifications(me, now)
            + _registration_expired_notifications(me, now)
            + _unassigned_notification(me, now)
            + _transfer_request_notifications(me)
        )
        dismissed = _dismissed_keys(me.recordId)
        items = [i for i in items if i['key'] not in dismissed]
        items.sort(key=lambda i: (_SEVERITY_ORDER.get(i['severity'], 9), i['referenceOn'] or ''))
        return {'items': items}


class NotificationDismissResource(Resource):
    method_decorators = [jwt_required()]

    def post(self):
        me = current_user()
        data = request.get_json(silent=True) or {}
        key = (data.get('key') or '').strip()
        if not key:
            return {'error': 'key is required'}, 400

        if not NotificationDismissal.query.filter_by(userId=me.recordId, notificationKey=key).first():
            db.session.add(NotificationDismissal(userId=me.recordId, notificationKey=key))
            db.session.commit()
        return {}, 204
