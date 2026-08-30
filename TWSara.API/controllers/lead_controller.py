from datetime import timedelta

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from auth import current_user, role_required
from db import db
from models import (
    BuilderProject,
    CustLeadPrimary,
    CustProject,
    LeadComment,
    LeadFollowUp,
    LookupLeadCategory,
    LookupLeadSource,
    LookupLeadStatus,
    ProjectUnitConfiguration,
    UserSara,
    utcnow,
)

SORT_COLUMNS = {
    'createdOn': CustProject.createdOn,
    'leadName': CustLeadPrimary.leadName,
    'leadLocation': CustLeadPrimary.leadLocation,
    'status': LookupLeadStatus.recordName,
    'category': LookupLeadCategory.recordName,
    'nextFollowUpOn': CustProject.nextFollowUpOn,
}


def _related_leads_payload(lead):
    return [
        {
            'recordId': sibling.recordId,
            'projectName': sibling.project.projectName if sibling.project else None,
            'builderName': sibling.project.builder.builderName if sibling.project else None,
            'statusName': sibling.status.recordName if sibling.status else None,
            'assignedToUsername': sibling.assignedTo.username if sibling.assignedTo else None,
        }
        for sibling in lead.customer.leads
        if sibling.recordId != lead.recordId
    ]


def _lead_payload(lead):
    return {
        'recordId': lead.recordId,
        'customer': {
            'recordId': lead.customer.recordId,
            'leadName': lead.customer.leadName,
            'contactNumber': lead.customer.contactNumber,
            'alternateNumber': lead.customer.alternateNumber,
            'leadLocation': lead.customer.leadLocation,
        },
        'project': (
            {
                'recordId': lead.project.recordId,
                'projectName': lead.project.projectName,
                'builderRecordId': lead.project.builderRecordId,
                'builderName': lead.project.builder.builderName,
                'configurations': [
                    {'recordId': c.recordId, 'configurationLabel': c.configurationLabel}
                    for c in lead.project.configurations
                ],
            }
            if lead.project
            else None
        ),
        'isCustLeadRegistered': lead.isCustLeadRegistered,
        'registeredOn': lead.registeredOn.isoformat() if lead.registeredOn else None,
        'registrationExpiryDate': (
            lead.registrationExpiryDate.isoformat() if lead.registrationExpiryDate else None
        ),
        'assignedToUserId': lead.assignedToUserId,
        'assignedToUsername': lead.assignedTo.username if lead.assignedTo else None,
        'leadStatusId': lead.leadStatusId,
        'leadStatusName': lead.status.recordName if lead.status else None,
        'leadCategoryId': lead.leadCategoryId,
        'leadCategoryName': lead.category.recordName if lead.category else None,
        'leadSourceId': lead.leadSourceId,
        'leadSourceName': lead.source.recordName if lead.source else None,
        'leadSourceDetail': lead.leadSourceDetail,
        'nextFollowUpOn': lead.nextFollowUpOn.isoformat() if lead.nextFollowUpOn else None,
        'interestedConfigId': lead.interestedConfigId,
        'interestedConfigLabel': lead.interestedConfig.configurationLabel if lead.interestedConfig else None,
        'relatedLeads': _related_leads_payload(lead),
        'createdOn': lead.createdOn.isoformat() if lead.createdOn else None,
        'convertedOn': lead.convertedOn.isoformat() if lead.convertedOn else None,
    }


def _apply_lead_status(lead, status_id):
    """Set leadStatusId, stamping convertedOn the first time it becomes Converted."""
    lead.leadStatusId = status_id
    if status_id is not None:
        status = LookupLeadStatus.query.get(status_id)
        if status and status.recordName == 'Converted' and lead.convertedOn is None:
            lead.convertedOn = utcnow()


def _status_id_by_name(name):
    status = LookupLeadStatus.query.filter_by(recordName=name).first()
    return status.recordId if status else None


# The lead status only moves forward along this path, and never by a free
# choice: New -> Contacted is a manual, commented action; Site Visit
# Scheduled and Negotiation are set automatically (see site_visit_controller
# — scheduling a visit / marking one Completed); Converted/On Hold/Lost are
# manual, commented actions reachable once contact has actually happened.
MANUAL_STATUS_TRANSITIONS = {
    'New': ['Contacted'],
    'Contacted': ['Lost', 'On Hold'],
    'Site Visit Scheduled': ['Lost', 'On Hold'],
    'Negotiation': ['Converted', 'On Hold', 'Lost'],
}


