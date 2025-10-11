from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, exceptions, ExpiredSignatureError
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .config import settings
from .database import get_db
from .models.token_blacklist import TokenBlacklist
from .models.user import User as UserModel
from .security import encrypt_password, decrypt_password

# Configure logger
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None

class UserInDB(UserModel):
    __allow_unmapped__ = True
    hashed_password: str

def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    current_time = datetime.now(timezone.utc)
    if expires_delta:
        expire = current_time + expires_delta
    else:
        expire = current_time + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": current_time,
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    current_time = datetime.now(timezone.utc)
    if expires_delta:
        expire = current_time + expires_delta
    else:
        expire = current_time + timedelta(days=7)
    to_encode.update({
        "exp": expire,
        "iat": current_time,
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

async def get_user_from_token(token: str, db: AsyncSession) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    expired_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")
        if username is None or jti is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except ExpiredSignatureError:
        import logging
        logger = logging.getLogger("app.auth")
        logger.error(f"Auth validation: Expired signature.")
        raise expired_token_exception
    except exceptions.JWSSignatureError:
        import logging
        logger = logging.getLogger("app.auth")
        logger.error(f"Auth validation: SIGNATURE MISMATCH. Check SECRET_KEY format in .env file.")
        raise credentials_exception
    except JWTError as e:
        import logging
        logger = logging.getLogger("app.auth")
        logger.error(f"JWT Validation issue: {str(e)}")
        raise credentials_exception

    if token_data.username is None:
        raise credentials_exception
    user = await db.get(UserModel, int(token_data.username))
    if user is None:
        import logging
        logger = logging.getLogger("app.auth")
        logger.error(f"User not found for ID: {token_data.username}")
        raise credentials_exception

    # Check if token JTI is blacklisted
    blacklisted_jti = await db.execute(
        select(TokenBlacklist).filter(TokenBlacklist.jti == jti)
    )
    if blacklisted_jti.scalar_one_or_none():
        import logging
        logger = logging.getLogger("app.auth")
        logger.error(f"Auth validation: JTI is blacklisted: {jti}")
        raise credentials_exception

    # Check if user's password has been changed after token was issued
    iat = payload.get("iat")
    if user.password_changed_at and iat is not None and iat < user.password_changed_at.timestamp():
        raise credentials_exception

    # Check if user's token has been revoked before
    if user.revoked_before and iat is not None and iat < user.revoked_before.timestamp():
        raise credentials_exception

    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    return await get_user_from_token(token, db)

async def get_current_active_user(current_user: UserModel = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

import bcrypt
import re
from typing import List, Tuple

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        # Log error without sensitive data
        logger.error(f"Password verification failed: {type(e).__name__}")
        return False

# 🔒 PASSWORD VALIDATION UTILITIES
class PasswordValidationError(Exception):
    """Custom exception for password validation errors"""
    pass

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength based on security requirements.

    Returns:
        Tuple[bool, List[str]]: (is_valid, error_messages)

    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    - No common weak patterns
    - No whitespace
    """
    errors = []

    # 1. Length requirement
    if len(password) < 8:
        errors.append("Password minimal 8 karakter")

    # 2. Uppercase letter requirement
    if not re.search(r'[A-Z]', password):
        errors.append("Password harus mengandung minimal 1 huruf besar (A-Z)")

    # 3. Lowercase letter requirement
    if not re.search(r'[a-z]', password):
        errors.append("Password harus mengandung minimal 1 huruf kecil (a-z)")

    # 4. Digit requirement
    if not re.search(r'\d', password):
        errors.append("Password harus mengandung minimal 1 angka (0-9)")

    # 5. Special character requirement
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password harus mengandung minimal 1 karakter spesial (!@#$%^&*(),.?\"{}|<>)")

    # 6. No whitespace
    if re.search(r'\s', password):
        errors.append("Password tidak boleh mengandung spasi atau whitespace")

    # 7. No common weak patterns
    weak_patterns = [
        r'123456', r'password', r'admin', r'qwerty',
        r'abc123', r'letmein', r'welcome', r'login'
    ]

    password_lower = password.lower()
    for pattern in weak_patterns:
        if pattern in password_lower:
            errors.append(f"Password tidak boleh mengandung pola umum seperti '{pattern}'")
            break

    # 8. No sequential characters
    if re.search(r'(.)\1{2,}', password):  # 3+ repeated chars
        errors.append("Password tidak boleh mengandung karakter berulang (contoh: aaa, 111)")

    # 9. No keyboard sequences
    keyboard_sequences = ['qwerty', 'asdf', '1234', 'abcd']
    for seq in keyboard_sequences:
        if seq in password_lower:
            errors.append(f"Password tidak boleh mengandung urutan keyboard seperti '{seq}'")
            break

    return len(errors) == 0, errors

def get_password_requirements() -> dict:
    """
    Get password requirements for user guidance.
    Returns dict with requirements for frontend display.
    """
    return {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special": True,
        "no_whitespace": True,
        "no_common_patterns": True,
        "no_repeated_chars": True,
        "allowed_special_chars": "!@#$%^&*(),.?\":{}|<>",
        "examples_valid": [
            "SecureP@ss123",
            "Billing2024!",
            "MyP@ssw0rd",
            "Art@com2024"
        ],
        "examples_invalid": [
            "password123",
            "admin",
            "12345678",
            "qwerty",
            "my password"
        ]
    }

def is_strong_password(password: str) -> bool:
    """
    Quick check if password meets minimum requirements.
    Returns boolean for simple validation.
    """
    is_valid, _ = validate_password_strength(password)
    return is_valid

async def authenticate_user(email: str, password: str, db: AsyncSession):
    stmt = select(UserModel).where(UserModel.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password):
        return None

    return user

async def get_current_user_with_permissions(
    required_permissions: list[str],
    current_user: UserModel = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    if current_user.role and current_user.role.name.lower() == "admin":
        return current_user

    user_permissions = (
        {
            permission.name
            for permission in current_user.role.permissions
        }
        if current_user.role and current_user.role.permissions
        else set()
    )

    if not all(perm in user_permissions for perm in required_permissions):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return current_user

async def get_current_active_user_for_refresh_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    if token_data.username is None:
        raise credentials_exception
    user = await db.get(UserModel, int(token_data.username))
    if user is None:
        raise credentials_exception

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid token type")

    blacklisted_token = await db.execute(
        select(TokenBlacklist).filter(TokenBlacklist.jti == payload.get("jti"))
    )
    if blacklisted_token.scalar_one_or_none():
        raise credentials_exception

    iat = payload.get("iat")
    if user.password_changed_at and iat is not None and iat < user.password_changed_at.timestamp():
        raise credentials_exception

    return user

def has_permission(required_permission: str):
    def permission_checker(current_user: UserModel = Depends(get_current_active_user)):
        if current_user.role and current_user.role.name.lower() == "admin":
            return True

        user_permissions = (
            {
                permission.name
                for permission in current_user.role.permissions
            }
            if current_user.role and current_user.role.permissions
            else set()
        )

        if required_permission not in user_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        
        return True
    return permission_checker
