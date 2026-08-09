from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
migrate = Migrate()


def create_app():

    app = Flask(__name__)

    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
    )

    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models
    from app import models

    # Blueprints
    from app.dashboard.routes import dashboard_bp
    from app.email_intelligence.routes import email_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(email_bp)

    # Home page
    @app.route("/")
    def home():
        return redirect(url_for("dashboard.dashboard"))

    return app