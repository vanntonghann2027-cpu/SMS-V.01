-- ============================================================================
-- ប្រព័ន្ធគ្រប់គ្រងពិន្ទុសិស្ស - SMS v0.1 (Student Management System Cambodia)
-- PostgreSQL Database Schema (ស្តង់ដារក្រសួងអប់រំ យុវជន និងកីឡា)
-- ============================================================================

-- 1. បង្កើត Extensions សំខាន់ៗ (ប្រសិនបើដំណើរការលើ Supabase ឬ PostgreSQL Server)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. តារាងឆ្នាំសិក្សា (Academic Years)
CREATE TABLE IF NOT EXISTS academic_years (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    year_name VARCHAR(50) NOT NULL UNIQUE, -- ឧ. '២០២៥-២០២៦', '២០២៦-២០២៧'
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. តារាងកម្រិតថ្នាក់ (Classes & Grades)
CREATE TABLE IF NOT EXISTS classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    academic_year_id UUID REFERENCES academic_years(id) ON DELETE CASCADE,
    grade_level VARCHAR(50) NOT NULL, -- 'grade_7', 'grade_8', 'grade_9', 'grade_10', 'grade_11_sci', 'grade_11_soc', 'grade_12_sci', 'grade_12_soc'
    class_name VARCHAR(100) NOT NULL, -- ឧ. 'ថ្នាក់ទី១២ វិទ្យាសាស្ត្រ', 'ថ្នាក់ទី ៧A'
    room_number VARCHAR(50),
    teacher_name VARCHAR(150), -- ឈ្មោះគ្រូបន្ទុកថ្នាក់
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. តារាងមុខវិជ្ជា និងមេគុណ (Subjects & Coefficients)
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL, -- ឧ. 'math', 'kh', 'phy', 'chem', 'bio'
    name VARCHAR(150) NOT NULL, -- ឧ. 'គណិតវិទ្យា', 'ភាសាខ្មែរ'
    max_score NUMERIC(5, 2) NOT NULL DEFAULT 100.00, -- 50, 75, 100, 125
    coefficient NUMERIC(3, 1) NOT NULL DEFAULT 1.0, -- 1.0, 1.5, 2.0
    is_enabled BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, code)
);

-- 5. តារាងព័ត៌មានសិស្ស (Students Information)
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id UUID REFERENCES classes(id) ON DELETE SET NULL,
    student_code VARCHAR(50) NOT NULL UNIQUE, -- ឧ. 'STU-001'
    khmer_name VARCHAR(150) NOT NULL, -- ឧ. 'សុខ ចិន្តា'
    latin_name VARCHAR(150), -- ឧ. 'SOK CHINDA'
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('ប្រុស', 'ស្រី')),
    dob DATE, -- ថ្ងៃខែឆ្នាំកំណើត
    phone VARCHAR(50),
    guardian_name VARCHAR(150), -- ឈ្មោះអាណាព្យាបាល
    address TEXT, -- អាសយដ្ឋានបច្ចុប្បន្ន
    avatar_url TEXT, -- រូបថតសិស្ស
    status VARCHAR(50) DEFAULT 'កំពុងរៀន', -- 'កំពុងរៀន', 'ឈប់រៀន', 'ផ្ទេរចេញ'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. តារាងពិន្ទុតាមមុខវិជ្ជា និងតាមខែ/ឆមាស (Scores Table)
-- គាំទ្ររាល់ ២១ periods: test_early, m01..m12, sem1_exam, sem1_monthly_avg, sem1_overall, sem2_exam, sem2_monthly_avg, sem2_overall, yearly
CREATE TABLE IF NOT EXISTS scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    period_key VARCHAR(50) NOT NULL, -- 'test_early', 'm01', 'm02', 'sem1_exam', 'yearly', ល.
    score_value NUMERIC(5, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, subject_id, period_key)
);

