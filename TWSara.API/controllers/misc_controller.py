from flask_restful import Resource

from models import BuilderPrimary, CustProject, LookupLeadStatus, UserSara


class HomeResource(Resource):
    def get(self):
        return {'message': 'SaraHive API'}


class PublicStatsResource(Resource):
    """Aggregate-only counts for the public marketing landing page — no auth,
    so it must never expose per-lead detail."""

    def get(self):
        total_leads = CustProject.query.count()
        converted_status = LookupLeadStatus.query.filter_by(recordName='Converted').first()
        converted_count = (
            CustProject.query.filter_by(leadStatusId=converted_status.recordId).count()
            if converted_status
            else 0
        )
        conversion_rate = round((converted_count / total_leads) * 100, 1) if total_leads else 0

        return {
            'totalLeads': total_leads,
            'totalBuilders': BuilderPrimary.query.filter_by(isActive=True).count(),
            'totalTeamMembers': UserSara.query.filter_by(isAdmin=False, isApproved=True).count(),
            'conversionRate': conversion_rate,
        }
