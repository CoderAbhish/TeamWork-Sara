from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from auth import current_user, role_required
from db import db
from models import BuilderPrimary, BuilderProject, LookupProjectStatus


def _builder_payload(builder):
    return {
        'recordId': builder.recordId,
        'builderName': builder.builderName,
        'isActive': builder.isActive,
        'projectCount': len(builder.projects),
        'createdOn': builder.createdOn.isoformat() if builder.createdOn else None,
    }


def _project_payload(project):
    return {
        'recordId': project.recordId,
        'builderRecordId': project.builderRecordId,
        'projectName': project.projectName,
        'lookupProjectStatusRecordId': project.lookupProjectStatusRecordId,
        'statusName': project.status.recordName if project.status else None,
        'startDate': project.startDate.isoformat() if project.startDate else None,
        'plannedCompletionDate': (
            project.plannedCompletionDate.isoformat() if project.plannedCompletionDate else None
        ),
        'actualCompletionDate': (
            project.actualCompletionDate.isoformat() if project.actualCompletionDate else None
        ),
    }


class BuilderListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        query = BuilderPrimary.query
        if request.args.get('includeInactive', '').lower() != 'true':
            query = query.filter_by(isActive=True)
        builders = query.order_by(BuilderPrimary.builderName).all()
        return {'items': [_builder_payload(b) for b in builders]}

    @role_required('admin')
    def post(self):
        data = request.get_json(silent=True) or {}
        builder_name = (data.get('builderName') or '').strip()
        if not builder_name:
            return {'error': 'builderName is required'}, 400

        builder = BuilderPrimary(builderName=builder_name, createdBy=current_user().recordId)
        db.session.add(builder)
        db.session.commit()
        return {'builder': _builder_payload(builder)}, 201


class BuilderResource(Resource):
    method_decorators = [jwt_required()]

    def get(self, builder_id):
        builder = BuilderPrimary.query.get(builder_id)
        if not builder:
            return {'error': 'builder not found'}, 404
        return {'builder': _builder_payload(builder)}

    @role_required('admin')
    def patch(self, builder_id):
        builder = BuilderPrimary.query.get(builder_id)
        if not builder:
            return {'error': 'builder not found'}, 404

        data = request.get_json(silent=True) or {}
        if 'builderName' in data:
            builder_name = (data.get('builderName') or '').strip()
            if not builder_name:
                return {'error': 'builderName cannot be empty'}, 400
            builder.builderName = builder_name
        if 'isActive' in data:
            builder.isActive = bool(data['isActive'])
        builder.modifiedBy = current_user().recordId

        db.session.commit()
        return {'builder': _builder_payload(builder)}


class BuilderProjectListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self, builder_id):
        builder = BuilderPrimary.query.get(builder_id)
        if not builder:
            return {'error': 'builder not found'}, 404
        projects = (
            BuilderProject.query.filter_by(builderRecordId=builder_id)
            .order_by(BuilderProject.recordId)
            .all()
        )
        return {'items': [_project_payload(p) for p in projects]}

    @role_required('admin')
    def post(self, builder_id):
        builder = BuilderPrimary.query.get(builder_id)
        if not builder:
            return {'error': 'builder not found'}, 404

        data = request.get_json(silent=True) or {}
        project_name = (data.get('projectName') or '').strip()
        if not project_name:
            return {'error': 'projectName is required'}, 400
        status_id = data.get('lookupProjectStatusRecordId')
        if not status_id or not LookupProjectStatus.query.get(status_id):
            return {'error': 'a valid lookupProjectStatusRecordId is required'}, 400

        project = BuilderProject(
            builderRecordId=builder_id,
            projectName=project_name,
            lookupProjectStatusRecordId=status_id,
            startDate=data.get('startDate') or None,
            plannedCompletionDate=data.get('plannedCompletionDate') or None,
            createdBy=current_user().recordId,
        )
        db.session.add(project)
        db.session.commit()
        return {'project': _project_payload(project)}, 201


class ProjectResource(Resource):
    method_decorators = [jwt_required()]

    def get(self, project_id):
        project = BuilderProject.query.get(project_id)
        if not project:
            return {'error': 'project not found'}, 404
        return {'project': _project_payload(project)}

    @role_required('admin')
    def patch(self, project_id):
        project = BuilderProject.query.get(project_id)
        if not project:
            return {'error': 'project not found'}, 404

        data = request.get_json(silent=True) or {}
        if 'projectName' in data:
            project_name = (data.get('projectName') or '').strip()
            if not project_name:
                return {'error': 'projectName cannot be empty'}, 400
            project.projectName = project_name
        if 'lookupProjectStatusRecordId' in data:
            if not LookupProjectStatus.query.get(data['lookupProjectStatusRecordId']):
                return {'error': 'invalid lookupProjectStatusRecordId'}, 400
            project.lookupProjectStatusRecordId = data['lookupProjectStatusRecordId']
        for field in ('startDate', 'plannedCompletionDate', 'actualCompletionDate'):
            if field in data:
                setattr(project, field, data[field] or None)
        project.modifiedBy = current_user().recordId

        db.session.commit()
        return {'project': _project_payload(project)}