-- 7. តារាងសង្ខេបលទ្ធផល និងចំណាត់ថ្នាក់ (Period Results & Ranking Summary)
CREATE TABLE IF NOT EXISTS period_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    period_key VARCHAR(50) NOT NULL,
    total_score NUMERIC(8, 2) DEFAULT 0.00, -- ពិន្ទុសរុបគុណមេគុណ
    average NUMERIC(5, 2) DEFAULT 0.00, -- មធ្យមភាគ
    percentage NUMERIC(5, 2) DEFAULT 0.00, -- ភាគរយលើ 100%
    rank INT, -- ចំណាត់ថ្នាក់ (លេខ១, លេខ២...)
    mention VARCHAR(5), -- A, B, C, D, E, F
    mention_khmer VARCHAR(50), -- ល្អប្រសើរ, ល្អណាស់, ល្អ, ល្អបង្គួរ, មធ្យម, ខ្សោយ
    is_passed BOOLEAN DEFAULT FALSE, -- ជាប់ ឬធ្លាក់
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, period_key)
);

-- 8. តារាងរៀបចំការប្រឡង និងអក្សរសម្ងាត់ (Exam Arrangements & Secret Codes)
CREATE TABLE IF NOT EXISTS exam_arrangements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    exam_name VARCHAR(150) DEFAULT 'ការប្រឡងឆមាស',
    academic_year VARCHAR(50) DEFAULT '២០២៦-២០២៧',
    grade_level VARCHAR(50),
    room_number VARCHAR(50) NOT NULL,
    desk_number VARCHAR(50) NOT NULL,
    secret_code VARCHAR(100),
    status VARCHAR(50) DEFAULT 'ធម្មតា',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, exam_name)
);

-- 9. Indexes ដើម្បីបង្កើនល្បឿន Query ពេលមានសិស្សរាប់ម៉ឺននាក់
CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_id);
CREATE INDEX IF NOT EXISTS idx_scores_student_period ON scores(student_id, period_key);
CREATE INDEX IF NOT EXISTS idx_period_results_rank ON period_results(period_key, rank);
CREATE INDEX IF NOT EXISTS idx_exam_arrangements_room ON exam_arrangements(room_number);

-- ============================================================================
-- ទិន្នន័យគំរូដំបូង (Initial Seed Data for Cambodian Schools)
-- ============================================================================

-- បញ្ចូលឆ្នាំសិក្សា
INSERT INTO academic_years (id, year_name, is_active)
VALUES ('a1b2c3d4-0001-4000-8000-000000000001', '២០២៦-២០២៧', TRUE)
ON CONFLICT (year_name) DO NOTHING;

-- បញ្ចូលថ្នាក់គំរូ (ថ្នាក់ទី១២ វិទ្យាសាស្ត្រ)
INSERT INTO classes (id, academic_year_id, grade_level, class_name, room_number, teacher_name)
VALUES (
    'c1b2c3d4-0001-4000-8000-000000000001',
    'a1b2c3d4-0001-4000-8000-000000000001',
    'grade_12_sci',
    'ថ្នាក់ទី១២ វិទ្យាសាស្ត្រ',
    'បន្ទប់ ២០១',
    'លោកគ្រូ សុខ សម្បត្តិ'
) ON CONFLICT DO NOTHING;

-- បញ្ចូលមុខវិជ្ជាស្តង់ដារ ថ្នាក់ទី១២ វិទ្យាសាស្ត្រ
INSERT INTO subjects (class_id, code, name, max_score, coefficient, is_enabled, sort_order)
VALUES 
    ('c1b2c3d4-0001-4000-8000-000000000001', 'math', 'គណិតវិទ្យា', 125, 2.0, TRUE, 1),
    ('c1b2c3d4-0001-4000-8000-000000000001', 'phy', 'រូបវិទ្យា', 75, 1.5, TRUE, 2),
    ('c1b2c3d4-0001-4000-8000-000000000001', 'chem', 'គីមីវិទ្យា', 75, 1.5, TRUE, 3),
    ('c1b2c3d4-0001-4000-8000-000000000001', 'bio', 'ជីវវិទ្យា', 75, 1.5, TRUE, 4),
    ('c1b2c3d4-0001-4000-8000-000000000001', 'kh', 'ភាសាខ្មែរ', 75, 1.0, TRUE, 5),
    ('c1b2c3d4-0001-4000-8000-000000000001', 'eng', 'ភាសាបរទេស', 50, 1.0, TRUE, 6),
    ('c1b2c3d4-0001-4000-8000-000000000001', 'his', 'ប្រវត្តិវិទ្យា', 50, 1.0, TRUE, 7)
