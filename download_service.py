import os
import subprocess
import sqlite3
from datetime import datetime

# ====================================================================
# SoundCloud ダウンロード & スキャン処理
# 登録時またはスケジュール実行時に呼び出される
# ====================================================================

def log_message(username, message):
    """
    ダウンロード処理のログをファイルに記録
    
    ログファイル: logs/download_[username]_[date].log
    """
    # ログディレクトリが無ければ作成
    os.makedirs("logs", exist_ok=True)
    
    # ログファイルパス（日付ごとに分割）
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = f"logs/download_{username}_{today}.log"
    
    # タイムスタンプ付きでメッセージをログに追記
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    # コンソールにも出力
    print(log_entry.strip())

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
    
    # ディレクトリが存在しなければ作成
    os.makedirs(music_dir, exist_ok=True)
    log_message(username, f"Download directory: {music_dir}")
    
    # === yt-dlp コマンド構築 ===
    # -x: 音声抽出（MP3等に変換）
    # -f bestaudio: 最良の音声形式を自動選択（SoundCloud制限対策）
    # --embed-thumbnail: MP3にサムネイル埋め込み
    # --embed-metadata: ID3タグ埋め込み
    # --audio-format mp3, --audio-quality 128K: MP3 128kbpsで出力
    # --continue: ダウンロード中断時に続行
    # -o: 出力ファイル名形式（アーティスト/アップローダー - 曲名.mp3）
    cmd = [
        "yt-dlp",
        "-x",
        "-f", "bestaudio",
        "--embed-thumbnail",
        "--embed-metadata",
        "--audio-format", "mp3",
        "--audio-quality", "128K",
        "--continue",
        "--no-progress",
        "-o", os.path.join(music_dir, "%(artist,uploader)s - %(title)s.%(ext)s"),
        soundcloud_url
    ]
    
    try:
        # === Step 1: yt-dlp でダウンロード実行 ===
        # リアルタイムでログ出力するため Popen を使用
        log_message(username, "About to run yt-dlp command...")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # yt-dlp のリアルタイム出力を処理
        output_lines = []
        downloaded_count = 0
        skipped_count = 0
        
        try:
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                
                output_lines.append(line)
                
                # プレイリスト情報
                if 'Downloading' in line and 'items of' in line:
                    log_message(username, f"Playlist: {line}")
                
                # ダウンロード/スキップ判定
                if line.startswith('[download]'):
                    # スキップされた曲
                    if 'has already been' in line or 'already fully downloaded' in line:
                        if '.mp3' in line:
                            file_part = line.split('[download]')[-1].strip()
                            log_message(username, f"Skipped: {file_part}")
                        skipped_count += 1
                    # プレイリスト完了
                    elif 'Finished downloading playlist' in line:
                        log_message(username, f"Playlist complete: {line}")
                    # ダウンロード完了
                    elif '.mp3' in line and 'has already' not in line and 'Finished' not in line:
                        file_part = line.split('[download]')[-1].strip()
                        log_message(username, f"Downloaded: {file_part}")
                        downloaded_count += 1
            
            # プロセス完了待機 (timeout=18000 は5時間)
            result_returncode = process.wait(timeout=18000)
            
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            log_message(username, "Download timeout (exceeded 5 hour limit)")
            return
        
        log_message(username, f"yt-dlp finished - returncode: {result_returncode}")
        
        # エラーチェック
        if result_returncode != 0:
            log_message(username, f"Download error (returncode: {result_returncode})")
            return
        
        log_message(username, "Download successful via yt-dlp")
        log_message(username, f"Output lines: {len(output_lines)}")
        
        # 最終サマリー
        if downloaded_count > 0 or skipped_count > 0:
            log_message(username, f"Summary: {downloaded_count} downloaded, {skipped_count} skipped")
        
        # === Step 2: scan.py を実行して メタデータ抽出 & DB登録 ===
        # scan.py が MP3ファイルのID3タグを読み取り、DBに登録
        log_message(username, "Scanning music files for metadata...")
        cmd_scan = [
            "python", "scan.py", username
        ]
        result_scan = subprocess.run(cmd_scan, capture_output=True, text=True)
        if result_scan.returncode == 0:
            log_message(username, "Scan completed successfully")
        else:
            log_message(username, f"Scan warning: {result_scan.stderr[:100]}")
        
        # === Step 3: DB更新：last_download タイムスタンプ ===
        # ダウンロード完了時刻を記録（ISO 8601形式）
        conn = sqlite3.connect("music.db")
        c = conn.cursor()
        c.execute("""
            UPDATE users SET last_download = ? WHERE id = ?
        """, (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
        
        log_message(username, "Download and scan completed successfully!")
        
    # ダウンロードが5時間を超えた場合のタイムアウト処理
    except subprocess.TimeoutExpired:
        log_message(username, "Download timeout (exceeded 5 hour limit)")
    # その他のエラーをキャッチ（ファイルI/O等）
    except Exception as e:
        import traceback
        log_message(username, f"Exception occurred: {type(e).__name__}: {str(e)}")
        log_message(username, f"Traceback: {traceback.format_exc()}")


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
        log_message(username, "Scheduled download started")
        download_and_scan_user(user_id, username, soundcloud_url)


# === コマンドライン実行用 ===
# テスト用：python download_service.py で実行可能
if __name__ == "__main__":
    run_scheduled_downloads()
