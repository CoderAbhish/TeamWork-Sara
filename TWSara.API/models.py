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
    createdOn = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))
    modifiedOn = db.Column(db.DateTime(timezone=True), onupdate=utcnow)
    modifiedBy = db.Column(db.Integer, db.ForeignKey('user_sara.recordId'))

    builder = db.relationship('BuilderPrimary', back_populates='projects')
    status = db.relationship('LookupProjectStatus')
    leads = db.relationship('CustProject', back_populates='project')


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
    assignedToUserId = db.Column(
        db.Integer, db.ForeignKey('user_sara.recordId'), index=True
    )
    leadStatusId = db.Column(
        db.Integer, db.ForeignKey('lookup_lead_status.recordId'), index=True
    )
    leadCategoryId = db.Column(
        db.Integer, db.ForeignKey('lookup_lead_category.recordId'), index=True
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
    comments = db.relationship(
        'LeadComment', back_populates='lead', order_by='LeadComment.createdOn.desc()'
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
