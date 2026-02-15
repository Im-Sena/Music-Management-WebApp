# Flask本体と必要な機能を読み込む
from flask import Flask, request, send_file, abort, session, redirect, url_for, render_template

# SQLiteデータベース操作用
import sqlite3

# パス操作やセキュリティチェック用
import os
import hashlib

# スケジューラー
from apscheduler.schedulers.background import BackgroundScheduler
from download_service import run_scheduled_downloads

# ==============================
# Flaskアプリを作成
# ==============================
app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"  # 本番環境では環境変数から読み込む

# APScheduler 設定
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=run_scheduled_downloads,
    trigger="cron",
    hour=0,  # 毎日午前0時
    minute=0,
    id="soundcloud_download",
    name="SoundCloud daily download"
)
scheduler.start()


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


# ======================================================
# ======================================================
# ユーザー登録画面
# ======================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    # POST: フォーム送信処理
    if request.method == "POST":
        # フォームから入力値を取得（空文字列がデフォルト値）
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        # SoundCloud URLは任意（後で /profile から追加可能）
        soundcloud_url = request.form.get("soundcloud_url", "")
        
        # === バリデーション ===
        # ユーザー名またはパスワードが空でないか確認
        if not username or not password:
            return """
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .error { color: #dc3545; margin-bottom: 20px; }
            </style>
            <div class="error">
                <h2>Error</h2>
                <p>Username and password are required</p>
                <a href="/register">Back to Register</a>
            </div>
            """
        
        # パスワードと確認パスワードが一致しているか確認
        if password != confirm_password:
            return """
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .error { color: #dc3545; margin-bottom: 20px; }
            </style>
            <div class="error">
                <h2>Error</h2>
                <p>Passwords do not match</p>
                <a href="/register">Back to Register</a>
            </div>
            """
        
        # === データベース処理 ===
        conn = sqlite3.connect("music.db")
        c = conn.cursor()
        
        try:
            # パスワードをSHA256でハッシュ化
            hashed_password = hash_password(password)
            
            # ユーザーレコードを作成（soundcloud_urlは任意、空の場合はNULL）
            c.execute("""
                INSERT INTO users (username, password, soundcloud_url)
                VALUES (?, ?, ?)
            """, (username, hashed_password, soundcloud_url if soundcloud_url else None))
            conn.commit()
            
            # 新しく作成されたユーザーのIDを取得（バックグラウンド処理で必要）
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id = c.fetchone()[0]
            
            # === ユーザーディレクトリ作成 ===
            # ダウンロード音楽の保存先ディレクトリを作成
            user_dir = f"/home/sena/SoundCloud/{username}"
            os.makedirs(user_dir, exist_ok=True)
            
            conn.close()
            
            # === バックグラウンドダウンロード処理 ===
            # SoundCloud URLが指定されていれば、すぐにダウンロード開始
            if soundcloud_url:
                # ローカルインポート（ここでのみ使用するため）
                from threading import Thread
                from download_service import download_and_scan_user
                
                # バックグラウンドスレッドを作成
                # daemon=True で、メインアプリ終了時に自動終了
                # ユーザーはレスポンスを待つ必要なし（非ブロッキング）
                download_thread = Thread(
                    target=download_and_scan_user,
                    args=(user_id, username, soundcloud_url),
                    daemon=True
                )
                # スレッド開始：yt-dlp → scan.py → メタデータ抽出 → thumbnail保存 → DB更新
                download_thread.start()
                
                # ダウンロード中である旨をユーザーに通知
                success_msg = """
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .success { color: #28a745; }
                </style>
                <div class="success">
                    <h2>Registration Successful!</h2>
                    <p>User created successfully.</p>
                    <p><strong>Your SoundCloud likes are being downloaded in the background.</strong></p>
                    <p>Check your profile later to see the download progress.</p>
                    <a href="/login">Go to Login</a>
                </div>
                """
            # URLが指定されなかった場合は、後で /profile から追加できることを説明
            else:
                success_msg = """
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .success { color: #28a745; }
                </style>
                <div class="success">
                    <h2>Registration Successful!</h2>
                    <p>User created successfully. You can now log in.</p>
                    <p>You can add your SoundCloud URL later in your profile to start downloading.</p>
                    <a href="/login">Go to Login</a>
                </div>
                """
            
            return success_msg
        # ユーザー名が既に存在する場合（UNIQUE制約に引っかかった）
        except sqlite3.IntegrityError:
            conn.close()
            return """
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .error { color: #dc3545; margin-bottom: 20px; }
            </style>
            <div class="error">
                <h2>Error</h2>
                <p>Username already exists</p>
                <a href="/register">Back to Register</a>
            </div>
            """
    
    # GET: 登録フォーム画面を表示（テンプレートから）
    return render_template("register.html")


