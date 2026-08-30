from datetime import datetime, timezone

from db import db


def utcnow():
    return datetime.now(timezone.utc)


class LookupProjectStatus(db.Model):
    __tablename__ = 'lookup_project_status'

    recordId = db.Column(db.Integer, primary_key=True)
    recordName = db.Column(db.String(255), nullable=False, unique=True)


class LookupLeadStatus(db.Model):
    __tablename__ = 'lookup_lead_status'

    recordId = db.Column(db.Integer, primary_key=True)
    recordName = db.Column(db.String(255), nullable=False, unique=True)


class LookupLeadCategory(db.Model):
    __tablename__ = 'lookup_lead_category'

    recordId = db.Column(db.Integer, primary_key=True)
    recordName = db.Column(db.String(255), nullable=False, unique=True)


class LookupPropertyType(db.Model):
    """Structure of the property: Individual, Flat, Villa, Plot, Farm Land, ..."""

    __tablename__ = 'lookup_property_type'

    recordId = db.Column(db.Integer, primary_key=True)
    recordName = db.Column(db.String(255), nullable=False, unique=True)


class LookupSaleType(db.Model):
    """Buy/sell type of the property: Resale, Sale, Rented."""

    __tablename__ = 'lookup_sale_type'

    recordId = db.Column(db.Integer, primary_key=True)
    recordName = db.Column(db.String(255), nullable=False, unique=True)


class LookupListingType(db.Model):
    """Market listing stage: New Launch, Under Construction, Ready to Move, Existing."""

    __tablename__ = 'lookup_listing_type'

    recordId = db.Column(db.Integer, primary_key=True)
    recordName = db.Column(db.String(255), nullable=False, unique=True)


class LookupLeadSource(db.Model):
    __tablename__ = 'lookup_lead_source'

    recordId = db.Column(db.Integer, primary_key=True)
    recordName = db.Column(db.String(255), nullable=False, unique=True)


class UserSara(db.Model):
    __tablename__ = 'user_sara'

    recordId = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True, index=True)
    emailId = db.Column(db.String(255), nullable=False, unique=True, index=True)
    # Not present in the original diagram: authentication is impossible without
    # a credential to check, so a hash column was added.
    passwordHash = db.Column(db.String(255), nullable=False)
    contactNumber = db.Column(db.String(10))
    alternateNumber = db.Column(db.String(10))
    isAdmin = db.Column(db.Boolean, nullable=False, default=False)
    isActive = db.Column(db.Boolean, nullable=False, default=True)
    # Team members can't use their account until an admin recognizes the
    # registration; admins are approved implicitly (see seed-admin / isAdmin checks).
    isApproved = db.Column(db.Boolean, nullable=False, default=False)
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    modifiedOn = db.Column(db.DateTime(timezone=True), onupdate=utcnow)
    modifiedBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))

    assignedLeads = db.relationship(
        'CustProject', back_populates='assignedTo', foreign_keys='CustProject.assignedToUserId'
    )
    comments = db.relationship('LeadComment', back_populates='author')

    @property
    def role(self):
        return 'admin' if self.isAdmin else 'teamMember'


class BuilderPrimary(db.Model):
    __tablename__ = 'builder_primary'

    recordId = db.Column(db.Integer, primary_key=True)
    builderName = db.Column(db.String(255), nullable=False)
    # Builders are deactivated, never deleted, so historical projects/leads
    # keep a valid reference.
    isActive = db.Column(db.Boolean, nullable=False, default=True)
    # How many days a lead registration with this builder stays valid — same
    # for every project of theirs (e.g. 10 days for Builder1). Used to
    # auto-fill CustProject.registrationExpiryDate when a lead is registered.
    leadRegistrationValidityDays = db.Column(db.Integer)
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    modifiedOn = db.Column(db.DateTime(timezone=True), onupdate=utcnow)
    modifiedBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))

    projects = db.relationship('BuilderProject', back_populates='builder')


