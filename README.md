# Music Management WebApp

フォルダ内のMP3ファイルをスキャンして、メタデータを抽出し、Webで検索・ダウンロードできるアプリケーション。

## 機能

-  **MP3自動スキャン**: 指定フォルダ内のすべてのMP3ファイルを自動検出
-  **メタデータ抽出**: タイトル、アーティスト、アルバム、年、ジャンルを自動抽出
-  **Web検索**: ブラウザでMP3ファイルを検索
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

### 3. MP3ファイルをスキャン

`scan.py` の `MUSIC_DIR` を自分の音楽フォルダに変更してから実行：

```python
MUSIC_DIR = "/path/to/your/music/folder/"
```

その後、実行：

```bash
python scan.py
```

### 4. Webアプリケーションを起動

```bash
python app.py
```

ブラウザで `http://localhost:5000/` にアクセス

### 仮想環境を終了する場合

```bash
deactivate
```

## 使用方法

### 検索

- **フォーム検索**: 検索ボックスにタイトル、アーティスト、またはアルバム名を入力
- **クエリパラメータ**: `http://localhost:5000/?q=検索文字`

### ダウンロード

検索結果の「Download」リンクからファイルをダウンロード

## ファイル構成

```
.
├── app.py          # Flaskアプリケーションのメインコード
├── init_db.py      # データベース初期化スクリプト
├── scan.py         # MP3ファイルスキャン・DB登録スクリプト
├── music.db        # SQLiteデータベース（自動生成）
└── README.md       # このファイル
```

## データベーススキーマ

```sql
CREATE TABLE songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    artist TEXT,
    album TEXT,
    year TEXT,
    genre TEXT,
    filepath TEXT UNIQUE
)
```

## 注意事項

- `scan.py` を複数回実行しても重複登録されません（`filepath` が UNIQUE）
- MP3ファイルにメタデータがない場合、タイトルはファイル名、その他は「Unknown」になります
- アルバムアートなどのメタデータには対応していません


