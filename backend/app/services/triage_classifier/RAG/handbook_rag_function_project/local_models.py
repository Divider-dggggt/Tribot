from __future__ import annotations

import json
from pathlib import Path
import joblib
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


class LocalClassifier:
    def __init__(self, cfg: dict):
        self.mode = cfg['local_model']['mode']
        self.label_map = cfg['local_model'].get('label_map', [1,2,3,4,5])
        if self.mode == 'sklearn_tfidf_logreg':
            self.vectorizer = joblib.load(cfg['local_model']['sklearn_vectorizer_pkl'])
            self.classifier = joblib.load(cfg['local_model']['sklearn_classifier_pkl'])
        elif self.mode == 'hf_sequence_classifier':
            model_dir = cfg['local_model']['hf_model_dir']
            self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
            self.model.eval()
            self.device = 'mps' if getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            self.max_length = int(cfg['local_model'].get('max_length', 512))
        else:
            raise ValueError(f"Unsupported local_model.mode: {self.mode}")

    def predict(self, text: str) -> dict:
        if self.mode == 'sklearn_tfidf_logreg':
            X = self.vectorizer.transform([text])
            probs = self.classifier.predict_proba(X)[0]
            idx = int(np.argmax(probs))
            return {'ats_category': int(self.label_map[idx]), 'confidence': float(np.max(probs))}
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=self.max_length)
        inputs = {k:v.to(self.device) for k,v in inputs.items()}
        with torch.inference_mode():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0].detach().cpu().numpy()
        idx = int(np.argmax(probs))
        return {'ats_category': int(self.label_map[idx]), 'confidence': float(np.max(probs))}