class BuilderProject(db.Model):
    __tablename__ = 'builder_project'

    recordId = db.Column(db.Integer, primary_key=True)
    builderRecordId = db.Column(
        db.Integer, db.ForeignKey('builder_primary.recordId'), nullable=False, index=True
    )
    # Missing from the original diagram entirely: a project needs a
    # human-readable name to be referenced anywhere (UI, CSV import/export).
    projectName = db.Column(db.String(255), nullable=False)
    # The diagram drew a line from LookupProjectStatus to this column but never
    # marked it "FK" — added the actual constraint so status values are validated.
    lookupProjectStatusRecordId = db.Column(
        db.Integer, db.ForeignKey('lookup_project_status.recordId'), nullable=False, index=True
    )
    startDate = db.Column(db.DateTime(timezone=True))
    plannedCompletionDate = db.Column(db.DateTime(timezone=True))
    actualCompletionDate = db.Column(db.DateTime(timezone=True))
    # Property details (extracted from builder cost-sheets / project brochures)
    # — location is the one field every listing has, so the API requires it
    # on every create/update (see builder_controller). Nullable at the DB
    # level only so this column can be added to the live table without a
    # backfill for projects that already existed before this field did.
    location = db.Column(db.String(255))
    propertyTypeId = db.Column(db.Integer, db.ForeignKey('lookup_property_type.recordId'), index=True)
    saleTypeId = db.Column(db.Integer, db.ForeignKey('lookup_sale_type.recordId'), index=True)
    listingTypeId = db.Column(db.Integer, db.ForeignKey('lookup_listing_type.recordId'), index=True)
    areaExtent = db.Column(db.String(100))
    structureDescription = db.Column(db.String(255))
    numberOfTowers = db.Column(db.Integer)
    totalUnits = db.Column(db.Integer)
    reraNumber = db.Column(db.String(100))
    approvalAuthority = db.Column(db.String(100))
    possessionDate = db.Column(db.DateTime(timezone=True))
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    modifiedOn = db.Column(db.DateTime(timezone=True), onupdate=utcnow)
    modifiedBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))

    builder = db.relationship('BuilderPrimary', back_populates='projects')
    status = db.relationship('LookupProjectStatus')
    propertyType = db.relationship('LookupPropertyType')
    saleType = db.relationship('LookupSaleType')
    listingType = db.relationship('LookupListingType')
    leads = db.relationship('CustProject', back_populates='project')
    managers = db.relationship(
        'ProjectManager', back_populates='project', order_by='ProjectManager.recordId'
    )
    configurations = db.relationship(
        'ProjectUnitConfiguration', back_populates='project', order_by='ProjectUnitConfiguration.recordId'
    )


class ProjectManager(db.Model):
    """A point-of-contact for a project — not a UserSara/team member."""

    __tablename__ = 'project_manager'

    recordId = db.Column(db.Integer, primary_key=True)
    projectId = db.Column(
        db.Integer, db.ForeignKey('builder_project.recordId'), nullable=False, index=True
    )
    managerName = db.Column(db.String(255), nullable=False)
    contactNumber = db.Column(db.String(10), nullable=False)
    emailId = db.Column(db.String(255))
    notes = db.Column(db.Text)
    isActive = db.Column(db.Boolean, nullable=False, default=True)
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    modifiedOn = db.Column(db.DateTime(timezone=True), onupdate=utcnow)
    modifiedBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))

    project = db.relationship('BuilderProject', back_populates='managers')


class ProjectUnitConfiguration(db.Model):
    """One sellable configuration within a project — "2 BHK", "4 Bedroom East
    corner", "Villa", etc. — each with its own size/price."""

    __tablename__ = 'project_unit_configuration'

    recordId = db.Column(db.Integer, primary_key=True)
    projectId = db.Column(
        db.Integer, db.ForeignKey('builder_project.recordId'), nullable=False, index=True
    )
    configurationLabel = db.Column(db.String(255), nullable=False)
    sizeSqFt = db.Column(db.Numeric(10, 2))
    plotDimensionSqFt = db.Column(db.Numeric(10, 2))
    startingPriceAmount = db.Column(db.Numeric(14, 2))
    baseRatePerSqFt = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    modifiedOn = db.Column(db.DateTime(timezone=True), onupdate=utcnow)
    modifiedBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))

    project = db.relationship('BuilderProject', back_populates='configurations')


class CustLeadPrimary(db.Model):
    __tablename__ = 'cust_lead_primary'

    recordId = db.Column(db.Integer, primary_key=True)
    leadName = db.Column(db.String(255), nullable=False)
    contactNumber = db.Column(db.String(10), index=True)
    alternateNumber = db.Column(db.String(10))
    leadLocation = db.Column(db.String(255))
    createdBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    modifiedBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    modifiedOn = db.Column(db.DateTime(timezone=True), onupdate=utcnow)

    leads = db.relationship('CustProject', back_populates='customer')


