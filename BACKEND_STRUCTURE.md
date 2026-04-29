# Structure

```text
backend/
├── API_DOCUMENTATION.md              # Backend API reference
├── Dockerfile                        # Backend container setup
├── requirements.txt                  # Python dependencies
├── pytest.ini                        # Pytest configuration
├── app/
│   ├── main.py                       # FastAPI app entry point and router registration
│   ├── core/
│   │   ├── config.py                 # Environment configuration and secrets
│   │   ├── crypto.py                 # Encryption and decryption helpers
│   │   └── security.py               # JWT auth, password hashing, and role checks
│   ├── db/
│   │   ├── connection.py             # PostgreSQL connection setup
│   │   ├── users.py                  # User-related database operations
│   │   └── cases.py                  # Case-related database operations
│   ├── routers/
│   │   ├── auth.py                   # Login, logout, and current-user endpoints
│   │   ├── users.py                  # User management endpoints
│   │   ├── cases.py                  # Triage and case workflow endpoints
│   │   ├── analytics.py              # Daily analytics endpoint
│   │   ├── metrics.py                # Model evaluation metrics endpoint
│   │   └── health.py                 # Health check endpoint
│   ├── schemas/
│   │   ├── auth.py                   # Authentication request schema
│   │   ├── user.py                   # User request and response schemas
│   │   └── case.py                   # Case request and response schemas
│   └── services/
│       ├── anonymisation.py          # Dialogue de-identification logic
│       ├── soap_generator/
│       │   ├── summariser_service.py # Main SOAP summary service used by routes
│       │   ├── generator.py          # SOAP generation logic
│       │   ├── schemas.py            # SOAP-related data structures
│       │   └── config.yaml           # SOAP generator configuration
│       └── triage_classifier/
│           ├── triage_classifier_service.py   # Main ATS classification service
│           ├── severity_flagging.py           # Severity flag logic
│           ├── sprint2_deberta_classifier.py  # DeBERTa classifier integration
│           ├── baseline_predict.py            # Baseline prediction helper
│           └── models/                        # Stored evaluation/model artifacts
│               ├── baseline_classifier.pkl
│               ├── baseline_vectorizer.pkl
│               ├── model_eval.json
│               ├── rag_model_eval.json
│               ├── sprint2_deberta_model/
│               ├── sprint2_deberta_model-val.json
│               ├── sprint2_setfit_model/
│               └── sprint2_setfit_model-eval.json
└── tests/
    ├── unit/                         # Unit tests for isolated backend logic
    │   ├── test_anonymisation.py
    │   ├── test_sanity.py
    │   ├── test_security.py
    │   ├── test_severity_flagging.py
    │   └── test_triage_classifier_service.py
    ├── integration/                  # API and integration tests
    │   ├── test_auth_api.py
    │   ├── test_cases_api.py
    │   ├── test_cases_researcher_api.py
    │   ├── test_cases_workflows.py
    │   ├── test_health.py
    │   ├── test_health_api.py
    │   └── test_users_api.py
    ├── conftest.py                   # Shared pytest fixtures
    └── be-test-report.md             # Backend test report
```
