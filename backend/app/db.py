import os
import psycopg2
import json

def _connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )

def get_all_users():
    conn = _connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role, created_at FROM users ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "email": r[2], "role": r[3], "created_at": r[4]}
        for r in rows
    ]

def get_user_by_id(user_id):
    conn = _connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, role, created_at FROM users WHERE id = %s;", (user_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "email": row[2], "role": row[3], "created_at": row[4]}

def create_user(name, email, password, role):
    conn = _connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email, password, role) "
        "VALUES (%s, %s, %s, %s) RETURNING id, name, email, role, created_at;",
        (name, email, password, role),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"id": row[0], "name": row[1], "email": row[2], "role": row[3], "created_at": row[4]}

def update_user(user_id, name=None, email=None, password=None, role=None):
    existing = get_user_by_id(user_id)
    if not existing:
        return None

    new_name = name if name else existing["name"]
    new_email = email if email else existing["email"]
    new_password = password if password else None  # optional, can be None if not updating
    new_role = role if role else existing["role"]

    conn = _connection()
    cur = conn.cursor()
    if new_password:
        cur.execute(
            "UPDATE users SET name=%s, email=%s, password=%s, role=%s "
            "WHERE id=%s RETURNING id, name, email, role, created_at;",
            (new_name, new_email, new_password, new_role, user_id),
        )
    else:
        cur.execute(
            "UPDATE users SET name=%s, email=%s, role=%s "
            "WHERE id=%s RETURNING id, name, email, role, created_at;",
            (new_name, new_email, new_role, user_id),
        )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "email": row[2], "role": row[3], "created_at": row[4]}

def delete_user(user_id):
    conn = _connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s RETURNING id;", (user_id,))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not row:
        return None
    return {"id": row[0]}

def update_soap_summary(case_id: int, soap_summary: str):
    conn = _connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO soap_summaries (case_id, soap_summary)
        VALUES (%s, %s)
        ON CONFLICT (case_id) DO UPDATE SET soap_summary = EXCLUDED.soap_summary;
        """,
        (case_id, soap_summary)
    )
    conn.commit()
    cur.close()
    conn.close()

def add_model_eval(model_name: str, f1_score: float, precision: float, recall: float, conf_mat: json):
    conn = _connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO model_versions (model_name, f1_score, precision, recall, conf_mat) VALUES (%s, %s, %s, %s, %s) "
        "RETURNING model_id, model_name, f1_score, precision, recall, conf_mat",
        (model_name, f1_score, precision, recall, conf_mat)
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {
        "model_id": row[0],
        "model_name": row[1],
        "f1_score": row[2],
        "precision": row[3],
        "recall": row[4],
        "confusion_matrix": row[5]
    }

def add_classification_model(case_id: int, model_id: int, ats_classification: int, confidence_score: float):
    conn = _connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO classification_model (case_id, model_id, ats_classification, confidence_score) VALUES (%s, %s, %s, %s) RETURNING case_id, model_id, ats_classification, confidence_score;",
        (case_id, model_id, ats_classification, confidence_score)
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {
        "case_id": row[0],
        "model_id": row[1],
        "ats_classification": row[2],
        "confidence_score": row[3]
    }

def add_severity_flag(case_id: int, flag_category: int, flag_reason: str):
    conn = _connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO severity_flags (case_id, flag_category, flag_reason) VALUES (%s, %s, %s) RETURNING case_id, flag_category, flag_reason;",
        (case_id, flag_category, flag_reason)
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {
        "case_id": row[0],
        "flag_category": row[1],
        "flag_reason": row[2]
    }

def add_case(user_id: int, case_details: str, severity_flagged: bool = False):
    conn = _connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO cases (user_id, case_details, severity_flagged) VALUES (%s, %s, %s) RETURNING case_id, user_id, case_details, severity_flagged;",
        (user_id, case_details, severity_flagged)
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {
        "case_id": row[0],
        "user_id": row[1],
        "case_details": row[2],
        "severity_flagged": row[3]
    }


