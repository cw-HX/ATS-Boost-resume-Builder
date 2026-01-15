"""
Utility functions for input sanitization and validation.
"""
import re
import html
from typing import Any, Dict, List, Optional
import bleach


def sanitize_string(text: str) -> str:
    """
    Sanitize a string by removing potentially dangerous content.
    
    Args:
        text: Input string
        
    Returns:
        Sanitized string
    """
    if not text:
        return ""
    
    # HTML escape
    text = html.escape(text)
    
    # Remove any script tags that might have slipped through
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove other potentially dangerous HTML
    text = bleach.clean(text, tags=[], strip=True)
    
    return text.strip()


def sanitize_email(email: str) -> str:
    """
    Sanitize and validate email address.
    
    Args:
        email: Input email
        
    Returns:
        Sanitized email or empty string if invalid
    """
    if not email:
        return ""
    
    email = email.lower().strip()
    
    # Basic email pattern validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    
    return ""


def sanitize_url(url: str) -> str:
    """
    Sanitize and validate URL.
    
    Args:
        url: Input URL
        
    Returns:
        Sanitized URL or empty string if invalid
    """
    if not url:
        return ""
    
    url = url.strip()
    
    # Only allow http and https protocols
    if not url.startswith(('http://', 'https://')):
        if url.startswith('www.'):
            url = 'https://' + url
        else:
            return ""
    
    # Basic URL pattern validation
    pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    if re.match(pattern, url):
        return url
    
    return ""


def sanitize_phone(phone: str) -> str:
    """
    Sanitize phone number.
    
    Args:
        phone: Input phone number
        
    Returns:
        Sanitized phone number
    """
    if not phone:
        return ""
    
    # Keep only digits, spaces, hyphens, parentheses, and plus sign
    sanitized = re.sub(r'[^\d\s\-\+\(\)]', '', phone)
    return sanitized.strip()


def sanitize_dict(data: Dict[str, Any], keys_to_sanitize: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Recursively sanitize string values in a dictionary.
    
    Args:
        data: Input dictionary
        keys_to_sanitize: Optional list of keys to sanitize (sanitizes all if None)
        
    Returns:
        Sanitized dictionary
    """
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            if keys_to_sanitize is None or key in keys_to_sanitize:
                sanitized[key] = sanitize_string(value)
            else:
                sanitized[key] = value
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, keys_to_sanitize)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_string(item) if isinstance(item, str) else 
                sanitize_dict(item, keys_to_sanitize) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength and return detailed feedback.
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with validation results
    """
    issues = []
    score = 0
    
    # Length check
    if len(password) >= 8:
        score += 20
    else:
        issues.append("Password must be at least 8 characters")
    
    if len(password) >= 12:
        score += 10
    
    # Uppercase check
    if re.search(r'[A-Z]', password):
        score += 20
    else:
        issues.append("Password must contain at least one uppercase letter")
    
    # Lowercase check
    if re.search(r'[a-z]', password):
        score += 20
    else:
        issues.append("Password must contain at least one lowercase letter")
    
    # Digit check
    if re.search(r'\d', password):
        score += 15
    else:
        issues.append("Password must contain at least one digit")
    
    # Special character check
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 15
    else:
        issues.append("Password must contain at least one special character")
    
    return {
        "valid": len(issues) == 0,
        "score": score,
        "strength": "weak" if score < 50 else "medium" if score < 80 else "strong",
        "issues": issues
    }
