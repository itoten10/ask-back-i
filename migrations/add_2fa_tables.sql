-- 2要素認証機能のためのデータベースマイグレーション
-- 実行方法: MySQLクライアントでこのファイルを実行

-- usersテーブルに2FA関連カラムを追加
-- 既に存在する場合はエラーになるが、無視してOK
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS is_2fa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(255) NULL;

-- temp_tokensテーブルを作成
-- 既に存在する場合はエラーになるが、無視してOK
CREATE TABLE IF NOT EXISTS temp_tokens (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    token VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    INDEX idx_token (token),
    INDEX idx_email (email),
    INDEX idx_expires_at (expires_at)
);

-- マイグレーション完了メッセージ
SELECT '2FA migration completed successfully' AS status;


