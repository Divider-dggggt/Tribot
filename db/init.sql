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
    case_details TEXT NOT NULL, --dialogues
    severity_flagged BOOLEAN DEFAULT FALSE,
    user_override_category INT DEFAULT 0,
    override_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO cases (user_id, case_details) VALUES
(
1,
$$
Nurse: Hi there, I'm Sarah, one of the triage nurses. Come take a seat. Who's this little one?

Parent: This is Aria, she's two months old. She's had a fever today and she's just not herself.

Nurse: Okay, thank you for coming in. Let's start with when you first noticed she was warm. Was it earlier today or overnight?

Parent: Around mid-morning she felt a bit warm, but we thought maybe it was just the weather. But in the afternoon she got really hot, and we checked her temperature - it was 38.7.

Nurse: Alright. When you checked the temperature, was it under the arm, ear thermometer…?

Parent: Ear thermometer, we did it twice.

Nurse: Good. And how has she been behaving since then? More sleepy? Irritable?

Parent: More sleepy. She's usually quite alert, even at this age. But today she keeps dozing off during feeds.

Nurse: Okay. Speaking of feeds - how much has she taken today compared to usual?

Parent: Maybe half. She normally has 120mls a feed. Today she's had about 50 or 60mls at best.

Nurse: And wet nappies - how many has she had today?

Parent: Only two. Normally she has four or five by now.

Nurse: That's helpful to know. Any vomiting today? Either small spit-ups or full feeds coming back?

Parent: Just one little vomit earlier.

Nurse: Any cough, runny nose, breathing that looks different?

Parent: No cough or runny nose. Breathing looks normal to us.

Nurse: Any rash anywhere? Even faint blotches or spots?

Parent: No rash.

Nurse: Anyone at home unwell? Colds, COVID, flu?

Parent: Her dad has a bit of a cold, nothing serious.

Nurse: Has she travelled recently? Anyone visiting from overseas?

Parent: No, just home.

Nurse: Is she vaccinated as per schedule - she would have had her 6-week shots?

Parent: Yes, she had them right on time.

Nurse: Great. Any complications at birth? Was she full-term?

Parent: Full-term, no NICU, healthy pregnancy.

Nurse: Perfect. I'm just going to pop this thermometer under her arm and check her temp.

Nurse: Her temperature is still up - 38.5 - and I can see her heart rate is a bit fast.

Parent: Is she alright? She just seems so floppy compared to usual.

Nurse: I can see why you're worried. Babies this young can get sick quite quickly.

Parent: Is she likely to be admitted?

Nurse: For babies under 3 months, admission is common.

Parent: Okay, thank you.

Nurse: You've done the right thing bringing her in quickly.

Parent: Thank you.

Nurse: Grab all your things, and I'll walk you through now.
$$
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