class CustProject(db.Model):
    """A customer's interest in one specific project — the CRM "lead"."""

    __tablename__ = 'cust_project'

    recordId = db.Column(db.Integer, primary_key=True)
    customerId = db.Column(
        db.Integer, db.ForeignKey('cust_lead_primary.recordId'), nullable=False, index=True
    )
    # A lead can be created before a project is picked (only name + contact
    # are mandatory) — set later from the lead detail page.
    projectId = db.Column(
        db.Integer, db.ForeignKey('builder_project.recordId'), nullable=True, index=True
    )
    isCustLeadRegistered = db.Column(db.Boolean, nullable=False, default=False)
    # Stamped the first time isCustLeadRegistered flips true; expiry defaults
    # from the builder's leadRegistrationValidityDays but stays editable.
    registeredOn = db.Column(db.DateTime(timezone=True))
    registrationExpiryDate = db.Column(db.DateTime(timezone=True))
    assignedToUserId = db.Column(
        db.Integer, db.ForeignKey('user_sara.recordId'), index=True
    )
    leadStatusId = db.Column(
        db.Integer, db.ForeignKey('lookup_lead_status.recordId'), index=True
    )
    leadCategoryId = db.Column(
        db.Integer, db.ForeignKey('lookup_lead_category.recordId'), index=True
    )
    leadSourceId = db.Column(db.Integer, db.ForeignKey('lookup_lead_source.recordId'), index=True)
    # Free-text detail alongside the source, e.g. the syndicate person's name.
    leadSourceDetail = db.Column(db.String(255))
    # The next scheduled follow-up ("retouch") date/time for this lead.
    nextFollowUpOn = db.Column(db.DateTime(timezone=True))
    # Which unit configuration (if any) the lead is interested in.
    interestedConfigId = db.Column(
        db.Integer, db.ForeignKey('project_unit_configuration.recordId'), index=True
    )
    # Stamped once, the first time the status flips to "Converted" — drives
    # the converted-over-time chart without approximating from modifiedOn.
    convertedOn = db.Column(db.DateTime(timezone=True))
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    modifiedOn = db.Column(db.DateTime(timezone=True), onupdate=utcnow)
    modifiedBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))

    customer = db.relationship('CustLeadPrimary', back_populates='leads')
    project = db.relationship('BuilderProject', back_populates='leads')
    assignedTo = db.relationship(
        'UserSara', back_populates='assignedLeads', foreign_keys=[assignedToUserId]
    )
    status = db.relationship('LookupLeadStatus')
    category = db.relationship('LookupLeadCategory')
    source = db.relationship('LookupLeadSource')
    interestedConfig = db.relationship('ProjectUnitConfiguration')
    # cascade='all, delete-orphan' on every child log below: these rows are
    # only meaningful attached to their lead (comments, visits, follow-ups,
    # transfer requests), so deleting a lead must take them with it instead
    # of tripping their NOT NULL custProjectId FK.
    comments = db.relationship(
        'LeadComment', back_populates='lead', order_by='LeadComment.createdOn.desc()',
        cascade='all, delete-orphan',
    )
    siteVisits = db.relationship(
        'SiteVisit', back_populates='lead', order_by='SiteVisit.scheduledOn.desc()',
        cascade='all, delete-orphan',
    )
    followUps = db.relationship(
        'LeadFollowUp', back_populates='lead', order_by='LeadFollowUp.createdOn.desc()',
        cascade='all, delete-orphan',
    )
    transferRequests = db.relationship(
        'LeadTransferRequest', back_populates='lead', order_by='LeadTransferRequest.requestedOn.desc()',
        cascade='all, delete-orphan',
    )


class LeadComment(db.Model):
    __tablename__ = 'lead_comment'

    recordId = db.Column(db.Integer, primary_key=True)
    custProjectId = db.Column(
        db.Integer, db.ForeignKey('cust_project.recordId'), nullable=False, index=True
    )
    authorUserId = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'), nullable=False)
    commentText = db.Column(db.Text, nullable=False)
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    lead = db.relationship('CustProject', back_populates='comments')
    author = db.relationship('UserSara', back_populates='comments')


