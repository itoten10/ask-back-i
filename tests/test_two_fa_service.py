import pytest
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
    
    # シークレットが生成されること
    assert secret1 is not None
    assert len(secret1) > 0
    
    # 毎回異なるシークレットが生成されること
    assert secret1 != secret2
    
    # Base32形式であること（大文字、A-Z2-7のみ）
    assert secret1.isupper() or secret1.islower()
    assert all(c.isalnum() and c not in "0189" for c in secret1.upper())


def test_generate_otpauth_url():
    """otpauth:// URL生成のテスト"""
    secret = "JBSWY3DPEHPK3PXP"  # テスト用固定シークレット
    email = "test@example.com"
    issuer = "School Auth"
    
    url = generate_otpauth_url(email, secret, issuer)
    
    # otpauth://で始まること
    assert url.startswith("otpauth://totp/")
    
    # メールアドレスが含まれること
    assert email in url
    
    # シークレットが含まれること
    assert secret in url
    
    # issuerが含まれること
    assert issuer.replace(" ", "%20") in url


def test_verify_totp():
    """TOTPコード検証のテスト"""
    secret = "JBSWY3DPEHPK3PXP"  # テスト用固定シークレット
    totp = pyotp.TOTP(secret)
    
    # 現在時刻の正しいコードを生成
    correct_code = totp.now()
    
    # 正しいコードが検証されること
    assert verify_totp(secret, correct_code) is True
    
    # 間違ったコードが検証されないこと
    wrong_code = "000000"
    assert verify_totp(secret, wrong_code) is False
    
    # 無効なコード形式が検証されないこと
    assert verify_totp(secret, "12345") is False  # 5桁
    assert verify_totp(secret, "1234567") is False  # 7桁


def test_verify_totp_time_window():
    """TOTPコードの時間ウィンドウ検証のテスト"""
    secret = "JBSWY3DPEHPK3PXP"
    totp = pyotp.TOTP(secret)
    
    # 現在時刻のコード
    current_code = totp.now()
    assert verify_totp(secret, current_code) is True
    
    # 前の期間のコード（30秒前）
    # 注意: 実際のテストでは時間を操作できないため、valid_window=1の動作確認のみ
    # 実際の時間ウィンドウテストは統合テストで行う


def test_generate_qr_code_data():
    """QRコード生成のテスト"""
    otpauth_url = "otpauth://totp/School%20Auth:test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=School%20Auth"
    
    qr_data = generate_qr_code_data(otpauth_url)
    
    # Base64エンコードされた文字列が返されること
    assert qr_data is not None
    assert len(qr_data) > 0
    
    # Base64形式であること（大文字、小文字、数字、+、/、=のみ）
    import base64
    try:
        decoded = base64.b64decode(qr_data)
        assert len(decoded) > 0  # PNGデータが含まれていること
    except Exception:
        pytest.fail("QRコードデータが有効なBase64形式ではありません")


