from app.db.connection import get_connection

def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role, created_at FROM users ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "role": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]

def get_user_by_id(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, role, created_at FROM users WHERE id = %s;",
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[3],
        "created_at": row[4],
    }

def get_user_by_email(email: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, password, role FROM users WHERE email = %s;",
        (email,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "password": row[3],
        "role": row[4],
    }

def create_user(name: str, email: str, password: str, role: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (name, email, password, role)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name, email, role, created_at;
        """,
        (name, email, password, role),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[3],
        "created_at": row[4],
    }

def update_user(user_id: int, name=None, email=None, password=None, role=None):
    existing = get_user_by_id(user_id)
    if not existing:
        return None

    new_name = name if name else existing["name"]
    new_email = email if email else existing["email"]
    new_role = role if role else existing["role"]

    conn = get_connection()
    cur = conn.cursor()

    if password:
        cur.execute(
            """
            UPDATE users
            SET name = %s, email = %s, password = %s, role = %s
            WHERE id = %s
            RETURNING id, name, email, role, created_at;
            """,
            (new_name, new_email, password, new_role, user_id),
        )
    else:
        cur.execute(
            """
            UPDATE users
            SET name = %s, email = %s, role = %s
            WHERE id = %s
            RETURNING id, name, email, role, created_at;
            """,
            (new_name, new_email, new_role, user_id),
        )

    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[3],
        "created_at": row[4],
    }

def delete_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s RETURNING id;", (user_id,))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not row:
        return None

    return {"id": row[0]}

def revoke_token(token: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO revoked_tokens (token) VALUES (%s);", (token,))
    conn.commit()
    cur.close()
    conn.close()

def is_token_revoked(token: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT token FROM revoked_tokens WHERE token = %s;", (token,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row is not None
