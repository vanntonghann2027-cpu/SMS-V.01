#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to create SMS-V.01 SQLite Database (.db file)
Compatible with SQLite 3, DB Browser for SQLite, and SMS Cambodia Web App.
"""

import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "sms_database.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Students Table (Enhanced for GEIP Project School / សាលាគម្រោង)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id TEXT PRIMARY KEY,
        khmer_name TEXT NOT NULL,
        latin_name TEXT,
        gender TEXT CHECK(gender IN ('ប្រុស', 'ស្រី')),
        dob TEXT,
        class TEXT,
        class_type TEXT,
        phone TEXT,
        guardian TEXT,
        address TEXT,
        province_code TEXT,
        district_code TEXT,
        commune_code TEXT,
        village_code TEXT,
        geip_id TEXT,
        last_name TEXT,
        first_name TEXT,
        age INTEGER,
        pisa TEXT,
        student_type TEXT,
        condition TEXT,
        from_school_type TEXT,
        school_affiliation TEXT,
        previous_school TEXT,
        pob TEXT,
        indigenous TEXT,
        disability TEXT,
        assistive_device TEXT,
        orphan TEXT,
        id_poor TEXT,
        scholarship TEXT,
        insurance_card_no TEXT,
        birth_cert_no TEXT,
        student_phone TEXT,
        father_name TEXT,
        father_job TEXT,
        father_phone TEXT,
        mother_name TEXT,
        mother_job TEXT,
        mother_phone TEXT,
        guardian_job TEXT,
        guardian_address TEXT,
        caregiver_name TEXT,
        caregiver_job TEXT,
        caregiver_phone TEXT,
        caregiver_address TEXT,
        family_shelter TEXT,
        family_income TEXT,
        migration TEXT,
        domestic_violence TEXT,
        living_condition TEXT,
        siblings TEXT,
        chronic_disease TEXT,
        life_threatening_illness TEXT,
        health_issues TEXT,
        treatment_plan TEXT,
        treatment_means TEXT,
        health_provider TEXT,
        health_provider_phone TEXT,
        weight REAL,
        height REAL,
        bmi REAL,
        assessment_result TEXT,
        nutrition_issue TEXT,
        nutrition_intervention TEXT,
        student_status TEXT,
        status_date TEXT,
        dropout_reason TEXT,
        study_plan TEXT,
        youth_council_role TEXT,
        parent_participation TEXT,
        parent_request TEXT
    );
    """)
    # Add GEIP columns via safe ALTER TABLE
    geip_cols = [
        ("province_code", "TEXT"), ("district_code", "TEXT"), ("commune_code", "TEXT"), ("village_code", "TEXT"),
        ("pob_province_code", "TEXT"), ("pob_district_code", "TEXT"), ("pob_commune_code", "TEXT"), ("pob_village_code", "TEXT"),
        ("geip_id", "TEXT"), ("last_name", "TEXT"), ("first_name", "TEXT"), ("age", "INTEGER"), ("pisa", "TEXT"),
        ("student_type", "TEXT"), ("condition", "TEXT"), ("from_school_type", "TEXT"), ("school_affiliation", "TEXT"),
        ("previous_school", "TEXT"), ("pob", "TEXT"), ("indigenous", "TEXT"), ("disability", "TEXT"),
        ("assistive_device", "TEXT"), ("orphan", "TEXT"), ("id_poor", "TEXT"), ("scholarship", "TEXT"),
        ("insurance_card_no", "TEXT"), ("birth_cert_no", "TEXT"), ("student_phone", "TEXT"),
        ("father_name", "TEXT"), ("father_job", "TEXT"), ("father_phone", "TEXT"),
        ("mother_name", "TEXT"), ("mother_job", "TEXT"), ("mother_phone", "TEXT"),
        ("guardian_job", "TEXT"), ("guardian_address", "TEXT"),
        ("caregiver_name", "TEXT"), ("caregiver_job", "TEXT"), ("caregiver_phone", "TEXT"), ("caregiver_address", "TEXT"),
        ("family_shelter", "TEXT"), ("family_income", "TEXT"), ("migration", "TEXT"), ("domestic_violence", "TEXT"),
        ("living_condition", "TEXT"), ("siblings", "TEXT"), ("chronic_disease", "TEXT"),
        ("life_threatening_illness", "TEXT"), ("health_issues", "TEXT"), ("treatment_plan", "TEXT"),
        ("treatment_means", "TEXT"), ("health_provider", "TEXT"), ("health_provider_phone", "TEXT"),
        ("weight", "REAL"), ("height", "REAL"), ("bmi", "REAL"), ("assessment_result", "TEXT"),
        ("nutrition_issue", "TEXT"), ("nutrition_intervention", "TEXT"), ("student_status", "TEXT"),
        ("status_date", "TEXT"), ("dropout_reason", "TEXT"), ("study_plan", "TEXT"),
        ("youth_council_role", "TEXT"), ("parent_participation", "TEXT"), ("parent_request", "TEXT")
    ]
    for col_name, col_type in geip_cols:
        try: cursor.execute(f"ALTER TABLE students ADD COLUMN {col_name} {col_type};")
        except sqlite3.OperationalError: pass

    # 2. Subjects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        max_score REAL DEFAULT 100.0,
        coefficient REAL DEFAULT 1.0,
        is_enabled INTEGER DEFAULT 1
    );
    """)

    # 3. Scores Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        student_id TEXT,
        period_key TEXT,
        subject_code TEXT,
        score REAL,
        PRIMARY KEY (student_id, period_key, subject_code),
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_code) REFERENCES subjects(code) ON DELETE CASCADE
    );
    """)

    # 4. Exam Arrangements Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exam_arrangements (
        student_id TEXT PRIMARY KEY,
        khmer_name TEXT,
        room_number TEXT,
        desk_number TEXT,
        secret_code TEXT,
        grade TEXT,
        status TEXT
    );
    """)

    # 5. Administrative Divisions (Cambodia Geography: Provinces, Districts, Communes, Villages)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS administrative_divisions (
        code TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        name_khmer TEXT NOT NULL,
        name_latin TEXT,
        parent_code TEXT,
        reference TEXT,
        official_note TEXT,
        note_by_checker TEXT
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_parent ON administrative_divisions(parent_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_type ON administrative_divisions(type);")

    # Convenient Views
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_provinces AS 
    SELECT code, name_khmer, name_latin 
    FROM administrative_divisions 
    WHERE type = 'ខេត្ត'
    ORDER BY CAST(code AS INTEGER);
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_districts AS 
    SELECT code, type, name_khmer, name_latin, parent_code AS province_code 
    FROM administrative_divisions 
    WHERE type IN ('ស្រុក', 'ក្រុង', 'ខណ្ឌ')
    ORDER BY code;
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_communes AS 
    SELECT code, type, name_khmer, name_latin, parent_code AS district_code 
    FROM administrative_divisions 
    WHERE type IN ('ឃុំ', 'សង្កាត់')
    ORDER BY code;
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_villages AS 
    SELECT code, name_khmer, name_latin, parent_code AS commune_code 
    FROM administrative_divisions 
    WHERE type = 'ភូមិ'
    ORDER BY code;
    """)

    # Seed Administrative Divisions from CSV if available
    csv_geo_path = os.path.join(os.path.dirname(__file__), "administrative_divisions.csv")
    if os.path.exists(csv_geo_path):
        import csv
        with open(csv_geo_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            rows = [r for r in reader if r]
            cursor.executemany("""
            INSERT OR REPLACE INTO administrative_divisions 
            (code, type, name_khmer, name_latin, parent_code, reference, official_note, note_by_checker)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, rows)

    # 6. Default Standard Subjects
    default_subjects = [
        ('kh', 'ភាសាខ្មែរ', 100.0, 2.0, 1),
        ('math', 'គណិតវិទ្យា', 100.0, 2.0, 1),
        ('phy', 'រូបវិទ្យា', 100.0, 1.5, 1),
        ('chem', 'គីមីវិទ្យា', 100.0, 1.5, 1),
        ('bio', 'ជីវវិទ្យា', 100.0, 1.5, 1),
        ('hist', 'ប្រវត្តិវិទ្យា', 100.0, 1.0, 1),
        ('geo', 'ភូមិវិទ្យា', 100.0, 1.0, 1),
        ('mor', 'សីលធម៌-ពលរដ្ឋ', 100.0, 1.0, 1),
        ('eng', 'ភាសាអង់គ្លេស', 100.0, 1.0, 1),
        ('earth', 'ផែនដីវិទ្យា', 100.0, 1.0, 1),
        ('sport', 'កីឡា', 100.0, 1.0, 1)
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO subjects (code, name, max_score, coefficient, is_enabled)
    VALUES (?, ?, ?, ?, ?);
    """, default_subjects)

    conn.commit()
    conn.close()
    print(f"Successfully generated SQLite Database file at: {DB_PATH}")

if __name__ == "__main__":
    init_db()

