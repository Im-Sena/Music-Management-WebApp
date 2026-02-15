# Music Management WebApp

SoundCloud音楽を自動ダウンロード・管理し、Web上で検索・再生・ダウンロードできるマルチユーザー対応アプリケーション。

## 機能

-  **マルチユーザー対応**: 複数ユーザーの音楽ライブラリを独立管理
-  **ログイン認証**: ユーザーごとのセッション管理
-  **SoundCloud自動ダウンロード**: 登録ユーザーのいいね曲を毎日自動ダウンロード（APScheduler）
-  **MP3メタデータ抽出**: ID3タグからタイトル、アーティスト、アルバム、年、ジャンルを自動抽出
-  **サムネイル自動抽出**: MP3ファイルからアルバムアートを自動抽出して表示
-  **Web音楽プレイヤー**: HTML5 audio player で Web 上で再生
-  **Web検索**: タイトル、アーティスト、アルバムで曲を検索
-  **ダウンロード**: 検索結果から直接MP3ダウンロード
-  **ダウンロードログ**: 毎日のダウンロード履歴をタイムスタンプ付きで記録・表示

## 必要要件

- Python 3.10以上
- SQLite3
- インターネット接続（SoundCloud ダウンロード用）

### 依存Pythonパッケージ

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| Flask | 3.1.2 | Webフレームワーク |
| mutagen | 1.45+ | MP3メタデータ抽出 |
| yt-dlp | 2026.2.4+ | SoundCloud ダウンロード |
| APScheduler | 3.11.2 | 毎日のスケジュール実行 |

## セットアップ

### 1. リポジトリをクローン

```bash
git clone <repository_url>
cd app
```

### 2. 仮想環境を作成して有効化

```bash
# 仮想環境を作成
python3 -m venv venv

# 有効化（Linux/Mac）
source venv/bin/activate

# 有効化（Windows）
venv\Scripts\activate
```

### 3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

または個別にインストール:

```bash
pip install flask==3.1.2 mutagen==1.45 yt-dlp==2026.2.4 apscheduler==3.11.2
```

### 4. アプリケーションを起動

```bash
python app.py
```

- ブラウザで `http://localhost:5000/` を開く
- ログイン画面が表示されます

**注意**: 初回起動時に `music.db` が自動作成され、DBスキーマが自動初期化されます。`init_db.py` の手動実行は不要です。

## 使用方法

### 新規ユーザー登録（Web UI）

1. `http://localhost:5000/` にアクセス
2. 「Register」をクリック
3. ユーザー名、パスワード、SoundCloud likes URL を入力
4. 登録すると自動的に SoundCloud から音楽がダウンロード開始

**SoundCloud likes URL の例:**
```
https://soundcloud.com/your-username/likes
```

### ログイン

1. ユーザー名とパスワードを入力
2. 自分の音楽ライブラリが表示されます

### 音楽の検索と再生

1. **検索**: タイトル、アーティスト、またはアルバムで検索
2. **再生**: カードの「Play」ボタン、または「Now Playing」をクリック
3. **ダウンロード**: 「Download」ボタンで MP3 をダウンロード

### プロフィール管理

- 「Profile」ページで SoundCloud URL を変更
- 自動ダウンロード日時（最後のダウンロード時刻）を表示

### ダウンロード履歴の確認

1. 「Profile」ページの「View Download Logs」をクリック
2. 日別のダウンロード履歴をタイムスタンプ付きで表示
3. どの曲が何時にダウンロードされたかを追跡可能

## ファイル構成

```
.
├── app.py                    # メイン Flask アプリケーション
├── init_db.py              # DB初期化・マイグレーション（自動実行）
├── download_service.py      # SoundCloud ダウンロード・スケジュール処理
├── scan.py                 # MP3 メタデータ抽出・DB登録
├── add_user.py             # ユーザー作成用スクリプト（CLI）
├── reset_password.py       # パスワード変更用スクリプト（CLI）
├── migrate_db.py           # DB マイグレーション（オプション）
├── requirements.txt        # Python 依存パッケージ一覧
├── templates/              # Jinja2 HTML テンプレート
│   ├── base.html          # ナビゲーション・共通レイアウト
│   ├── login.html         # ログインページ
│   ├── register.html      # 登録ページ
│   ├── profile.html       # プロフィール・設定ページ
│   ├── library.html       # 音楽ライブラリ・検索結果
│   ├── player.html        # Web 音楽プレイヤー
│   └── logs.html          # ダウンロード履歴ログ表示
├── static/
│   ├── css/               # スタイルシート
│   │   ├── style.css      # グローバルスタイル
│   │   ├── library.css    # ライブラリページ専用
│   │   └── player.css     # プレイヤーページ専用
│   └── [自動生成]          # サムネイル画像等
├── logs/                   # ダウンロード履歴ログ（日別ファイル）
├── music.db               # SQLite データベース（自動生成）
├── .gitignore             # git 除外ファイル設定
├── README.md              # このファイル
└── [その他]
```

