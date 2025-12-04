import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv


load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _split_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    db_user: str = os.getenv("DB_USER", "")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: str = os.getenv("DB_PORT", "3306")
    db_name: str = os.getenv("DB_NAME", "")
    ssl_ca_path: str | None = os.getenv("SSL_CA_PATH")

    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret")
    access_token_ttl_min: int = int(os.getenv("ACCESS_TOKEN_TTL_MIN", "15"))
    refresh_token_ttl_days: int = int(os.getenv("REFRESH_TOKEN_TTL_DAY", "14"))

    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "")

    cors_origins: List[str] = field(
        default_factory=lambda: _split_csv(os.getenv("CORS_ORIGINS"))
    )

    refresh_cookie_name: str = os.getenv("REFRESH_COOKIE_NAME", "refresh_token")
    refresh_cookie_secure: bool = _get_bool("REFRESH_COOKIE_SECURE", True)
    refresh_cookie_path: str = os.getenv("REFRESH_COOKIE_PATH", "/")
    refresh_cookie_samesite: str | None = os.getenv("REFRESH_COOKIE_SAMESITE", "lax")
    refresh_cookie_domain: str | None = os.getenv("REFRESH_COOKIE_DOMAIN") or None

    # アクセストークンはフロントのメモリ保持のみ（Cookieへは保存しない）
    access_token_storage: str = "memory"

    # 2FA関連設定
    temp_token_expiration_minutes: int = int(os.getenv("TEMP_TOKEN_EXPIRATION_MINUTES", "10"))
    rate_limit_enabled: bool = _get_bool("RATE_LIMIT_ENABLED", True)
    rate_limit_max_attempts: int = int(os.getenv("RATE_LIMIT_MAX_ATTEMPTS", "5"))
    rate_limit_window_minutes: int = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "5"))
    encrypt_totp_secret: bool = _get_bool("ENCRYPT_TOTP_SECRET", False)
    encryption_key: str | None = os.getenv("ENCRYPTION_KEY")

    def database_url(self) -> str:
        return (
            f"mysql+asyncmy://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
