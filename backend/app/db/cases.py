import json

from app.core.crypto import decrypt_text, encrypt_text
from app.db.connection import get_connection



def add_case(user_id: int, name: str, medicare_number: str, case_details: str, severity_flagged: bool = False):

    encrypted_name = encrypt_text(name)
    encrypted_medicare_number = encrypt_text(medicare_number)
    encrypted_case_details = encrypt_text(case_details)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO cases (user_id, name, medicare_number, case_details, severity_flagged)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING case_id, user_id, name, medicare_number, case_details, severity_flagged, resolved_at;
        """,
        (user_id, encrypted_name, encrypted_medicare_number, encrypted_case_details, severity_flagged),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "case_id": row[0],
        "user_id": row[1],
        "name": decrypt_text(row[2]),
        "medicare_number": decrypt_text(row[3]),
        "case_details": decrypt_text(row[4]),
        "severity_flagged": row[5],
        "resolved_at": row[6],
    }


def get_case_by_id(case_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            c.case_id,
            c.user_id,
            c.name,
            c.medicare_number,
            c.case_details,
            c.severity_flagged,
            c.resolved_at,
            c.created_at,
            cm.ats_classification,
            cm.confidence_score,
            cm.clinician_override_at
        FROM cases c
        LEFT JOIN classification_model cm ON c.case_id = cm.case_id
        WHERE c.case_id = %s;
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
        "SELECT flag_category, flag_reason FROM severity_flags WHERE case_id = %s;",
        (case_id,),
    )
    severity_rows = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "case_id": case_row[0],
        "user_id": case_row[1],
        "name": decrypt_text(case_row[2]),
        "medicare_number": decrypt_text(case_row[3]),
        "case_details": decrypt_text(case_row[4]),
        "severity_flagged": case_row[5],
        "resolved_at": case_row[6],
        "created_at": case_row[7],
        "soap_summary": soap_summary,
        "ats_classification": case_row[8],
        "confidence_score": case_row[9],
        "clinician_override_at": case_row[10],
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
        SELECT
            c.case_id,
            c.user_id,
            c.name,
            c.medicare_number,
            c.case_details,
            c.severity_flagged,
            c.resolved_at,
            c.created_at,
            cm.ats_classification,
            cm.confidence_score,
            cm.clinician_override_at
        FROM cases c
        LEFT JOIN classification_model cm ON c.case_id = cm.case_id
        WHERE c.resolved_at IS NULL
        ORDER BY c.created_at DESC;
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "case_id": row[0],
            "user_id": row[1],
            "name": decrypt_text(row[2]),
            "medicare_number": decrypt_text(row[3]),
            "case_details": decrypt_text(row[4]),
            "severity_flagged": row[5],
            "resolved_at": row[6],
            "created_at": row[7],
            "ats_classification": row[8],
            "confidence_score": row[9],
            "clinician_override_at": row[10],
        }
        for row in rows
    ]


def get_resolved_cases():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            c.case_id,
            c.user_id,
            c.name,
            c.medicare_number,
            c.case_details,
            c.severity_flagged,
            c.resolved_at,
            c.created_at,
            cm.ats_classification,
            cm.confidence_score,
            cm.clinician_override_at
        FROM cases c
        LEFT JOIN classification_model cm ON c.case_id = cm.case_id
        WHERE c.resolved_at IS NOT NULL
        ORDER BY c.resolved_at DESC;
        """
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "case_id": row[0],
            "user_id": row[1],
            "name": decrypt_text(row[2]),
            "medicare_number": decrypt_text(row[3]),
            "case_details": decrypt_text(row[4]),
            "severity_flagged": row[5],
            "resolved_at": row[6],
            "created_at": row[7],
            "ats_classification": row[8],
            "confidence_score": row[9],
            "clinician_override_at": row[10],
        }
        for row in rows
    ]


def get_all_cases():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            c.case_id,
            c.user_id,
            c.name,
            c.medicare_number,
            c.case_details,
            c.severity_flagged,
            c.resolved_at,
            c.created_at,
            cm.ats_classification,
            cm.confidence_score,
            cm.clinician_override_at
        FROM cases c
        LEFT JOIN classification_model cm ON c.case_id = cm.case_id
        ORDER BY c.created_at DESC;
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "case_id": row[0],
            "user_id": row[1],
            "name": decrypt_text(row[2]),
            "medicare_number": decrypt_text(row[3]),
            "case_details": decrypt_text(row[4]),
            "severity_flagged": row[5],
            "resolved_at": row[6],
            "created_at": row[7],
            "ats_classification": row[8],
            "confidence_score": row[9],
            "clinician_override_at": row[10],
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
        INSERT INTO classification_model (
            case_id,
            model_name,
            ats_classification,
            confidence_score,
            clinician_override_at
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING case_id, model_name, ats_classification, confidence_score, clinician_override_at;
        """,
        (case_id, model_name, ats_classification, confidence_score, None),
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
        "clinician_override_at": row[4],
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


def override_ats_classification(case_id: int, ats_classification: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE classification_model
        SET ats_classification = %s,
            clinician_override_at = CURRENT_TIMESTAMP
        WHERE case_id = %s
        RETURNING case_id, ats_classification, clinician_override_at;
        """,
        (ats_classification, case_id),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "case_id": row[0],
        "ats_classification": row[1],
        "clinician_override_at": row[2],
    }