## データベーススキーマ

### users テーブル

| カラム | 型 | 説明 |
|--------|-----|------|
| id | INTEGER PRIMARY KEY | ユーザーID |
| username | TEXT UNIQUE | ユーザー名 |
| password | TEXT | SHA256 ハッシュ化パスワード |
| soundcloud_url | TEXT | SoundCloud likes URL（オプション） |
| created_at | TIMESTAMP | 作成日時 |
| last_download | TIMESTAMP | 最後のダウンロード日時 |

### songs テーブル

| カラム | 型 | 説明 |
|--------|-----|------|
| id | INTEGER PRIMARY KEY | 曲ID |
| user_id | INTEGER | ユーザーID（外部キー） |
| title | TEXT | 曲タイトル |
| artist | TEXT | アーティスト名 |
| album | TEXT | アルバム名 |
| year | TEXT | リリース年 |
| genre | TEXT | ジャンル |
| filepath | TEXT | MP3 ファイルパス |
| thumbnail | TEXT | サムネイル画像パス |
| created_at | TIMESTAMP | DB登録日時 |

## 自動ダウンロード機能

### スケジュール

- **毎日 00:00 UTC** に自動実行
- SoundCloud likes URL が設定されているユーザーのみ対象
- 背景でスケジュール実行（`APScheduler`）

### ログ保存

- ファイル: `logs/download_[username]_[YYYY-MM-DD].log`
- タイムスタンプ付き: `[HH:MM:SS] message`
- 各ステップ（ダウンロード、スキャン、DB登録等）を記録

### 登録時の即時ダウンロード

- ユーザー登録時に SoundCloud URL が設定されている場合
- バックグラウンドスレッドで即座にダウンロード開始
- ブラウザはブロックされずに完了まで待機

## 使用例

### 仮想環境での実行

```bash
# リポジトリをクローン
git clone <repository_url>
cd app

# 仮想環境を作成・有効化
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate     # Windows

# パッケージをインストール
pip install -r requirements.txt

# アプリケーションを起動
python app.py

# ブラウザで http://localhost:5000 を開く
```

### ユーザー登録（CLI）

Web UI での登録も可能ですが、CLI でも登録可能です：

```bash
# パスワードをプロンプトで入力
python add_user.py john

# またはコマンドラインで直接指定
python add_user.py john password123
```

### パスワード変更・リセット

ユーザーがパスワードを忘れた場合、CLI で新しいパスワードを設定できます：

```bash
# ユーザー john のパスワードをリセット
python reset_password.py john

# プロンプトで新しいパスワードを入力
新しいパスワードを入力: ****
パスワードを再入力: ****
✓ パスワードが正常に変更されました
```

## トラブルシューティング

### ポート 5000 が使用中

```bash
# 別のポートで起動
python -c "import app; app.app.run(port=8000)"
```

### SoundCloud URL が無効

- `https://soundcloud.com/username/likes` の形式か確認
- ユーザー名が正しいか確認
- プロフィール設定ページで URL を再入力して保存

### ダウンロードが失敗

- ダウンロード履歴ログ（Profile > View Download Logs）でエラーメッセージを確認
- インターネット接続を確認
- `yt-dlp` が最新版か確認: `pip install --upgrade yt-dlp`

### DB エラー

- 初回起動時に自動初期化されます
- 問題が続く場合: `rm music.db` で削除し、`python app.py` で再初期化

## セキュリティに関する注意

- **開発環境専用**: 本番環境での使用は推奨しません
- **パスワードハッシング**: SHA256 を使用（本番環境では bcrypt 推奨）
- **Secret Key**: `app.py` の `secret_key` を変更してください
- **ユーザー隔離**: 各ユーザーは自分の曲のみアクセス可能

## ライセンス

MIT License

## 作者

Im-Sena


