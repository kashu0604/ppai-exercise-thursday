import os

import psycopg
from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()

app = Flask(__name__)


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(database_url)


@app.route("/")
def index():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name FROM students ORDER BY name"
        ).fetchall()
    names = [row[0] for row in rows]
    return render_template("index.html", names=names)


if __name__ == "__main__":
    app.run(debug=True)
