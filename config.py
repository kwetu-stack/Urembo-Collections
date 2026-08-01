import os
from dotenv import load_dotenv

load_dotenv()


def get_database_url():
    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///urembo.db"
    )

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    return database_url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "kwetu-urembo-secret-key")

    GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")

    GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")

    GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI")

    GMAIL_SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly"
    ]

    SQLALCHEMY_DATABASE_URI = get_database_url()

    SQLALCHEMY_TRACK_MODIFICATIONS = False
