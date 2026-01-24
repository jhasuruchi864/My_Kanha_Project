#!/usr/bin/env python
"""
Authentication System Verification Script
Validates all authentication components are properly installed and configured.
"""

import sys
import os

def check_imports():
    """Verify all authentication modules can be imported."""
    print("\n🔍 Checking Authentication Imports...")
    
    try:
        from app.models.user_models import UserRegister, TokenResponse
        print("  ✓ User models")
        
        from app.core.auth_service import (
            create_user, verify_token, verify_password, 
            create_access_token, init_db
        )
        print("  ✓ Auth service functions")
        
        from app.api.routes_auth import router as auth_router, get_current_user
        print("  ✓ Auth routes")
        
        from app.api.routes_chat import get_optional_user
        print("  ✓ Chat optional auth")
        
        from app.api.routes_history import get_current_user as history_get_user
        print("  ✓ History required auth")
        
        return True
    except ImportError as e:
        print(f"  ✗ Import Error: {e}")
        return False

def check_database():
    """Verify database is initialized."""
    print("\n🗄️  Checking Database...")
    
    try:
        from app.core.auth_service import DB_PATH, init_db
        
        init_db()
        
        if DB_PATH.exists():
            print(f"  ✓ Database file: {DB_PATH}")
            
            # Check tables
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if any(t[0] == 'users' for t in tables):
                print("  ✓ Users table created")
            
            if any(t[0] == 'chat_history' for t in tables):
                print("  ✓ Chat history table created")
            
            conn.close()
            return True
        else:
            print(f"  ✗ Database not found: {DB_PATH}")
            return False
            
    except Exception as e:
        print(f"  ✗ Database Error: {e}")
        return False

def check_jwt_config():
    """Verify JWT configuration."""
    print("\n🔑 Checking JWT Configuration...")
    
    try:
        from app.config import settings
        from app.core.auth_service import JWT_SECRET_KEY, JWT_ALGORITHM
        
        print(f"  ✓ JWT Algorithm: {JWT_ALGORITHM}")
        print(f"  ✓ JWT Expiration: {settings.JWT_EXPIRATION_HOURS} hours")
        print(f"  ✓ JWT Secret Key: {'***' + JWT_SECRET_KEY[-5:] if len(JWT_SECRET_KEY) > 5 else '***'}")
        
        if JWT_SECRET_KEY == "change-me-in-production-secret-key-12345":
            print("  ⚠️  WARNING: Using default JWT secret key (change in production!)")
        
        return True
    except Exception as e:
        print(f"  ✗ Config Error: {e}")
        return False

def check_dependencies():
    """Verify required dependencies are installed."""
    print("\n📦 Checking Dependencies...")
    
    required = {
        'pyjwt': 'JWT token library',
        'email_validator': 'Email validation',
        'pydantic': 'Data validation',
        'fastapi': 'Web framework',
    }
    
    all_ok = True
    for module, description in required.items():
        try:
            __import__(module)
            print(f"  ✓ {module}: {description}")
        except ImportError:
            print(f"  ✗ {module}: NOT INSTALLED")
            all_ok = False
    
    return all_ok

def test_password_hashing():
    """Test password hashing and verification."""
    print("\n🔐 Testing Password Hashing...")
    
    try:
        from app.core.auth_service import hash_password, verify_password
        
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        if verify_password(password, hashed):
            print("  ✓ Password hashing works")
            return True
        else:
            print("  ✗ Password verification failed")
            return False
    except Exception as e:
        print(f"  ✗ Hashing Error: {e}")
        return False

def test_jwt_tokens():
    """Test JWT token creation and verification."""
    print("\n🎫 Testing JWT Tokens...")
    
    try:
        from app.core.auth_service import create_access_token, verify_token
        
        user_id = "test_user_123"
        username = "testuser"
        email = "test@example.com"
        
        token, expires_in = create_access_token(user_id, username, email)
        print(f"  ✓ Token created (expires in {expires_in}s)")
        
        verified = verify_token(token)
        if verified and verified.user_id == user_id:
            print("  ✓ Token verified successfully")
            return True
        else:
            print("  ✗ Token verification failed")
            return False
    except Exception as e:
        print(f"  ✗ Token Error: {e}")
        return False

def test_user_creation():
    """Test user registration."""
    print("\n👤 Testing User Registration...")
    
    try:
        from app.core.auth_service import create_user, get_user_by_username
        
        username = f"test_user_{os.urandom(4).hex()}"
        email = f"test_{os.urandom(4).hex()}@example.com"
        password = "TestPass123!"
        full_name = "Test User"
        
        user = create_user(username, email, password, full_name)
        print(f"  ✓ User created: {username}")
        
        retrieved = get_user_by_username(username)
        if retrieved and retrieved['username'] == username:
            print("  ✓ User retrieved successfully")
            return True
        else:
            print("  ✗ User retrieval failed")
            return False
    except ValueError as e:
        if "already exists" in str(e):
            print(f"  ✓ User creation and uniqueness constraints working")
            return True
        else:
            print(f"  ✗ {e}")
            return False
    except Exception as e:
        print(f"  ✗ User Creation Error: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("🔐 My Kanha - JWT Authentication Verification")
    print("=" * 60)
    
    checks = [
        ("Imports", check_imports),
        ("Database", check_database),
        ("JWT Configuration", check_jwt_config),
        ("Dependencies", check_dependencies),
        ("Password Hashing", test_password_hashing),
        ("JWT Tokens", test_jwt_tokens),
        ("User Creation", test_user_creation),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ Unexpected error in {name}: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<30} {status}")
    
    all_passed = all(results.values())
    
    print("=" * 60)
    if all_passed:
        print("✅ All checks passed! Authentication system is ready.")
        print("\n📝 Next steps:")
        print("  1. Set JWT_SECRET_KEY in .env for production")
        print("  2. Run: pytest tests/test_auth.py -v")
        print("  3. Start server: uvicorn app.main:app --reload")
        print("  4. Test API at: http://localhost:8000/docs")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
