from datetime import datetime, timedelta, timezone

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from auth import current_user
from controllers.lead_controller import _lead_payload
from models import CustProject, LookupLeadCategory, LookupLeadStatus

PERIODS = {
    'week': 8,
    'month': 12,
    'quarter': 8,
    'year': 5,
}


def _scope(query, me):
    if me.role == 'teamMember':
        return query.filter(CustProject.assignedToUserId == me.recordId)
    return query


def _bucket_label(dt, period):
    if period == 'week':
        start = dt - timedelta(days=dt.weekday())
        return start.strftime('%b %-d')
    if period == 'month':
        return dt.strftime('%b %Y')
    if period == 'quarter':
        return f'Q{(dt.month - 1) // 3 + 1} {dt.year}'
    return str(dt.year)


def _period_key(dt, period):
    if period == 'week':
        start = dt - timedelta(days=dt.weekday())
        return (start.year, start.month, start.day)
    if period == 'month':
        return (dt.year, dt.month)
    if period == 'quarter':
        return (dt.year, (dt.month - 1) // 3)
    return (dt.year,)


class ConvertedOverTimeResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        me = current_user()
        period = request.args.get('period', 'month')
        if period not in PERIODS:
            return {'error': 'period must be one of week, month, quarter, year'}, 400

        now = datetime.now(timezone.utc)
        window = PERIODS[period]

        # Build the fixed trailing window of buckets first (zero-filled),
        # oldest to newest, so the chart's x-axis is always consistent.
        buckets = []
        for i in range(window - 1, -1, -1):
            if period == 'week':
                point = now - timedelta(weeks=i)
            elif period == 'month':
                month_index = now.month - 1 - i
                year = now.year + month_index // 12
                month = month_index % 12 + 1
                point = now.replace(year=year, month=month, day=1)
            elif period == 'quarter':
                quarter_index = (now.month - 1) // 3 - i
                year = now.year + quarter_index // 4
                quarter = quarter_index % 4
                point = now.replace(year=year, month=quarter * 3 + 1, day=1)
            else:
                point = now.replace(year=now.year - i, month=1, day=1)
            buckets.append({'key': _period_key(point, period), 'label': _bucket_label(point, period), 'count': 0})

        counts_by_key = {b['key']: b for b in buckets}

        query = _scope(CustProject.query, me).filter(CustProject.convertedOn.isnot(None))
        for lead in query.all():
            key = _period_key(lead.convertedOn, period)
            if key in counts_by_key:
                counts_by_key[key]['count'] += 1

        return {'buckets': [{'label': b['label'], 'count': b['count']} for b in buckets]}


class LeadsByCategoryResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        me = current_user()
        categories = LookupLeadCategory.query.order_by(LookupLeadCategory.recordId).all()
        items = []
        for category in categories:
            count = _scope(CustProject.query, me).filter(CustProject.leadCategoryId == category.recordId).count()
            items.append({'name': category.recordName, 'count': count})

        uncategorized = _scope(CustProject.query, me).filter(CustProject.leadCategoryId.is_(None)).count()
        if uncategorized:
            items.append({'name': 'Uncategorized', 'count': uncategorized})

        return {'items': items}


class HotLeadsResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        me = current_user()
        query = (
            _scope(CustProject.query, me)
            .join(LookupLeadCategory)
            .join(LookupLeadStatus)
            .filter(LookupLeadCategory.recordName == 'Hot')
            .filter(LookupLeadStatus.recordName.notin_(['Converted', 'Lost']))
        )
        leads = query.order_by(CustProject.createdOn.asc()).limit(10).all()
        return {'items': [_lead_payload(lead) for lead in leads]}
