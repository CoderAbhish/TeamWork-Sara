from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from auth import current_user, role_required
from db import db
from models import (
    BuilderPrimary,
    BuilderProject,
    CustProject,
    LookupListingType,
    LookupProjectStatus,
    LookupPropertyType,
    LookupSaleType,
    ProjectManager,
    ProjectUnitConfiguration,
)


def _builder_payload(builder):
    return {
        'recordId': builder.recordId,
        'builderName': builder.builderName,
        'isActive': builder.isActive,
        'leadRegistrationValidityDays': builder.leadRegistrationValidityDays,
        'projectCount': len(builder.projects),
        'createdOn': builder.createdOn.isoformat() if builder.createdOn else None,
    }


def _manager_payload(manager):
    return {
        'recordId': manager.recordId,
        'projectId': manager.projectId,
        'managerName': manager.managerName,
        'contactNumber': manager.contactNumber,
        'emailId': manager.emailId,
        'notes': manager.notes,
        'isActive': manager.isActive,
    }


def _configuration_payload(config):
    return {
        'recordId': config.recordId,
        'projectId': config.projectId,
        'configurationLabel': config.configurationLabel,
        'sizeSqFt': float(config.sizeSqFt) if config.sizeSqFt is not None else None,
        'plotDimensionSqFt': float(config.plotDimensionSqFt) if config.plotDimensionSqFt is not None else None,
        'startingPriceAmount': float(config.startingPriceAmount) if config.startingPriceAmount is not None else None,
        'baseRatePerSqFt': float(config.baseRatePerSqFt) if config.baseRatePerSqFt is not None else None,
        'notes': config.notes,
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
        'location': project.location,
        'propertyTypeId': project.propertyTypeId,
        'propertyTypeName': project.propertyType.recordName if project.propertyType else None,
        'saleTypeId': project.saleTypeId,
        'saleTypeName': project.saleType.recordName if project.saleType else None,
        'listingTypeId': project.listingTypeId,
        'listingTypeName': project.listingType.recordName if project.listingType else None,
        'areaExtent': project.areaExtent,
        'structureDescription': project.structureDescription,
        'numberOfTowers': project.numberOfTowers,
        'totalUnits': project.totalUnits,
        'reraNumber': project.reraNumber,
        'approvalAuthority': project.approvalAuthority,
        'possessionDate': project.possessionDate.isoformat() if project.possessionDate else None,
        'managers': [_manager_payload(m) for m in project.managers if m.isActive],
        'configurations': [_configuration_payload(c) for c in project.configurations],
    }


_PROJECT_DETAIL_FIELDS = (
    'areaExtent',
    'structureDescription',
    'reraNumber',
    'approvalAuthority',
)
_PROJECT_DETAIL_INT_FIELDS = ('numberOfTowers', 'totalUnits')
_PROJECT_DETAIL_DATE_FIELDS = ('possessionDate',)
_PROJECT_DETAIL_LOOKUP_FIELDS = {
    'propertyTypeId': LookupPropertyType,
    'saleTypeId': LookupSaleType,
    'listingTypeId': LookupListingType,
}


def _apply_project_detail_fields(project, data):
    """Applies the optional property-detail fields shared by create/update."""
    for field in _PROJECT_DETAIL_FIELDS:
        if field in data:
            value = (data.get(field) or '').strip() if isinstance(data.get(field), str) else data.get(field)
            setattr(project, field, value or None)
    for field in _PROJECT_DETAIL_INT_FIELDS:
        if field in data:
            setattr(project, field, data[field] if data[field] not in ('', None) else None)
    for field in _PROJECT_DETAIL_DATE_FIELDS:
        if field in data:
            setattr(project, field, data[field] or None)
    for field, lookup_model in _PROJECT_DETAIL_LOOKUP_FIELDS.items():
        if field in data:
            value = data[field]
            if value and not lookup_model.query.get(value):
                return f'invalid {field}'
            setattr(project, field, value or None)
    return None


def _team_member_has_project(user_id, project_id):
    return (
        CustProject.query.filter_by(projectId=project_id, assignedToUserId=user_id).first()
        is not None
    )


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
        if 'leadRegistrationValidityDays' in data:
            value = data['leadRegistrationValidityDays']
            builder.leadRegistrationValidityDays = int(value) if value not in ('', None) else None
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
        location = (data.get('location') or '').strip()
        if not location:
            return {'error': 'location is required'}, 400
        status_id = data.get('lookupProjectStatusRecordId')
        if not status_id or not LookupProjectStatus.query.get(status_id):
            return {'error': 'a valid lookupProjectStatusRecordId is required'}, 400

        project = BuilderProject(
            builderRecordId=builder_id,
            projectName=project_name,
            location=location,
            lookupProjectStatusRecordId=status_id,
            startDate=data.get('startDate') or None,
            plannedCompletionDate=data.get('plannedCompletionDate') or None,
            createdBy=current_user().recordId,
        )
        detail_error = _apply_project_detail_fields(project, data)
        if detail_error:
            return {'error': detail_error}, 400
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
        if 'location' in data:
            location = (data.get('location') or '').strip()
            if not location:
                return {'error': 'location cannot be empty'}, 400
            project.location = location
        for field in ('startDate', 'plannedCompletionDate', 'actualCompletionDate'):
            if field in data:
                setattr(project, field, data[field] or None)
        detail_error = _apply_project_detail_fields(project, data)
        if detail_error:
            return {'error': detail_error}, 400
        project.modifiedBy = current_user().recordId

        db.session.commit()
        return {'project': _project_payload(project)}


