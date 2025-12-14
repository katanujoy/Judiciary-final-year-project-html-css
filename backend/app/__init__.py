# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ---------------------------------------------
    # CORS FIX - Allow frontend at 5500 to access API at 5000
    # ---------------------------------------------
    CORS(app,
         resources={r"/api/*": {"origins": "http://localhost:5500"}},
         supports_credentials=True)

    # ---------------------------------------------
    # Initialize Extensions
    # ---------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # ---------------------------------------------
    # Register Blueprints
    # ---------------------------------------------
    from app.routes.auth import auth_bp
    from app.routes.cases import cases_bp
    from app.routes.files import files_bp
    from app.routes.search import search_bp
    from app.routes.backup import backup_bp
    from app.routes.users import users_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(cases_bp, url_prefix="/api/cases")
    app.register_blueprint(files_bp, url_prefix="/api/files")
    app.register_blueprint(search_bp, url_prefix="/api/search")
    app.register_blueprint(backup_bp, url_prefix="/api/backup")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")

    # ---------------------------------------------
    # Ensure folders exist
    # ---------------------------------------------
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["BACKUP_DIR"], exist_ok=True)

    return app
