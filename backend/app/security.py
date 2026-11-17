import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .db import engine, one

bearer = HTTPBearer(auto_error=False)


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=32768,
                            r=8, p=1, maxmem=64 * 1024 * 1024)
    return f"{salt}:{digest.hex()}"


def verify_password(password, stored):
    return hmac.compare_digest(password_hash(password, stored.split(":")[0]), stored)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def current_staff(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if credentials is None:
        raise HTTPException(401, "請先登入", headers={"WWW-Authenticate": "Bearer"})
    hashed = token_hash(credentials.credentials)
    with engine.connect() as connection:
        staff = one(connection, """
            SELECT a.id, a.username, a.organization_id
            FROM sessions s JOIN staff_accounts a ON a.id = s.staff_id
            WHERE s.token_hash = :token AND s.expires_at > now()
              AND s.revoked_at IS NULL AND a.enabled
        """, token=hashed)
    if staff is None:
        raise HTTPException(401, "登入憑證已失效", headers={"WWW-Authenticate": "Bearer"})
    return {**staff, "token_hash": hashed}
