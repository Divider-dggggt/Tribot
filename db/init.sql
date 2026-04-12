CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK (role IN ('Admin','Clinician','Researcher')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email, password, role) VALUES
(
'Admin',
'admin@example.com',
'$argon2id$v=19$m=65536,t=3,p=4$TMnZO4fQWqsVovRey1kLgQ$1PRETjl0mi3jRUA0qmmPBwA5+MEYo6YIP8AOEyN4Jtc',
'Admin'
);

CREATE TABLE cases (
    case_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    name TEXT NOT NULL,
    medicare_number TEXT NOT NULL,
    case_details TEXT NOT NULL, --dialogues
    severity_flagged BOOLEAN DEFAULT FALSE,
    -- user_override_category INT DEFAULT 0,
    -- override_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL
);


CREATE TABLE soap_summaries (
    case_id INT PRIMARY KEY REFERENCES cases(case_id),
    soap_summary TEXT
);

CREATE TABLE classification_model (
    case_id INT REFERENCES cases(case_id),
    model_name TEXT,
    ats_classification INT, -- ATS category
    confidence_score FLOAT,
    clinician_override_at TIMESTAMP NULL,
    PRIMARY KEY (case_id)
);

CREATE TABLE severity_flags (
    case_id INT REFERENCES cases(case_id),
    flag_category INT NOT NULL, -- 1-5
    flag_reason TEXT,
    PRIMARY KEY (case_id, flag_category)
);

CREATE TABLE revoked_tokens (
    token TEXT PRIMARY KEY,
    revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
