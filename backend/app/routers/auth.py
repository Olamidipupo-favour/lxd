from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import secrets
from ..db import get_db
from ..models import AdminUser
from ..auth import verify_password, create_access_token, create_refresh_token, hash_password, get_current_admin
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginReq(BaseModel):
    email: EmailStr
    password: str


class SetupReq(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = "user"


class PasswordResetReq(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    password: str


@router.post("/setup")
async def setup(req: SetupReq, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AdminUser))
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Admin already exists")
    user = AdminUser(email=req.email.lower(), hashed_password=hash_password(req.password), first_name=req.first_name, last_name=req.last_name, role="admin", is_active=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"ok": True}


@router.get("/setup-status")
async def setup_status(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AdminUser.id).limit(1))
    return {"admin_exists": res.scalar_one_or_none() is not None}


@router.post("/login")
async def login(req: LoginReq, response: Response, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AdminUser).where(AdminUser.email == req.email.lower()))
    user = res.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user.last_login_at = datetime.utcnow()
    await db.commit()
    access = create_access_token({"sub": user.email})
    refresh = create_refresh_token({"sub": user.email})
    response.set_cookie("access_token", access, httponly=True, secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE, max_age=settings.JWT_ACCESS_TTL_MIN * 60)
    response.set_cookie("refresh_token", refresh, httponly=True, secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE, max_age=settings.JWT_REFRESH_TTL_DAYS * 24 * 3600)
    return {"ok": True, "email": user.email}


@router.get("/me")
async def me(user: AdminUser = Depends(get_current_admin)):
    return {"email": user.email, "id": str(user.id), "first_name": user.first_name, "last_name": user.last_name, "role": user.role}


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    res = await db.execute(select(AdminUser).order_by(AdminUser.created_at.desc()))
    users = []
    for u in res.scalars():
        users.append({
            "id": str(u.id),
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        })
    return {"users": users}


@router.post("/users")
async def create_user(req: UserCreate, db: AsyncSession = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    res = await db.execute(select(AdminUser).where(AdminUser.email == req.email.lower()))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = AdminUser(email=req.email.lower(), hashed_password=hash_password(req.password), first_name=req.first_name, last_name=req.last_name, role=req.role or "user", is_active=True)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"ok": True, "id": str(new_user.id)}


@router.put("/users/{user_id}")
async def update_user(user_id: str, req: dict, db: AsyncSession = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    from uuid import UUID
    try:
        res = await db.execute(select(AdminUser).where(AdminUser.id == UUID(user_id)))
        target = res.scalar_one_or_none()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if "first_name" in req:
        target.first_name = req["first_name"]
    if "last_name" in req:
        target.last_name = req["last_name"]
    if "role" in req:
        target.role = req["role"]
    if "is_active" in req:
        target.is_active = bool(req["is_active"])
    if "password" in req and req["password"]:
        target.hashed_password = hash_password(req["password"])
    await db.commit()
    return {"ok": True}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    from uuid import UUID
    try:
        res = await db.execute(select(AdminUser).where(AdminUser.id == UUID(user_id)))
        target = res.scalar_one_or_none()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await db.delete(target)
    await db.commit()
    return {"ok": True}


@router.post("/reset-password")
async def request_password_reset(req: PasswordResetReq, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AdminUser).where(AdminUser.email == req.email.lower()))
    user = res.scalar_one_or_none()
    if not user:
        return {"ok": True}
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    await db.commit()
    return {"ok": True, "token": token}


@router.post("/reset-password/confirm")
async def confirm_password_reset(req: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AdminUser).where(AdminUser.password_reset_token == req.token))
    user = res.scalar_one_or_none()
    if not user or not user.password_reset_expires or user.password_reset_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user.hashed_password = hash_password(req.password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.commit()
    return {"ok": True}
