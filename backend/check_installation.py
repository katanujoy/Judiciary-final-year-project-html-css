# check_installation.py
import sys
import os

print("🔍 Checking Installation...")
print("="*60)

# Check Python version
print(f"Python: {sys.version}")

# Check current directory
print(f"\nCurrent directory: {os.getcwd()}")

# Check if required files exist
required_files = [
    'app/__init__.py',
    'app/models/__init__.py',
    'app/routes/auth.py',
    'config.py',
    'requirements.txt'
]

print("\n📁 Checking required files:")
for file in required_files:
    if os.path.exists(file):
        print(f"  ✅ {file}")
    else:
        print(f"  ❌ {file} - MISSING")

# Try to import modules
print("\n🔧 Testing imports:")
try:
    from flask import Flask
    print("  ✅ Flask")
except ImportError as e:
    print(f"  ❌ Flask: {e}")

try:
    from flask_cors import CORS
    print("  ✅ Flask-CORS")
except ImportError as e:
    print(f"  ❌ Flask-CORS: {e}")

try:
    from flask_jwt_extended import JWTManager
    print("  ✅ Flask-JWT-Extended")
except ImportError as e:
    print(f"  ❌ Flask-JWT-Extended: {e}")

try:
    import bcrypt
    print("  ✅ bcrypt")
except ImportError as e:
    print(f"  ❌ bcrypt: {e}")

# Check if we can create the app
print("\n🚀 Testing app creation:")
try:
    from app import create_app
    app = create_app()
    print("  ✅ App created successfully")
    
    with app.app_context():
        print("  ✅ App context works")
        
except Exception as e:
    print(f"  ❌ Error creating app: {e}")

print("\n" + "="*60)
print("📋 Next Steps:")
print("1. Run: pip install -r requirements.txt")
print("2. Run: python create_tables.py")
print("3. Run: python run.py")
print("4. Open: http://localhost:5500")
print("="*60)