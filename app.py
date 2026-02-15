# Flask本体と必要な機能を読み込む
from flask import Flask, request, send_file, abort

# SQLiteデータベース操作用
import sqlite3

# パス操作やセキュリティチェック用
import os


# ==============================
# Flaskアプリを作成
# ==============================
app = Flask(__name__)


# ==============================
# 画像フォルダ設定
# ==============================
# ここを変更するだけで画像保存場所を変更できる
# 絶対パスで指定している
IMAGE_DIR = "/home/sena/app/static/thumbnails"


# ======================================================
# トップページ（曲一覧・検索）
# ======================================================
@app.route("/")
def index():

    # URLの ?q=xxx を取得
    # 例: http://localhost:5000/?q=test
    # qが無ければ空文字になる
    q = request.args.get("q", "")

    # データベースに接続
    conn = sqlite3.connect("music.db")

    # SQLを実行するためのカーソル作成
    c = conn.cursor()

    # ----------------------------
    # 検索処理
    # ----------------------------
    if q:
        # LIKE を使った部分一致検索
        # %文字% で「含む」検索になる
        # ? を使うのはSQLインジェクション対策
        c.execute("""
            SELECT * FROM songs
            WHERE title LIKE ?
            OR artist LIKE ?
            OR album LIKE ?
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        # 検索ワードが無い場合は最大100件表示
        c.execute("SELECT * FROM songs LIMIT 100")

    # SQL実行結果を全て取得
    songs = c.fetchall()

    # データベース接続終了
    conn.close()

    # ----------------------------
    # HTML生成（文字列として組み立て）
    # ----------------------------
    html = """
    <h1>Music Search</h1>
    <form>
        <input name="q" placeholder="Search">
        <button type="submit">Search</button>
    </form>
    <ul>
    """

    # 取得した曲を1件ずつ処理
    for song in songs:

        # song の中身（例）
        # song[0] = id
        # song[1] = title
        # song[2] = artist
        # song[3] = album
        # song[4] = year
        # song[5] = genre
        # song[6] = filepath
        # song[7] = thumbnail

        thumbnail_html = ""

        # サムネイルが存在する場合のみ表示
        if song[7]:

            # フルパスが入っている可能性があるので
            # ファイル名だけ取り出す
            # 例:
            # /home/sena/.../thumbnail/a.jpg
            # → a.jpg
            filename = os.path.basename(song[7])

            # 画像は /image/ ルート経由で配信する
            # ブラウザはサーバー内部パスを直接読めないため
            # Flaskを経由して配信する必要がある
            thumbnail_html = f"<img src='/image/{filename}' width='120'><br>"

        # 曲情報をHTMLに追加
        html += f"""
        <li>
            {thumbnail_html}
            <b>{song[1]}</b><br>
            {song[2]}<br>
            <a href='/download/{song[0]}'>Download</a>
        </li>
        """

    html += "</ul>"

    # 最終的にHTMLをブラウザへ返す
    return html


# ======================================================
# 画像配信ルート
# ======================================================
# /image/xxx.jpg にアクセスされたらこの関数が実行される
@app.route("/image/<path:filename>")
def serve_image(filename):

    # 画像のフルパスを作る
    # IMAGE_DIR + ファイル名
    file_path = os.path.join(IMAGE_DIR, filename)

    # ----------------------------
    # セキュリティ対策
    # ----------------------------
    # ../ を使ったディレクトリ攻撃を防ぐ
    # 画像フォルダ外にアクセスできないようにする
    if not os.path.abspath(file_path).startswith(os.path.abspath(IMAGE_DIR)):
        return abort(403)  # アクセス禁止

    # ファイルが存在しなければ404
    if not os.path.exists(file_path):
        return abort(404)

    # 画像をブラウザへ送信
    return send_file(file_path)


# ======================================================
# 音楽ダウンロードルート
# ======================================================
# /download/5 のようにアクセスすると実行される
@app.route("/download/<int:id>")
def download(id):

    # データベース接続
    conn = sqlite3.connect("music.db")
    c = conn.cursor()

    # 指定されたIDの音楽ファイルパスを取得
    c.execute("SELECT filepath FROM songs WHERE id=?", (id,))
    result = c.fetchone()

    conn.close()

    # ファイルが存在すれば送信
    # as_attachment=True により「ダウンロード」扱いになる
    if result:
        return send_file(result[0], as_attachment=True)

    # 無ければ404
    return "File not found", 404


# ======================================================
# Flaskサーバー起動
# ======================================================
# 0.0.0.0 にすることで外部からもアクセス可能
# port=5000 で起動
app.run(host="0.0.0.0", port=5000)
