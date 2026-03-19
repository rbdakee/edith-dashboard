import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(secret: str, expires_hours: int = 24) -> str:
    payload = {"sub": "doszhan", "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours)}
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_jwt(token: str, secret: str = "") -> bool:
    if not token or not secret:
        return False
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
        return True
    except JWTError:
        return False
