import os
import sqlite3
import sys
# mp3からメタデータを読み込むためのライブラリ
from mutagen.id3 import ID3

# コマンドライン引数からユーザー名を取得
if len(sys.argv) < 2:
    print("Usage: python scan.py <username> [music_directory]")
    print("Example: python scan.py sena /home/sena/SoundCloud/sena/")
    sys.exit(1)

USERNAME = sys.argv[1]

# 音楽ディレクトリはコマンドラインで指定、なければデフォルト
if len(sys.argv) >= 3:
    MUSIC_DIR = sys.argv[2]
else:
    MUSIC_DIR = f"/home/sena/SoundCloud/{USERNAME}/"

# サムネイル保存先（音楽ディレクトリ直下）
THUMB_DIR = os.path.join(MUSIC_DIR, "thumbnails")

# サムネ保存フォルダが無ければ作る
os.makedirs(THUMB_DIR, exist_ok=True)

# SQLiteに接続
conn = sqlite3.connect("music.db")
c = conn.cursor()

# ユーザーが存在するか確認
c.execute("SELECT id FROM users WHERE username = ?", (USERNAME,))
user = c.fetchone()

if not user:
    print(f"User '{USERNAME}' not found in database.")
    print("Please create the user first using: python add_user.py <username>")
    conn.close()
    sys.exit(1)

user_id = user[0]

print(f"Scanning music for user: {USERNAME}")
print(f"Music directory: {MUSIC_DIR}")

# ディレクトリを再帰的に探索
for root, _, files in os.walk(MUSIC_DIR):
    for file in files:

        # mp3のみ処理
        if file.endswith(".mp3"):
            path = os.path.join(root, file)

            try:
                # mp3からメタデータを読み込む
                audio = ID3(path)

                # 各種タグ取得
                title = audio.get("TIT2")
                artist = audio.get("TPE1")
                album = audio.get("TALB")
                year = audio.get("TDRC")
                genre = audio.get("TCON")

                # タグ一覧
                # TIT2 → タイトル
                # TPE1 → アーティスト
                # TALB → アルバム
                # TDRC → 年
                # TCON → ジャンル
                # APIC → 画像（アルバムアート）

                # 値が存在すればその値、無ければデフォルト
                title = title.text[0] if title else file
                artist = artist.text[0] if artist else "Unknown"
                album = album.text[0] if album else "Unknown"
                year = str(year.text[0]) if year else ""
                genre = genre.text[0] if genre else ""

                # サムネイル取得処理
                thumbnail_path = None

                # APICタグが存在するか確認
                if audio.getall("APIC"):
                    # 複数ある場合もあるが最初の1枚を使う
                    apic = audio.getall("APIC")[0]

                    # ファイル名を安全な形に変換
                    safe_name = file.replace(" ", "_").replace(".mp3", "")

                    thumb_filename = f"{safe_name}.jpg"
                    thumbnail_path = os.path.join(THUMB_DIR, thumb_filename)

                    # 画像データを書き出す（バイナリ保存）
                    with open(thumbnail_path, "wb") as img:
                        img.write(apic.data)

                # SQLクエリ実行
                # すでに同じuser_idとfilepathがあれば無視
                c.execute("""
                    INSERT OR IGNORE INTO songs
                    (user_id, title, artist, album, year, genre, filepath, thumbnail)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, title, artist, album, year, genre, path, thumbnail_path))

                print(f"Added: {title}")

            except Exception as e:
                print(f"Error reading {file}: {e}")

# DB変更確定
conn.commit()

# 接続終了
conn.close()

print("Scan complete.")