def _project_or_404(project_id):
    return BuilderProject.query.get(project_id)


class ProjectManagerListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self, project_id):
        project = _project_or_404(project_id)
        if not project:
            return {'error': 'project not found'}, 404
        return {'items': [_manager_payload(m) for m in project.managers if m.isActive]}

    def post(self, project_id):
        me = current_user()
        project = _project_or_404(project_id)
        if not project:
            return {'error': 'project not found'}, 404
        if me.role != 'admin' and not _team_member_has_project(me.recordId, project_id):
            return {'error': 'forbidden'}, 403

        data = request.get_json(silent=True) or {}
        manager_name = (data.get('managerName') or '').strip()
        contact_number = (data.get('contactNumber') or '').strip()
        if not manager_name or not contact_number:
            return {'error': 'managerName and contactNumber are required'}, 400

        manager = ProjectManager(
            projectId=project_id,
            managerName=manager_name,
            contactNumber=contact_number,
            emailId=(data.get('emailId') or '').strip() or None,
            notes=(data.get('notes') or '').strip() or None,
            createdBy=me.recordId,
        )
        db.session.add(manager)
        db.session.commit()
        return {'manager': _manager_payload(manager)}, 201


class ProjectManagerResource(Resource):
    method_decorators = [jwt_required()]

    def _owned_or_none(self, manager_id, me):
        manager = ProjectManager.query.get(manager_id)
        if not manager:
            return None
        if me.role != 'admin' and not _team_member_has_project(me.recordId, manager.projectId):
            return None
        return manager

    def patch(self, manager_id):
        me = current_user()
        manager = self._owned_or_none(manager_id, me)
        if not manager:
            return {'error': 'manager not found'}, 404

        data = request.get_json(silent=True) or {}
        if 'managerName' in data:
            manager_name = (data.get('managerName') or '').strip()
            if not manager_name:
                return {'error': 'managerName cannot be empty'}, 400
            manager.managerName = manager_name
        if 'contactNumber' in data:
            contact_number = (data.get('contactNumber') or '').strip()
            if not contact_number:
                return {'error': 'contactNumber cannot be empty'}, 400
            manager.contactNumber = contact_number
        if 'emailId' in data:
            manager.emailId = (data.get('emailId') or '').strip() or None
        if 'notes' in data:
            manager.notes = (data.get('notes') or '').strip() or None
        if 'isActive' in data:
            manager.isActive = bool(data['isActive'])
        manager.modifiedBy = me.recordId

        db.session.commit()
        return {'manager': _manager_payload(manager)}

    def delete(self, manager_id):
        me = current_user()
        manager = self._owned_or_none(manager_id, me)
        if not manager:
            return {'error': 'manager not found'}, 404
        db.session.delete(manager)
        db.session.commit()
        return {}, 204


class ProjectConfigurationListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self, project_id):
        project = _project_or_404(project_id)
        if not project:
            return {'error': 'project not found'}, 404
        return {'items': [_configuration_payload(c) for c in project.configurations]}

    @role_required('admin')
    def post(self, project_id):
        project = _project_or_404(project_id)
        if not project:
            return {'error': 'project not found'}, 404

        data = request.get_json(silent=True) or {}
        label = (data.get('configurationLabel') or '').strip()
        if not label:
            return {'error': 'configurationLabel is required'}, 400

        config = ProjectUnitConfiguration(
            projectId=project_id,
            configurationLabel=label,
            sizeSqFt=data.get('sizeSqFt') or None,
            plotDimensionSqFt=data.get('plotDimensionSqFt') or None,
            startingPriceAmount=data.get('startingPriceAmount') or None,
            baseRatePerSqFt=data.get('baseRatePerSqFt') or None,
            notes=(data.get('notes') or '').strip() or None,
            createdBy=current_user().recordId,
        )
        db.session.add(config)
        db.session.commit()
        return {'configuration': _configuration_payload(config)}, 201


class ProjectConfigurationResource(Resource):
    method_decorators = [role_required('admin')]

    def patch(self, config_id):
        config = ProjectUnitConfiguration.query.get(config_id)
        if not config:
            return {'error': 'configuration not found'}, 404

        data = request.get_json(silent=True) or {}
        if 'configurationLabel' in data:
            label = (data.get('configurationLabel') or '').strip()
            if not label:
                return {'error': 'configurationLabel cannot be empty'}, 400
            config.configurationLabel = label
        for field in ('sizeSqFt', 'plotDimensionSqFt', 'startingPriceAmount', 'baseRatePerSqFt'):
            if field in data:
                setattr(config, field, data[field] if data[field] not in ('', None) else None)
        if 'notes' in data:
            config.notes = (data.get('notes') or '').strip() or None
        config.modifiedBy = current_user().recordId

        db.session.commit()
        return {'configuration': _configuration_payload(config)}

    def delete(self, config_id):
        config = ProjectUnitConfiguration.query.get(config_id)
        if not config:
            return {'error': 'configuration not found'}, 404
        db.session.delete(config)
        db.session.commit()
        return {}, 204
