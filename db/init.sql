CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK (role IN ('admin','clinician','researcher')) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    password_changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMPTZ NULL
);

INSERT INTO users (name, email, password, role) VALUES
(
'Admin',
'admin@example.com',
'$argon2id$v=19$m=65536,t=3,p=4$TMnZO4fQWqsVovRey1kLgQ$1PRETjl0mi3jRUA0qmmPBwA5+MEYo6YIP8AOEyN4Jtc',
'admin'
);

CREATE TABLE cases (
    case_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    patient_name TEXT NOT NULL,
    medicare_number TEXT NOT NULL,
    severity_flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ NULL,
    ats_category INT NOT NULL CHECK (ats_category BETWEEN 1 AND 5),
    ats_source TEXT NOT NULL CHECK (ats_source IN ('model', 'rule', 'override')),
    override_ats INT NULL CHECK (override_ats BETWEEN 1 AND 5),
    override_reason TEXT NULL,
    override_at TIMESTAMPTZ NULL,
    age INT NULL CHECK (age >= 0 AND age <= 150),
    gender TEXT NULL CHECK (gender IN ('male', 'female', 'other'))
);

CREATE TABLE case_dialogues (
    case_id INT PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
    case_dialogue TEXT NOT NULL
);

CREATE TABLE clinical_summaries (
    case_id INT PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
    soap_summary TEXT,
    brief_summary TEXT
);

CREATE TABLE model_predictions (
    case_id INT PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
    pred_ats INT NOT NULL CHECK (pred_ats BETWEEN 1 AND 5),
    pred_confidence FLOAT CHECK (pred_confidence >= 0 AND pred_confidence <= 1),
    model_used TEXT
);

CREATE TABLE severity_flags (
    case_id INT PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
    flag_ats INT NOT NULL CHECK (flag_ats BETWEEN 1 AND 5),
    flag_notes TEXT
);

CREATE TABLE revoked_tokens (
    token TEXT PRIMARY KEY,
    revoked_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
