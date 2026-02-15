# Flask本体と必要な機能を読み込む
from flask import Flask, request, send_file, abort, session, redirect, url_for

# SQLiteデータベース操作用
import sqlite3

# パス操作やセキュリティチェック用
import os
import hashlib


# ==============================
# Flaskアプリを作成
# ==============================
app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"  # 本番環境では環境変数から読み込む


# ==============================
# ヘルパー関数
# ==============================
def hash_password(password):
    """パスワードをハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user_id():
    """セッションから現在のユーザーIDを取得"""
    return session.get("user_id")

def get_current_username():
    """セッションから現在のユーザー名を取得"""
    return session.get("username")


# ======================================================# ======================================================
# ログイン画面
# ======================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        
        conn = sqlite3.connect("music.db")
        c = conn.cursor()
        
        # ユーザーを検索
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and user[1] == hash_password(password):
            # ログイン成功
            session["user_id"] = user[0]
            session["username"] = username
            return redirect(url_for("index"))
        else:
            return """
            <h2>Login Failed</h2>
            <p>Invalid username or password</p>
            <a href="/login">Back to Login</a>
            """
    
    # ログイン画面を表示
    return """
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .login-form { max-width: 300px; margin: 0 auto; }
        input { display: block; width: 100%; margin: 10px 0; padding: 8px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
    </style>
    <h1>Music Management - Login</h1>
    <div class="login-form">
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
    """


# ======================================================
# トップページ（曲一覧・検索）
# ======================================================
@app.route("/")
def index():
    # ログインしているか確認
    if not get_current_user_id():
        return redirect(url_for("login"))

    # URLの ?q=xxx を取得
    q = request.args.get("q", "")
    
    user_id = get_current_user_id()
    username = get_current_username()

    # データベースに接続
    conn = sqlite3.connect("music.db")

    # SQLを実行するためのカーソル作成
    c = conn.cursor()

    # ----------------------------
    # 検索処理
    # ----------------------------
    if q:
        # ユーザーのみの曲を検索
        c.execute("""
            SELECT id, title, artist, album, year, genre, filepath, thumbnail FROM songs
            WHERE user_id = ? AND (title LIKE ? OR artist LIKE ? OR album LIKE ?)
        """, (user_id, f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        # 検索ワードが無い場合は最大100件表示（ユーザーのみ）
        c.execute("""
            SELECT id, title, artist, album, year, genre, filepath, thumbnail FROM songs
            WHERE user_id = ?
            LIMIT 100
        """, (user_id,))

    # SQL実行結果を全て取得
    songs = c.fetchall()

    # データベース接続終了
    conn.close()

    # ----------------------------
    # HTML生成（文字列として組み立て）
    # ----------------------------
    html = f"""
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; }}
        .user-info {{ font-size: 0.9em; color: #666; }}
        .search-form {{ margin-bottom: 20px; }}
        input[type="text"] {{ padding: 8px; width: 300px; }}
        button {{ padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }}
        button:hover {{ background: #0056b3; }}
        .logout {{ background: #dc3545; padding: 5px 10px; text-decoration: none; color: white; border-radius: 3px; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }}
        .song-info {{ display: flex; align-items: center; gap: 15px; }}
        .thumbnail {{ width: 50px; height: 50px; object-fit: cover; border-radius: 5px; }}
        .song-details {{ flex-grow: 1; }}
        .artist {{ color: #666; font-size: 0.9em; }}
    </style>
    <div class="header">
        <h1>Music Management</h1>
        <div>
            <span class="user-info">Logged in as: <strong>{username}</strong></span>
            <a href="/logout" class="logout">Logout</a>
        </div>
    </div>
    
    <div class="search-form">
        <form method="get">
            <input type="text" name="q" placeholder="Search by title, artist, or album" value="{q}">
            <button type="submit">Search</button>
        </form>
    </div>
    
    <ul>
    """

    # 取得した曲を1件ずつ処理
    for song in songs:

        # song の中身
        # song[0] = id
        # song[1] = title
        # song[2] = artist
        # song[3] = album
        # song[4] = year
        # song[5] = genre
        # song[6] = filepath
        # song[7] = thumbnail

        song_id, title, artist, album, year, genre, filepath, thumbnail = song

        thumbnail_html = ""

        # サムネイルが存在する場合のみ表示
        if thumbnail:
            # サムネイルパスはフルパス: /home/sena/SoundCloud/username/thumbnails/image.jpg
            thumbnail_html = f"<img src='/image/{song_id}' class='thumbnail'>"

        # 曲情報をHTMLに追加
        html += f"""
        <li>
            <div class="song-info">
                {thumbnail_html}
                <div class="song-details">
                    <b>{title}</b><br>
                    <span class="artist">{artist}</span>
                    {f"<br><small>{album} ({year})</small>" if album != "Unknown" else ""}
                </div>
                <a href="/download/{song_id}">Download</a>
            </div>
        """

    html += "</ul>"

    # 最終的にHTMLをブラウザへ返す
    return html


# ======================================================
# ログアウト
# ======================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ======================================================
# 画像配信ルート
# ======================================================
@app.route("/image/<int:song_id>")
def serve_image(song_id):
    # ログインしているか確認
    if not get_current_user_id():
        return abort(403)
    
    # データベースから画像パスを取得（ユーザー確認付き）
    conn = sqlite3.connect("music.db")
    c = conn.cursor()
    c.execute("SELECT thumbnail FROM songs WHERE id = ? AND user_id = ?", 
              (song_id, get_current_user_id()))
    result = c.fetchone()
    conn.close()
    
    if not result or not result[0]:
        return abort(404)
    
    file_path = result[0]
    
    # ファイルが存在するか確認
    if not os.path.exists(file_path):
        return abort(404)

    return send_file(file_path)


# ======================================================
# 音楽ダウンロードルート
# ======================================================
@app.route("/download/<int:id>")
def download(id):
    # ログインしているか確認
    if not get_current_user_id():
        return redirect(url_for("login"))

    # データベース接続
    conn = sqlite3.connect("music.db")
    c = conn.cursor()

    # ユーザーチェック付きでファイルパスを取得
    c.execute("SELECT filepath FROM songs WHERE id = ? AND user_id = ?", (id, get_current_user_id()))
    result = c.fetchone()

    conn.close()

    if result:
        return send_file(result[0], as_attachment=True)

    return "File not found", 404


# ======================================================
# Flaskサーバー起動
# ======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
