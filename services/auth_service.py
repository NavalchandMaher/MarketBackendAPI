import os
import secrets
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from bson import ObjectId
from bson.errors import InvalidId

from db.mongodb import users, settings

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class AuthService:
    @staticmethod
    def _hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    @staticmethod
    def _create_token(subject: str, expires_delta: timedelta) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_access_token(subject: str) -> str:
        return AuthService._create_token(subject, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    @staticmethod
    def create_refresh_token(subject: str) -> str:
        return AuthService._create_token(subject, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            logger.debug(f"[AUTH] Token decoded successfully. Subject: {payload.get('sub')}")
            return payload
        except JWTError as exc:
            logger.error(f"[AUTH] Token decode failed: {str(exc)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid or expired token"
            ) from exc

    @staticmethod
    def _string_to_object_id(user_id_str: str) -> Optional[ObjectId]:
        """
        Safely convert a string to MongoDB ObjectId.
        Returns None if the string is not a valid ObjectId.
        """
        try:
            return ObjectId(user_id_str)
        except InvalidId:
            logger.warning(f"Invalid ObjectId format: {user_id_str}")
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        return users.find_one({"email": email.lower()})

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by ID (string representation of ObjectId).
        Converts the string back to ObjectId for MongoDB query.
        """
        logger.debug(f"[AUTH] Looking up user by ID: {user_id}")
        
        # Convert string to ObjectId
        object_id = AuthService._string_to_object_id(user_id)
        if not object_id:
            logger.warning(f"[AUTH] Invalid user ID format: {user_id}")
            return None
        
        try:
            user = users.find_one({"_id": object_id})
            if user:
                logger.debug(f"[AUTH] User found: {user.get('email')}")
            else:
                logger.warning(f"[AUTH] User not found for ObjectId: {object_id}")
            return user
        except Exception as e:
            logger.error(f"[AUTH] Error retrieving user: {str(e)}")
            return None

    ALLOWED_ROLES = {"Admin", "Trader"}

    @staticmethod
    def create_user(payload: Dict[str, Any]) -> Dict[str, Any]:
        email = payload.get("email", "").strip().lower()
        logger.debug(f"[AUTH] Attempting to create user: {email}")
        
        if AuthService.get_user_by_email(email):
            logger.warning(f"[AUTH] Registration failed - email already exists: {email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        requested_role = str(payload.get("role", "Trader")).title()
        if requested_role not in AuthService.ALLOWED_ROLES:
            requested_role = "Trader"

        if requested_role == "Admin":
            logger.debug("[AUTH] Admin registration requested")
            if users.count_documents({"role": "Admin"}, limit=1) > 0:
                logger.warning("[AUTH] Admin registration blocked - admin already exists")
                raise HTTPException(
                    status_code=403,
                    detail="Only one Admin user is allowed",
                )

        user_doc = {
            "user_id": str(uuid.uuid4()),
            "full_name": payload.get("full_name", ""),
            "email": email,
            "mobile_number": payload.get("mobile_number", ""),
            "password": AuthService._hash_password(payload["password"]),
            "role": requested_role,
            "status": "ACTIVE",
            "created_date": datetime.utcnow(),
            "last_login": None,
            "default_symbol": payload.get("default_symbol", "BTCUSDT"),
            "default_timeframe": payload.get("default_timeframe", "5m"),
            "theme": payload.get("theme", "dark"),
            "notification_settings": payload.get("notification_settings", {"email": True, "telegram": False, "push": True}),
        }
        
        try:
            result = users.insert_one(user_doc)
            user_doc["id"] = str(result.inserted_id)
            user_doc.pop("_id", None)
            logger.info(f"[AUTH] User created successfully: {email} (ObjectId: {result.inserted_id})")
            return user_doc
        except Exception as e:
            logger.error(f"[AUTH] Failed to create user: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create user")

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        user = AuthService.get_user_by_email(email)
        if not user:
            logger.warning(f"[AUTH] Authentication failed - user not found: {email}")
            return None
        if not AuthService._verify_password(password, user.get("password", "")):
            logger.warning(f"[AUTH] Authentication failed - invalid password: {email}")
            return None
        if str(user.get("status", "ACTIVE")).upper() != "ACTIVE":
            logger.warning(f"[AUTH] Authentication failed - inactive account: {email}")
            return None
        logger.debug(f"[AUTH] User authenticated successfully: {email}")
        return user

    @staticmethod
    def login_user(email: str, password: str) -> Dict[str, Any]:
        logger.info(f"[AUTH] Login attempt: {email}")
        user = AuthService.authenticate_user(email, password)
        if not user:
            logger.warning(f"[AUTH] Login failed - invalid credentials or inactive account: {email}")
            raise HTTPException(status_code=401, detail="Invalid credentials or inactive account")
        
        try:
            # Update last login
            users.update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.utcnow()}})
            logger.debug(f"[AUTH] Updated last_login for user: {email}")
            
            # Create tokens using the ObjectId (convert to string for JWT)
            user_object_id = str(user["_id"])
            access_token = AuthService.create_access_token(user_object_id)
            refresh_token = AuthService.create_refresh_token(user_object_id)
            
            logger.info(f"[AUTH] Login successful: {email} (ObjectId: {user_object_id})")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "id": user_object_id,
                    "user_id": user.get("user_id"),
                    "full_name": user.get("full_name"),
                    "email": user.get("email"),
                    "role": user.get("role"),
                    "default_symbol": user.get("default_symbol"),
                    "default_timeframe": user.get("default_timeframe"),
                    "theme": user.get("theme"),
                },
            }
        except Exception as e:
            logger.error(f"[AUTH] Login error: {str(e)}")
            raise HTTPException(status_code=500, detail="Login failed")

    @staticmethod
    def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
        """
        Extract and verify JWT token, then retrieve the authenticated user from MongoDB.
        This is the main dependency injection function for protected endpoints.
        """
        logger.debug(f"[AUTH] Processing authentication token")
        
        # Decode the token
        payload = AuthService.decode_token(token)
        user_id_str = payload.get("sub")
        
        if not user_id_str:
            logger.error("[AUTH] Token has no subject (user_id)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user identifier"
            )
        
        logger.debug(f"[AUTH] Token subject (user_id): {user_id_str}")
        
        # Retrieve user from database
        user = AuthService.get_user_by_id(user_id_str)
        if not user:
            logger.error(f"[AUTH] User not found in database for ObjectId: {user_id_str}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if str(user.get("status", "ACTIVE")).upper() != "ACTIVE":
            logger.warning(f"[AUTH] Access denied for inactive user: {user.get('email')}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )
        
        logger.debug(f"[AUTH] Authentication successful for user: {user.get('email')}")
        return user

    @staticmethod
    def get_optional_current_user(authorization: Optional[str] = Header(default=None)) -> Optional[Dict[str, Any]]:
        """
        Optionally extract user from Authorization header if present.
        Returns None if no valid token is provided.
        """
        if not authorization or not authorization.startswith("Bearer "):
            logger.debug("[AUTH] No Bearer token provided")
            return None
        
        token = authorization.split(" ", 1)[1].strip()
        try:
            payload = AuthService.decode_token(token)
            user_id_str = payload.get("sub")
            if not user_id_str:
                logger.warning("[AUTH] Optional token has no subject")
                return None
            
            user = AuthService.get_user_by_id(user_id_str)
            if user:
                logger.debug(f"[AUTH] Optional user authenticated: {user.get('email')}")
            else:
                logger.warning(f"[AUTH] Optional user not found for ObjectId: {user_id_str}")
            return user
        except HTTPException:
            logger.debug("[AUTH] Optional token validation failed (expected)")
            return None

    @staticmethod
    def require_role(*roles: str):
        def dependency(user: Dict[str, Any] = Depends(AuthService.get_current_user)) -> Dict[str, Any]:
            if user.get("role") not in roles:
                raise HTTPException(status_code=403, detail="Forbidden")
            return user
        return dependency

    @staticmethod
    def update_password(user_id: str, new_password: str) -> None:
        """
        Update a user's password.
        user_id should be the string representation of ObjectId.
        """
        logger.debug(f"[AUTH] Updating password for user: {user_id}")
        
        object_id = AuthService._string_to_object_id(user_id)
        if not object_id:
            logger.error(f"[AUTH] Invalid user ID format for password update: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        try:
            hashed_password = AuthService._hash_password(new_password)
            result = users.update_one({"_id": object_id}, {"$set": {"password": hashed_password}})
            
            if result.modified_count == 0:
                logger.warning(f"[AUTH] Password update failed - user not found: {user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            
            logger.info(f"[AUTH] Password updated successfully for user: {user_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[AUTH] Error updating password: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update password")

    @staticmethod
    def refresh_token(refresh_token: str) -> Dict[str, Any]:
        """
        Use a refresh token to get a new access token.
        """
        logger.info("[AUTH] Token refresh attempt")
        
        try:
            payload = AuthService.decode_token(refresh_token)
            user_id_str = payload.get("sub")
            
            if not user_id_str:
                logger.error("[AUTH] Refresh token has no subject")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            user = AuthService.get_user_by_id(user_id_str)
            if not user:
                logger.error(f"[AUTH] User not found during refresh: {user_id_str}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            access_token = AuthService.create_access_token(str(user["_id"]))
            logger.info(f"[AUTH] Token refreshed successfully for user: {user.get('email')}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[AUTH] Token refresh failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
