from flask_jwt_extended import jwt_required
from flask_restful import Resource

from models import LookupLeadCategory, LookupLeadStatus, LookupProjectStatus


def _options(model):
    rows = model.query.order_by(model.recordId).all()
    return [{'recordId': r.recordId, 'recordName': r.recordName} for r in rows]


class ProjectStatusListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        return {'items': _options(LookupProjectStatus)}


class LeadStatusListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        return {'items': _options(LookupLeadStatus)}


class LeadCategoryListResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        return {'items': _options(LookupLeadCategory)}
