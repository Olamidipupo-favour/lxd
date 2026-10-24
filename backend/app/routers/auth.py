from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
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


@router.post("/setup")
async def setup(req: SetupReq, db: AsyncSession = Depends(get_db)):
    # only allow if no admin exists
    res = await db.execute(select(AdminUser))
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Admin already exists")
    user = AdminUser(email=req.email.lower(), hashed_password=hash_password(req.password), is_active=True)
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
    access = create_access_token({"sub": user.email})
    refresh = create_refresh_token({"sub": user.email})
    response.set_cookie("access_token", access, httponly=True, secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE, max_age=settings.JWT_ACCESS_TTL_MIN * 60)
    response.set_cookie("refresh_token", refresh, httponly=True, secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE, max_age=settings.JWT_REFRESH_TTL_DAYS * 24 * 3600)
    return {"ok": True, "email": user.email}


@router.get("/me")
async def me(user: AdminUser = Depends(get_current_admin)):
    return {"email": user.email, "id": str(user.id)}
