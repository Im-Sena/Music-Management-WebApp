import sqlite3

conn = sqlite3.connect("music.db")
c = conn.cursor()

# soundcloud_url カラムが存在するか確認
c.execute("PRAGMA table_info(users)")
columns = [col[1] for col in c.fetchall()]

if "soundcloud_url" not in columns:
    c.execute("ALTER TABLE users ADD COLUMN soundcloud_url TEXT")
    conn.commit()
    print("Added soundcloud_url column to users table")
else:
    print("soundcloud_url column already exists")

if "last_download" not in columns:
    c.execute("ALTER TABLE users ADD COLUMN last_download TIMESTAMP")
    conn.commit()
    print("Added last_download column to users table")
else:
    print("last_download column already exists")

conn.close()
