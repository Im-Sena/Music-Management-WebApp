import sqlite3
#music.dbに接続
conn = sqlite3.connect("music.db")
#sqlを実行するためのカーソル
c = conn.cursor()

c.execute("""
CREATE TABLE songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    artist TEXT,
    album TEXT,
    year TEXT,
    genre TEXT,
    filepath TEXT UNIQUE,
    thumbnail TEXT
)
""")

#INTEGER PRIMARY KEY AUTOINCREMENT　は自動で増える番号
#filepath TEXT UNIQUE -> 同じ曲を2回登録できない。

#変更を確定
conn.commit()

conn.close()

print("Database initialized.")

