import os
import sqlite3
import sys
from mutagen.id3 import ID3

# ====================================================================
# MP3 ファイルスキャン & メタデータ抽出ツール
# download_service.py から呼び出される
# ====================================================================

# === コマンドライン引数処理 ===
# 使用方法: python scan.py <username> [music_directory]
if len(sys.argv) < 2:
    print("Usage: python scan.py <username> [music_directory]")
    print("Example: python scan.py sena /home/sena/SoundCloud/sena/")
    sys.exit(1)

# ユーザー名を取得
USERNAME = sys.argv[1]

# 音楽ディレクトリを決定
# 指定があればそれを使用、なければデフォルトパス
if len(sys.argv) >= 3:
    MUSIC_DIR = sys.argv[2]
else:
    MUSIC_DIR = f"/home/sena/SoundCloud/{USERNAME}/"

# === サムネイル保存ディレクトリ ===
# thumbnails/ フォルダを作成（MP3から抽出したアルバムアートを保存）
THUMB_DIR = os.path.join(MUSIC_DIR, "thumbnails")
os.makedirs(THUMB_DIR, exist_ok=True)

# === データベース接続 ===
conn = sqlite3.connect("music.db")
c = conn.cursor()

# === ユーザー存在確認 ===
# スキャン対象のユーザーがDB内に存在するか確認
c.execute("SELECT id FROM users WHERE username = ?", (USERNAME,))
user = c.fetchone()

if not user:
    print(f"User '{USERNAME}' not found in database.")
    print("Please create the user first using: python add_user.py <username>")
    conn.close()
    sys.exit(1)

# ユーザーIDを保存（DB登録時に必要）
user_id = user[0]

print(f"Scanning music for user: {USERNAME}")
print(f"Music directory: {MUSIC_DIR}")

# === MP3ファイル探索 ===
# 指定ディレクトリを再帰的に探索してMP3ファイルを検出
for root, _, files in os.walk(MUSIC_DIR):
    for file in files:
        # MP3ファイルのみ処理（他のファイルは無視）
        if file.endswith(".mp3"):
            path = os.path.join(root, file)

            try:
                # === メタデータ抽出 ===
                # mutagen.ID3 を使ってMP3ファイルのID3タグを読み込み
                audio = ID3(path)

                # 各種タグを取得（存在しない場合は None）
                title = audio.get("TIT2")      # TIT2: タイトル
                artist = audio.get("TPE1")     # TPE1: アーティスト
                album = audio.get("TALB")      # TALB: アルバム名
                year = audio.get("TDRC")       # TDRC: 録音年
                genre = audio.get("TCON")      # TCON: ジャンル
                # APIC: アルバムアート（画像）は後で処理

                # タグを文字列に変換（ID3オブジェクトを文字列化）
                # 値が存在すればその値、無ければデフォルト値
                title = title.text[0] if title else file
                artist = artist.text[0] if artist else "Unknown"
                album = album.text[0] if album else "Unknown"
                year = str(year.text[0]) if year else ""
                genre = genre.text[0] if genre else ""

                # === アルバムアート（サムネイル）抽出 ===
                thumbnail_path = None

                # APICタグが存在するか確認（APIC: Attached Picture）
                if audio.getall("APIC"):
                    # 複数のアルバムアートがある場合、最初のものを使用
                    apic = audio.getall("APIC")[0]

                    # ファイル名を安全な形に変換（スペースなどを削除）
                    safe_name = file.replace(" ", "_").replace(".mp3", "")
                    thumb_filename = f"{safe_name}.jpg"
                    thumbnail_path = os.path.join(THUMB_DIR, thumb_filename)

                    # 画像データをJPEGファイルとして保存
                    with open(thumbnail_path, "wb") as img:
                        img.write(apic.data)

                # === DB 登録 ===
                # INSERT OR IGNORE: 同じuser_idとfilepathの組み合わせは無視
                # （重複登録を防ぐ）
                c.execute("""
                    INSERT OR IGNORE INTO songs
                    (user_id, title, artist, album, year, genre, filepath, thumbnail)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, title, artist, album, year, genre, path, thumbnail_path))

                print(f"Added: {title}")

            # MP3読み込みエラーやデータベースエラーをキャッチ
            except Exception as e:
                print(f"Error reading {file}: {e}")

# === DB確定 ===
# 全ての INSERT 処理を確定
conn.commit()

# === 接続終了 ===
conn.close()

print("Scan complete.")
