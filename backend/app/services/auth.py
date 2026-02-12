"""Authentication service: JWT creation, validation, password hashing."""

import datetime
import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.exceptions import AuthError
from app.models import BlacklistedToken, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    """Create a short-lived JWT access token for the given user."""
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": expire,
            "type": "access",
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "jti": str(uuid.uuid4()),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_refresh_token(user_id: int) -> str:
    """Create a long-lived JWT refresh token for the given user."""
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=settings.refresh_token_expire_days
    )
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "jti": str(uuid.uuid4()),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_token(token: str, expected_type: str = "access", db: Session | None = None) -> int:
    """Decode and validate a JWT token, returning the user ID.

    Raises AuthError on invalid, expired, revoked, or wrong-type tokens.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except JWTError:
        raise AuthError(message="Invalid or expired token")
    if payload.get("type") != expected_type:
        raise AuthError(message="Invalid token type")
    user_id = payload.get("sub")
    if user_id is None:
        raise AuthError(message="Invalid token")

    # Check token blacklist
    jti = payload.get("jti")
    if jti and db:
        blacklisted = db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first()
        if blacklisted:
            raise AuthError(message="Token has been revoked")

    return int(user_id)


def blacklist_token(token: str, db: Session) -> None:
    """Add a token's JTI to the blacklist."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
        jti = payload.get("jti")
        if jti:
            existing = db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first()
            if not existing:
                db.add(BlacklistedToken(jti=jti))
                db.commit()
    except JWTError:
        pass  # Token is already invalid, no need to blacklist


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: extract and validate the current authenticated user."""
    if token is None:
        raise AuthError(message="Not authenticated")
    user_id = decode_token(token, expected_type="access", db=db)
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        raise AuthError(message="User not found")
    return user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """FastAPI dependency: return the current user if authenticated, else None."""
    if token is None:
        return None
    try:
        user_id = decode_token(token, expected_type="access", db=db)
    except AuthError:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
