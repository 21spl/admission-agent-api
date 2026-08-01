from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from passlib.context import CryptContext
import jwt
from app.core.config import settings

# Explicitly select bcrypt for industry-standard password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt before saving it to Neon."""
    return pwd_context.hash(password)





def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compares incoming plain text login credentials against a saved hash."""
    return pwd_context.verify(plain_password, hashed_password)




def create_access_token(
    user_id: str, 
    user_type: str, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a secure cryptographically-signed JWT Access Token.
    Stores the user UUID inside the 'sub' claim and the user type inside 'type'.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Store identity tokens and scope constraints within the payload
    to_encode = {
        "exp": expire,
        "sub": str(user_id),
        "user_type": user_type
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


