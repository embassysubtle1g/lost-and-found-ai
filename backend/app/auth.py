import secrets

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from .db import engine, one, query
from .security import current_staff, password_hash, token_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
DUMMY_PASSWORD = password_hash(secrets.token_hex(24))


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=160)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=160)
    new_password: str = Field(min_length=10, max_length=160)


class Organization(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=240)
    phone: str = Field(min_length=1, max_length=50)


@router.post("/login")
def login(data: Login):
    with engine.begin() as connection:
        account = one(connection, """
            SELECT id, password_hash, enabled FROM staff_accounts
            WHERE username = :username FOR UPDATE
        """, username=data.username)
        valid = verify_password(data.password, account.password_hash if account else DUMMY_PASSWORD)
        if account is None or not valid or not account.enabled:
            raise HTTPException(401, "帳號或密碼錯誤")
        token = secrets.token_urlsafe(32)
        query(connection, """
            INSERT INTO sessions(token_hash, staff_id, expires_at)
            VALUES (:token, :staff, now() + interval '8 hours')
        """, token=token_hash(token), staff=account.id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(staff=Depends(current_staff)):
    with engine.connect() as connection:
        organization = one(connection, """
            SELECT id, name, address, phone FROM organizations WHERE id = :id
        """, id=staff["organization_id"])
    return {"id": staff["id"], "username": staff["username"], "organization": dict(organization)}


@router.post("/logout", status_code=204)
def logout(staff=Depends(current_staff)):
    with engine.begin() as connection:
        query(connection, "UPDATE sessions SET revoked_at = now() WHERE token_hash = :token",
              token=staff["token_hash"])
    return Response(status_code=204)


@router.put("/password", status_code=204)
def change_password(data: PasswordChange, staff=Depends(current_staff)):
    with engine.begin() as connection:
        account = one(connection, "SELECT password_hash FROM staff_accounts WHERE id = :id FOR UPDATE",
                      id=staff["id"])
        if not verify_password(data.current_password, account.password_hash):
            raise HTTPException(400, "原密碼不正確")
        query(connection, "UPDATE staff_accounts SET password_hash = :hash WHERE id = :id",
              hash=password_hash(data.new_password), id=staff["id"])
        query(connection, "UPDATE sessions SET revoked_at = now() WHERE staff_id = :id",
              id=staff["id"])
    return Response(status_code=204)


@router.put("/organization")
def update_organization(data: Organization, staff=Depends(current_staff)):
    from sqlalchemy.exc import IntegrityError

    try:
        with engine.begin() as connection:
            organization = one(connection, """
                UPDATE organizations SET name = :name, address = :address, phone = :phone
                WHERE id = :id RETURNING id, name, address, phone
            """, id=staff["organization_id"], **data.model_dump())
    except IntegrityError as exc:
        raise HTTPException(409, "機構名稱已存在") from exc
    return dict(organization)
