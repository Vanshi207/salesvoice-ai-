from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from pydantic import BaseModel

TokenType = Literal["access", "refresh"]


class TokenPayload(BaseModel):
    sub: str
    role: str
    type: TokenType
    exp: int


class InvalidToken(Exception):
    pass


def create_token(user_id: str, role: str, token_type: TokenType,
                 secret: str, algorithm: str, expires_in: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_in).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, secret: str, algorithm: str,
                 expected_type: TokenType = "access") -> TokenPayload:
    try:
        data = jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.PyJWTError as e:
        raise InvalidToken(str(e)) from e
    payload = TokenPayload(**data)
    if payload.type != expected_type:
        raise InvalidToken(f"expected a {expected_type} token")
    return payload
