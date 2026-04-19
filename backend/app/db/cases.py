import json

from app.core.crypto import decrypt_text, encrypt_text
from app.db.connection import get_connection
from datetime import date
from psycopg2.extras import RealDictCursor
from typing import Any


def _decrypt_case_identity(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("patient_name") is not None:
        row["patient_name"] = decrypt_text(row["patient_name"])
    if row.get("medicare_number") is not None:
        row["medicare_number"] = decrypt_text(row["medicare_number"])
    return row


def _decrypt_case_dialogue(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("case_dialogue") is not None:
        row["case_dialogue"] = decrypt_text(row["case_dialogue"])
    return row


def add_case(
    user_id: int,
    patient_name: str,
    medicare_number: str,
    case_dialogue: str,
    severity_flagged: bool,
    ats_category: int,
    ats_source: str,
    age: int | None = None,
    gender: str | None = None,
    override_ats: int | None = None,
    override_reason: str | None = None,
):

    encrypted_patient_name = encrypt_text(patient_name)
    encrypted_medicare_number = encrypt_text(medicare_number)
    encrypted_case_dialogue = encrypt_text(case_dialogue)

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            INSERT INTO cases (
                user_id,
                patient_name,
                medicare_number,
                severity_flagged,
                ats_category,
                ats_source,
                override_ats,
                override_reason,
                age,
                gender
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING
                case_id,
                user_id,
                patient_name,
                medicare_number,
                severity_flagged,
                created_at,
                resolved_at,
                ats_category,
                ats_source,
                override_ats,
                override_reason,
                age,
                gender;
            """,
            (
                user_id,
                encrypted_patient_name,
                encrypted_medicare_number,
                severity_flagged,
                ats_category,
                ats_source,
                override_ats,
                override_reason,
                age,
                gender,
            ),
        )
        case_row = dict(cur.fetchone())

        cur.execute(
            """
            INSERT INTO case_dialogues (case_id, case_dialogue)
            VALUES (%s, %s)
            RETURNING case_dialogue;
            """,
            (case_row["case_id"], encrypted_case_dialogue),
        )
        dialogue_row = dict(cur.fetchone())

        conn.commit()

        case_row["case_dialogue"] = decrypt_text(dialogue_row["case_dialogue"])
        return _decrypt_case_identity(case_row)
    
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def get_case_by_id(case_id: int):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            SELECT
                c.case_id,
                c.user_id,
                c.patient_name,
                c.medicare_number,
                cd.case_dialogue,
                c.severity_flagged,
                c.created_at,
                c.resolved_at,
                c.ats_category,
                c.ats_source,
                c.override_ats,
                c.override_reason,
                c.age,
                c.gender,
                mp.pred_ats,
                mp.pred_confidence,
                mp.model_used,
                sf.flag_ats,
                sf.flag_notes,
                cs.soap_summary,
                cs.brief_summary
            FROM cases c
            LEFT JOIN case_dialogues cd
                ON c.case_id = cd.case_id
            LEFT JOIN model_predictions mp
                ON c.case_id = mp.case_id
            LEFT JOIN severity_flags sf
                ON c.case_id = sf.case_id
            LEFT JOIN clinical_summaries cs
                ON c.case_id = cs.case_id
            WHERE c.case_id = %s;
            """,
            (case_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        
        result = dict(row)
        result = _decrypt_case_identity(result)
        result = _decrypt_case_dialogue(result)
        return result

    finally:
        cur.close()
        conn.close()

def get_open_cases():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            SELECT
                c.case_id,
                c.user_id,
                c.patient_name,
                c.medicare_number,
                c.severity_flagged,
                c.created_at,
                c.resolved_at,
                c.ats_category,
                c.ats_source,
                c.override_ats,
                c.override_reason,
                c.age,
                c.gender
            FROM cases c
            WHERE c.resolved_at IS NULL
            ORDER BY c.created_at DESC;
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
        return [_decrypt_case_identity(row) for row in rows]

    finally:
        cur.close()
        conn.close()


def get_resolved_cases():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            SELECT
                c.case_id,
                c.user_id,
                c.patient_name,
                c.medicare_number,
                c.severity_flagged,
                c.created_at,
                c.resolved_at,
                c.ats_category,
                c.ats_source,
                c.override_ats,
                c.override_reason,
                c.age,
                c.gender
            FROM cases c
            WHERE c.resolved_at IS NOT NULL
            ORDER BY c.resolved_at DESC;
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
        return [_decrypt_case_identity(row) for row in rows]

    finally:
        cur.close()
        conn.close()


def get_all_cases():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            SELECT
                c.case_id,
                c.user_id,
                c.patient_name,
                c.medicare_number,
                c.severity_flagged,
                c.created_at,
                c.resolved_at,
                c.ats_category,
                c.ats_source,
                c.override_ats,
                c.override_reason,
                c.age,
                c.gender
            FROM cases c
            ORDER BY c.created_at DESC;
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
        return [_decrypt_case_identity(row) for row in rows]

    finally:
        cur.close()
        conn.close()

def resolve_case(case_id: int):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
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

        if not row:
            return None

        return dict(row)

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def reopen_case(case_id: int):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
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

        if not row:
            return None

        return dict(row)

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def upsert_clinical_summary(case_id: int, soap_summary: str, brief_summary: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            INSERT INTO clinical_summaries (case_id, soap_summary, brief_summary)
            VALUES (%s, %s, %s)
            ON CONFLICT (case_id) DO UPDATE
            SET
                soap_summary = EXCLUDED.soap_summary,
                brief_summary = EXCLUDED.brief_summary
            RETURNING case_id, soap_summary, brief_summary;
            """,
            (case_id, soap_summary, brief_summary),
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row)

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def add_model_prediction(case_id: int, pred_ats: int, pred_confidence: float, model_used: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            INSERT INTO model_predictions (
                case_id,
                pred_ats,
                pred_confidence,
                model_used
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (case_id) DO UPDATE
            SET
                pred_ats = EXCLUDED.pred_ats,
                pred_confidence = EXCLUDED.pred_confidence,
                model_used = EXCLUDED.model_used
            RETURNING case_id, pred_ats, pred_confidence, model_used;
            """,
            (case_id, pred_ats, pred_confidence, model_used),
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row)

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def add_severity_flag(case_id: int, flag_ats: int, flag_notes: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            INSERT INTO severity_flags (case_id, flag_ats, flag_notes)
            VALUES (%s, %s, %s)
            ON CONFLICT (case_id) DO UPDATE
            SET
                flag_ats = EXCLUDED.flag_ats,
                flag_notes = EXCLUDED.flag_notes
            RETURNING case_id, flag_ats, flag_notes;
            """,
            (case_id, flag_ats, flag_notes),
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row)

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def override_ats_classification(case_id: int, override_ats: int, override_reason: str = ""):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            UPDATE cases
            SET
                override_ats = %s,
                override_reason = %s,
                ats_category = %s,
                ats_source = 'override'
            WHERE case_id = %s
            RETURNING
                case_id,
                ats_category,
                ats_source,
                override_ats,
                override_reason;
            """,
            (override_ats, override_reason, override_ats, case_id),
        )
        row = cur.fetchone()
        conn.commit()

        if not row:
            return None

        return dict(row)

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def undo_ats_override(case_id: int):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            SELECT
                c.case_id,
                c.ats_source,
                c.override_ats,
                mp.pred_ats,
                sf.flag_ats
            FROM cases c
            LEFT JOIN model_predictions mp
                ON c.case_id = mp.case_id
            LEFT JOIN severity_flags sf
                ON c.case_id = sf.case_id
            WHERE c.case_id = %s;
            """,
            (case_id,),
        )
        row = cur.fetchone()

        if not row:
            return None

        row = dict(row)

        if row["ats_source"] != "override":
            return {"error": "Case is not currently overridden"}

        pred_ats = row["pred_ats"]
        flag_ats = row["flag_ats"]

        if pred_ats is None and flag_ats is None:
            return {"error": "No model or rule ATS available to restore"}

        if flag_ats is None:
            restored_ats = pred_ats
            restored_source = "model"
        elif pred_ats is None:
            restored_ats = flag_ats
            restored_source = "rule"
        elif flag_ats <= pred_ats:
            restored_ats = flag_ats
            restored_source = "rule"
        else:
            restored_ats = pred_ats
            restored_source = "model"

        cur.execute(
            """
            UPDATE cases
            SET
                ats_category = %s,
                ats_source = %s,
                override_ats = NULL,
                override_reason = NULL
            WHERE case_id = %s
            RETURNING
                case_id,
                ats_category,
                ats_source,
                override_ats,
                override_reason;
            """,
            (restored_ats, restored_source, case_id),
        )
        updated = cur.fetchone()
        conn.commit()

        return dict(updated)

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def has_open_case_for_medicare(medicare_number: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT medicare_number
        FROM cases
        WHERE resolved_at IS NULL;
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    for row in rows:
        stored_medicare = decrypt_text(row[0])
        if stored_medicare == medicare_number:
            return True

    return False


from datetime import date
from psycopg2.extras import RealDictCursor

def get_case_analytics(target_date: date | None = None):
    if target_date is None:
        target_date = date.today()

    print(target_date)
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            SELECT
                case_id,
                resolved_at,
                ats_category,
                gender,
                age,
                created_at
            FROM cases
            WHERE DATE(created_at) = %s
            ORDER BY created_at DESC;
            """,
            (target_date,),
        )
        rows = [dict(row) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

    def blank_bucket():
        return {
            "total_cases": 0,
            "ats": {
                "cat_1": 0,
                "cat_2": 0,
                "cat_3": 0,
                "cat_4": 0,
                "cat_5": 0,
            },
            "gender": {
                "male": 0,
                "female": 0,
                "other": 0,
                "unknown": 0,
            },
            "age": {
                "0_4": 0,
                "5_12": 0,
                "13_17": 0,
                "18_25": 0,
                "26_45": 0,
                "46_65": 0,
                "65_plus": 0,
                "unknown": 0,
            },
        }

    def normalise_gender(value):
        if not value:
            return "unknown"
        value = value.strip().lower()
        if value in {"male", "m"}:
            return "male"
        if value in {"female", "f"}:
            return "female"
        if value == "other":
            return "other"
        return "unknown"

    def age_bucket(value):
        if value is None:
            return "unknown"
        if 0 <= value <= 4:
            return "0_4"
        if 5 <= value <= 12:
            return "5_12"
        if 13 <= value <= 17:
            return "13_17"
        if 18 <= value <= 25:
            return "18_25"
        if 26 <= value <= 45:
            return "26_45"
        if 46 <= value <= 65:
            return "46_65"
        if value >= 66:
            return "65_plus"
        return "unknown"

    result = {
        "date": str(target_date),
        "open_cases": blank_bucket(),
        "resolved_cases": blank_bucket(),
    }

    for row in rows:
        bucket = result["resolved_cases"] if row["resolved_at"] is not None else result["open_cases"]

        bucket["total_cases"] += 1

        ats = row.get("ats_category")
        if ats in {1, 2, 3, 4, 5}:
            bucket["ats"][f"cat_{ats}"] += 1

        bucket["gender"][normalise_gender(row.get("gender"))] += 1
        bucket["age"][age_bucket(row.get("age"))] += 1

    return result

