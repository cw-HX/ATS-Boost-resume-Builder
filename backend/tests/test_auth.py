"""
Unit tests for authentication.
"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.core.security import hash_password, verify_password, create_access_token, decode_token


class TestPasswordHashing:
    """Tests for password hashing functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Tests for JWT token functions."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "test_user_id"}
        token = create_access_token(data)
        
        assert token is not None
        assert len(token) > 0
    
    def test_decode_valid_token(self):
        """Test decoding valid token."""
        data = {"sub": "test_user_id"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == "test_user_id"
        assert payload["type"] == "access"
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = decode_token(invalid_token)
        
        assert payload is None
