"""OAuth token verification for Google and Apple sign-in."""

import jwt as pyjwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import settings


def verify_google_token(token: str) -> dict:
    """Verify a Google ID token and return user info.

    Returns dict with 'sub', 'email', and 'email_verified' keys.
    Raises ValueError if token is invalid.
    """
    try:
        idinfo = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_client_id,
        )
        if idinfo.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
            raise ValueError("Invalid issuer")
        if not idinfo.get("email_verified", False):
            raise ValueError("Email not verified by Google")
        return {
            "sub": idinfo["sub"],
            "email": idinfo["email"].lower().strip(),
        }
    except Exception as e:
        raise ValueError(f"Invalid Google token: {e}") from e


def verify_apple_token(identity_token: str) -> dict:
    """Verify an Apple identity token and return user info.

    Returns dict with 'sub' and 'email' keys.
    Raises ValueError if token is invalid.
    """
    try:
        # Decode without verification first to get the header
        header = pyjwt.get_unverified_header(identity_token)

        # Fetch Apple's public keys
        import httpx

        resp = httpx.get("https://appleid.apple.com/auth/keys", timeout=10)
        resp.raise_for_status()
        apple_keys = resp.json()

        # Find the matching key
        matching_key = None
        for key in apple_keys["keys"]:
            if key["kid"] == header["kid"]:
                matching_key = key
                break
        if matching_key is None:
            raise ValueError("No matching Apple public key found")

        public_key = pyjwt.algorithms.RSAAlgorithm.from_jwk(matching_key)

        payload = pyjwt.decode(
            identity_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.apple_client_id,
            issuer="https://appleid.apple.com",
        )

        email = payload.get("email", "").lower().strip()
        if not email:
            raise ValueError("No email in Apple token")

        return {
            "sub": payload["sub"],
            "email": email,
        }
    except pyjwt.ExpiredSignatureError:
        raise ValueError("Apple token has expired")
    except pyjwt.InvalidTokenError as e:
        raise ValueError(f"Invalid Apple token: {e}") from e
    except Exception as e:
        raise ValueError(f"Apple token verification failed: {e}") from e