def _registration_block_reason(lead):
    """Why a lead can't be registered right now, or None if it's fine.
    The expiry date is always derived from the builder's configured
    validity window — never entered by hand — so registration is blocked
    until that's in place."""
    if not lead.project or not lead.project.builder:
        return 'This lead is not linked to a project yet. Assign a project before registering it.'
    builder_name = lead.project.builder.builderName
    if not lead.project.builder.leadRegistrationValidityDays:
        return (
            f'The lead registration validity for "{builder_name}" has not been set yet. '
            'Please ask an admin to configure it before registering this lead.'
        )
    return None


def _apply_registration(lead, is_registered):
    """Set isCustLeadRegistered, stamping registeredOn and deriving
    registrationExpiryDate from the builder's configured validity window
    the first time it flips true."""
    was_registered = lead.isCustLeadRegistered
    lead.isCustLeadRegistered = is_registered

    if is_registered and not was_registered:
        lead.registeredOn = utcnow()
        validity_days = lead.project.builder.leadRegistrationValidityDays
        lead.registrationExpiryDate = utcnow() + timedelta(days=validity_days)


def _comment_payload(comment):
    return {
        'recordId': comment.recordId,
        'commentText': comment.commentText,
        'authorUsername': comment.author.username if comment.author else None,
        'createdOn': comment.createdOn.isoformat() if comment.createdOn else None,
    }


def _owned_lead_or_none(lead_id, me):
    lead = CustProject.query.get(lead_id)
    if not lead:
        return None
    if me.role == 'teamMember' and lead.assignedToUserId != me.recordId:
        return None
    return lead


def _validate_assignee(assignee_id):
    if assignee_id is None:
        return None
    assignee = UserSara.query.get(assignee_id)
    if not assignee or assignee.isAdmin:
        return 'assignedToUserId must be an existing team member'
    return None


EXTRA_LEAD_FIELD_KEYS = {
    'isCustLeadRegistered',
    'leadSourceId',
    'leadSourceDetail',
    'interestedConfigId',
}


def _apply_extra_lead_fields(lead, data):
    """Applies the fields both team members and admins may edit on a lead:
    registration, lead source, interested configuration. Status changes go
    through LeadStatusTransitionResource and follow-ups through
    LeadFollowUpListResource — both require a mandatory comment and are not
    part of this generic PATCH. Returns an error string, or None on success."""
    if 'leadSourceId' in data:
        if data['leadSourceId'] is not None and not LookupLeadSource.query.get(data['leadSourceId']):
            return 'invalid leadSourceId'
        lead.leadSourceId = data['leadSourceId']
    if 'leadSourceDetail' in data:
        lead.leadSourceDetail = (data.get('leadSourceDetail') or '').strip() or None
    if 'interestedConfigId' in data:
        config_id = data['interestedConfigId']
        if config_id is not None and not ProjectUnitConfiguration.query.get(config_id):
            return 'invalid interestedConfigId'
        lead.interestedConfigId = config_id or None
    if 'isCustLeadRegistered' in data:
        is_registered = bool(data['isCustLeadRegistered'])
        if is_registered and not lead.isCustLeadRegistered:
            block_reason = _registration_block_reason(lead)
            if block_reason:
                return block_reason
        _apply_registration(lead, is_registered)
    return None


def _filtered_lead_query(me, args):
    """The base leads query shared by the paginated list and the
    'select all filtered' id lookup — keeps both in lockstep."""
    query = (
        CustProject.query.join(CustLeadPrimary)
        .outerjoin(BuilderProject)
        .outerjoin(LookupLeadStatus)
        .outerjoin(LookupLeadCategory)
    )

    if me.role == 'teamMember':
        query = query.filter(CustProject.assignedToUserId == me.recordId)
    elif args.get('assignedToUserId'):
        query = query.filter(CustProject.assignedToUserId == int(args['assignedToUserId']))

    if args.get('status'):
        query = query.filter(CustProject.leadStatusId == int(args['status']))
    if args.get('category'):
        query = query.filter(CustProject.leadCategoryId == int(args['category']))
    if args.get('builderId'):
        query = query.filter(BuilderProject.builderRecordId == int(args['builderId']))
    if args.get('projectId'):
        query = query.filter(CustProject.projectId == int(args['projectId']))
    if args.get('leadSourceId'):
        query = query.filter(CustProject.leadSourceId == int(args['leadSourceId']))
    if args.get('followUpDue', '').lower() == 'true':
        query = query.filter(
            CustProject.nextFollowUpOn.isnot(None), CustProject.nextFollowUpOn <= utcnow()
        )
    if args.get('search'):
        like = f"%{args['search']}%"
        query = query.filter(
            db.or_(
                CustLeadPrimary.leadName.ilike(like),
                CustLeadPrimary.contactNumber.ilike(like),
                CustLeadPrimary.leadLocation.ilike(like),
            )
        )
    return query


class LeadListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        me = current_user()
        query = _filtered_lead_query(me, request.args)

        # Powers "select all N filtered leads" in the UI — the same filters
        # as the paginated list, but every matching id, unpaginated.
        if request.args.get('idsOnly', '').lower() == 'true':
            return {'ids': [row.recordId for row in query.with_entities(CustProject.recordId).all()]}

        sort_col = SORT_COLUMNS.get(request.args.get('sortBy'), CustProject.createdOn)
        query = query.order_by(
            sort_col.asc() if request.args.get('sortDir') == 'asc' else sort_col.desc()
        )

        page = max(int(request.args.get('page', 1)), 1)
        page_size = min(max(int(request.args.get('pageSize', 20)), 1), 100)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            'items': [_lead_payload(lead) for lead in items],
            'total': total,
            'page': page,
            'pageSize': page_size,
        }

    @role_required('admin')
    def post(self):
        data = request.get_json(silent=True) or {}

        # A lead can be interested in more than one project (same or
        # different builders) — projectIds creates one CustProject "pipeline"
        # row per project, all against the same customer, in a single call.
        # projectId (singular) is kept for backward compatibility.
        project_ids = data.get('projectIds')
        if project_ids is not None:
            if not isinstance(project_ids, list) or not project_ids:
                return {'error': 'projectIds must be a non-empty list'}, 400
        else:
            project_ids = [data.get('projectId')] if data.get('projectId') else [None]

        for pid in project_ids:
            if pid and not BuilderProject.query.get(pid):
                return {'error': f'invalid projectId: {pid}'}, 400

        customer_id = data.get('customerId')
        customer_reused = False
        if customer_id:
            customer = CustLeadPrimary.query.get(customer_id)
            if not customer:
                return {'error': 'customer not found'}, 404
            customer_reused = True
        else:
            lead_name = (data.get('leadName') or '').strip()
            contact_number = (data.get('contactNumber') or '').strip()
            if not lead_name or not contact_number:
                return {'error': 'leadName and contactNumber are required for a new customer'}, 400
            customer = CustLeadPrimary.query.filter_by(contactNumber=contact_number).first()
            if not customer:
                customer = CustLeadPrimary(
                    leadName=lead_name,
                    contactNumber=contact_number,
                    alternateNumber=(data.get('alternateNumber') or '').strip() or None,
                    leadLocation=(data.get('leadLocation') or '').strip() or None,
                    createdBy=current_user().recordId,
                )
                db.session.add(customer)
                db.session.flush()
            else:
                customer_reused = True

        assignee_error = _validate_assignee(data.get('assignedToUserId'))
        if assignee_error:
            return {'error': assignee_error}, 400

        status_id = data.get('leadStatusId')
        if not status_id:
            default_status = LookupLeadStatus.query.filter_by(recordName='New').first()
            status_id = default_status.recordId if default_status else None

        leads = []
        for pid in project_ids:
            lead = CustProject(
                customerId=customer.recordId,
                projectId=pid,
                assignedToUserId=data.get('assignedToUserId'),
                leadCategoryId=data.get('leadCategoryId'),
                createdBy=current_user().recordId,
            )
            _apply_lead_status(lead, status_id)
            extra_error = _apply_extra_lead_fields(lead, data)
            if extra_error:
                return {'error': extra_error}, 400
            db.session.add(lead)
            leads.append(lead)

        db.session.commit()
        if data.get('projectIds') is not None:
            return {'leads': [_lead_payload(lead) for lead in leads], 'customerReused': customer_reused}, 201
        return {'lead': _lead_payload(leads[0]), 'customerReused': customer_reused}, 201