# ======================================================
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
    
    # ログイン画面を表示（テンプレートから）
    return render_template("login.html")


# ======================================================
# プロフィールページ
# ======================================================
@app.route("/profile", methods=["GET", "POST"])
def profile():
    # ログインしているか確認
    if not get_current_user_id():
        return redirect(url_for("login"))
    
    user_id = get_current_user_id()
    username = get_current_username()
    
    if request.method == "POST":
        soundcloud_url = request.form.get("soundcloud_url", "")
        
        conn = sqlite3.connect("music.db")
        c = conn.cursor()
        c.execute("""
            UPDATE users SET soundcloud_url = ? WHERE id = ?
        """, (soundcloud_url, user_id))
        conn.commit()
        
        # 現在のURLを取得
        c.execute("SELECT soundcloud_url FROM users WHERE id = ?", (user_id,))
        current_url = c.fetchone()[0]
        conn.close()
        
        return f"""
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .success {{ color: #28a745; margin-bottom: 20px; }}
            input {{ display: block; width: 100%; margin: 10px 0; padding: 8px; }}
            button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }}
            button:hover {{ background: #0056b3; }}
            .back-link {{ margin-top: 20px; }}
            .back-link a {{ color: #007bff; text-decoration: none; }}
        </style>
        <div class="container">
            <h1>Profile - {username}</h1>
            <div class="success">✓ SoundCloud URL updated successfully!</div>
            <p>Current URL: <strong>{current_url if current_url else 'Not set'}</strong></p>
            <p>Your music will be automatically downloaded from this URL once per day.</p>
            <div class="back-link">
                <a href="/">Back to Music Library</a>
            </div>
        </div>
        """
    
    # GET リクエスト：プロフィール表示
    conn = sqlite3.connect("music.db")
    c = conn.cursor()
    c.execute("""
        SELECT soundcloud_url, last_download FROM users WHERE id = ?
    """, (user_id,))
    result = c.fetchone()
    conn.close()
    
    soundcloud_url = result[0] if result and result[0] else ""
    last_download = result[1] if result and result[1] else "Never"
    
    return f"""
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .form-group {{ margin-bottom: 20px; }}
        label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
        input {{ display: block; width: 100%; padding: 10px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px; }}
        button:hover {{ background: #0056b3; }}
        .info {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .info p {{ margin: 10px 0; }}
        .back-link {{ margin-top: 20px; }}
        .back-link a {{ color: #007bff; text-decoration: none; }}
    </style>
    <div class="container">
        <h1>Profile - {username}</h1>
        
        <div class="info">
            <p><strong>Last Download:</strong> {last_download}</p>
            <p>Your music will be automatically downloaded from your SoundCloud likes once per day.</p>
        </div>
        
        <form method="post">
            <div class="form-group">
                <label for="soundcloud_url">SoundCloud Likes URL:</label>
                <input type="url" id="soundcloud_url" name="soundcloud_url" 
                       placeholder="https://soundcloud.com/your-username/likes" 
                       value="{soundcloud_url}">
                <small>Example: https://soundcloud.com/your-username/likes</small>
            </div>
            <button type="submit">Save SoundCloud URL</button>
            <a href="/" style="color: #007bff; text-decoration: none;">Back to Music Library</a>
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
            <a href="/profile" style="color: #007bff; text-decoration: none; margin-left: 15px;">Profile</a>
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
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        scheduler.shutdown()
