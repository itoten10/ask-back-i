-- 2要素認証機能のためのデータベースマイグレーション（MySQL用）
-- MySQL 5.7以降で実行してください

-- usersテーブルに2FA関連カラムを追加
-- カラムが既に存在するかチェックしてから追加
SET @dbname = DATABASE();
SET @tablename = "users";
SET @columnname1 = "is_2fa_enabled";
SET @columnname2 = "totp_secret";

SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = @columnname1)
  ) > 0,
  "SELECT 'Column is_2fa_enabled already exists' AS status;",
  CONCAT("ALTER TABLE ", @tablename, " ADD COLUMN ", @columnname1, " BOOLEAN NOT NULL DEFAULT FALSE;")
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = @columnname2)
  ) > 0,
  "SELECT 'Column totp_secret already exists' AS status;",
  CONCAT("ALTER TABLE ", @tablename, " ADD COLUMN ", @columnname2, " VARCHAR(255) NULL;")
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- temp_tokensテーブルを作成
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

SELECT '2FA migration completed successfully' AS status;


