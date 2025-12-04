# データベースマイグレーション手順

## 2要素認証機能のためのマイグレーション

### 方法1: MySQLクライアントで実行（推奨）

```bash
# Azure MySQLに接続
mysql -h gen10-mysql-dev-01.mysql.database.azure.com \
      -u students \
      -p \
      --ssl-mode=REQUIRED \
      --ssl-ca=./DigiCertGlobalRootG2.crt.pem \
      ask

# マイグレーションSQLを実行
source migrations/add_2fa_tables_mysql.sql
```

または、SQLファイルを直接実行：

```bash
mysql -h gen10-mysql-dev-01.mysql.database.azure.com \
      -u students \
      -p \
      --ssl-mode=REQUIRED \
      --ssl-ca=./DigiCertGlobalRootG2.crt.pem \
      ask < migrations/add_2fa_tables_mysql.sql
```

### 方法2: Pythonスクリプトで実行

```bash
cd ask_back
uv run python migrations/run_migration.py
```

### 手動実行（MySQLクライアントツール使用）

1. MySQL WorkbenchやDBeaverなどのツールで接続
2. `migrations/add_2fa_tables_mysql.sql` の内容を実行

### 確認

マイグレーションが成功したか確認：

```sql
-- usersテーブルの構造確認
DESCRIBE users;

-- temp_tokensテーブルの存在確認
SHOW TABLES LIKE 'temp_tokens';

-- temp_tokensテーブルの構造確認
DESCRIBE temp_tokens;
```