ON CONFLICT (class_id, code) DO NOTHING;

-- បញ្ចូលសិស្សគំរូ
INSERT INTO students (id, class_id, student_code, khmer_name, latin_name, gender, dob, phone, guardian_name, address)
VALUES 
    ('d1b2c3d4-0001-4000-8000-000000000001', 'c1b2c3d4-0001-4000-8000-000000000001', 'STU-001', 'សុខ ចិន្តា', 'SOK CHINDA', 'ស្រី', '2008-03-12', '012 345 678', 'សុខ វិបុល', 'ភ្នំពេញ'),
    ('d1b2c3d4-0002-4000-8000-000000000002', 'c1b2c3d4-0001-4000-8000-000000000001', 'STU-002', 'រស់ វីរៈ', 'ROS VIRAK', 'ប្រុស', '2008-06-25', '098 765 432', 'រស់ សុផល', 'ភ្នំពេញ'),
    ('d1b2c3d4-0003-4000-8000-000000000003', 'c1b2c3d4-0001-4000-8000-000000000001', 'STU-003', 'ចាន់ ស្រីនីន', 'CHAN SREYNIN', 'ស្រី', '2008-01-18', '010 889 900', 'ចាន់ ផល្លា', 'ភ្នំពេញ')
ON CONFLICT (student_code) DO NOTHING;

