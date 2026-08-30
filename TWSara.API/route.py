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
    ProjectConfigurationListResource,
    ProjectConfigurationResource,
    ProjectManagerListResource,
    ProjectManagerResource,
    ProjectResource,
    ProjectSearchResource,
)
from controllers.lead_controller import (
    LeadAssignResource,
    LeadBulkStatusResource,
    LeadCommentListResource,
    LeadFollowUpListResource,
    LeadListResource,
    LeadResource,
    LeadStatusTransitionResource,
)
from controllers.lead_suggestion_controller import (
    LeadSuggestionApproveResource,
    LeadSuggestionImportResource,
    LeadSuggestionListResource,
    LeadSuggestionRejectResource,
)
from controllers.lead_transfer_controller import (
    LeadTransferApproveResource,
    LeadTransferRejectResource,
    LeadTransferRequestListResource,
)
from controllers.lookup_controller import (
    LeadCategoryListResource,
    LeadSourceListResource,
    LeadStatusListResource,
    ListingTypeListResource,
    ProjectStatusListResource,
    PropertyTypeListResource,
    SaleTypeListResource,
)
from controllers.misc_controller import HomeResource, PublicStatsResource
from controllers.notification_controller import NotificationDismissResource, NotificationListResource
from controllers.report_controller import LeadExportResource, LeadImportResource
from controllers.site_visit_controller import (
    SiteVisitListResource,
    SiteVisitRescheduleResource,
    SiteVisitResource,
)
from controllers.team_controller import (
    TeamMemberLeadsResource,
    TeamMemberListResource,
    TeamMemberOptionsResource,
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
    api.add_resource(PropertyTypeListResource, '/api/lookups/property-types')
    api.add_resource(SaleTypeListResource, '/api/lookups/sale-types')
    api.add_resource(ListingTypeListResource, '/api/lookups/listing-types')
    api.add_resource(LeadSourceListResource, '/api/lookups/lead-sources')

    api.add_resource(BuilderListResource, '/api/builders')
    api.add_resource(BuilderResource, '/api/builders/<int:builder_id>')
    api.add_resource(BuilderProjectListResource, '/api/builders/<int:builder_id>/projects')
    api.add_resource(ProjectSearchResource, '/api/projects/search')
    api.add_resource(ProjectResource, '/api/projects/<int:project_id>')
    api.add_resource(ProjectManagerListResource, '/api/projects/<int:project_id>/managers')
    api.add_resource(ProjectManagerResource, '/api/project-managers/<int:manager_id>')
    api.add_resource(ProjectConfigurationListResource, '/api/projects/<int:project_id>/configurations')
    api.add_resource(ProjectConfigurationResource, '/api/project-configurations/<int:config_id>')

    api.add_resource(LeadListResource, '/api/leads')
    api.add_resource(LeadResource, '/api/leads/<int:lead_id>')
    api.add_resource(LeadAssignResource, '/api/leads/assign')
    api.add_resource(LeadBulkStatusResource, '/api/leads/bulk-status')
    api.add_resource(LeadStatusTransitionResource, '/api/leads/<int:lead_id>/status')
    api.add_resource(LeadCommentListResource, '/api/leads/<int:lead_id>/comments')
    api.add_resource(LeadFollowUpListResource, '/api/leads/<int:lead_id>/follow-ups')
    api.add_resource(LeadImportResource, '/api/leads/import')
    api.add_resource(LeadExportResource, '/api/leads/export')
    api.add_resource(SiteVisitListResource, '/api/leads/<int:lead_id>/site-visits')
    api.add_resource(SiteVisitResource, '/api/site-visits/<int:visit_id>')
    api.add_resource(SiteVisitRescheduleResource, '/api/site-visits/<int:visit_id>/reschedule')

    api.add_resource(LeadSuggestionListResource, '/api/lead-suggestions')
    api.add_resource(LeadSuggestionApproveResource, '/api/lead-suggestions/<int:suggestion_id>/approve')
    api.add_resource(LeadSuggestionRejectResource, '/api/lead-suggestions/<int:suggestion_id>/reject')
    api.add_resource(LeadSuggestionImportResource, '/api/lead-suggestions/import')

    api.add_resource(LeadTransferRequestListResource, '/api/lead-transfer-requests')
    api.add_resource(LeadTransferApproveResource, '/api/lead-transfer-requests/<int:transfer_id>/approve')
    api.add_resource(LeadTransferRejectResource, '/api/lead-transfer-requests/<int:transfer_id>/reject')

    api.add_resource(ConvertedOverTimeResource, '/api/analytics/converted-over-time')
    api.add_resource(LeadsByCategoryResource, '/api/analytics/leads-by-category')
    api.add_resource(HotLeadsResource, '/api/analytics/hot-leads')

    api.add_resource(NotificationListResource, '/api/notifications')
    api.add_resource(NotificationDismissResource, '/api/notifications/dismiss')

    api.add_resource(TeamMemberOptionsResource, '/api/team-members/options')
    api.add_resource(TeamMemberListResource, '/api/team-members')
    api.add_resource(TeamMemberResource, '/api/team-members/<int:user_id>')
    api.add_resource(TeamMemberLeadsResource, '/api/team-members/<int:user_id>/leads')

    return api
