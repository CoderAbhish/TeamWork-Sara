"""Helpers shared between report_controller (CSV import) and
lead_suggestion_controller (suggestion approval) — both upsert a customer
by contact number the same way.
"""

from db import db
from models import CustLeadPrimary


def get_or_create_customer(lead_name, contact_number, alternate_number, location, me_id):
    customer = CustLeadPrimary.query.filter_by(contactNumber=contact_number).first()
    if customer:
        customer.leadName = lead_name
        if alternate_number:
            customer.alternateNumber = alternate_number
        if location:
            customer.leadLocation = location
        customer.modifiedBy = me_id
        return customer, False

    customer = CustLeadPrimary(
        leadName=lead_name,
        contactNumber=contact_number,
        alternateNumber=alternate_number or None,
        leadLocation=location or None,
        createdBy=me_id,
    )
    db.session.add(customer)
    db.session.flush()
    return customer, True
