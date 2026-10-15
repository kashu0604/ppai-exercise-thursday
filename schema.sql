-- Student intake: 3NF schema (PostgreSQL)

CREATE TABLE students (
    netid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    school_year TEXT NOT NULL
        CHECK (school_year IN ('First-year', 'Sophomore', 'Junior', 'Senior')),
    intro_programming TEXT NOT NULL
        CHECK (intro_programming IN ('took_it', 'equivalent', 'neither')),
    skill_programming INTEGER NOT NULL
        CHECK (skill_programming BETWEEN 1 AND 5),
    skill_data_stats INTEGER NOT NULL
        CHECK (skill_data_stats BETWEEN 1 AND 5),
    skill_frontend_design INTEGER NOT NULL
        CHECK (skill_frontend_design BETWEEN 1 AND 5),
    skill_business_pitch INTEGER NOT NULL
        CHECK (skill_business_pitch BETWEEN 1 AND 5),
    working_style TEXT,
    interests TEXT,
    semester_goal TEXT,
    submitted_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE tools (
    tool_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE student_tools (
    netid TEXT NOT NULL REFERENCES students (netid) ON DELETE CASCADE,
    tool_id INTEGER NOT NULL REFERENCES tools (tool_id) ON DELETE CASCADE,
    PRIMARY KEY (netid, tool_id)
);

CREATE TABLE availability_slots (
    slot_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE student_availability (
    netid TEXT NOT NULL REFERENCES students (netid) ON DELETE CASCADE,
    slot_id INTEGER NOT NULL REFERENCES availability_slots (slot_id) ON DELETE CASCADE,
    PRIMARY KEY (netid, slot_id)
);
