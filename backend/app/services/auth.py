"""Authentication service for JWT token management and password hashing."""

import datetime
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import BlacklistedToken, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt-hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: The plaintext password to check.
        hashed_password: The bcrypt hash to verify against.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    """Create a short-lived JWT access token for a user.

    Args:
        user_id: The user's primary key to encode in the token.

    Returns:
        The encoded JWT access token string.
    """
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
    """Create a long-lived JWT refresh token for a user.

    Args:
        user_id: The user's primary key to encode in the token.

    Returns:
        The encoded JWT refresh token string.
    """
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

    Args:
        token: The JWT token string to decode.
        expected_type: Expected token type ('access' or 'refresh').
        db: Optional database session for blacklist checking.

    Returns:
        The user ID extracted from the token.

    Raises:
        HTTPException: 401 if the token is invalid, expired, wrong type, or blacklisted.
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token blacklist
    jti = payload.get("jti")
    if jti and db:
        blacklisted = db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first()
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

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
    """FastAPI dependency that extracts and validates the current authenticated user.

    Args:
        token: The Bearer token from the Authorization header.
        db: Database session for user lookup and token validation.

    Returns:
        The authenticated active User.

    Raises:
        HTTPException: 401 if not authenticated or user not found.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_token(token, expected_type="access", db=db)
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """FastAPI dependency that optionally extracts the current user.

    Returns None instead of raising an error when no valid token is provided.

    Args:
        token: The optional Bearer token from the Authorization header.
        db: Database session for user lookup and token validation.

    Returns:
        The authenticated active User, or None if not authenticated.
    """
    if token is None:
        return None
    try:
        user_id = decode_token(token, expected_type="access", db=db)
    except HTTPException:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
