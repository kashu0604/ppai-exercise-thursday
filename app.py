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


def format_average(value):
    if value is None:
        return None
    return f"{float(value):.2f}"


@app.route("/")
def index():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name FROM students ORDER BY name"
        ).fetchall()
        averages_row = conn.execute(
            """
            SELECT
                AVG(skill_programming),
                AVG(skill_data_stats),
                AVG(skill_frontend_design),
                AVG(skill_business_pitch)
            FROM students
            """
        ).fetchone()

    names = [row[0] for row in rows]
    averages = [
        ("Programming", format_average(averages_row[0])),
        ("Data / stats", format_average(averages_row[1])),
        ("Frontend design", format_average(averages_row[2])),
        ("Business pitch", format_average(averages_row[3])),
    ]
    return render_template("index.html", names=names, averages=averages)


if __name__ == "__main__":
    app.run(debug=True)
