import os
import sqlite3
#mp3からメタデータを読み込むためのライブラリ
from mutagen.id3 import ID3


MUSIC_DIR = "/home/sena/SoundCloud/test/"


conn = sqlite3.connect("music.db")
c = conn.cursor()

for root, _, files in os.walk(MUSIC_DIR):
    for file in files:
        #mp3のみ処理
        if file.endswith(".mp3"):
            path = os.path.join(root, file)

            try:
                #mp3からメタデータを読み込む
                audio = ID3(path)

                title = audio.get("TIT2")
                artist = audio.get("TPE1")
                album = audio.get("TALB")
                year = audio.get("TDRC")
                genre = audio.get("TCON")
                
                #TIT2	タイトル
                #TPE1	アーティスト
                #TALB	アルバム
                #TDRC	年
                #TCON	ジャンル

                #titleが存在すればその値
                #無ければファイル名
                title = title.text[0] if title else file
                artist = artist.text[0] if artist else "Unknown"
                album = album.text[0] if album else "Unknown"
                year = str(year.text[0]) if year else ""
                genre = genre.text[0] if genre else ""

                #SQLクエリを実行
                #すでに同じ filepath があればエラーにせず無視する
                c.execute("""
                    INSERT OR IGNORE INTO songs
                    (title, artist, album, year, genre, filepath)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, artist, album, year, genre, path))

                print(f"Added: {title}")

            except Exception as e:
                print(f"Error reading {file}: {e}")

conn.commit()
conn.close()

print("Scan complete.")
