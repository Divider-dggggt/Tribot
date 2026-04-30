# Structure

```text
backend/
├── API_DOCUMENTATION.md                              # Backend API reference
├── Dockerfile                                        # Backend container setup
├── requirements.txt                                  # Python dependencies
├── pytest.ini                                        # Pytest configuration
├── app/
│   ├── main.py                                       # FastAPI app entry point and router registration
│   ├── core/
│   │   ├── config.py                                 # Environment configuration and secrets
│   │   ├── crypto.py                                 # Encryption and decryption helpers
│   │   └── security.py                               # JWT auth, password hashing, and role checks
│   ├── db/
│   │   ├── connection.py                             # PostgreSQL connection setup
│   │   ├── users.py                                  # User-related database operations
│   │   └── cases.py                                  # Case-related database operations
│   ├── routers/
│   │   ├── auth.py                                   # Login, logout, and current-user endpoints
│   │   ├── users.py                                  # User management endpoints
│   │   ├── cases.py                                  # Triage and case workflow endpoints
│   │   ├── analytics.py                              # Daily analytics endpoint
│   │   ├── metrics.py                                # Model evaluation metrics endpoint
│   │   └── health.py                                 # Health check endpoint
│   ├── schemas/
│   │   ├── auth.py                                   # Authentication request schema
│   │   ├── user.py                                   # User request and response schemas
│   │   └── case.py                                   # Case request and response schemas
│   └── services                                      # ML/clinical service layer used by backend routes
│       ├── TRIBOT_SERVICES.md                        # overview of backend ML services and Docker usage
│       ├── anonymisation.py                          # rule-based PII detection and masking for clinical dialogue
│       ├── sample_data                               # shared sample triage dialogues and scenario fixtures
│       │   ├── 0001.txt
│       │   ├── 0005.txt
│       │   ├── anon-test.txt
│       │   └── scenarios.json
│       ├── soap_generator                            # LLM-based SOAP note generation and evaluation tools
│       │   ├── __init__.py
│       │   ├── benchmark                             # fact-aware benchmark for SOAP generation quality
│       │   │   ├── README.md                         # benchmark usage notes
│       │   │   ├── benchmark                         # benchmark scoring/parsing package
│       │   │   │   ├── __init__.py
│       │   │   │   ├── handbook_index.py             # ETEK handbook PDF chunking and TF-IDF retrieval
│       │   │   │   ├── scoring.py                    # structure/fact/safety scoring logic
│       │   │   │   ├── soap_parsing.py               # flattens SOAP JSON into comparable facts
│       │   │   │   └── text_utils.py                 # text normalization and fuzzy/TF-IDF matching
│       │   │   ├── data                              # gold labels, generated samples, and benchmark outputs
│       │   │   │   ├── challenge_set.json
│       │   │   │   ├── eval_gold.json
│       │   │   │   ├── evaluation_results_generated_samples.json
│       │   │   │   ├── generated_outputs_from_samples.json
│       │   │   │   ├── gold_annotations.json
│       │   │   │   ├── gold_as_predictions.json
│       │   │   │   └── handbook_index                # persisted retrieval index for handbook alignment
│       │   │   │       ├── chunks.json
│       │   │   │       ├── matrix.pkl
│       │   │   │       └── vectorizer.pkl
│       │   │   ├── requirements.txt
│       │   │   └── scripts                           # CLI utilities for rebuilding/evaluating benchmark data
│       │   │       ├── build_gold_from_scenarios.py  # derives heuristic gold SOAP facts from scenarios
│       │   │       ├── build_handbook_index.py       # builds local handbook retrieval artifacts
│       │   │       └── evaluate_generated_json.py    # evaluates generated SOAP JSON against gold annotations
│       │   ├── config.py                             # loads LLM config and resolves model endpoint
│       │   ├── config.yaml                           # OpenAI-compatible SOAP generator model config
│       │   ├── generator.py                          # core prompt, LLM call, JSON extraction, normalization
│       │   ├── scenarios.json                        # local/backward-compatible SOAP sample scenarios
│       │   ├── schemas.py                            # Pydantic request/result schemas for SOAP output
│       │   ├── soap_test.py                          # Docker-friendly smoke test and lightweight evaluation runner
│       │   ├── summariser_service.py                 # formats generated SOAP as markdown plus brief summary
│       │   └── tools.py                              # public service wrappers used by other backend modules
│       └── triage_classifier                         # ATS prediction, safety flagging, and RAG triage services
│           ├── RAG                                   # handbook-grounded retrieval augmented triage classifier
│           │   ├── README.md                         # Docker usage for RAG indexing and LLM prediction
│           │   ├── artifacts                         # prebuilt BM25/vector retrieval index files
│           │   │   ├── bm25.pkl
│           │   │   ├── embeddings.npy
│           │   │   ├── faiss.index
│           │   │   ├── handbook_chunks.json
│           │   │   └── index_meta.json
│           │   ├── assets                            # source handbook/reference files
│           │   │   └── emergency_triage_education_kit_-_second_edition.pdf
│           │   ├── configs                           # RAG retrieval and LLM configuration
│           │   │   ├── app_config.example.yaml
│           │   │   ├── app_config.yaml
│           │   │   └── llm_config.yaml
│           │   ├── eval_llm_rag.py                   # batch evaluation entry point for LLM/RAG predictions
│           │   ├── handbook_rag_function_project     # RAG implementation package
│           │   │   ├── __init__.py
│           │   │   ├── chunking.py                   # parses handbook PDF into retrievable chunks
│           │   │   ├── config.py                     # resolves RAG config paths
│           │   │   ├── indexing.py                   # builds BM25/vector indices
│           │   │   ├── llm_branch.py                 # calls LLM with retrieved handbook evidence
│           │   │   ├── local_models.py               # optional local classifier branch
│           │   │   ├── normalize.py                  # converts query + retrieval into handbook-fit summary
│           │   │   ├── pipeline.py                   # public ingest/local/LLM prediction functions
│           │   │   └── retrieval.py                  # BM25 + vector retrieval over handbook chunks
│           │   ├── requirements.txt
│           │   └── test_llm_scenario.py              # single-scenario RAG smoke test
│           ├── baseline_predict.py                   # TF-IDF/logistic-regression baseline inference
│           ├── models                                # persisted classifier models and evaluation summaries
│           │   ├── baseline_classifier.pkl
│           │   ├── baseline_vectorizer.pkl
│           │   ├── model_eval.json
│           │   ├── rag_model_eval.json
│           │   ├── sprint2_deberta_model             # packaged DeBERTa ATS classifier
│           │   │   ├── added_tokens.json
│           │   │   ├── config.json
│           │   │   ├── model.safetensors
│           │   │   ├── special_tokens_map.json
│           │   │   ├── spm.model
│           │   │   ├── tokenizer.json
│           │   │   ├── tokenizer_config.json
│           │   │   └── training_args.bin
│           │   ├── sprint2_deberta_model-val.json
│           │   ├── sprint2_setfit_model              # packaged SetFit ATS classifier
│           │   │   ├── 1_Pooling
│           │   │   │   └── config.json
│           │   │   ├── 2_Normalize
│           │   │   ├── README.md
│           │   │   ├── config.json
│           │   │   ├── config_sentence_transformers.json
│           │   │   ├── config_setfit.json
│           │   │   ├── model.safetensors
│           │   │   ├── model_head.pkl
│           │   │   ├── modules.json
│           │   │   ├── sentence_bert_config.json
│           │   │   ├── special_tokens_map.json
│           │   │   ├── tokenizer.json
│           │   │   ├── tokenizer_config.json
│           │   │   └── vocab.txt
│           │   └── sprint2_setfit_model-eval.json
│           ├── sample_data                           # local triage classifier examples
│           ├── severity_flagging.py                  # rule-based high-risk presentation safety layer
│           ├── sprint2_deberta_classifier.py         # DeBERTa model loading and prediction wrapper
│           ├── sprint2_setfit_classifier.py          # SetFit model loading and prediction wrapper
│           ├── sprint3_rag.py                        # backend wrapper for RAG-based ATS prediction
│           └── triage_classifier_service.py          # orchestrates ATS classifier outputs for backend use
└── tests/
    ├── unit/                                         # Unit tests for isolated backend logic
    │   ├── test_anonymisation.py
    │   ├── test_sanity.py
    │   ├── test_security.py
    │   ├── test_severity_flagging.py
    │   └── test_triage_classifier_service.py
    ├── integration/                                  # API and integration tests
    │   ├── test_auth_api.py
    │   ├── test_cases_api.py
    │   ├── test_cases_researcher_api.py
    │   ├── test_cases_workflows.py
    │   ├── test_health.py
    │   ├── test_health_api.py
    │   └── test_users_api.py
    ├── conftest.py                                   # Shared pytest fixtures
    └── be-test-report.md                             # Backend test report
```