class LeadFollowUp(db.Model):
    """A logged follow-up ('retouch') on a lead. Append-only, with a
    mandatory comment each time, so the full contact history is preserved
    rather than silently overwriting a single 'next follow-up' field."""

    __tablename__ = 'lead_follow_up'

    recordId = db.Column(db.Integer, primary_key=True)
    custProjectId = db.Column(
        db.Integer, db.ForeignKey('cust_project.recordId'), nullable=False, index=True
    )
    followUpOn = db.Column(db.DateTime(timezone=True), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))

    lead = db.relationship('CustProject', back_populates='followUps')
    author = db.relationship('UserSara')


class LeadSuggestion(db.Model):
    """A lead a team member proposes; becomes a real CustProject on approval."""

    __tablename__ = 'lead_suggestion'

    recordId = db.Column(db.Integer, primary_key=True)
    leadName = db.Column(db.String(255), nullable=False)
    contactNumber = db.Column(db.String(10), nullable=False)
    alternateNumber = db.Column(db.String(10))
    leadLocation = db.Column(db.String(255))
    # Team members can only point at the existing catalog, never create new
    # builders/projects — both nullable since a suggestion may be raw contact info.
    builderId = db.Column(db.Integer, db.ForeignKey('builder_primary.recordId'))
    projectId = db.Column(db.Integer, db.ForeignKey('builder_project.recordId'))
    status = db.Column(db.String(20), nullable=False, default='pending')
    suggestedByUserId = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'), nullable=False)
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    reviewedByUserId = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    reviewedOn = db.Column(db.DateTime(timezone=True))
    resultingLeadId = db.Column(db.Integer, db.ForeignKey('cust_project.recordId'))

    builder = db.relationship('BuilderPrimary')
    project = db.relationship('BuilderProject')
    suggestedBy = db.relationship('UserSara', foreign_keys=[suggestedByUserId])
    reviewedBy = db.relationship('UserSara', foreign_keys=[reviewedByUserId])
    resultingLead = db.relationship('CustProject')


class LeadTransferRequest(db.Model):
    """A team member's request to hand a lead they own to another team
    member — takes effect only once an admin approves it."""

    __tablename__ = 'lead_transfer_request'

    recordId = db.Column(db.Integer, primary_key=True)
    custProjectId = db.Column(
        db.Integer, db.ForeignKey('cust_project.recordId'), nullable=False, index=True
    )
    fromUserId = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'), nullable=False)
    toUserId = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    requestedOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    reviewedByUserId = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    reviewedOn = db.Column(db.DateTime(timezone=True))
    reviewComment = db.Column(db.Text)

    lead = db.relationship('CustProject', back_populates='transferRequests')
    fromUser = db.relationship('UserSara', foreign_keys=[fromUserId])
    toUser = db.relationship('UserSara', foreign_keys=[toUserId])
    reviewedBy = db.relationship('UserSara', foreign_keys=[reviewedByUserId])


class SiteVisit(db.Model):
    """A scheduled site visit for a lead-project combination."""

    __tablename__ = 'site_visit'

    recordId = db.Column(db.Integer, primary_key=True)
    custProjectId = db.Column(
        db.Integer, db.ForeignKey('cust_project.recordId'), nullable=False, index=True
    )
    scheduledOn = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Scheduled')
    notes = db.Column(db.Text)
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    modifiedOn = db.Column(db.DateTime(timezone=True), onupdate=utcnow)
    modifiedBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))

    lead = db.relationship('CustProject', back_populates='siteVisits')


class NotificationDismissal(db.Model):
    """Notifications aren't persisted rows — they're computed fresh from
    current data on every request (follow-ups due, expired registrations,
    unassigned leads, pending transfers), since there's no background
    scheduler in this app to generate them ahead of time. This table is
    just the "I've seen this one" marker per user + notification key, so a
    dismissed reminder doesn't reappear on the next poll."""

    __tablename__ = 'notification_dismissal'
    __table_args__ = (db.UniqueConstraint('userId', 'notificationKey', name='uq_notification_dismissal'),)

    recordId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'), nullable=False, index=True)
    notificationKey = db.Column(db.String(255), nullable=False)
    dismissedOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
