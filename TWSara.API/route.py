"""The API's URL map.

Every route the API exposes is registered here, in one place — the actual
request handling lives in controllers/.
"""

from flask_restful import Api

from controllers.analytics_controller import (
    ConvertedOverTimeResource,
    HotLeadsResource,
    LeadsByCategoryResource,
)
from controllers.auth_controller import LoginResource, MeResource, RegisterResource
from controllers.builder_controller import (
    BuilderListResource,
    BuilderProjectListResource,
    BuilderResource,
    ProjectResource,
)
from controllers.lead_controller import (
    LeadAssignResource,
    LeadCommentListResource,
    LeadListResource,
    LeadResource,
)
from controllers.lead_suggestion_controller import (
    LeadSuggestionApproveResource,
    LeadSuggestionImportResource,
    LeadSuggestionListResource,
    LeadSuggestionRejectResource,
)
from controllers.lookup_controller import (
    LeadCategoryListResource,
    LeadStatusListResource,
    ProjectStatusListResource,
)
from controllers.misc_controller import HomeResource, PublicStatsResource
from controllers.report_controller import LeadExportResource, LeadImportResource
from controllers.team_controller import (
    TeamMemberLeadsResource,
    TeamMemberListResource,
    TeamMemberResource,
)


def register_routes(app):
    api = Api(app)

    api.add_resource(HomeResource, '/')
    api.add_resource(PublicStatsResource, '/api/public/stats')

    api.add_resource(LoginResource, '/api/auth/login')
    api.add_resource(RegisterResource, '/api/auth/register')
    api.add_resource(MeResource, '/api/auth/me')

    api.add_resource(ProjectStatusListResource, '/api/lookups/project-statuses')
    api.add_resource(LeadStatusListResource, '/api/lookups/lead-statuses')
    api.add_resource(LeadCategoryListResource, '/api/lookups/lead-categories')

    api.add_resource(BuilderListResource, '/api/builders')
    api.add_resource(BuilderResource, '/api/builders/<int:builder_id>')
    api.add_resource(BuilderProjectListResource, '/api/builders/<int:builder_id>/projects')
    api.add_resource(ProjectResource, '/api/projects/<int:project_id>')

    api.add_resource(LeadListResource, '/api/leads')
    api.add_resource(LeadResource, '/api/leads/<int:lead_id>')
    api.add_resource(LeadAssignResource, '/api/leads/assign')
    api.add_resource(LeadCommentListResource, '/api/leads/<int:lead_id>/comments')
    api.add_resource(LeadImportResource, '/api/leads/import')
    api.add_resource(LeadExportResource, '/api/leads/export')

    api.add_resource(LeadSuggestionListResource, '/api/lead-suggestions')
    api.add_resource(LeadSuggestionApproveResource, '/api/lead-suggestions/<int:suggestion_id>/approve')
    api.add_resource(LeadSuggestionRejectResource, '/api/lead-suggestions/<int:suggestion_id>/reject')
    api.add_resource(LeadSuggestionImportResource, '/api/lead-suggestions/import')

    api.add_resource(ConvertedOverTimeResource, '/api/analytics/converted-over-time')
    api.add_resource(LeadsByCategoryResource, '/api/analytics/leads-by-category')
    api.add_resource(HotLeadsResource, '/api/analytics/hot-leads')

    api.add_resource(TeamMemberListResource, '/api/team-members')
    api.add_resource(TeamMemberResource, '/api/team-members/<int:user_id>')
    api.add_resource(TeamMemberLeadsResource, '/api/team-members/<int:user_id>/leads')

    return api
