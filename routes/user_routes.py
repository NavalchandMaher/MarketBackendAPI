import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from bson import ObjectId
from bson.errors import InvalidId

from services.common.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


class UserProfilePayload(BaseModel):
    full_name: Optional[str] = None
    mobile_number: Optional[str] = None
    default_symbol: Optional[str] = None
    default_timeframe: Optional[str] = None
    theme: Optional[str] = None
    notification_settings: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


@router.get("/me")
def me(user=Depends(AuthService.get_current_user)):
    logger.debug(f"[ROUTES] Get /users/me for: {user.get('email')}")
    return {
        "id": str(user["_id"]),
        "user_id": user.get("user_id"),
        "full_name": user.get("full_name"),
        "email": user.get("email"),
        "mobile_number": user.get("mobile_number"),
        "role": user.get("role"),
        "status": user.get("status"),
        "created_date": user.get("created_date"),
        "last_login": user.get("last_login"),
        "default_symbol": user.get("default_symbol"),
        "default_timeframe": user.get("default_timeframe"),
        "theme": user.get("theme"),
        "notification_settings": user.get("notification_settings"),
    }


@router.put("/me")
def update_me(payload: UserProfilePayload, user=Depends(AuthService.get_current_user)):
    logger.debug(f"[ROUTES] Update /users/me for: {user.get('email')}")
    from db.mongodb import users
    update = {k: v for k, v in payload.model_dump(exclude_none=True).items() if v is not None}
    
    if not update:
        logger.debug(f"[ROUTES] No updates provided for user: {user.get('email')}")
        return {"success": True, "message": "No updates provided"}
    
    users.update_one({"_id": user["_id"]}, {"$set": update})
    logger.info(f"[ROUTES] User profile updated: {user.get('email')}")
    return {"success": True, "message": "Profile updated"}


@router.get("")
def list_users(user=Depends(AuthService.require_role("Admin"))):
    logger.debug(f"[ROUTES] Admin list_users request")
    from db.mongodb import users as user_collection
    docs = list(user_collection.find({}, {"password": 0}))
    return [{"id": str(doc["_id"]), **{k: v for k, v in doc.items() if k != "_id"}} for doc in docs]


@router.get("/{user_id}")
def get_user(user_id: str, user=Depends(AuthService.require_role("Admin"))):
    logger.debug(f"[ROUTES] Admin get_user request for: {user_id}")
    from db.mongodb import users as user_collection
    
    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        logger.warning(f"[ROUTES] Invalid user_id format: {user_id}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    doc = user_collection.find_one({"_id": object_id}, {"password": 0})
    if not doc:
        logger.warning(f"[ROUTES] User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.put("/{user_id}")
def update_user(user_id: str, payload: UserProfilePayload, user=Depends(AuthService.require_role("Admin"))):
    logger.debug(f"[ROUTES] Admin update_user request for: {user_id}")
    from db.mongodb import users as user_collection
    
    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        logger.warning(f"[ROUTES] Invalid user_id format: {user_id}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    update = {k: v for k, v in payload.model_dump(exclude_none=True).items() if v is not None}
    
    if not update:
        logger.debug(f"[ROUTES] No updates provided for user: {user_id}")
        return {"success": True, "message": "No updates provided"}

    if "status" in update:
        update["status"] = str(update["status"]).upper()
        if update["status"] not in {"ACTIVE", "DISABLED"}:
            raise HTTPException(status_code=400, detail="Invalid status value")
        if str(user_id) == str(user["_id"]) and update["status"] == "DISABLED":
            raise HTTPException(status_code=403, detail="Admin cannot disable own account")
    
    result = user_collection.update_one({"_id": object_id}, {"$set": update})
    
    if result.matched_count == 0:
        logger.warning(f"[ROUTES] User not found for update: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info(f"[ROUTES] User updated: {user_id}")
    return {"success": True, "message": "User updated"}


@router.delete("/{user_id}")
def delete_user(user_id: str, user=Depends(AuthService.require_role("Admin"))):
    logger.debug(f"[ROUTES] Admin delete_user request for: {user_id}")
    from db.mongodb import users as user_collection
    
    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        logger.warning(f"[ROUTES] Invalid user_id format: {user_id}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    result = user_collection.delete_one({"_id": object_id})
    
    if result.deleted_count == 0:
        logger.warning(f"[ROUTES] User not found for deletion: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info(f"[ROUTES] User deleted: {user_id}")
    return {"success": True}
