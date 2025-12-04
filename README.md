# 📘 ask_back Backend README

> FastAPI × uv を利用した ask_app バックエンド開発環境構築ガイドです。

---

## 📘 uv（次世代Pythonパッケージマネージャ）完全ガイド

Tech0 / ask_app（FastAPI バックエンド）チーム向け

---

## 🎉 まずは結論：チームメンバーが clone した後に行うこと

```sh
#まずはUVがインストールされていることを確認
uv --version
#インストールされていない場合は、READMEの「🛠️ 1. uv のインストール方法」を参照してください。

git clone git@github.com:e10tech/ask_back.git
cd ask_back

uv sync                  # 依存を再現
uv run fastapi dev main.py
```

### 💡 メモ：uv sync は以下を自動で行います
```sh
1️⃣ 必要な Python バージョンの存在チェック
2️⃣ なかったら自動インストール（uv が持ってる高速 installer）
3️⃣ .venv を正しい Python で自動構築
4️⃣ 依存パッケージを uv.lock に基づいて再現
```

---

## 🔧 新たにライブラリを追加したい場合

uv を利用する場合は非常にシンプルです。

### 📌 基本コマンド

```sh
uv add パッケージ名
```

### 📘 例：SQLAlchemy や Pydantic を追加したい場合

```sh
uv add sqlalchemy
uv add pydantic
```

### 📘 例：FastAPI でよく利用する追加ライブラリ

```sh
uv add python-dotenv
uv add passlib[bcrypt]
uv add email-validator
```

### 📌 削除したい場合

```sh
uv remove パッケージ名
```

---

## ✨ ポイント

uv add を実行すると pyproject.toml に自動で追記されます。

uv.lock も自動更新されるため、依存の固定が常に最新となります。

チームメンバーは uv sync を実行するだけで同じ環境を再現できます。

---

## 🌟 uvとは？

uv は Python の以下の機能をすべてまとめて高速に扱える次世代ツールです。

- 仮想環境（venv）
- パッケージ管理（pip）
- ロックファイル管理（pip-tools / poetry 的）
- Python バージョン管理（pyenv 的）

### 🔥 特徴まとめ

- 超高速（pip の 10〜100倍速い）
- ディレクトリごとの .venv を自動管理
- activate 不要 → uv run で仮想環境を自動検出
- uv lock で依存バージョンを固定
- FastAPI との相性抜群（fastapi dev と組み合わせると快適）

---

## 🛠️ 1. uv のインストール方法

### 🔵 Windows（PowerShell 推奨）

📌 公式インストーラ

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

🔍 インストールログ例

Downloading uv ...
Installing to C:\Users\<username>\.local\bin
everything's installed!

📌 PATH が通っていない場合

```powershell
$env:Path = "$env:UserProfile\.local\bin;$env:Path"
```

### 🍎 macOS

📌 公式インストーラ（推奨）

```sh
curl -fsSL https://astral.sh/uv/install.sh | sh
```

📌 Homebrew（代替）

※ 一部のバージョンで遅れる可能性あり

```sh
brew install uv
```

🔍 PATH が通っていない場合

```sh
export PATH="$HOME/.local/bin:$PATH"
```

#### 🧩 PATH が通っていない場合とは？

PATH とは、OS が「コマンドを探す場所のリスト」です。

uv をインストールしても PATH にそのフォルダが入っていないと、OS は uv を見つけられません。

その結果、次のようなエラーが出ます。

```
uv : The term 'uv' is not recognized...
uv: command not found
```

🔍 簡単に言うと…

「uv は存在するが、どこにあるか OS が知らない状態」です。

✔ PATH が通っていると…

どの場所からでも：

```sh
uv --version
```

が動作します。

✔ PATH が通っていないと…

OS が uv を見つけられず "コマンドが認識されない" となります。


✔ バージョン確認（共通）

```sh
uv --version
```

---

## 🧱 2. プロジェクト作成（FastAPI 用）

FastAPI バックエンドはこの 2 行で最短セットアップが可能です。

```sh
uv init -p 3.11 ask_back
cd ask_back
```

### 📁 自動生成される構造

```
ask_back/
├── .venv/              ← 仮想環境（自動）
├── pyproject.toml      ← 依存管理
├── uv.lock             ← ロックファイル（コミット推奨）
└── main.py             ← サンプルアプリ
```

---

## 📦 3. 依存パッケージの追加

FastAPI + DB 用の依存をまとめてインストール：

```sh
uv add "fastapi[standard]" sqlalchemy pydantic pydantic-settings pymysql python-dotenv
```

### 📌 説明

- fastapi[standard] → FastAPI 本体 + 開発ツール（fastapi dev / uvicorn）
- sqlalchemy → DB ORM
- pydantic / pydantic-settings → モデル・設定管理
- pymysql → Azure MySQL 用ドライバ
- python-dotenv → .env 読み込み

---

## 🚀 4. FastAPI の起動方法

### 🧪 開発サーバー（最新版推奨）

```sh
uv run fastapi dev main.py
```

### ✨ 特徴

- 自動リロード
- .env 自動読み込み
- アプリ自動検出
- ログが見やすい
- OpenAPI ドキュメント /docs も自動生成

### 🌐 アクセス

http://127.0.0.1:8000
http://127.0.0.1:8000/docs

### 🏭 本番サーバー（reload なし）

```sh
uv run fastapi run main.py
```

---

## 🔧 5. uv でよく使うコマンドまとめ

### 📌 仮想環境・依存管理

```sh
uv init -p 3.11 myapp      # プロジェクト作成
uv venv                    # .venv を手動作成
uv add fastapi             # 依存追加
uv remove fastapi          # 削除
uv sync                    # lock に従って依存を再現
uv lock                    # lock 更新
uv pip list                # 仮想環境のパッケージ一覧
```

### 📌 実行系

```sh
uv run python main.py         # 仮想環境自動適用
uv run fastapi dev main.py    # FastAPI 開発サーバー
uv run uvicorn main:app       # 従来型 Uvicorn 実行
```

---

## 🔐 6. .env の管理（ローカル / 本番）

.env.local

```
APP_ENV=local
DATABASE_URL=sqlite:///./app.db
```

.env.production

```
APP_ENV=production
DATABASE_URL=mysql+pymysql://user:password@host:3306/db_name
```

.gitignore に追加

```
.env
.env.*
!.env.example
```

---

## 🧱 7. プロジェクト構造（ベストプラクティス）

```
ask_back/
  app/
    __init__.py
    api.py
    config.py
    crud.py
    database.py
    models.py
    schemas.py
  .env.local
  .env.production
  main.py
  pyproject.toml
  uv.lock
```

---

## 🧠 8. よくあるトラブルと対処

| トラブル                | 原因                | 解決策                |
|-------------------------|---------------------|-----------------------|
| ModuleNotFoundError     | 依存未インストール  | uv sync を実行        |
| .venv が使われない      | 別フォルダで実行    | プロジェクト直下で uv run |
| .env が読まれない       | config の env_file の設定違い | Config.env_file を確認 |
| Windows の CRLF 警告    | OS 仕様             | 無視OK / .gitattributes で統一 |

---

## 🌈 9. まとめ（uv の強み）

- activate 不要（自動で .venv を検知）
- uv add で依存管理が簡単
- uv sync でチーム全員の環境が完全再現
- fastapi dev が最強の開発サーバー
- uv.lock をコミットしてバージョン固定が可能
