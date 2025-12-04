"""データベース接続不要のTOTPサービステスト（スタンドアロン実行用）"""
import sys
sys.path.insert(0, '.')

import pyotp
from app.services.two_fa_service import (
    generate_otpauth_url,
    generate_qr_code_data,
    generate_totp_secret,
    verify_totp,
)


def test_generate_totp_secret():
    """TOTPシークレット生成のテスト"""
    secret1 = generate_totp_secret()
    secret2 = generate_totp_secret()
    
    assert secret1 is not None
    assert len(secret1) > 0
    assert secret1 != secret2
    print("✓ test_generate_totp_secret passed")


def test_generate_otpauth_url():
    """otpauth:// URL生成のテスト"""
    secret = "JBSWY3DPEHPK3PXP"
    email = "test@example.com"
    issuer = "School Auth"
    
    url = generate_otpauth_url(email, secret, issuer)
    
    assert url.startswith("otpauth://totp/")
    # メールアドレスはURLエンコードされる可能性がある
    assert email in url or email.replace("@", "%40") in url
    assert secret in url
    print("✓ test_generate_otpauth_url passed")


def test_verify_totp():
    """TOTPコード検証のテスト"""
    secret = "JBSWY3DPEHPK3PXP"
    totp = pyotp.TOTP(secret)
    
    correct_code = totp.now()
    assert verify_totp(secret, correct_code) is True
    assert verify_totp(secret, "000000") is False
    print("✓ test_verify_totp passed")


def test_generate_qr_code_data():
    """QRコード生成のテスト"""
    otpauth_url = "otpauth://totp/School%20Auth:test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=School%20Auth"
    
    qr_data = generate_qr_code_data(otpauth_url)
    
    assert qr_data is not None
    assert len(qr_data) > 0
    
    import base64
    decoded = base64.b64decode(qr_data)
    assert len(decoded) > 0
    print("✓ test_generate_qr_code_data passed")


if __name__ == "__main__":
    print("Running TOTP service tests...")
    try:
        test_generate_totp_secret()
        test_generate_otpauth_url()
        test_verify_totp()
        test_generate_qr_code_data()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

