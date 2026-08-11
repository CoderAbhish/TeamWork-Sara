import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()


def init_app(app):
    db_user = os.environ["DB_USERNAME"]
    db_password = quote_plus(os.environ["DB_PASSWORD"])
    db_host = os.environ["DB_HOST"]
    db_port = os.environ["DB_PORT"]
    db_name = os.environ["DB_NAME"]
    db_sslmode = os.environ.get("DB_SSLMODE", "require")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        f"?sslmode={db_sslmode}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
