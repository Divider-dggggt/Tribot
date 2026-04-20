# ATS Triage Model Comparison README

## Overview

This document summarizes the current comparison of four approaches for ATS triage classification from nurse–patient dialogue:

- Baseline model
- SetFit
- DeBERTa
- RAG pipeline

All results below are based on the same evaluation set and use weighted precision, recall, F1-score, and a 5-class confusion matrix.

## Performance Summary

### Baseline model
- **F1-score:** 0.4148
- **Precision:** 0.4749
- **Recall:** 0.4400

This model performed the worst overall. The confusion matrix shows that it struggled especially on the middle categories, with many ATS 2 and ATS 3 cases being pushed toward neighboring classes. This suggests that a simple lexical model is not strong enough to capture the clinical nuance and contextual dependencies in triage dialogue.

### SetFit
- **F1-score:** 0.5000
- **Precision:** 0.6918
- **Recall:** 0.5000

SetFit improved on the baseline and benefited from sentence-level semantic representations, but performance was still clearly limited. It was better than the baseline at capturing coarse semantic similarity, yet it still confused adjacent ATS levels quite often, especially in ATS 2–4. This indicates that embedding-based shallow classification helps, but is not sufficient for fine-grained triage boundaries.

### DeBERTa
- **F1-score:** 0.9018
- **Precision:** 0.9131
- **Recall:** 0.9000

DeBERTa achieved the best overall performance. It produced the strongest class separation and the most stable confusion matrix, with only a small number of ATS 2/3 and ATS 3/4 boundary errors. This suggests that end-to-end transformer fine-tuning is highly effective for this task, especially when the model needs to understand subtle risk cues, symptom combinations, and contextual modifiers across the full conversation.

### RAG
- **F1-score:** 0.8484
- **Precision:** 0.8645
- **Recall:** 0.8400

The RAG pipeline also performed strongly and was clearly better than the baseline and SetFit, though still below DeBERTa. Its main strength is that it grounds the decision in handbook-aligned evidence, which makes the reasoning more controllable and explainable. The remaining errors suggest that retrieval and handbook-fit normalization help substantially, but the final decision process is still somewhat less discriminative than the strongest fine-tuned classifier.

## Speed Comparison

### Baseline model
The baseline model is the fastest approach. It uses TF-IDF vectorization plus logistic regression, so both training and inference are lightweight and CPU-friendly. It is suitable as a quick benchmark and for rapid prototyping.

### SetFit
SetFit is still relatively lightweight compared with large transformer fine-tuning. Inference is usually efficient, but training is slower than the baseline because it first learns sentence embeddings and then trains a classifier. It is a good middle-ground model when resources are limited.

### DeBERTa
DeBERTa is the heaviest of the pure classification models. Training is significantly slower and requires more compute, and inference is also more expensive than the baseline or SetFit. However, this extra cost is justified by the much stronger predictive performance.

### RAG
RAG is usually the slowest at inference time because it is a pipeline rather than a single classifier. It needs retrieval, handbook-fit normalization, and then either local classification or LLM-based explanation/decision. Even in a lightweight version, it introduces more latency than a direct classifier. Its value is not raw speed, but knowledge grounding and interpretability.

## Architecture Summary

### Baseline model
The baseline model uses a **decoupled vectorization-classification architecture**:
- **Vectorization:** TF-IDF
- **Classifier:** Logistic Regression

Text is converted into sparse lexical features, and the classifier is trained on top of those fixed features. This is a traditional machine learning pipeline.

### SetFit
SetFit uses a **two-stage semantic classification architecture**:
- A sentence-transformer-style embedding model learns task-relevant sentence representations
- A lightweight classifier is trained on top of the resulting embeddings

This means vectorization and classification are still partially separated, but the representation is much more semantic than TF-IDF.

### DeBERTa
DeBERTa uses an **end-to-end transformer sequence classification architecture**:
- Tokenized dialogue is passed through a contextual encoder
- A classification head predicts one of the five ATS levels
- The entire network is fine-tuned jointly

This allows the model to learn contextual language patterns, long-range dependencies, and subtle clinical distinctions directly from the training data.

### RAG
The RAG system uses a **retrieval-grounded decision architecture**:
- User query / dialogue is matched against the ATS handbook with BM25 + vector retrieval
- Relevant handbook chunks are extracted
- A handbook-fit normalizer converts the input into a more guideline-aligned representation
- The downstream branch then performs LLM-based classification

This architecture is not just a classifier; it is a decision pipeline grounded in external knowledge.

## Why Each Model Was Used

### Baseline model
The baseline was used because it is simple, fast, interpretable, and easy to deploy. It provides a minimal reference point for whether the task is learnable at all with standard text classification features.

### SetFit
SetFit was chosen as an efficient semantic baseline. Compared with the baseline model, it can capture sentence-level meaning rather than only lexical overlap, while still remaining lighter than full transformer fine-tuning.

### DeBERTa
DeBERTa was selected as the main supervised classifier because the input format is long, semi-structured triage dialogue. The ATS task depends on subtle contextual cues, interactions between symptoms, and risk modifiers across the conversation, so a strong contextual encoder is well matched to the problem.

### RAG
RAG was used because ATS classification is not only a prediction task but also a guideline-based decision task. By grounding the decision in the Australian ATS handbook, the system becomes more explainable, more controllable, and closer to real clinical reasoning. It is particularly useful when handbook alignment and evidence citation matter as much as raw accuracy.

## Final Takeaway

- **Best predictive model:** DeBERTa
- **Best lightweight baseline:** Baseline TF-IDF + Logistic Regression
- **Best semantic lightweight model:** SetFit
- **Best knowledge-grounded / explainable system:** RAG

In practice, DeBERTa is currently the strongest pure classifier, while RAG is the most promising framework when handbook alignment, interpretability, and retrieval-grounded reasoning are important.

## How to switch model for SOAP and RAG

### RAG:

Under **backend/app/services/triage_classifier/RAG/configs/llm_config.yaml**, replace Url, model with your own API url and model. Under **backend/.env** replace LLM_API_KEY= with your own API key.

### SOAP Generation

Under **backend/app/services/soap_generator/config.yaml** replace url, model with your own API url and model, Under **backend/.env** replace LLM_API_KEY= with your own API key.
