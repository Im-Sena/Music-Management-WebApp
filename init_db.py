import sqlite3
#music.dbに接続
conn = sqlite3.connect("music.db")
#sqlを実行するためのカーソル
c = conn.cursor()

# ユーザーテーブル
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 曲テーブル（user_idを追加）
c.execute("""
CREATE TABLE IF NOT EXISTS songs (
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
""")

#変更を確定
conn.commit()

conn.close()

print("Database initialized.")

