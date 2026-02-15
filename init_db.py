import sqlite3

def init_database():
    """
    データベースを初期化・マイグレーション
    
    初回起動時：新しいスキーマでテーブル作成
    既存DB時：足りないカラムを自動追加
    """
    conn = sqlite3.connect("music.db")
    c = conn.cursor()

    # === ユーザーテーブル作成 ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # === 曲テーブル作成 ===
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

    # === 自動マイグレーション ===
    # 既存DBに足りないカラムがあれば自動追加
    
    # soundcloud_url カラムをチェック・追加
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    
    if "soundcloud_url" not in columns:
        print("Adding soundcloud_url column to users table...")
        c.execute("ALTER TABLE users ADD COLUMN soundcloud_url TEXT")
        conn.commit()
        print("✓ soundcloud_url column added")
    
    # last_download カラムをチェック・追加
    if "last_download" not in columns:
        print("Adding last_download column to users table...")
        c.execute("ALTER TABLE users ADD COLUMN last_download TIMESTAMP")
        conn.commit()
        print("✓ last_download column added")

    # コミット・クローズ
    conn.commit()
    conn.close()
    
    print("✓ Database initialization complete")


if __name__ == "__main__":
    init_database()


