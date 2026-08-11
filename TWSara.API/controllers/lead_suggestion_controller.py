import csv
import io

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from auth import current_user, role_required
from controllers.lead_controller import _apply_lead_status, _lead_payload
from controllers.lead_shared import get_or_create_customer
from db import db
from models import (
    BuilderPrimary,
    BuilderProject,
    CustProject,
    LeadSuggestion,
    LookupLeadStatus,
    utcnow,
)


def _suggestion_payload(s):
    return {
        'recordId': s.recordId,
        'leadName': s.leadName,
        'contactNumber': s.contactNumber,
        'alternateNumber': s.alternateNumber,
        'leadLocation': s.leadLocation,
        'builderId': s.builderId,
        'builderName': s.builder.builderName if s.builder else None,
        'projectId': s.projectId,
        'projectName': s.project.projectName if s.project else None,
        'status': s.status,
        'suggestedByUserId': s.suggestedByUserId,
        'suggestedByUsername': s.suggestedBy.username if s.suggestedBy else None,
        'createdOn': s.createdOn.isoformat() if s.createdOn else None,
        'reviewedOn': s.reviewedOn.isoformat() if s.reviewedOn else None,
        'resultingLeadId': s.resultingLeadId,
    }


class LeadSuggestionListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        me = current_user()
        query = LeadSuggestion.query
        if me.role == 'teamMember':
            query = query.filter_by(suggestedByUserId=me.recordId)
        elif request.args.get('status'):
            query = query.filter_by(status=request.args['status'])

        items = query.order_by(LeadSuggestion.createdOn.desc()).all()
        return {'items': [_suggestion_payload(s) for s in items]}

    def post(self):
        me = current_user()
        if me.role != 'teamMember':
            return {'error': 'only team members can suggest leads'}, 403

        data = request.get_json(silent=True) or {}
        lead_name = (data.get('leadName') or '').strip()
        contact_number = (data.get('contactNumber') or '').strip()
        if not lead_name or not contact_number:
            return {'error': 'leadName and contactNumber are required'}, 400

        project_id = data.get('projectId')
        if project_id and not BuilderProject.query.get(project_id):
            return {'error': 'invalid projectId'}, 400
        builder_id = data.get('builderId')
        if builder_id and not BuilderPrimary.query.get(builder_id):
            return {'error': 'invalid builderId'}, 400

        suggestion = LeadSuggestion(
            leadName=lead_name,
            contactNumber=contact_number,
            alternateNumber=(data.get('alternateNumber') or '').strip() or None,
            leadLocation=(data.get('leadLocation') or '').strip() or None,
            builderId=builder_id,
            projectId=project_id,
            suggestedByUserId=me.recordId,
        )
        db.session.add(suggestion)
        db.session.commit()
        return {'suggestion': _suggestion_payload(suggestion)}, 201


class LeadSuggestionApproveResource(Resource):
    method_decorators = [role_required('admin')]

    def post(self, suggestion_id):
        suggestion = LeadSuggestion.query.get(suggestion_id)
        if not suggestion:
            return {'error': 'suggestion not found'}, 404
        if suggestion.status != 'pending':
            return {'error': f'suggestion already {suggestion.status}'}, 409

        data = request.get_json(silent=True) or {}
        project_id = data.get('projectId', suggestion.projectId)
        if project_id and not BuilderProject.query.get(project_id):
            return {'error': 'invalid projectId'}, 400

        me = current_user()
        customer, _ = get_or_create_customer(
            suggestion.leadName,
            suggestion.contactNumber,
            suggestion.alternateNumber,
            suggestion.leadLocation,
            me.recordId,
        )

        default_status = LookupLeadStatus.query.filter_by(recordName='New').first()
        lead = CustProject(
            customerId=customer.recordId,
            projectId=project_id,
            assignedToUserId=suggestion.suggestedByUserId,
            createdBy=me.recordId,
        )
        _apply_lead_status(lead, default_status.recordId if default_status else None)
        db.session.add(lead)
        db.session.flush()

        suggestion.status = 'approved'
        suggestion.reviewedByUserId = me.recordId
        suggestion.reviewedOn = utcnow()
        suggestion.resultingLeadId = lead.recordId
        db.session.commit()

        return {'suggestion': _suggestion_payload(suggestion), 'lead': _lead_payload(lead)}


class LeadSuggestionRejectResource(Resource):
    method_decorators = [role_required('admin')]

    def post(self, suggestion_id):
        suggestion = LeadSuggestion.query.get(suggestion_id)
        if not suggestion:
            return {'error': 'suggestion not found'}, 404
        if suggestion.status != 'pending':
            return {'error': f'suggestion already {suggestion.status}'}, 409

        me = current_user()
        suggestion.status = 'rejected'
        suggestion.reviewedByUserId = me.recordId
        suggestion.reviewedOn = utcnow()
        db.session.commit()
        return {'suggestion': _suggestion_payload(suggestion)}


class LeadSuggestionImportResource(Resource):
    method_decorators = [jwt_required()]

    def post(self):
        me = current_user()
        if me.role != 'teamMember':
            return {'error': 'only team members can suggest leads'}, 403

        upload = request.files.get('file')
        if not upload:
            return {'error': 'a CSV file is required (form field "file")'}, 400

        stream = io.TextIOWrapper(upload.stream, encoding='utf-8-sig')
        reader = csv.DictReader(stream)
        missing_columns = [c for c in ('leadName', 'contactNumber') if c not in (reader.fieldnames or [])]
        if missing_columns:
            return {'error': f'missing required column(s): {", ".join(missing_columns)}'}, 400

        created = 0
        errors = []
        for row_number, row in enumerate(reader, start=2):
            lead_name = (row.get('leadName') or '').strip()
            contact_number = (row.get('contactNumber') or '').strip()
            if not lead_name or not contact_number:
                errors.append({'row': row_number, 'message': 'leadName and contactNumber are required'})
                continue

            builder_name = (row.get('builderName') or '').strip()
            project_name = (row.get('projectName') or '').strip()
            builder = (
                BuilderPrimary.query.filter(db.func.lower(BuilderPrimary.builderName) == builder_name.lower()).first()
                if builder_name
                else None
            )
            project = (
                BuilderProject.query.filter(
                    BuilderProject.builderRecordId == builder.recordId,
                    db.func.lower(BuilderProject.projectName) == project_name.lower(),
                ).first()
                if builder and project_name
                else None
            )

            db.session.add(
                LeadSuggestion(
                    leadName=lead_name,
                    contactNumber=contact_number,
                    alternateNumber=(row.get('alternateNumber') or '').strip() or None,
                    leadLocation=(row.get('leadLocation') or '').strip() or None,
                    builderId=builder.recordId if builder else None,
                    projectId=project.recordId if project else None,
                    suggestedByUserId=me.recordId,
                )
            )
            created += 1

        db.session.commit()
        return {'created': created, 'errors': errors}
