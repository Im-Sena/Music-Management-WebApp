from flask import Flask, request, send_file
import sqlite3

app = Flask(__name__)

#ブラウザで "/" にアクセスされたらこの関数を実行する
@app.route("/")
def index():
    
    #http://localhost:5000/?q=test
    q = request.args.get("q", "")

    conn = sqlite3.connect("music.db")
    c = conn.cursor()

    #検索文字があれば検索モード
    #WHERE title LIKE ? likeは部分一致検索
    if q:
   	    c.execute("""
            SELECT * FROM songs
            WHERE title LIKE ?
            OR artist LIKE ?
            OR album LIKE ?
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))

    else:
        c.execute("SELECT * FROM songs LIMIT 100")

    songs = c.fetchall()
    conn.close()

    html = """
    <h1>Music Search</h1>
    <form>
        <input name="q" placeholder="Search">
        <button type="submit">Search</button>
    </form>
    <ul>
    """

    for song in songs:
        html += f"<li>{song[1]} <a href='/download/{song[0]}'>Download</a></li>"

    html += "</ul>"
    return html


@app.route("/download/<int:id>")
def download(id):
    conn = sqlite3.connect("music.db")
    c = conn.cursor()
    c.execute("SELECT filepath FROM songs WHERE id=?", (id,))
    result = c.fetchone()
    conn.close()

    if result:
        return send_file(result[0], as_attachment=True)
    return "File not found", 404


app.run(host="0.0.0.0", port=5000)
