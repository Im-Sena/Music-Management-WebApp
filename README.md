# Music Management WebApp

複数ユーザーの音楽ライブラリをWeb上で管理・検索・ダウンロードできるアプリケーション。

## 機能

-  **マルチユーザー対応**: 複数ユーザーの音楽ライブラリを独立管理
-  **ログイン認証**: ユーザーごとのセッション管理
-  **MP3自動スキャン**: `/home/sena/SoundCloud/{ユーザー名}/` 形式のディレクトリ対応
-  **メタデータ抽出**: タイトル、アーティスト、アルバム、年、ジャンルを自動抽出
-  **サムネイル表示**: MP3ファイルからアルバムアートを自動抽出
-  **Web検索**: タイトル、アーティスト、アルバムで検索
-  **ダウンロード**: 検索結果から直接ダウンロード

## 必要要件

- Python 3.7以上
- SQLite3
- 以下のPythonパッケージ:
  - Flask
  - mutagen

### インストール

#### オプション1: 仮想環境を使用（推奨）

```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化（Linux/Mac）
source venv/bin/activate

# 仮想環境を有効化（Windows）
venv\Scripts\activate

# 必要なパッケージをインストール
pip install flask mutagen
```

#### オプション2: グローバルインストール

```bash
pip install flask mutagen
```

## セットアップ

### 1. 仮想環境の有効化（仮想環境を使用する場合）

```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. データベースの初期化

```bash
python init_db.py
```

これで `music.db` が作成されます。

### 3. ユーザーを作成

```bash
# パスワードプロンプト付き（推奨）
python add_user.py username

# またはコマンドラインでパスワード指定
python add_user.py username password
```

複数ユーザーを作成する場合は、ユーザーごとに実行します。

### 4. 音楽ファイルのセットアップ

各ユーザーの音楽ファイルを以下の構造に配置してください：

```
/home/sena/SoundCloud/
├── senna/
│   ├── song1.mp3
│   ├── song2.mp3
│   └── ...
├── user2/
│   ├── track1.mp3
│   └── ...
└── ...
```

### 5. MP3ファイルをスキャン

各ユーザーの音楽をスキャンしてデータベースに登録します：

```bash
# sennaユーザーをスキャン（デフォルトディレクトリ使用）
python scan.py senna

# user2をスキャン
python scan.py user2

# カスタムディレクトリを指定
python scan.py username /custom/music/path/
```

### 6. Webアプリケーションを起動

```bash
python app.py
```

ブラウザで `http://localhost:5000/` にアクセス
- ログイン画面が表示されます
- 作成したユーザー名とパスワードでログイン

### 仮想環境を終了する場合

```bash
deactivate
```

## 使用方法

### ログイン

1. `http://localhost:5000/` にアクセス
2. ユーザー名とパスワードを入力してログイン
3. 自分の音楽ライブラリが表示されます

### 曲の検索と再生

- タイトル、アーティスト、またはアルバムで検索
- 検索結果から「Download」をクリックしてダウンロード

### ログアウト

右上の「Logout」ボタンをクリック

## ファイル構成

```
.
├── app.py            # Flaskアプリケーション（ログイン、Web検索）
├── init_db.py        # データベース初期化スクリプト
├── add_user.py       # ユーザー作成スクリプト
├── scan.py           # MP3ファイルスキャン・DB登録スクリプト
├── music.db          # SQLiteデータベース（自動生成、.gitignore対象）
├── static/           # サムネイル画像フォルダ（自動生成、.gitignore対象）
└── README.md         # このファイル
```

## データベーススキーマ

### usersテーブル

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### songsテーブル

```sql
CREATE TABLE songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    artist TEXT,
    album TEXT,
    year TEXT,
    genre TEXT,
    filepath TEXT NOT NULL,
    thumbnail TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, filepath)
)
```

## 注意事項

- 同じユーザーが同じファイルパスの曲を複数回登録することはできません（`UNIQUE(user_id, filepath)`）
- MP3ファイルにメタデータがない場合、タイトルはファイル名、その他は「Unknown」になります
- パスワードはSHA256でハッシュ化されて保存されます（本番環境ではbcryptの使用を推奨）
- 各ユーザーは自分の曲のみ表示・ダウンロード可能です
- `static/` フォルダと `music.db` はGitで管理されません（`.gitignore`に登録済み）

## トラブルシューティング

**ユーザーが作成されません**
```bash
# DBが正しく初期化されているか確認
sqlite3 music.db ".schema"
```

**曲がスキャンされません**
```bash
# ユーザーが存在するか確認
sqlite3 music.db "SELECT * FROM users;"

# ファイルパスが正しいか確認
ls -la /home/sena/SoundCloud/username/
```

**ログインできません**
- ユーザー名とパスワードが正しいか確認してください
- ブラウザのキャッシュをクリアしてもう一度試してください

## ライセンス

MIT License

## 作者

Im-Sena


