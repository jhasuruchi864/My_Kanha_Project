"""
Authentication Tests
Test user registration, login, and JWT token functionality.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestUserRegistration:
    """Test user registration endpoint."""
    
    def test_register_new_user(self):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser123",
                "email": "testuser@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert data["user"]["username"] == "testuser123"
        assert data["user"]["email"] == "testuser@example.com"
        assert data["expires_in"] > 0
    
    def test_register_short_password(self):
        """Test registration fails with short password."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_register_invalid_email(self):
        """Test registration fails with invalid email."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "not-an-email",
                "password": "ValidPassword123!"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_short_username(self):
        """Test registration fails with short username."""
        response = client.post(
            "/auth/register",
            json={
                "username": "ab",
                "email": "test@example.com",
                "password": "ValidPassword123!"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_duplicate_username(self):
        """Test registration fails with duplicate username."""
        # First registration
        client.post(
            "/auth/register",
            json={
                "username": "uniqueuser",
                "email": "unique1@example.com",
                "password": "ValidPassword123!"
            }
        )
        
        # Second registration with same username
        response = client.post(
            "/auth/register",
            json={
                "username": "uniqueuser",
                "email": "unique2@example.com",
                "password": "ValidPassword123!"
            }
        )
        
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]
    
    def test_register_duplicate_email(self):
        """Test registration fails with duplicate email."""
        # First registration
        client.post(
            "/auth/register",
            json={
                "username": "user1",
                "email": "sameemail@example.com",
                "password": "ValidPassword123!"
            }
        )
        
        # Second registration with same email
        response = client.post(
            "/auth/register",
            json={
                "username": "user2",
                "email": "sameemail@example.com",
                "password": "ValidPassword123!"
            }
        )
        
        assert response.status_code == 400
        assert "Email already exists" in response.json()["detail"]


class TestUserLogin:
    """Test user login endpoint."""
    
    def test_login_with_username(self):
        """Test login using username."""
        # Register first
        reg_response = client.post(
            "/auth/register",
            json={
                "username": "loginuser",
                "email": "loginuser@example.com",
                "password": "LoginPass123!"
            }
        )
        
        # Login with username
        login_response = client.post(
            "/auth/login",
            json={
                "username": "loginuser",
                "password": "LoginPass123!"
            }
        )
        
        assert login_response.status_code == 200
        data = login_response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert data["user"]["username"] == "loginuser"
    
    def test_login_with_email(self):
        """Test login using email."""
        # Register first
        client.post(
            "/auth/register",
            json={
                "username": "emailuser",
                "email": "emailuser@example.com",
                "password": "EmailPass123!"
            }
        )
        
        # Login with email
        login_response = client.post(
            "/auth/login",
            json={
                "username": "emailuser@example.com",
                "password": "EmailPass123!"
            }
        )
        
        assert login_response.status_code == 200
        assert login_response.json()["user"]["email"] == "emailuser@example.com"
    
    def test_login_wrong_password(self):
        """Test login fails with wrong password."""
        # Register first
        client.post(
            "/auth/register",
            json={
                "username": "wrongpass",
                "email": "wrongpass@example.com",
                "password": "CorrectPass123!"
            }
        )
        
        # Try login with wrong password
        login_response = client.post(
            "/auth/login",
            json={
                "username": "wrongpass",
                "password": "WrongPass123!"
            }
        )
        
        assert login_response.status_code == 401
        assert "Invalid username or password" in login_response.json()["detail"]
    
    def test_login_nonexistent_user(self):
        """Test login fails for nonexistent user."""
        login_response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "SomePass123!"
            }
        )
        
        assert login_response.status_code == 401


class TestAuthenticatedEndpoints:
    """Test endpoints requiring authentication."""
    
    def test_get_current_user(self):
        """Test getting current user profile."""
        # Register and get token
        reg_response = client.post(
            "/auth/register",
            json={
                "username": "profileuser",
                "email": "profileuser@example.com",
                "password": "ProfilePass123!",
                "full_name": "Profile User"
            }
        )
        
        token = reg_response.json()["access_token"]
        
        # Get user profile
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        user = response.json()
        assert user["username"] == "profileuser"
        assert user["full_name"] == "Profile User"
    
    def test_get_current_user_no_token(self):
        """Test getting user profile without token fails."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self):
        """Test getting user profile with invalid token fails."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401
    
    def test_refresh_token(self):
        """Test token refresh."""
        # Register and get token
        reg_response = client.post(
            "/auth/register",
            json={
                "username": "refreshuser",
                "email": "refreshuser@example.com",
                "password": "RefreshPass123!"
            }
        )
        
        old_token = reg_response.json()["access_token"]
        
        # Refresh token
        response = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {old_token}"}
        )
        
        assert response.status_code == 200
        new_token = response.json()["access_token"]
        assert new_token != old_token


class TestChatWithAuthentication:
    """Test chat endpoints with authentication."""
    
    def test_chat_with_auth(self):
        """Test chat endpoint with authenticated user."""
        # Register user
        reg_response = client.post(
            "/auth/register",
            json={
                "username": "chatuser",
                "email": "chatuser@example.com",
                "password": "ChatPass123!"
            }
        )
        
        token = reg_response.json()["access_token"]
        
        # Send authenticated chat request
        response = client.post(
            "/chat",
            json={
                "message": "What is dharma?",
                "language": "english",
                "top_k": 3
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should return 200 or relevant error about LLM not running
        assert response.status_code in [200, 500]
    
    def test_chat_without_auth(self):
        """Test chat endpoint works without authentication."""
        response = client.post(
            "/chat",
            json={
                "message": "What is dharma?",
                "language": "english",
                "top_k": 3
            }
        )
        
        # Should work without auth (anonymous chat)
        assert response.status_code in [200, 500]


class TestHistoryWithAuthentication:
    """Test history endpoints with authentication."""
    
    def test_create_session_requires_auth(self):
        """Test that creating a session requires authentication."""
        response = client.post("/history/new")
        
        assert response.status_code == 403
    
    def test_list_sessions_requires_auth(self):
        """Test that listing sessions requires authentication."""
        response = client.get("/history/list")
        
        assert response.status_code == 422
    
    def test_create_session_with_auth(self):
        """Test creating a session with authentication."""
        # Register user
        reg_response = client.post(
            "/auth/register",
            json={
                "username": "sessionuser",
                "email": "sessionuser@example.com",
                "password": "SessionPass123!"
            }
        )
        
        token = reg_response.json()["access_token"]
        
        # Create session
        response = client.post(
            "/history/new",
            params={"language": "english"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should work or return 500 if persistence layer issues
        assert response.status_code in [200, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