-- ============================================================================
-- SQL Function សម្រាប់គណនាចំណាត់ថ្នាក់ និងមធ្យមភាគដោយស្វ័យប្រវត្តិ
-- ============================================================================
CREATE OR REPLACE FUNCTION calculate_period_ranks(p_class_id UUID, p_period_key VARCHAR)
RETURNS VOID AS $$
BEGIN
    -- គណនាពិន្ទុសរុប និងមធ្យមភាគ រួចបញ្ចូលទៅក្នុង period_results
    INSERT INTO period_results (student_id, period_key, total_score, average, percentage, mention, mention_khmer, is_passed)
    SELECT 
        s.id AS student_id,
        p_period_key AS period_key,
        COALESCE(SUM(sc.score_value * sub.coefficient), 0) AS total_score,
        CASE 
            WHEN COALESCE(SUM(sub.coefficient), 0) > 0 THEN 
                COALESCE(SUM(sc.score_value * sub.coefficient), 0) / SUM(sub.coefficient)
            ELSE 0 
        END AS average,
        CASE 
            WHEN COALESCE(SUM(sub.max_score * sub.coefficient), 0) > 0 THEN 
                (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / SUM(sub.max_score * sub.coefficient)) * 100
            ELSE 0 
        END AS percentage,
        -- និទ្ទេស
        CASE 
            WHEN (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / NULLIF(SUM(sub.max_score * sub.coefficient), 0)) * 100 >= 85 THEN 'A'
            WHEN (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / NULLIF(SUM(sub.max_score * sub.coefficient), 0)) * 100 >= 80 THEN 'B'
            WHEN (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / NULLIF(SUM(sub.max_score * sub.coefficient), 0)) * 100 >= 70 THEN 'C'
            WHEN (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / NULLIF(SUM(sub.max_score * sub.coefficient), 0)) * 100 >= 60 THEN 'D'
            WHEN (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / NULLIF(SUM(sub.max_score * sub.coefficient), 0)) * 100 >= 50 THEN 'E'
            ELSE 'F'
        END AS mention,
        CASE 
            WHEN (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / NULLIF(SUM(sub.max_score * sub.coefficient), 0)) * 100 >= 85 THEN 'ល្អប្រសើរ'
            WHEN (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / NULLIF(SUM(sub.max_score * sub.coefficient), 0)) * 100 >= 80 THEN 'ល្អណាស់'
            WHEN (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / NULLIF(SUM(sub.max_score * sub.coefficient), 0)) * 100 >= 70 THEN 'ល្អ'
            WHEN (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / NULLIF(SUM(sub.max_score * sub.coefficient), 0)) * 100 >= 60 THEN 'ល្អបង្គួរ'
            WHEN (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / NULLIF(SUM(sub.max_score * sub.coefficient), 0)) * 100 >= 50 THEN 'មធ្យម'
            ELSE 'ខ្សោយ'
        END AS mention_khmer,
        CASE 
            WHEN (COALESCE(SUM(sc.score_value * sub.coefficient), 0) / NULLIF(SUM(sub.max_score * sub.coefficient), 0)) * 100 >= 50 THEN TRUE
            ELSE FALSE
        END AS is_passed
    FROM students s
    JOIN subjects sub ON sub.class_id = p_class_id AND sub.is_enabled = TRUE
    LEFT JOIN scores sc ON sc.student_id = s.id AND sc.subject_id = sub.id AND sc.period_key = p_period_key
    WHERE s.class_id = p_class_id
    GROUP BY s.id
    ON CONFLICT (student_id, period_key) 
    DO UPDATE SET 
        total_score = EXCLUDED.total_score,
        average = EXCLUDED.average,
        percentage = EXCLUDED.percentage,
        mention = EXCLUDED.mention,
        mention_khmer = EXCLUDED.mention_khmer,
        is_passed = EXCLUDED.is_passed,
        updated_at = CURRENT_TIMESTAMP;

    -- ធ្វើបច្ចុប្បន្នភាពចំណាត់ថ្នាក់ (Dense Rank)
    WITH ranked AS (
        SELECT 
            id,
            DENSE_RANK() OVER (ORDER BY total_score DESC) as new_rank
        FROM period_results
        WHERE period_key = p_period_key
          AND student_id IN (SELECT id FROM students WHERE class_id = p_class_id)
    )
    UPDATE period_results pr
    SET rank = ranked.new_rank
    FROM ranked
    WHERE pr.id = ranked.id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 11. តារាងរដ្ឋបាលភូមិសាស្ត្រកម្ពុជា (Cambodia Administrative Geography)
-- ខេត្ត/រាជធានី (25), ស្រុក/ខណ្ឌ/ក្រុង (204), ឃុំ/សង្កាត់ (1,652), ភូមិ (14,437)
-- ============================================================================
CREATE TABLE IF NOT EXISTS administrative_divisions (
    code VARCHAR(20) PRIMARY KEY,
    type VARCHAR(50) NOT NULL, -- 'ខេត្ត', 'ស្រុក', 'ក្រុង', 'ខណ្ឌ', 'ឃុំ', 'សង្កាត់', 'ភូមិ'
    name_khmer VARCHAR(150) NOT NULL,
    name_latin VARCHAR(150),
    parent_code VARCHAR(20),
    reference VARCHAR(255),
    official_note TEXT,
    note_by_checker TEXT
);

CREATE INDEX IF NOT EXISTS idx_admin_parent ON administrative_divisions(parent_code);
CREATE INDEX IF NOT EXISTS idx_admin_type ON administrative_divisions(type);

-- ទិដ្ឋភាពងាយស្រួលប្រើប្រាស់ (Views)
CREATE OR REPLACE VIEW v_provinces AS 
SELECT code, name_khmer, name_latin 
FROM administrative_divisions 
WHERE type = 'ខេត្ត'
ORDER BY CAST(code AS INTEGER);

CREATE OR REPLACE VIEW v_districts AS 
SELECT code, type, name_khmer, name_latin, parent_code AS province_code 
FROM administrative_divisions 
WHERE type IN ('ស្រុក', 'ក្រុង', 'ខណ្ឌ')
ORDER BY code;

