import os
import subprocess
import sqlite3
from datetime import datetime

# ====================================================================
# SoundCloud ダウンロード & スキャン処理
# 登録時またはスケジュール実行時に呼び出される
# ====================================================================

def download_and_scan_user(user_id, username, soundcloud_url):
    """
    ユーザーのSoundCloud likes から音楽をダウンロードしてスキャン
    
    処理流れ:
    1. yt-dlp で SoundCloud likes をMP3でダウンロード
    2. scan.py でメタデータを抽出 & DB登録 & thumbnail保存
    3. last_download タイムスタンプをDB更新
    
    Args:
        user_id: ユーザーID
        username: ユーザー名（ディレクトリ名、スキャン対象）
        soundcloud_url: SoundCloud likes URL
    """
    
    # SoundCloud URL が未設定の場合はスキップ
    if not soundcloud_url:
        print(f"[{username}] SoundCloud URL not set, skipping")
        return
    
    # ユーザーのダウンロードディレクトリ
    music_dir = f"/home/sena/SoundCloud/{username}"
    
    # === ログ出力 ===
    print(f"\n{'='*60}")
    print(f"Starting download for user: {username}")
    print(f"URL: {soundcloud_url}")
    print(f"{'='*60}")
    
    # === yt-dlp コマンド構築 ===
    # -x: 音声抽出（MP3等に変換）
    # --embed-thumbnail: MP3にサムネイル埋め込み
    # --embed-metadata: ID3タグ埋め込み
    # --audio-format mp3, --audio-quality 128K: MP3 128kbpsで出力
    # -o: 出力ファイル名形式（アーティスト - 曲名.mp3）
    cmd = [
        "yt-dlp",
        "-x",
        "--embed-thumbnail",
        "--embed-metadata",
        "--audio-format", "mp3",
        "--audio-quality", "128K",
        "-o", os.path.join(music_dir, "%(artist)s - %(title)s.%(ext)s"),
        soundcloud_url
    ]
    
    try:
        # === Step 1: yt-dlp でダウンロード実行 ===
        # timeout=3600 (1時間のタイムアウト)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        # ダウンロードエラーチェック
        if result.returncode != 0:
            print(f"Error downloading: {result.stderr}")
            return
        
        print(f"Download successful: {result.stdout}")
        
        # === Step 2: scan.py を実行して メタデータ抽出 & DB登録 ===
        # scan.py が MP3ファイルのID3タグを読み取り、DBに登録
        print(f"Scanning music files...")
        cmd_scan = [
            "python", "scan.py", username
        ]
        result_scan = subprocess.run(cmd_scan, capture_output=True, text=True)
        print(f"Scan output: {result_scan.stdout}")
        
        # === Step 3: DB更新：last_download タイムスタンプ ===
        # ダウンロード完了時刻を記録（ISO 8601形式）
        conn = sqlite3.connect("music.db")
        c = conn.cursor()
        c.execute("""
            UPDATE users SET last_download = ? WHERE id = ?
        """, (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
        
        print(f"[{username}] Download and scan completed successfully!")
        
    # ダウンロードが1時間を超えた場合のタイムアウト処理
    except subprocess.TimeoutExpired:
        print(f"[{username}] Download timeout (> 1 hour)")
    # その他のエラーをキャッチ（ファイルI/O等）
    except Exception as e:
        print(f"[{username}] Error: {str(e)}")


# ====================================================================
# スケジュール実行：毎日 00:00 に呼び出される
# ====================================================================

def run_scheduled_downloads():
    """
    スケジュール済みダウンロードを実行
    
    処理:
    1. DB から soundcloud_url が設定されているユーザーを取得
    2. 各ユーザーに対して download_and_scan_user() を実行
    3. 全ユーザーの処理が完了
    
    注意: APScheduler から毎日 00:00 UTC に自動実行される
    """
    
    conn = sqlite3.connect("music.db")
    c = conn.cursor()
    
    # soundcloud_url が設定されているユーザーを取得
    # NULL または空文字列は除外
    c.execute("""
        SELECT id, username, soundcloud_url FROM users WHERE soundcloud_url IS NOT NULL AND soundcloud_url != ''
    """)
    users = c.fetchall()
    conn.close()
    
    # ダウンロード対象のユーザー数をログ出力
    print(f"Found {len(users)} users with SoundCloud URLs")
    
    # 各ユーザーのダウンロードを順番に実行
    for user_id, username, soundcloud_url in users:
        download_and_scan_user(user_id, username, soundcloud_url)


# === コマンドライン実行用 ===
# テスト用：python download_service.py で実行可能
if __name__ == "__main__":
    run_scheduled_downloads()
