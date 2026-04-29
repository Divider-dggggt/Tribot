# Backend API Documentation

## Base URL

Local backend:

```text
http://localhost:8000
```

Interactive Swagger docs:

```text
http://localhost:8000/docs
```

## Authentication

The backend uses JWT bearer authentication.

1. Call `POST /login`
2. Copy the returned `access_token`
3. Send it in protected requests as:

```http
Authorization: Bearer <access_token>
```

## Role Access Summary

| Role | Main Access |
| --- | --- |
| `admin` | User management, deactivated user management, health check, analytics |
| `clinician` | Create/view/update triage cases, resolve/reopen cases, override ATS, generate summaries |
| `researcher` | View cases, model metrics, analytics |

## Common Error Responses

| Status | Meaning |
| --- | --- |
| `400` | Invalid request or business rule failure |
| `401` | Invalid token or login failed |
| `403` | Authenticated but not allowed for the route |
| `404` | Resource not found |
| `409` | Conflict, for example duplicate open Medicare case |
| `500` | Unexpected backend failure |

---

## Auth Endpoints

### `POST /login`

Authenticate a user and return a bearer token.

Request body:

```json
{
  "email": "admin@example.com",
  "password": "password123"
}
```

Response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "role": "admin"
}
```

### `POST /logout`

Revoke the current token.

Access:
- Any authenticated user

Response:

```json
{
  "msg": "Logged out successfully"
}
```

---

## User Management Endpoints

All user-management routes are admin-only unless noted otherwise.

### `GET /users`

Return active users only.

### `GET /users/all`

Return all users, including deactivated users.

### `GET /users/deactivated`

Return deactivated users only.

### `GET /users/{user_id}`

Return one user by ID.

### `POST /users`

Create a new user.

Request body:

```json
{
  "name": "Jane Clinician",
  "email": "jane@example.com",
  "password": "securepass",
  "role": "clinician"
}
```

Response:

```json
{
  "id": 2,
  "name": "Jane Clinician",
  "email": "jane@example.com",
  "role": "clinician",
  "created_at": "2026-04-29T01:20:00+00:00",
  "deactivated_at": null
}
```

### `PUT /users/{user_id}`

Update a user.

Access:
- Admin can update any user
- Non-admin users can update only their own account

Password rules:
- Clinician/researcher changing their own password must send `old_password`
- New password cannot be the same as the current password
- Admin can reset another user's password without `old_password`
- Admin cannot change another admin's password

Example self-service password change:

```json
{
  "old_password": "oldpassword123",
  "password": "newpassword456"
}
```

Example admin role/email update:

```json
{
  "email": "updated@example.com",
  "role": "researcher"
}
```

### `PATCH /users/{user_id}/deactivate`

Soft-deactivate a user account.

Notes:
- The user remains in the database
- Deactivated users cannot log in
- Admin cannot deactivate their own account

### `PATCH /users/{user_id}/reactivate`

Reactivate a previously deactivated account.

---

## Case and Triage Endpoints

The backend exposes both `/cases` and `/triage` paths for the same case workflow in several routes.

### `POST /cases`
### `POST /triage`

Create a new case.

Access:
- `clinician`

Query params:
- `fast_response` default `true`
- `generate_summary` default `true`

Business rules:
- A new case cannot be created if the same Medicare number already has an open case
- Medicare number must be exactly 11 digits
- `gender` must be `male`, `female`, or `other` if provided

Fast response behaviour:
- If `fast_response=true`, the case is created immediately
- Placeholder values are returned for `soap_summary` and `brief_summary`
- The real SOAP summary is generated in the background and saved afterwards
- If `fast_response=false`, the endpoint waits for summary generation before responding

Request body:

```json
{
  "patient_name": "Lily Smith",
  "medicare_number": "12345678901",
  "case_dialogue": "Parent: Lily has been vomiting since yesterday...",
  "age": 4,
  "gender": "female"
}
```

Response with `fast_response=true`:

```json
{
  "case_id": 10,
  "patient_name": "Lily Smith",
  "medicare_number": "12345678901",
  "case_dialogue": "Parent: Lily has been vomiting since yesterday...",
  "severity_flagged": true,
  "created_at": "2026-04-29T01:40:00+00:00",
  "resolved_at": null,
  "ats_category": 2,
  "ats_source": "rule",
  "override_ats": null,
  "override_reason": null,
  "age": 4,
  "gender": "female",
  "pred_ats": 3,
  "pred_confidence": 0.82,
  "model_used": "deberta",
  "flag_ats": 2,
  "flag_notes": "Moderate dehydration risk",
  "soap_summary": "Generating clinical summary...",
  "brief_summary": "Generating clinical summary..."
}
```

### `GET /cases`
### `GET /triage`

Return case list.

Access:
- Any authenticated user

Query params:
- `resolved=false` returns open cases
- `resolved=true` returns resolved cases

Researcher behaviour:
- `patient_name` is returned as `[REDACTED]`
- `medicare_number` is returned as `[REDACTED]`
- `case_dialogue` is de-identified before response

### `GET /cases/{case_id}`
### `GET /triage/{case_id}`

Return one case with prediction, summary, and severity information when available.

Access:
- Any authenticated user

### `PATCH /cases/{case_id}/resolve`
### `PATCH /triage/{case_id}/resolve`

Mark a case as resolved.

Access:
- `clinician`

Response:

```json
{
  "case_id": 10,
  "resolved_at": "2026-04-29T02:00:00+00:00"
}
```

### `PATCH /cases/{case_id}/reopen`
### `PATCH /triage/{case_id}/reopen`

Reopen a resolved case.

Access:
- `clinician`

### `PATCH /cases/{case_id}/ats`
### `PATCH /triage/{case_id}/ats`

Override ATS classification.

Access:
- `clinician`

Request body:

```json
{
  "override_ats": 3,
  "override_reason": "Patient is clinically stable on assessment."
}
```

Response:

```json
{
  "case_id": 10,
  "ats_category": 3,
  "ats_source": "override",
  "override_ats": 3,
  "override_reason": "Patient is clinically stable on assessment.",
  "message": "ATS classification overridden successfully"
}
```

### `PATCH /cases/{case_id}/ats/undo`
### `PATCH /triage/{case_id}/ats/undo`

Remove an ATS override and restore the previous ATS source.

Access:
- `clinician`

### `POST /cases/{case_id}/summary`
### `POST /triage/{case_id}/summary`

Generate or regenerate SOAP and brief summaries for an existing case.

Access:
- `clinician`

Query params:
- `fast_response=false` by default

If `fast_response=true`, placeholder text is returned immediately and summary generation is completed in the background.
If `fast_response=false`, the endpoint waits and returns the generated SOAP and brief summaries in the same response.

---

## Analytics Endpoint

### `GET /analytics`

Return daily analytics grouped into open and resolved cases.

Access:
- `admin`
- `researcher`

Query params:
- `date=YYYY-MM-DD` optional
- defaults to the current day if omitted

Response shape:

```json
{
  "date": "2026-04-29",
  "open_cases": {
    "total_cases": 3,
    "ats": {
      "cat_1": 0,
      "cat_2": 1,
      "cat_3": 1,
      "cat_4": 1,
      "cat_5": 0
    },
    "gender": {
      "male": 1,
      "female": 1,
      "other": 0,
      "unknown": 1
    },
    "age": {
      "0_4": 1,
      "5_12": 0,
      "13_17": 0,
      "18_25": 0,
      "26_45": 1,
      "46_65": 1,
      "65_plus": 0,
      "unknown": 0
    }
  },
  "resolved_cases": {
    "total_cases": 1,
    "ats": {
      "cat_1": 0,
      "cat_2": 0,
      "cat_3": 1,
      "cat_4": 0,
      "cat_5": 0
    },
    "gender": {
      "male": 0,
      "female": 1,
      "other": 0,
      "unknown": 0
    },
    "age": {
      "0_4": 0,
      "5_12": 0,
      "13_17": 0,
      "18_25": 0,
      "26_45": 1,
      "46_65": 0,
      "65_plus": 0,
      "unknown": 0
    }
  }
}
```

---

## Model Metrics Endpoint

### `GET /model-metrics`

Return the stored evaluation metrics for the currently configured classifier model.

Access:
- `researcher`

Response:

```json
{
  "model_name": "deberta",
  "metrics": {
    "accuracy": 0.84,
    "macro_f1": 0.79,
    "confusion_matrix": [
      [12, 1, 0, 0, 0],
      [2, 18, 3, 0, 0],
      [0, 2, 20, 1, 0],
      [0, 0, 1, 14, 2],
      [0, 0, 0, 1, 9]
    ]
  }
}
```

The exact metric keys depend on the contents of:

```text
backend/app/services/triage_classifier/models/model_eval.json
```

---

## Health Endpoint

### `GET /health`

Return backend health status.

Access:
- `admin`

Checks:
- API availability
- Database connectivity
- Encryption key presence
- Route registration count

Response:

```json
{
  "status": "ok",
  "checks": {
    "api": "ok",
    "database": "ok",
    "encryption_key": "ok",
    "routes_loaded": "ok (20 routes)"
  }
}
```

---

## Notes

- Sensitive case identity fields are stored encrypted in the database and decrypted only in backend responses.
- Researcher responses are anonymised before being returned.
- Passwords are hashed using Argon2.
- Soft delete is implemented using user deactivation rather than permanent removal.
- Timestamps are returned as timezone-aware values and should be treated as UTC by the frontend.
