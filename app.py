from flask import Flask, render_template, request, redirect, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Secret key: take from env in prod; safe default for local dev
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

# SQLite DB path: override on Render with DB_PATH=/tmp/pinball.db
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "pinball.db"))

# ---------- DATABASE HELPERS ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ---------- ROUTES ----------
@app.route("/")
def index():
    conn = get_db()
    leaderboard = conn.execute(
        "SELECT name, score, created_at FROM scores ORDER BY score DESC LIMIT 10"
    ).fetchall()
    recent = conn.execute(
        "SELECT name, score, created_at FROM scores ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return render_template("index.html", leaderboard=leaderboard, recent=recent)

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "").strip()
    score_text = request.form.get("score", "").replace(",", "").strip()

    if not name or not score_text.isdigit():
        flash("Invalid name or score.", "error")
        return redirect("/")

    score = int(score_text)
    conn = get_db()
    conn.execute(
        "INSERT INTO scores (name, score, created_at) VALUES (?, ?, ?)",
        (name, score, datetime.utcnow().isoformat(timespec="seconds"))
    )
    conn.commit()
    conn.close()
    # fun randomized banner handled in template via flash text
    flash("Score submitted successfully!", "ok")
    return redirect("/")

@app.route("/clear", methods=["POST"])
def clear():
    conn = get_db()
    conn.execute("DELETE FROM scores")
    conn.commit()
    conn.close()
    flash("Leaderboard cleared.", "ok")
    return redirect("/")

# ---------- APP STARTUP (dev only; Gunicorn runs app:app in prod) ----------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5001))
    # No debug flag here to satisfy security scanners.
    app.run(host="127.0.0.1", port=port)