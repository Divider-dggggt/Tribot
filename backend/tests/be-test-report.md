# Backend Tests

## Summary

Backend testing used pytest and pytest-cov. Unit tests covered core business logic including ATS severity rules, anonymisation behaviour, authentication helpers, and triage decision logic. FastAPI integration tests used TestClient to verify API routing, request validation, permission checks, success responses, and error handling.

External or environment-dependent dependencies were mocked/stubbed where appropriate. This included ML model inference, SOAP summary generation, anonymisation calls inside API routes, authentication identity resolution, and database operations. Mocking these dependencies allowed the tests to isolate backend API behaviour and business logic without relying on model files, external libraries, background tasks, or a live PostgreSQL database.

Coverage was measured using pytest-cov with a .coveragerc file. Direct database implementation files were omitted from coverage because the assessed backend behaviour is tested through API-level integration tests with mocked database boundaries, while database persistence depends on the runtime PostgreSQL environment.

## API / Integration tests

The integration tests were API-level integration tests rather than full end-to-end browser tests. They exercised FastAPI routes through TestClient, including dependency injection, request validation, response models, role-based access checks, and error handling. External services and database calls were mocked so each test remained deterministic and focused on backend behaviour.

## Coverage

```
====================================================== tests coverage ======================================================
_____________________________________ coverage: platform linux, python 3.11.15-final-0 _____________________________________

Name                                                           Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------------------------
app/__init__.py                                                    0      0   100%
app/core/config.py                                                10      2    80%   11, 14
app/core/crypto.py                                                 9      3    67%   6, 12, 16
app/core/security.py                                              53     23    57%   21-23, 38-62
app/main.py                                                       14      0   100%
app/routers/analytics.py                                           8      1    88%   14
app/routers/auth.py                                               20      2    90%   37-38
app/routers/cases.py                                             127     29    77%   16-26, 40-42, 55, 97-98, 122-131, 156-158, 166, 179, 196, 236, 242, 273-285, 307-308
app/routers/health.py                                             31      5    84%   36-37, 42-44
app/routers/metrics.py                                            12      3    75%   22-25
app/routers/users.py                                              78     49    37%   16-17, 22-25, 30-33, 41, 46-55, 60-102, 110-113, 118-121
app/schemas/auth.py                                                4      0   100%
app/schemas/case.py                                              103      6    94%   17, 33, 40, 47, 100, 110
app/schemas/user.py                                               18      0   100%
app/services/anonymisation.py                                     87     24    72%   187-194, 216-228, 236-250, 253
app/services/soap_generator/__init__.py                            2      0   100%
app/services/soap_generator/config.py                             71     26    63%   36, 42, 48, 58, 64, 70-74, 98, 102-124
app/services/soap_generator/generator.py                          99     19    81%   122, 126-127, 132, 135-137, 155, 159, 246-256
app/services/soap_generator/schemas.py                            32      0   100%
app/services/soap_generator/summariser_service.py                 20      0   100%
app/services/soap_generator/tools.py                              25      8    68%   33, 66-74
app/services/triage_classifier/severity_flagging.py              147     29    80%   419-423, 478-481, 494, 509, 514, 550, 554, 573-582, 591-601, 605
app/services/triage_classifier/sprint2_deberta_classifier.py      66     51    23%   19-40, 56-86, 95-104, 113-123, 127
app/services/triage_classifier/triage_classifier_service.py       47     18    62%   75-84, 93-103, 107
--------------------------------------------------------------------------------------------
TOTAL                                                           1083    298    72%
============================================== 53 passed, 1 warning in 12.64s ==============================================
```