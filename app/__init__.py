from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix


db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app():

    app = Flask(__name__)

    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
    )

    # Secret key for session-based login
    app.secret_key = "urembo-secret-key-2026"

    # Load configuration
    app.config.from_object("config.Config")

    # Initialize extensions
    db.init_app(app)

    # We'll enable Flask-Login after creating the User model
    # login_manager.init_app(app)

    migrate.init_app(app, db)

    # Import models so Flask-Migrate can detect them
    from app import models

    # login_manager.login_view = "auth.login"

    # Import blueprints
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.agents.routes import agents_bp
    from app.sim_issuance.routes import sim_bp
    from app.performance.routes import performance_bp
    from app.email_intelligence.routes import email_bp

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(sim_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(email_bp)

    return app
