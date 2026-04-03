import json

from app.db.connection import get_connection


def add_case(user_id: int, case_details: str, severity_flagged: bool = False):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO cases (user_id, case_details, severity_flagged)
        VALUES (%s, %s, %s)
        RETURNING case_id, user_id, case_details, severity_flagged;
        """,
        (user_id, case_details, severity_flagged),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "case_id": row[0],
        "user_id": row[1],
        "case_details": row[2],
        "severity_flagged": row[3],
    }


def get_case_by_id(case_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT case_id, user_id, case_details, severity_flagged, created_at
        FROM cases
        WHERE case_id = %s;
        """,
        (case_id,),
    )
    case_row = cur.fetchone()
    if not case_row:
        cur.close()
        conn.close()
        return None

    cur.execute(
        "SELECT soap_summary FROM soap_summaries WHERE case_id = %s;",
        (case_id,),
    )
    soap_row = cur.fetchone()
    soap_summary = soap_row[0] if soap_row else ""

    cur.execute(
        """
        SELECT model_name, ats_classification, confidence_score
        FROM classification_model
        WHERE case_id = %s;
        """,
        (case_id,),
    )
    classification_row = cur.fetchone()
    classification = (
        {
            "model_name": classification_row[0],
            "ats_classification": classification_row[1],
            "confidence_score": classification_row[2],
        }
        if classification_row
        else {}
    )

    cur.execute(
        "SELECT flag_category, flag_reason FROM severity_flags WHERE case_id = %s;",
        (case_id,),
    )
    severity_rows = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "case_id": case_row[0],
        "user_id": case_row[1],
        "case_details": case_row[2],
        "severity_flagged": case_row[3],
        "created_at": case_row[4],
        "soap_summary": soap_summary,
        "classification": classification,
        "severity_flags": [
            {"flag_category": row[0], "flag_reason": row[1]}
            for row in severity_rows
        ],
    }

def get_open_cases():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT case_id, user_id, case_details, severity_flagged, resolved_at, created_at
        FROM cases
        WHERE resolved_at IS NULL
        ORDER BY created_at DESC;
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "case_id": row[0],
            "user_id": row[1],
            "case_details": row[2],
            "severity_flagged": row[3],
            "resolved_at": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]

def get_resolved_cases():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT case_id, user_id, case_details, severity_flagged, resolved_at, created_at
        FROM cases
        WHERE resolved_at IS NOT NULL
        ORDER BY resolved_at DESC;
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "case_id": row[0],
            "user_id": row[1],
            "case_details": row[2],
            "severity_flagged": row[3],
            "resolved_at": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]

def get_all_cases():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT case_id, user_id, case_details, severity_flagged, resolved_at, created_at
        FROM cases
        ORDER BY created_at DESC;
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "case_id": row[0],
            "user_id": row[1],
            "case_details": row[2],
            "severity_flagged": row[3],
            "resolved_at": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]

def resolve_case(case_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE cases
        SET resolved_at = CURRENT_TIMESTAMP
        WHERE case_id = %s
        RETURNING case_id, resolved_at;
        """,
        (case_id,),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "case_id": row[0],
        "resolved_at": row[1],
    }

def reopen_case(case_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE cases
        SET resolved_at = NULL
        WHERE case_id = %s
        RETURNING case_id, resolved_at;
        """,
        (case_id,),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "case_id": row[0],
        "resolved_at": row[1],
    }



def update_soap_summary(case_id: int, soap_summary: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO soap_summaries (case_id, soap_summary)
        VALUES (%s, %s)
        ON CONFLICT (case_id) DO UPDATE
        SET soap_summary = EXCLUDED.soap_summary;
        """,
        (case_id, soap_summary),
    )
    conn.commit()
    cur.close()
    conn.close()


def add_classification_model(case_id: int, model_name: str, ats_classification: int, confidence_score: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO classification_model (case_id, model_name, ats_classification, confidence_score)
        VALUES (%s, %s, %s, %s)
        RETURNING case_id, model_name, ats_classification, confidence_score;
        """,
        (case_id, model_name, ats_classification, confidence_score),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "case_id": row[0],
        "model_name": row[1],
        "ats_classification": row[2],
        "confidence_score": row[3],
    }


def add_severity_flag(case_id: int, flag_category: int, flag_reason: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO severity_flags (case_id, flag_category, flag_reason)
        VALUES (%s, %s, %s)
        RETURNING case_id, flag_category, flag_reason;
        """,
        (case_id, flag_category, flag_reason),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "case_id": row[0],
        "flag_category": row[1],
        "flag_reason": row[2],
    }


def add_model_eval(model_name: str, f1_score: float, precision: float, recall: float, conf_mat: json):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO model_versions (model_name, f1_score, precision, recall, conf_mat)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING model_id, model_name, f1_score, precision, recall, conf_mat;
        """,
        (model_name, f1_score, precision, recall, conf_mat),
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
        "confusion_matrix": row[5],
    }


def get_model_metrics_by_name(model_name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT model_id, model_name, f1_score, precision, recall, conf_mat
        FROM model_versions
        WHERE model_name = %s;
        """,
        (model_name,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "model_id": row[0],
        "model_name": row[1],
        "f1_score": row[2],
        "precision": row[3],
        "recall": row[4],
        "confusion_matrix": row[5],
    }
