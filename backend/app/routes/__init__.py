# app/routes/__init__.py
from .auth import auth_bp
from .cases import cases_bp
from .files import files_bp
from .search import search_bp
from .backup import backup_bp
from .users import users_bp
from .reports import reports_bp

__all__ = [
    'auth_bp',
    'cases_bp',
    'files_bp',
    'search_bp',
    'backup_bp',
    'users_bp',
    'reports_bp'
]