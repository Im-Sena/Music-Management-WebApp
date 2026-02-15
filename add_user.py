import sqlite3
import sys
import hashlib

def hash_password(password):
    """パスワードをハッシュ化（簡易版。本番はbcryptを使用）"""
    return hashlib.sha256(password.encode()).hexdigest()

if len(sys.argv) < 2:
    print("Usage: python add_user.py <username> [password]")
    print("If password is not provided, you will be prompted to enter it")
    sys.exit(1)

USERNAME = sys.argv[1]

# パスワード入力
if len(sys.argv) >= 3:
    PASSWORD = sys.argv[2]
else:
    import getpass
    PASSWORD = getpass.getpass("Enter password: ")

conn = sqlite3.connect("music.db")
c = conn.cursor()

try:
    hashed_password = hash_password(PASSWORD)
    c.execute("""
        INSERT INTO users (username, password)
        VALUES (?, ?)
    """, (USERNAME, hashed_password))
    conn.commit()
    print(f"User '{USERNAME}' created successfully!")
except sqlite3.IntegrityError:
    print(f"User '{USERNAME}' already exists!")
finally:
    conn.close()
