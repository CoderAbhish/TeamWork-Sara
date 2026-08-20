import os

from flask import Flask
from flask_cors import CORS

from auth import init_jwt
from db import init_app as init_db
from route import register_routes

API_PORT = int(os.environ.get('API_PORT', 5000))

app = Flask(__name__)
init_db(app)
init_jwt(app)
CORS(app, resources={r"/api/*": {"origins": os.environ.get("CORS_ORIGIN", "http://localhost:5173")}})

register_routes(app)


@app.cli.command('init-db')
def init_db_command():
    """Create all tables that don't exist yet."""
    import models  # noqa: F401  (registers models with SQLAlchemy metadata)
    from db import db

    db.create_all()
    print('Database tables created.')


@app.cli.command('reset-db')
def reset_db_command():
    """Drop and recreate every table. Destructive — for dev use only."""
    import models  # noqa: F401  (registers models with SQLAlchemy metadata)
    from db import db

    db.drop_all()
    db.create_all()
    print('Database tables dropped and recreated.')


@app.cli.command('seed-lookups')
def seed_lookups_command():
    """Seed the lookup tables with their default option lists (idempotent)."""
    from db import db
    from models import (
        LookupLeadCategory,
        LookupLeadSource,
        LookupLeadStatus,
        LookupListingType,
        LookupProjectStatus,
        LookupPropertyType,
        LookupSaleType,
    )

    def seed(model, names):
        added = 0
        for name in names:
            if not model.query.filter_by(recordName=name).first():
                db.session.add(model(recordName=name))
                added += 1
        return added

    added = 0
    added += seed(
        LookupProjectStatus,
        ['Planning', 'Under Construction', 'Nearing Completion', 'Completed', 'On Hold'],
    )
    added += seed(
        LookupLeadStatus,
        ['New', 'Contacted', 'Site Visit Scheduled', 'Negotiation', 'Converted', 'Lost', 'On Hold'],
    )
    added += seed(LookupLeadCategory, ['New/Fresh', 'Warm', 'Hot', 'Cold', 'Dead'])
    added += seed(
        LookupPropertyType,
        ['Individual', 'Flat/Apartment', 'Villa', 'Row House', 'Plot', 'Farm Land'],
    )
    added += seed(LookupSaleType, ['Resale', 'Sale', 'Rented'])
    added += seed(
        LookupListingType,
        ['New Launch', 'Under Construction', 'Ready to Move', 'Existing'],
    )
    added += seed(LookupLeadSource, ['Syndicate', 'Meta', 'Google', 'IVR Calling', 'Other'])

    db.session.commit()
    print(f'Seeded lookup tables ({added} new rows).')


@app.cli.command('seed-admin')
def seed_admin_command():
    """Create the admin user for local testing (idempotent)."""
    import bcrypt

    from db import db
    from models import UserSara

    if UserSara.query.filter_by(username='Sara').first():
        print('Admin user already exists.')
        return

    password_hash = bcrypt.hashpw(b'SaraHoney123Comb', bcrypt.gensalt()).decode('utf-8')
    admin = UserSara(
        username='Sara',
        emailId='sara@example.com',
        passwordHash=password_hash,
        contactNumber='0000000000',
        isAdmin=True,
        isActive=True,
        isApproved=True,
    )
    db.session.add(admin)
    db.session.commit()
    print('Admin user created (username=Sara)')


if __name__ == '__main__':
    app.run(port=API_PORT, debug=True)
