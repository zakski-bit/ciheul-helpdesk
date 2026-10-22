import hashlib
import hmac
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .config import settings

def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _b64_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data.encode('utf-8'))

def hash_password(password: str) -> str:
    """Hash password using PBKDF2 HMAC SHA-256 with per-user random cryptographic salt."""
    import os
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with constant-time comparison supporting salted and legacy formats."""
    try:
        if "$" in hashed_password:
            salt, hash_val = hashed_password.split("$", 1)
            computed = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
            return hmac.compare_digest(computed, hash_val)
        else:
            # Fallback for legacy static-salt hashes
            legacy_salt = settings.SECRET_KEY[:16].encode('utf-8')
            computed = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), legacy_salt, 100000).hex()
            return hmac.compare_digest(computed, hashed_password)
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate self-contained standard HS256 JWT Token."""
    to_encode = data.copy()
    if expires_delta:
        expire = time.time() + expires_delta.total_seconds()
    else:
        expire = time.time() + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    to_encode.update({"exp": int(expire)})
    
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(to_encode, separators=(',', ':')).encode('utf-8'))
    
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(settings.SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify HS256 JWT Token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(settings.SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
        actual_sig = _b64_decode(sig_b64)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        payload_json = _b64_decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
        
        if "exp" in payload and time.time() > payload["exp"]:
            return None  # Token expired
        
        return payload
    except Exception:
        return None