class LeadResource(Resource):
    method_decorators = [jwt_required()]

    def get(self, lead_id):
        lead = _owned_lead_or_none(lead_id, current_user())
        if not lead:
            return {'error': 'lead not found'}, 404
        return {'lead': _lead_payload(lead)}

    def patch(self, lead_id):
        me = current_user()
        lead = _owned_lead_or_none(lead_id, me)
        if not lead:
            return {'error': 'lead not found'}, 404

        data = request.get_json(silent=True) or {}

        if me.role == 'teamMember':
            allowed_keys = {'leadCategoryId'} | EXTRA_LEAD_FIELD_KEYS
            if not set(data.keys()) <= allowed_keys:
                return {
                    'error': 'team members may only update category/registration/source/'
                    'interested-configuration fields here — status changes go through '
                    '/leads/<id>/status and follow-ups through /leads/<id>/follow-ups'
                }, 403
            if 'leadCategoryId' in data and data['leadCategoryId'] is not None:
                if not LookupLeadCategory.query.get(data['leadCategoryId']):
                    return {'error': 'invalid leadCategoryId'}, 400
                lead.leadCategoryId = data['leadCategoryId']
            extra_error = _apply_extra_lead_fields(lead, data)
            if extra_error:
                return {'error': extra_error}, 400
            lead.modifiedBy = me.recordId
        else:
            customer_data = data.get('customer') or {}
            if customer_data:
                for field in ('leadName', 'contactNumber', 'alternateNumber', 'leadLocation'):
                    if field in customer_data:
                        setattr(lead.customer, field, customer_data[field])
                lead.customer.modifiedBy = me.recordId

            if 'projectId' in data:
                if data['projectId'] is not None and not BuilderProject.query.get(data['projectId']):
                    return {'error': 'invalid projectId'}, 400
                lead.projectId = data['projectId']
            if 'assignedToUserId' in data:
                assignee_error = _validate_assignee(data['assignedToUserId'])
                if assignee_error:
                    return {'error': assignee_error}, 400
                lead.assignedToUserId = data['assignedToUserId']
            if 'leadCategoryId' in data and data['leadCategoryId'] is not None:
                if not LookupLeadCategory.query.get(data['leadCategoryId']):
                    return {'error': 'invalid leadCategoryId'}, 400
                lead.leadCategoryId = data['leadCategoryId']
            extra_error = _apply_extra_lead_fields(lead, data)
            if extra_error:
                return {'error': extra_error}, 400
            lead.modifiedBy = me.recordId

        db.session.commit()
        return {'lead': _lead_payload(lead)}

    @role_required('admin')
    def delete(self, lead_id):
        lead = CustProject.query.get(lead_id)
        if not lead:
            return {'error': 'lead not found'}, 404
        db.session.delete(lead)
        db.session.commit()
        return {}, 204


class LeadStatusTransitionResource(Resource):
    """The only way to move a lead's status by hand — status/category can no
    longer be set through the generic PATCH. Site Visit Scheduled and
    Negotiation are set automatically elsewhere (site_visit_controller);
    every transition here requires a mandatory comment, logged onto the
    lead's comment thread so the reasoning behind each change is kept."""

    method_decorators = [jwt_required()]

    def post(self, lead_id):
        me = current_user()
        lead = _owned_lead_or_none(lead_id, me)
        if not lead:
            return {'error': 'lead not found'}, 404

        data = request.get_json(silent=True) or {}
        to_status_id = data.get('toStatusId')
        comment_text = (data.get('comment') or '').strip()

        if not to_status_id:
            return {'error': 'toStatusId is required'}, 400
        if not comment_text:
            return {'error': 'a comment is required for every status change'}, 400

        to_status = LookupLeadStatus.query.get(to_status_id)
        if not to_status:
            return {'error': 'invalid toStatusId'}, 400

        from_status_name = lead.status.recordName if lead.status else None
        allowed = MANUAL_STATUS_TRANSITIONS.get(from_status_name, [])
        if to_status.recordName not in allowed:
            return {
                'error': f'cannot move a lead from "{from_status_name}" to "{to_status.recordName}"'
            }, 400

        _apply_lead_status(lead, to_status_id)
        lead.modifiedBy = me.recordId
        comment = LeadComment(
            custProjectId=lead_id,
            authorUserId=me.recordId,
            commentText=f'Status changed to {to_status.recordName}: {comment_text}',
        )
        db.session.add(comment)
        db.session.commit()
        return {'lead': _lead_payload(lead), 'comment': _comment_payload(comment)}


class LeadAssignResource(Resource):
    method_decorators = [role_required('admin')]

    def post(self):
        data = request.get_json(silent=True) or {}
        lead_ids = data.get('leadIds') or []
        user_id = data.get('userId')

        if not lead_ids or not user_id:
            return {'error': 'leadIds and userId are required'}, 400

        assignee_error = _validate_assignee(user_id)
        if assignee_error:
            return {'error': assignee_error}, 400

        leads = CustProject.query.filter(CustProject.recordId.in_(lead_ids)).all()
        for lead in leads:
            lead.assignedToUserId = user_id
            lead.modifiedBy = current_user().recordId
        db.session.commit()

        return {'updated': len(leads)}


