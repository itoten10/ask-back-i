import pyotp
import qrcode
from io import BytesIO
from base64 import b64encode

from app.core.config import settings
from app.models.user import User


def generate_totp_secret() -> str:
    """TOTPシークレットキー生成（Base32形式）"""
    return pyotp.random_base32()


def generate_otpauth_url(email: str, secret: str, issuer: str = "School Auth") -> str:
    """otpauth:// URL生成"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=email,
        issuer_name=issuer
    )


def verify_totp(secret: str, code: str) -> bool:
    """TOTPコード検証"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # 前後1期間（30秒）の許容


def generate_qr_code_data(otpauth_url: str) -> str:
    """QRコード画像をBase64エンコードした文字列として生成"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(otpauth_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return b64encode(buffer.getvalue()).decode("utf-8")


