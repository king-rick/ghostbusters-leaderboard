# app.py
# Ghostbusters Pinball Leaderboard (v2: removed "Machine" input, added default)

import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"  # TODO: set a secure key via env var if deploying

# --- Database ---------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "pinball.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS scores (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      machine TEXT,
      score INTEGER NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_scores_machine ON scores(machine);
    """)
    conn.commit()
    conn.close()

# --- Routes -----------------------------------------------------------

@app.route("/")
def home():
    conn = get_db()
    leaderboard = conn.execute("""
        SELECT name, MAX(score) AS best_score
        FROM scores
        GROUP BY name
        ORDER BY best_score DESC
        LIMIT 10
    """).fetchall()

    recent = conn.execute("""
        SELECT name, score, created_at
        FROM scores
        ORDER BY datetime(created_at) DESC
        LIMIT 20
    """).fetchall()
    conn.close()

    return render_template("index.html", leaderboard=leaderboard, recent=recent)

@app.route("/submit", methods=["POST"])
def submit():
    name = (request.form.get("name") or "").strip()
    score_raw = (request.form.get("score") or "").replace(",", "").strip()

    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("home"))

    try:
        score = int(score_raw)
        if score <= 0:
            raise ValueError
    except ValueError:
        flash("Score must be a positive whole number.", "error")
        return redirect(url_for("home"))

    conn = get_db()
    conn.execute(
        "INSERT INTO scores (name, machine, score, created_at) VALUES (?, ?, ?, ?)",
        (name, 'Ghostbusters', score, datetime.utcnow().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()

    flash("Score submitted!", "ok")
    return redirect(url_for("home"))

# --- Entrypoint -------------------------------------------------------

if __name__ == "__main__":
    init_db()
    import sys
    port = 5000
    if "-p" in sys.argv:
        try:
            port = int(sys.argv[sys.argv.index("-p") + 1])
        except Exception:
            pass
    app.run(debug=True, port=port)