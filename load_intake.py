"""Load class_dataset.csv into the student-intake PostgreSQL schema."""

from __future__ import annotations

import csv
import os
import re
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "class_dataset.csv"
SCHEMA_PATH = ROOT / "schema.sql"
EMAIL_SUFFIX = re.compile(r"@nyu\.edu$", re.IGNORECASE)


def clean_netid(raw: str) -> str:
    return EMAIL_SUFFIX.sub("", raw.strip())


def nullable_text(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = raw.strip()
    if not value or value == "#NAME?":
        return None
    return value


def split_semicolon(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split(";") if part.strip()]


def parse_submitted_at(raw: str) -> datetime:
    return datetime.fromisoformat(raw.strip())


def reset_schema(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        DROP TABLE IF EXISTS student_availability CASCADE;
        DROP TABLE IF EXISTS student_tools CASCADE;
        DROP TABLE IF EXISTS availability_slots CASCADE;
        DROP TABLE IF EXISTS tools CASCADE;
        DROP TABLE IF EXISTS students CASCADE;
        """
    )
    conn.execute(SCHEMA_PATH.read_text())


def load_rows(conn: psycopg.Connection) -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    tool_ids: dict[str, int] = {}
    slot_ids: dict[str, int] = {}

    for row in rows:
        netid = clean_netid(row["netid"])
        conn.execute(
            """
            INSERT INTO students (
                netid, name, school_year, intro_programming,
                skill_programming, skill_data_stats,
                skill_frontend_design, skill_business_pitch,
                working_style, interests, semester_goal, submitted_at
            ) VALUES (
                %(netid)s, %(name)s, %(school_year)s, %(intro_programming)s,
                %(skill_programming)s, %(skill_data_stats)s,
                %(skill_frontend_design)s, %(skill_business_pitch)s,
                %(working_style)s, %(interests)s, %(semester_goal)s,
                %(submitted_at)s
            )
            """,
            {
                "netid": netid,
                "name": row["name"].strip(),
                "school_year": row["school_year"].strip(),
                "intro_programming": row["intro_programming"].strip(),
                "skill_programming": int(row["skill_programming"]),
                "skill_data_stats": int(row["skill_data_stats"]),
                "skill_frontend_design": int(row["skill_frontend_design"]),
                "skill_business_pitch": int(row["skill_business_pitch"]),
                "working_style": nullable_text(row["working_style"]),
                "interests": nullable_text(row["interests"]),
                "semester_goal": nullable_text(row["semester_goal"]),
                "submitted_at": parse_submitted_at(row["submitted_at"]),
            },
        )

        for tool_name in split_semicolon(row["tools"]):
            if tool_name not in tool_ids:
                tool_id = conn.execute(
                    """
                    INSERT INTO tools (name) VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING tool_id
                    """,
                    (tool_name,),
                ).fetchone()[0]
                tool_ids[tool_name] = tool_id
            conn.execute(
                """
                INSERT INTO student_tools (netid, tool_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (netid, tool_ids[tool_name]),
            )

        for slot_name in split_semicolon(row["availability"]):
            if slot_name not in slot_ids:
                slot_id = conn.execute(
                    """
                    INSERT INTO availability_slots (name) VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING slot_id
                    """,
                    (slot_name,),
                ).fetchone()[0]
                slot_ids[slot_name] = slot_id
            conn.execute(
                """
                INSERT INTO student_availability (netid, slot_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (netid, slot_ids[slot_name]),
            )


def print_counts(conn: psycopg.Connection) -> None:
    tables = [
        "students",
        "tools",
        "student_tools",
        "availability_slots",
        "student_availability",
    ]
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")

    cleaned = conn.execute(
        "SELECT netid FROM students WHERE netid IN ('yo2162', 'ryf2010') ORDER BY netid"
    ).fetchall()
    print("cleaned email netids:", [row[0] for row in cleaned])

    null_style = conn.execute(
        "SELECT COUNT(*) FROM students WHERE working_style IS NULL"
    ).fetchone()[0]
    print(f"students with NULL working_style: {null_style}")


def database_url() -> str:
    load_dotenv(ROOT / ".env")
    dsn = os.environ.get("DATABASE_URL")
    if dsn:
        return dsn
    env_path = ROOT / ".env"
    if env_path.exists():
        first_line = env_path.read_text().strip().splitlines()[0].strip()
        if first_line.startswith("postgresql://") or first_line.startswith("postgres://"):
            return first_line
    raise SystemExit("DATABASE_URL is not set")


def main() -> None:
    dsn = database_url()

    with psycopg.connect(dsn) as conn:
        reset_schema(conn)
        load_rows(conn)
        print_counts(conn)
        conn.commit()


if __name__ == "__main__":
    main()
