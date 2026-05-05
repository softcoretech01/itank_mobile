# auth_router.py
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import get_db_connection
import os
import hashlib
import binascii
import jwt
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production")
JWT_ALGORITHM = "HS256"
JWT_EXP_DAYS = int(os.getenv("JWT_EXP_DAYS", "1"))


# ------------------ MODELS ------------------

class RegisterRequest(BaseModel):
    name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    hod: Optional[str] = None
    supervisor: Optional[str] = None
    email: EmailStr
    login_name: str
    password: str
    role_id: int


class LoginRequest(BaseModel):
    login_name: str
    password: str


class LogoutRequest(BaseModel):
    token: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ------------------ HELPERS ------------------

def hash_password(password: str, salt: Optional[str] = None):
    if salt is None:
        salt = binascii.hexlify(os.urandom(16)).decode()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return binascii.hexlify(dk).decode(), salt


def create_jwt_token(payload: dict) -> str:
    expire = datetime.utcnow() + timedelta(days=JWT_EXP_DAYS)
    payload.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _get_token_subject_from_header(authorization: Optional[str]) -> Optional[int]:
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    try:
        payload = jwt.decode(parts[1], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload.get("emp_id"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ------------------ REGISTER ------------------

@router.post("/register")
def register_user(body: RegisterRequest):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Using stored procedure for registration
            # sp_RegisterUser handles login_name check, role check, emp_id generation and insertion
            pwd_hash, salt = hash_password(body.password)
            try:
                cursor.callproc("sp_RegisterUser", (
                    body.name, body.department, body.designation,
                    body.hod, body.supervisor, body.email, body.login_name,
                    pwd_hash, salt, body.role_id
                ))
                conn.commit()
                return {"success": True, "message": "User registered"}
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg:
                    return JSONResponse(status_code=409, content={"success": False, "message": error_msg})
                if "No such role" in error_msg:
                    return JSONResponse(status_code=400, content={"success": False, "message": error_msg})
                raise e
    finally:
        conn.close()


# ------------------ LOGIN ------------------

@router.post("/login")
def login_user(body: LoginRequest):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch user details using stored procedure
            cursor.callproc("sp_GetUserDetails", (body.login_name,))
            user = cursor.fetchone()

            if not user:
                return JSONResponse(status_code=401, content={"success": False, "message": "Invalid credentials"})

            pwd_hash, _ = hash_password(body.password, user["password_salt"])
            if pwd_hash != user["password_hash"]:
                return JSONResponse(status_code=401, content={"success": False, "message": "Password incorrect"})

            emp_id = user["emp_id"]
            role_id = user["role_id"]

            # Fetch web access permissions using stored procedure
            cursor.callproc("sp_GetUserRights", (role_id,))
            web_access = cursor.fetchall()

            # Manage session (force logout previous and create new) using stored procedure
            cursor.callproc("sp_ManageLoginSession", (emp_id, user["email"], user["login_name"]))

            token = create_jwt_token({
                "emp_id": emp_id,
                "email": user["email"],
                "login_name": user["login_name"]
            })

            conn.commit()
            return {"success": True, "message": "Login successful", "data": {"token": token, "role_id": role_id, "web_access": web_access, "emp_id": emp_id, "login_name": user["login_name"]}}

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
    )

    finally:
        conn.close()


# ------------------ LOGOUT ------------------

@router.post("/logout")
def logout_user(authorization: Optional[str] = Header(None), body: Optional[LogoutRequest] = None):
    token = authorization or (f"Bearer {body.token}" if body and body.token else None)

    try:
        emp_id = _get_token_subject_from_header(token)
    except HTTPException:
        return {"success": True}

    if not emp_id:
        return {"success": True}

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Use stored procedure for logout
            cursor.callproc("sp_LogoutUser", (emp_id,))
            conn.commit()
            return {"success": True}
    finally:
        conn.close()


# ------------------ CHANGE PASSWORD ------------------

@router.post("/change-password")
def change_password(body: ChangePasswordRequest, authorization: str = Header(...)):
    emp_id = _get_token_subject_from_header(authorization)
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check session and get user details using SP if needed, 
            # but here we can just reuse sp_GetUserDetails by login_name if we had it,
            # but we have emp_id. Let's just use sp_GetUserDetails for now if we can 
            # or just call a direct check.
            cursor.execute("SELECT 1 FROM login_sessions WHERE emp_id=%s AND still_logged_in=1", (emp_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=401, detail="Session expired")

            cursor.execute("SELECT * FROM users WHERE emp_id=%s", (emp_id,))
            user = cursor.fetchone()

            pwd_hash, _ = hash_password(body.current_password, user["password_salt"])
            if pwd_hash != user["password_hash"]:
                return JSONResponse(status_code=400, content={"success": False, "message": "Wrong password"})

            new_hash, new_salt = hash_password(body.new_password)
            # Use stored procedure for password update
            cursor.callproc("sp_ChangePassword", (emp_id, new_hash, new_salt))
            conn.commit()
            return {"success": True, "message": "Password updated"}
    finally:
        conn.close()


# ------------------ OPERATORS ------------------

@router.get("/operators")
def get_operators():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Use stored procedure for getting operators
            cursor.callproc("sp_GetOperators")
            return {"success": True, "data": cursor.fetchall()}
    finally:
        conn.close()
