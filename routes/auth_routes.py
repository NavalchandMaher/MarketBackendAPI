import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

from services.common.auth_service import AuthService, oauth2_scheme

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterPayload(BaseModel):
    full_name: str
    email: EmailStr
    mobile_number: Optional[str] = None
    password: str
    role: Optional[str] = "Trader"
    default_symbol: Optional[str] = "BTCUSDT"
    default_timeframe: Optional[str] = "5m"
    theme: Optional[str] = "dark"
    notification_settings: Optional[Dict[str, Any]] = None


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class RefreshPayload(BaseModel):
    refresh_token: str


class ForgotPasswordPayload(BaseModel):
    email: EmailStr


class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str


class ChangePasswordPayload(BaseModel):
    current_password: str
    new_password: str


@router.post("/register", status_code=201)
def register(payload: RegisterPayload):
    return AuthService.create_user(payload.model_dump())


@router.post("/login")
def login(payload: LoginPayload):
    return AuthService.login_user(str(payload.email), payload.password)


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    return {"success": True, "message": "Logout successful"}


@router.post("/refresh")
def refresh(payload: RefreshPayload):
    return AuthService.refresh_token(payload.refresh_token)


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordPayload):
    return {"success": True, "message": "Password reset instructions sent"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordPayload):
    return {"success": True, "message": "Password reset successful"}


@router.post("/change-password")
def change_password(payload: ChangePasswordPayload, user=Depends(AuthService.get_current_user)):
    logger.info(f"[ROUTES] Change password request for user: {user.get('email')}")
    
    # Verify current password
    if not AuthService._verify_password(payload.current_password, user.get("password", "")):
        logger.warning(f"[ROUTES] Change password failed - invalid current password for user: {user.get('email')}")
        raise HTTPException(status_code=401, detail="Invalid current password")
    
    # Update password
    AuthService.update_password(str(user["_id"]), payload.new_password)
    logger.info(f"[ROUTES] Password changed successfully for user: {user.get('email')}")
    
    return {"success": True, "message": "Password changed successfully"}
