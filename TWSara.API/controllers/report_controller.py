import csv
import io

from flask import Response, request
from flask_restful import Resource

from auth import current_user, role_required
from controllers.lead_controller import _apply_lead_status
from controllers.lead_shared import get_or_create_customer
from db import db
from models import (
    BuilderPrimary,
    BuilderProject,
    CustLeadPrimary,
    CustProject,
    LookupLeadCategory,
    LookupLeadStatus,
    LookupProjectStatus,
)

IMPORT_COLUMNS = [
    'leadName',
    'contactNumber',
    'alternateNumber',
    'leadLocation',
    'builderName',
    'projectName',
    'status',
    'category',
]

EXPORT_COLUMNS = [
    'leadName',
    'contactNumber',
    'alternateNumber',
    'leadLocation',
    'builderName',
    'projectName',
    'projectStatus',
    'leadStatus',
    'leadCategory',
    'assignedTo',
    'createdOn',
]


def _get_or_create_builder(name, me_id):
    builder = BuilderPrimary.query.filter(db.func.lower(BuilderPrimary.builderName) == name.lower()).first()
    if not builder:
        builder = BuilderPrimary(builderName=name, createdBy=me_id)
        db.session.add(builder)
        db.session.flush()
    return builder


def _get_or_create_project(builder, name, me_id):
    project = BuilderProject.query.filter(
        BuilderProject.builderRecordId == builder.recordId,
        db.func.lower(BuilderProject.projectName) == name.lower(),
    ).first()
    if not project:
        default_status = LookupProjectStatus.query.order_by(LookupProjectStatus.recordId).first()
        project = BuilderProject(
            builderRecordId=builder.recordId,
            projectName=name,
            lookupProjectStatusRecordId=default_status.recordId if default_status else None,
            createdBy=me_id,
        )
        db.session.add(project)
        db.session.flush()
    return project


class LeadImportResource(Resource):
    method_decorators = [role_required('admin')]

    def post(self):
        upload = request.files.get('file')
        if not upload:
            return {'error': 'a CSV file is required (form field "file")'}, 400

        me = current_user()
        stream = io.TextIOWrapper(upload.stream, encoding='utf-8-sig')
        reader = csv.DictReader(stream)

        missing_columns = [c for c in ('leadName', 'contactNumber') if c not in (reader.fieldnames or [])]
        if missing_columns:
            return {'error': f'missing required column(s): {", ".join(missing_columns)}'}, 400

        default_status = LookupLeadStatus.query.filter_by(recordName='New').first()

        created = 0
        updated = 0
        errors = []

        for row_number, row in enumerate(reader, start=2):
            lead_name = (row.get('leadName') or '').strip()
            contact_number = (row.get('contactNumber') or '').strip()
            builder_name = (row.get('builderName') or '').strip()
            project_name = (row.get('projectName') or '').strip()

            if not lead_name or not contact_number:
                errors.append({'row': row_number, 'message': 'leadName and contactNumber are required'})
                continue
            if bool(builder_name) != bool(project_name):
                errors.append({'row': row_number, 'message': 'builderName and projectName must both be given, or both left blank'})
                continue

            status_name = (row.get('status') or '').strip()
            category_name = (row.get('category') or '').strip()
            status = LookupLeadStatus.query.filter(db.func.lower(LookupLeadStatus.recordName) == status_name.lower()).first() if status_name else None
            category = LookupLeadCategory.query.filter(db.func.lower(LookupLeadCategory.recordName) == category_name.lower()).first() if category_name else None

            customer, _ = get_or_create_customer(
                lead_name,
                contact_number,
                (row.get('alternateNumber') or '').strip(),
                (row.get('leadLocation') or '').strip(),
                me.recordId,
            )

            project = None
            if builder_name and project_name:
                builder = _get_or_create_builder(builder_name, me.recordId)
                project = _get_or_create_project(builder, project_name, me.recordId)

            lead = (
                CustProject.query.filter_by(customerId=customer.recordId, projectId=project.recordId).first()
                if project
                else None
            )
            if lead:
                if status:
                    _apply_lead_status(lead, status.recordId)
                if category:
                    lead.leadCategoryId = category.recordId
                lead.modifiedBy = me.recordId
                updated += 1
            else:
                lead = CustProject(
                    customerId=customer.recordId,
                    projectId=project.recordId if project else None,
                    leadCategoryId=category.recordId if category else None,
                    createdBy=me.recordId,
                )
                _apply_lead_status(lead, status.recordId if status else (default_status.recordId if default_status else None))
                db.session.add(lead)
                created += 1

        db.session.commit()
        return {'created': created, 'updated': updated, 'errors': errors}


class LeadExportResource(Resource):
    method_decorators = [role_required('admin')]

    def get(self):
        query = (
            CustProject.query.join(CustLeadPrimary)
            .outerjoin(BuilderProject)
            .outerjoin(BuilderPrimary)
        )
        if request.args.get('status'):
            query = query.filter(CustProject.leadStatusId == int(request.args['status']))
        if request.args.get('category'):
            query = query.filter(CustProject.leadCategoryId == int(request.args['category']))
        if request.args.get('builderId'):
            query = query.filter(BuilderProject.builderRecordId == int(request.args['builderId']))
        if request.args.get('projectId'):
            query = query.filter(CustProject.projectId == int(request.args['projectId']))
        if request.args.get('assignedToUserId'):
            query = query.filter(CustProject.assignedToUserId == int(request.args['assignedToUserId']))

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(EXPORT_COLUMNS)
        for lead in query.order_by(CustProject.createdOn.desc()).all():
            writer.writerow([
                lead.customer.leadName,
                lead.customer.contactNumber,
                lead.customer.alternateNumber or '',
                lead.customer.leadLocation or '',
                lead.project.builder.builderName if lead.project else '',
                lead.project.projectName if lead.project else '',
                lead.project.status.recordName if lead.project and lead.project.status else '',
                lead.status.recordName if lead.status else '',
                lead.category.recordName if lead.category else '',
                lead.assignedTo.username if lead.assignedTo else '',
                lead.createdOn.isoformat() if lead.createdOn else '',
            ])

        return Response(
            buffer.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=leads_export.csv'},
        )