CREATE OR REPLACE VIEW v_communes AS 
SELECT code, type, name_khmer, name_latin, parent_code AS district_code 
FROM administrative_divisions 
WHERE type IN ('ឃុំ', 'សង្កាត់')
ORDER BY code;

CREATE OR REPLACE VIEW v_villages AS 
SELECT code, name_khmer, name_latin, parent_code AS commune_code 
FROM administrative_divisions 
WHERE type = 'ភូមិ'
ORDER BY code;

-- ============================================================================
-- 12. តារាងសម្រាប់ Cloud Sync ពិន្ទុ និងទិន្នន័យសិស្សតាមរយៈ Supabase (SMS Cloud Sync)
-- ចំណាំ៖ សូម Copy ផ្នែកទី 12 ខាងក្រោមនេះទៅ Run ក្នុង Supabase -> SQL Editor
-- ============================================================================

-- 12.1 តារាងពិន្ទុសិស្ស (អនុញ្ញាតឱ្យគ្រូពេញសិទ្ធិ Sync ពិន្ទុតាមមុខវិជ្ជាដោយមិនជាន់គ្នា)
CREATE TABLE IF NOT EXISTS public.sms_scores (
    student_id TEXT NOT NULL,
    period_key TEXT NOT NULL,
    subject_code TEXT NOT NULL,
    score NUMERIC(6, 2),
    updated_by TEXT DEFAULT 'teacher',
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (student_id, period_key, subject_code)
);

CREATE INDEX IF NOT EXISTS idx_sms_scores_period ON public.sms_scores(period_key);
CREATE INDEX IF NOT EXISTS idx_sms_scores_student ON public.sms_scores(student_id);

-- 12.2 តារាងព័ត៌មានសិស្ស (Sync បញ្ជីសិស្សរួមគ្នា)
CREATE TABLE IF NOT EXISTS public.sms_students (
    id TEXT PRIMARY KEY,
    class_name TEXT,
    full_name TEXT,
    gender TEXT,
    student_json JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

-- 12.3 តារាងការកំណត់ប្រព័ន្ធរួម (មុខវិជ្ជា, មេគុណ, ការរៀបចំបន្ទប់ប្រឡង...)
CREATE TABLE IF NOT EXISTS public.sms_app_state (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

-- បើកដំណើរការ Row Level Security (RLS) តាមស្តង់ដារសុវត្ថិភាព Supabase
ALTER TABLE public.sms_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sms_students ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sms_app_state ENABLE ROW LEVEL SECURITY;

-- ផ្តល់សិទ្ធិដល់តួនាទី anon និង authenticated ក្នុងការអាន និងបញ្ចូលទិន្នន័យតាមរយៈ Data API
GRANT ALL ON TABLE public.sms_scores TO anon, authenticated;
GRANT ALL ON TABLE public.sms_students TO anon, authenticated;
GRANT ALL ON TABLE public.sms_app_state TO anon, authenticated;

-- បង្កើតគោលការណ៍ RLS (Policies) សម្រាប់អនុញ្ញាតការ Sync ពិន្ទុ
DROP POLICY IF EXISTS "Allow read sms_scores" ON public.sms_scores;
CREATE POLICY "Allow read sms_scores" ON public.sms_scores
    FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "Allow insert sms_scores" ON public.sms_scores;
CREATE POLICY "Allow insert sms_scores" ON public.sms_scores
    FOR INSERT TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "Allow update sms_scores" ON public.sms_scores;
CREATE POLICY "Allow update sms_scores" ON public.sms_scores
    FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow delete sms_scores" ON public.sms_scores;
CREATE POLICY "Allow delete sms_scores" ON public.sms_scores
    FOR DELETE TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "Allow all sms_students" ON public.sms_students;
CREATE POLICY "Allow all sms_students" ON public.sms_students
    FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all sms_app_state" ON public.sms_app_state;
CREATE POLICY "Allow all sms_app_state" ON public.sms_app_state
    FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);


