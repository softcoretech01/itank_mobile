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
            cursor.execute("SELECT 1 FROM users WHERE login_name=%s", (body.login_name,))
            if cursor.fetchone():
                return JSONResponse(status_code=409, content={"success": False, "message": "Login name already exists"})

            # Check if role_id exists in role_master
            cursor.execute("SELECT 1 FROM role_master WHERE role_id=%s", (body.role_id,))
            if not cursor.fetchone():
                return JSONResponse(status_code=400, content={"success": False, "message": "No such role present"})

            cursor.execute("SELECT COALESCE(MAX(emp_id),1000)+1 AS eid FROM users")
            emp_id = cursor.fetchone()["eid"]

            pwd_hash, salt = hash_password(body.password)

            cursor.execute("""
                INSERT INTO users (emp_id,name,department,designation,hod,supervisor,
                email,login_name,password_hash,password_salt,role_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                emp_id, body.name, body.department, body.designation,
                body.hod, body.supervisor, body.email, body.login_name,
                pwd_hash, salt, body.role_id
            ))
            conn.commit()
            return {"success": True, "message": "User registered"}
    finally:
        conn.close()


# ------------------ LOGIN ------------------

@router.post("/login")
def login_user(body: LoginRequest):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE BINARY login_name=%s", (body.login_name,))
            user = cursor.fetchone()

            if not user:
                return JSONResponse(status_code=401, content={"success": False, "message": "Invalid credentials"})

            pwd_hash, _ = hash_password(body.password, user["password_salt"])
            if pwd_hash != user["password_hash"]:
                return JSONResponse(status_code=401, content={"success": False, "message": "Password incorrect"})

            emp_id = user["emp_id"]
            role_id = user["role_id"]

            # Fetch web access permissions
            cursor.execute("""
                SELECT screen, edit_only, read_only
                FROM role_rights
                WHERE user_role_id = %s AND module_access = 'Web Application'
                AND (edit_only = 1 OR read_only = 1)
            """, (role_id,))
            web_access = cursor.fetchall()

            # 🔑 FORCE LOGOUT ALL PREVIOUS SESSIONS
            cursor.execute("UPDATE login_sessions SET still_logged_in=0 WHERE emp_id=%s", (emp_id,))

            # ✅ CREATE CLEAN SESSION
            cursor.execute("""
                INSERT INTO login_sessions (
                    emp_id, email, login_name, logged_in_at, still_logged_in
                )   
                VALUES (%s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE
                    still_logged_in = 1,
                    logged_in_at = VALUES(logged_in_at)
            """, (
                emp_id,
                user["email"],
                user["login_name"],
                datetime.utcnow()
            ))


            token = create_jwt_token({
                "emp_id": emp_id,
                "email": user["email"],
                "login_name": user["login_name"]
            })

            conn.commit()
            return {"success": True, "message": "Login successful", "data": {"token": token, "role_id": role_id, "web_access": web_access}}

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
            cursor.execute("UPDATE login_sessions SET still_logged_in=0 WHERE emp_id=%s", (emp_id,))
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
            cursor.execute("""
                SELECT 1 FROM login_sessions WHERE emp_id=%s AND still_logged_in=1
            """, (emp_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=401, detail="Session expired")

            cursor.execute("SELECT * FROM users WHERE emp_id=%s", (emp_id,))
            user = cursor.fetchone()

            pwd_hash, _ = hash_password(body.current_password, user["password_salt"])
            if pwd_hash != user["password_hash"]:
                return JSONResponse(status_code=400, content={"success": False, "message": "Wrong password"})

            new_hash, new_salt = hash_password(body.new_password)
            cursor.execute("""
                UPDATE users SET password_hash=%s,password_salt=%s WHERE emp_id=%s
            """, (new_hash, new_salt, emp_id))
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
            cursor.execute("SELECT emp_id,name FROM users WHERE role='operator'")
            return {"success": True, "data": cursor.fetchall()}
    finally:
        conn.close()
