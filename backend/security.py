"""PBKDF2 hashed passwords and opaque revocable sessions (never JWT in WebView)."""
import hashlib, hmac, os, secrets
from datetime import timedelta, timezone
from .models import utcnow

ROLES=('admin','director','project_manager','mep_lead','construction_lead','qa','engineer','viewer')
PROJECT_ROLES=ROLES[1:]

def password_hash(password: str) -> str:
    if len(password)<12: raise ValueError('Mật khẩu tối thiểu 12 ký tự')
    salt=secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,260000)
    return f'pbkdf2_sha256$260000${salt.hex()}${digest.hex()}'

def verify_password(password: str, encoded: str) -> bool:
    try:
        kind,n,salt,expected=encoded.split('$')
        if kind!='pbkdf2_sha256':return False
        digest=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),int(n))
        return hmac.compare_digest(digest,bytes.fromhex(expected))
    except (ValueError,TypeError): return False

def make_session(db,user_id):
    from .models import SessionToken
    token=secrets.token_urlsafe(36)
    db.add(SessionToken(user_id=user_id,token_hash=hashlib.sha256(token.encode()).hexdigest(),expires_at=utcnow()+timedelta(hours=8)))
    db.commit()
    return token
