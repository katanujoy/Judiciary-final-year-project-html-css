from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # --- CORS ---
    CORS(app,
         resources={r"/api/*": {"origins": "*"}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )

    # Preflight OPTIONS handler
    @app.before_request
    def handle_options():
        if request.method == "OPTIONS":
            return jsonify({"message": "CORS Preflight OK"}), 200

    # Import models so SQLAlchemy recognizes them
    from app.models import User, Case, CaseFile, Backup, FileBackup, AuditLog

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.backup import backup_bp
    from app.routes.files import files_bp
    from app.routes.search import search_bp
    from app.routes.users import users_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(backup_bp, url_prefix='/api')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(search_bp, url_prefix='/api')
    app.register_blueprint(users_bp, url_prefix='/api')

    # Root route for testing
    @app.route('/')
    def index():
        return jsonify({"message": "Judicial File Backup System API running!"})

    return app
