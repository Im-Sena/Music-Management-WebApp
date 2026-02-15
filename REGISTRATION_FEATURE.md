# 初回登録時の即座ダウンロード開始機能

## 機能説明 (Feature Description)

ユーザー登録時に SoundCloud URL を入力すると、登録完了直後にバックグラウンドで自動的にダウンロードが開始されます。

**English**: When users register with a SoundCloud URL, background downloading starts immediately after registration completes.

## 実装詳細 (Implementation Details)

### 1. 登録フォーム (Registration Form)

**Location**: `/register` (GET request)

Form fields:
- `username` - ユーザー名 (required)
- `password` - パスワード (required)
- `confirm_password` - パスワード確認 (required)
- `soundcloud_url` - SoundCloud URL (optional)

Example URL: `https://soundcloud.com/your-username/likes`

### 2. 登録処理 (Registration Handler)

**Location**: `/register` (POST request)

Process:
1. ユーザーバリデーション
2. ユーザー登録（パスワード: SHA256ハッシュ化）
3. ユーザーディレクトリ作成: `/home/sena/SoundCloud/{username}/`
4. **SoundCloud URL が指定されている場合のみ**:
   - バックグラウンドスレッド開始
   - Thread target: `download_and_scan_user(user_id, username, soundcloud_url)`
   - 非ブロッキング（ユーザーはすぐに成功ページを見られる）

### 3. ダウンロード処理 (Download Process)

実行順序:
```
yt-dlp download (mp3, 128K quality)
    ↓
scan.py (metadata extraction)
    ↓
Thumbnail extraction & storage
    ↓
last_download timestamp update in database
```

実行時間: 30分～数時間（SoundCloud likes の数による）

### 4. ユーザーへのメッセージ

**SoundCloud URL を指定した場合:**
```
Registration Successful!

User created successfully.

Your SoundCloud likes are being downloaded in the background.

Check your profile later to see the download progress.

[Go to Login]
```

**SoundCloud URL を指定しない場合:**
```
Registration Successful!

User created successfully. You can now log in.

You can add your SoundCloud URL later in your profile to start downloading.

[Go to Login]
```

## データベース (Database)

### Users Table Schema

```
id               INTEGER   PRIMARY KEY
username         TEXT      UNIQUE NOT NULL
password         TEXT      NOT NULL (SHA256 hashed)
created_at       TIMESTAMP AUTO
soundcloud_url   TEXT      NULLABLE
last_download    TIMESTAMP NULLABLE (set after download completes)
```

### Example Data

```
id | username | password           | soundcloud_url                          | last_download
1  | test     | (hashed)           | NULL                                    | NULL
2  | tksk     | (hashed)           | https://soundcloud.com/fxoxyn7q0vuj... | 2025-01-15T14:30:45
3  | newuser  | (hashed)           | https://soundcloud.com/abc/likes        | NULL (downloading)
```

## 使用例 (Usage Examples)

### 例1: SoundCloud URL を指定して登録

```
1. /register にアクセス
2. フォーム入力:
   - Username: john_doe
   - Password: secure_password123
   - Confirm Password: secure_password123
   - SoundCloud URL: https://soundcloud.com/john_doe/likes
3. Register をクリック
4. "Your SoundCloud likes are being downloaded in the background" を表示
5. "Go to Login" をクリック
6. ログイン
7. /profile で last_download の更新を確認（数時間後）
```

### 例2: URL なしで登録してから後で追加

```
1. /register にアクセス
2. フォーム入力:
   - Username: jane_doe
   - Password: password456
   - Confirm Password: password456
   - SoundCloud URL: (空)
3. Register をクリック
4. "You can add your SoundCloud URL later..." を表示
5. /login でログイン
6. /profile で SoundCloud URL を入力
7. Save をクリック → ダウンロード開始
```

## 技術仕様 (Technical Specifications)

### Threading

```python
from threading import Thread
from download_service import download_and_scan_user

download_thread = Thread(
    target=download_and_scan_user,
    args=(user_id, username, soundcloud_url),
    daemon=True
)
download_thread.start()
```

**注意点**:
- Daemon thread なので、メインアプリが終了するとスレッドも終了
- 非ブロッキング：ユーザーレスポンスを待たない
- エラーハンドリング：download_service.py が例外をキャッチして出力

### ダウンロード タイムアウト

```python
subprocess.run(cmd, timeout=3600)  # 1時間
```

### スケジューラとの関係

- **登録時の即座ダウンロード**: Threading で即座に実行
- **毎日自動ダウンロード**: APScheduler で 00:00 UTC に実行

両者は独立しており、競合しない。

## トラブルシューティング (Troubleshooting)

### Q: ダウンロードが失敗しているか確認するには？

A: Flask コンソール出力を確認してください
```
python app.py
# ... Flask server output ...
# [background thread output]
Starting download for user: username
Download successful: ...
Scan output: ...
```

### Q: /profile で last_download が NULL のままです

A: ダウンロードがまだ完了していません。コンソール出力を確認してください。

### Q: 登録後にダウンロードが開始されない

A: SoundCloud URL が正しいか確認してください。例：
```
✓ https://soundcloud.com/username/likes
✓ https://soundcloud.com/user-123/likes
✗ https://soundcloud.com/likes （不完全）
✗ soundcloud.com/username/likes （プロトコルなし）
```

## ファイル変更履歴 (File Changes)

### Modified: `/home/sena/app/app.py`

**Changes**:
- Lines 56-125: `/register` POST handler updated
  - `soundcloud_url` 抽出
  - Database INSERT に soundcloud_url を追加
  - Background thread 起動（URL があれば）
  - 条件付き success message
  
- Lines 165-200: `/register` GET handler updated
  - soundcloud_url input field 追加
  - Help text 追加
  - Form width 拡大（300px → 450px）

### Unchanged Files

- `download_service.py` - 既に `download_and_scan_user()` 関数を実装
- `migrate_db.py` - 既に soundcloud_url column を追加
- `scan.py` - 既に metadata extraction を実装
- `init_db.py` - 既に schema を定義

## 互換性 (Compatibility)

✓ 既存ユーザーに影響なし
✓ soundcloud_url は nullable なので古いレコードも動作
✓ URL なしで登録したユーザーは /profile から後で URL を追加可能
✓ フォーム送信時に URL フィールドが空でも動作

## バージョン情報 (Version Info)

- Python: 3.10+
- Flask: 3.1.2
- threading: Built-in (Python std lib)
- yt-dlp: 2026.2.4+
- mutagen: 1.45+

## ライセンス (License)

Same as main project