class LeadBulkStatusResource(Resource):
    """Bulk status change over a multi-selected set of leads (e.g. every
    lead matching the current filters). Each lead's current status is
    checked against MANUAL_STATUS_TRANSITIONS individually — leads for
    which the target isn't a legal transition are skipped and reported
    rather than failing the whole batch. The mandatory comment is tagged
    "BULK UPDATE" so it's obviously distinct from a one-off note in the
    per-lead comment thread."""

    method_decorators = [role_required('admin')]

    def post(self):
        me = current_user()
        data = request.get_json(silent=True) or {}
        lead_ids = data.get('leadIds') or []
        to_status_id = data.get('toStatusId')
        comment_text = (data.get('comment') or '').strip()

        if not lead_ids:
            return {'error': 'leadIds is required'}, 400
        if not to_status_id:
            return {'error': 'toStatusId is required'}, 400
        if not comment_text:
            return {'error': 'a comment is required for every status change'}, 400

        to_status = LookupLeadStatus.query.get(to_status_id)
        if not to_status:
            return {'error': 'invalid toStatusId'}, 400

        leads = CustProject.query.filter(CustProject.recordId.in_(lead_ids)).all()
        updated = 0
        skipped = []
        for lead in leads:
            from_status_name = lead.status.recordName if lead.status else None
            allowed = MANUAL_STATUS_TRANSITIONS.get(from_status_name, [])
            if to_status.recordName not in allowed:
                skipped.append({
                    'leadId': lead.recordId,
                    'reason': f'cannot move from "{from_status_name}" to "{to_status.recordName}"',
                })
                continue

            _apply_lead_status(lead, to_status_id)
            lead.modifiedBy = me.recordId
            db.session.add(LeadComment(
                custProjectId=lead.recordId,
                authorUserId=me.recordId,
                commentText=f'BULK UPDATE: Status changed to {to_status.recordName}: {comment_text}',
            ))
            updated += 1

        db.session.commit()
        return {'updated': updated, 'skipped': skipped}


class LeadCommentListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self, lead_id):
        lead = _owned_lead_or_none(lead_id, current_user())
        if not lead:
            return {'error': 'lead not found'}, 404
        return {'items': [_comment_payload(c) for c in lead.comments]}

    def post(self, lead_id):
        me = current_user()
        if me.role != 'teamMember':
            return {'error': 'only team members can add comments'}, 403
        lead = _owned_lead_or_none(lead_id, me)
        if not lead:
            return {'error': 'lead not found'}, 404

        data = request.get_json(silent=True) or {}
        text = (data.get('commentText') or '').strip()
        if not text:
            return {'error': 'commentText is required'}, 400

        comment = LeadComment(custProjectId=lead_id, authorUserId=me.recordId, commentText=text)
        db.session.add(comment)
        db.session.commit()
        return {'comment': _comment_payload(comment)}, 201


def _follow_up_payload(f):
    return {
        'recordId': f.recordId,
        'followUpOn': f.followUpOn.isoformat() if f.followUpOn else None,
        'comment': f.comment,
        'authorUsername': f.author.username if f.author else None,
        'createdOn': f.createdOn.isoformat() if f.createdOn else None,
    }


class LeadFollowUpListResource(Resource):
    """Logs a follow-up ('retouch') on a lead. Append-only and immutable —
    each entry needs its own comment, and the full history is kept rather
    than overwriting a single next-follow-up field."""

    method_decorators = [jwt_required()]

    def get(self, lead_id):
        lead = _owned_lead_or_none(lead_id, current_user())
        if not lead:
            return {'error': 'lead not found'}, 404
        return {'items': [_follow_up_payload(f) for f in lead.followUps]}

    def post(self, lead_id):
        me = current_user()
        lead = _owned_lead_or_none(lead_id, me)
        if not lead:
            return {'error': 'lead not found'}, 404

        data = request.get_json(silent=True) or {}
        follow_up_on = data.get('followUpOn')
        comment_text = (data.get('comment') or '').strip()
        if not follow_up_on:
            return {'error': 'followUpOn is required'}, 400
        if not comment_text:
            return {'error': 'a comment is required for every follow-up'}, 400

        follow_up = LeadFollowUp(
            custProjectId=lead_id, followUpOn=follow_up_on, comment=comment_text, createdBy=me.recordId,
        )
        db.session.add(follow_up)
        lead.nextFollowUpOn = follow_up_on
        lead.modifiedBy = me.recordId
        db.session.commit()
        return {'followUp': _follow_up_payload(follow_up), 'lead': _lead_payload(lead)}, 201
