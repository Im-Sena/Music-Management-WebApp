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

# DB初期化・マイグレーション
from init_db import init_database

# ==============================
# Flaskアプリを作成
# ==============================
# アプリ起動時にDBを初期化
init_database()

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
        conn.close()
        
        # 更新後、同じページにリダイレクト（更新完了メッセージを表示する場合は別途実装）
        return redirect(url_for("profile"))
    
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
    
    # ログファイルがあるか確認
    logs_dir = "logs"
    log_files_available = False
    if os.path.exists(logs_dir):
        for filename in os.listdir(logs_dir):
            if filename.startswith(f"download_{username}_") and filename.endswith(".log"):
                log_files_available = True
                break
    
    return render_template(
        "profile.html",
        username=username,
        soundcloud_url=soundcloud_url,
        last_download=last_download,
        log_files_available=log_files_available
    )


# === トップページ（曲一覧・検索）===
@app.route("/")
def index():
    # ログインしているか確認
    if not get_current_user_id():
        return redirect(url_for("login"))

    # URLの ?q=xxx を取得（検索キーワード）
    q = request.args.get("q", "")
    
    user_id = get_current_user_id()

    # データベースに接続
    conn = sqlite3.connect("music.db")
    c = conn.cursor()

    # === 検索処理 ===
    if q:
        # ユーザーの曲から検索
        c.execute("""
            SELECT id, title, artist, album, year, genre, filepath, thumbnail FROM songs
            WHERE user_id = ? AND (title LIKE ? OR artist LIKE ? OR album LIKE ?)
            ORDER BY title ASC
        """, (user_id, f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        # 検索ワードが無い場合は全て表示
        c.execute("""
            SELECT id, title, artist, album, year, genre, filepath, thumbnail FROM songs
            WHERE user_id = ?
            ORDER BY title ASC
        """, (user_id,))

    # SQL実行結果を全て取得
    songs = c.fetchall()
    conn.close()

    # テンプレートにデータを渡して返す
    return render_template("library.html", songs=songs, q=q)


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
# プレイヤーページ
# ======================================================
@app.route("/player/<int:song_id>")
def player(song_id):
    """
    音楽再生ページ
    
    指定された曲を再生するページを表示
    次の曲・前の曲への移動もサポート
    """
    # ログインしているか確認
    if not get_current_user_id():
        return redirect(url_for("login"))

    user_id = get_current_user_id()

    conn = sqlite3.connect("music.db")
    c = conn.cursor()

    # === 指定された曲の情報を取得 ===
    c.execute("""
        SELECT id, title, artist, album, year, genre, filepath, thumbnail FROM songs
        WHERE id = ? AND user_id = ?
    """, (song_id, user_id))
    
    song = c.fetchone()

    if not song:
        conn.close()
        return "Song not found", 404

    # === ユーザーの曲を全て取得（プレイリスト用） ===
    c.execute("""
        SELECT id, title, artist, album, year, genre, filepath, thumbnail FROM songs
        WHERE user_id = ?
        ORDER BY title ASC
    """, (user_id,))
    
    all_songs = c.fetchall()
    conn.close()

    # === 前の曲・次の曲を取得 ===
    current_index = None
    prev_song = None
    next_song = None

    for idx, s in enumerate(all_songs):
        if s[0] == song_id:
            current_index = idx
            if idx > 0:
                prev_song = all_songs[idx - 1]
            if idx < len(all_songs) - 1:
                next_song = all_songs[idx + 1]
            break

    total_songs = len(all_songs)

    # テンプレートにデータを渡す
    return render_template(
        "player.html",
        song=song,
        prev_song=prev_song,
        next_song=next_song,
        current_index=current_index,
        total_songs=total_songs
    )


# ======================================================
# ダウンロードログビューア
# ======================================================
@app.route("/logs")
def view_logs():
    """
    ユーザーのダウンロードログを表示
    ログファイル: logs/download_[username]_[date].log
    """
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    
    # ユーザー情報を取得
    conn = sqlite3.connect("music.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        abort(404)
    
    username = result[0]
    
    # ログディレクトリから該当ユーザーのログファイルを探す
    logs_dir = "logs"
    log_files = []
    
    if os.path.exists(logs_dir):
        for filename in os.listdir(logs_dir):
            # logs/download_[username]_[date].log の形式
            if filename.startswith(f"download_{username}_") and filename.endswith(".log"):
                log_files.append(filename)
    
    # ファイルを日付の降順でソート（新しい順）
    log_files.sort(reverse=True)
    
    # 各ログファイルの内容を読み込み
    logs_content = {}
    for filename in log_files:
        log_path = os.path.join(logs_dir, filename)
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs_content[filename] = f.read()
        except Exception as e:
            logs_content[filename] = f"Error reading log: {str(e)}"
    
    return render_template(
        "logs.html",
        username=username,
        log_files=log_files,
        logs_content=logs_content
    )


# ======================================================
# Flaskサーバー起動
# ======================================================
if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        scheduler.shutdown()
