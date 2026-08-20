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


def _apply_registration(lead, is_registered, explicit_expiry='__unset__'):
    """Set isCustLeadRegistered, stamping registeredOn the first time it flips
    true and defaulting registrationExpiryDate from the builder's configured
    validity window unless an explicit expiry was given."""
    was_registered = lead.isCustLeadRegistered
    lead.isCustLeadRegistered = is_registered

    if explicit_expiry != '__unset__':
        lead.registrationExpiryDate = explicit_expiry or None

    if is_registered and not was_registered:
        lead.registeredOn = utcnow()
        if explicit_expiry == '__unset__' and lead.project and lead.project.builder:
            validity_days = lead.project.builder.leadRegistrationValidityDays
            if validity_days:
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
    'registrationExpiryDate',
    'leadSourceId',
    'leadSourceDetail',
    'nextFollowUpOn',
    'interestedConfigId',
}


def _apply_extra_lead_fields(lead, data):
    """Applies the fields both team members and admins may edit on a lead:
    registration, lead source, next follow-up, interested configuration.
    Returns an error string, or None on success."""
    if 'leadSourceId' in data:
        if data['leadSourceId'] is not None and not LookupLeadSource.query.get(data['leadSourceId']):
            return 'invalid leadSourceId'
        lead.leadSourceId = data['leadSourceId']
    if 'leadSourceDetail' in data:
        lead.leadSourceDetail = (data.get('leadSourceDetail') or '').strip() or None
    if 'nextFollowUpOn' in data:
        lead.nextFollowUpOn = data['nextFollowUpOn'] or None
    if 'interestedConfigId' in data:
        config_id = data['interestedConfigId']
        if config_id is not None and not ProjectUnitConfiguration.query.get(config_id):
            return 'invalid interestedConfigId'
        lead.interestedConfigId = config_id or None
    if 'isCustLeadRegistered' in data or 'registrationExpiryDate' in data:
        is_registered = (
            bool(data['isCustLeadRegistered'])
            if 'isCustLeadRegistered' in data
            else lead.isCustLeadRegistered
        )
        explicit_expiry = data['registrationExpiryDate'] if 'registrationExpiryDate' in data else '__unset__'
        _apply_registration(lead, is_registered, explicit_expiry)
    return None


class LeadListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        me = current_user()
        query = (
            CustProject.query.join(CustLeadPrimary)
            .outerjoin(BuilderProject)
            .outerjoin(LookupLeadStatus)
            .outerjoin(LookupLeadCategory)
        )

        if me.role == 'teamMember':
            query = query.filter(CustProject.assignedToUserId == me.recordId)
        elif request.args.get('assignedToUserId'):
            query = query.filter(CustProject.assignedToUserId == int(request.args['assignedToUserId']))

        if request.args.get('status'):
            query = query.filter(CustProject.leadStatusId == int(request.args['status']))
        if request.args.get('category'):
            query = query.filter(CustProject.leadCategoryId == int(request.args['category']))
        if request.args.get('builderId'):
            query = query.filter(BuilderProject.builderRecordId == int(request.args['builderId']))
        if request.args.get('projectId'):
            query = query.filter(CustProject.projectId == int(request.args['projectId']))
        if request.args.get('leadSourceId'):
            query = query.filter(CustProject.leadSourceId == int(request.args['leadSourceId']))
        if request.args.get('followUpDue', '').lower() == 'true':
            query = query.filter(
                CustProject.nextFollowUpOn.isnot(None), CustProject.nextFollowUpOn <= utcnow()
            )
        if request.args.get('search'):
            like = f"%{request.args['search']}%"
            query = query.filter(
                db.or_(
                    CustLeadPrimary.leadName.ilike(like),
                    CustLeadPrimary.contactNumber.ilike(like),
                    CustLeadPrimary.leadLocation.ilike(like),
                )
            )

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
        project_id = data.get('projectId')
        if project_id and not BuilderProject.query.get(project_id):
            return {'error': 'invalid projectId'}, 400

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

        lead = CustProject(
            customerId=customer.recordId,
            projectId=project_id,
            assignedToUserId=data.get('assignedToUserId'),
            leadCategoryId=data.get('leadCategoryId'),
            createdBy=current_user().recordId,
        )
        _apply_lead_status(lead, status_id)
        extra_error = _apply_extra_lead_fields(lead, data)
        if extra_error:
            return {'error': extra_error}, 400
        db.session.add(lead)
        db.session.commit()
        return {'lead': _lead_payload(lead), 'customerReused': customer_reused}, 201


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
            allowed_keys = {'leadStatusId', 'leadCategoryId'} | EXTRA_LEAD_FIELD_KEYS
            if not set(data.keys()) <= allowed_keys:
                return {
                    'error': 'team members may only update status/category/registration/'
                    'source/follow-up/interested-configuration fields'
                }, 403
            if 'leadStatusId' in data and data['leadStatusId'] is not None:
                if not LookupLeadStatus.query.get(data['leadStatusId']):
                    return {'error': 'invalid leadStatusId'}, 400
                _apply_lead_status(lead, data['leadStatusId'])
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
            if 'leadStatusId' in data and data['leadStatusId'] is not None:
                if not LookupLeadStatus.query.get(data['leadStatusId']):
                    return {'error': 'invalid leadStatusId'}, 400
                _apply_lead_status(lead, data['leadStatusId'])
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
