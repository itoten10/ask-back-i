import jwt

from app.core.security import (
    create_access_token,
    hash_password,
    now_utc,
    verify_password,
)


def test_password_hash_roundtrip():
    raw = "s3cret!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed)
    assert not verify_password("bad", hashed)


def test_create_access_token_contains_claims():
    token = create_access_token(
        {"sub": "123", "role": "admin"},
        secret="test-secret",
        expires_minutes=5,
    )
    decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])
    assert decoded["sub"] == "123"
    assert decoded["role"] == "admin"
    assert decoded["exp"] >= int(now_utc().timestamp())
