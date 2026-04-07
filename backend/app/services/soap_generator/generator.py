import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .config import (
    ConfigError,
    load_llm_settings,
    resolve_model_endpoint,
)
from .schemas import SOAPRequest, SOAPResult


SYSTEM_PROMPT = """
You are a clinical documentation assistant.

Your job is to convert emergency triage dialogue into a structured SOAP note.

Important rules:
1. Do NOT invent facts that are not stated in the dialogue.
2. Separate patient/parent-reported information from clinician-observed information.
3. If information is missing, use null or an empty list.
4. Preserve clinically relevant negatives (e.g. no vomiting, no rash, no chest pain).
5. Assessment must be preliminary only, not a definitive diagnosis unless explicitly stated.
6. Plan should include:
   - next steps
   - likely investigations
   - transfer/disposition
   - monitoring
   - review arrangements
7. If no explicit plan is stated, prefer:
   - "Awaiting medical assessment."
   If even that is not appropriate, use:
   - "Not stated."
8. Use concise professional clinical language.
9. Output JSON only. No markdown fences. No extra commentary.
10. After the "soap" object, include "brief_summary": a short (2–3 sentences) summary in plain language for the patient/family or quick reading. Focus on: who, main concern, and what happens next. Do not use jargon; keep it brief and readable.
"""

USER_PROMPT_TEMPLATE = """
Convert the following triage case into structured SOAP JSON.

Case metadata:
- Scenario number: {scenario_number}
- Scenario summary header: {scenario_summary_header}
- ATS category: {ats_category}
- ATS note: {ats_note}

Dialogue:
{dialogue_text}

Return JSON in exactly this schema:
{{
  "scenario_number": "",
  "summary_header": "",
  "soap": {{
    "subjective": {{
      "chief_complaint": "",
      "history_of_present_illness": [],
      "associated_symptoms": [],
      "negatives": [],
      "relevant_history": []
    }},
    "objective": {{
      "vitals": {{}},
      "exam_findings": [],
      "observed_general_state": []
    }},
    "assessment": [],
    "plan": []
  }},
  "brief_summary": ""
}}
The "brief_summary" must be 2–3 short sentences in plain language for the user (who, main concern, what happens next). No jargon.
"""


class SOAPGenerationError(Exception):
    pass


class SOAPGenerator:
    def __init__(
        self,
        config_path: str = "config.yaml",
        default_provider: str = "Doubao",
        default_series: str = "32K",
        default_model_index: int = 0,
        temperature: float = 0.1,
        max_retries: int = 2,
    ) -> None:
        self.config_path = str(Path(config_path))
        self.temperature = temperature
        self.max_retries = max_retries

        llm_settings = load_llm_settings(self.config_path)
        self.llm_settings = llm_settings

        self.client = OpenAI(
            api_key=llm_settings.api_key,
            base_url=llm_settings.url,
        )

        self.default_provider = default_provider
        self.default_series = default_series
        self.default_model_index = default_model_index

    @staticmethod
    def _extract_json_from_text(text: str) -> Dict[str, Any]:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise SOAPGenerationError("No JSON object found in model response.")

        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as e:
            raise SOAPGenerationError(f"Failed to parse JSON from model response: {e}") from e

    @staticmethod
    def _normalize_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @staticmethod
    def _normalize_vitals(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @classmethod
    def _normalize_result(cls, raw: Dict[str, Any], req: SOAPRequest) -> Dict[str, Any]:
        soap = raw.get("soap", {}) if isinstance(raw, dict) else {}
        subjective = soap.get("subjective", {}) if isinstance(soap, dict) else {}
        objective = soap.get("objective", {}) if isinstance(soap, dict) else {}

        assessment = cls._normalize_list(soap.get("assessment"))
        if not assessment:
            assessment = ["Preliminary assessment not clearly stated."]

        plan = cls._normalize_list(soap.get("plan"))
        if not plan:
            plan = ["Awaiting medical assessment."]

        brief_summary = raw.get("brief_summary")
        if not isinstance(brief_summary, str):
            brief_summary = ""
        else:
            brief_summary = brief_summary.strip()

        return {
            "scenario_number": raw.get("scenario_number") or (req.scenario_number or ""),
            "summary_header": raw.get("summary_header") or (req.scenario_summary_header or ""),
            "soap": {
                "subjective": {
                    "chief_complaint": subjective.get("chief_complaint") or "",
                    "history_of_present_illness": cls._normalize_list(
                        subjective.get("history_of_present_illness")
                    ),
                    "associated_symptoms": cls._normalize_list(
                        subjective.get("associated_symptoms")
                    ),
                    "negatives": cls._normalize_list(subjective.get("negatives")),
                    "relevant_history": cls._normalize_list(
                        subjective.get("relevant_history")
                    ),
                },
                "objective": {
                    "vitals": cls._normalize_vitals(objective.get("vitals")),
                    "exam_findings": cls._normalize_list(objective.get("exam_findings")),
                    "observed_general_state": cls._normalize_list(
                        objective.get("observed_general_state")
                    ),
                },
                "assessment": assessment,
                "plan": plan,
            },
            "brief_summary": brief_summary,
        }

    def _resolve_request_model(self, request: SOAPRequest) -> str:
        provider = request.provider or self.default_provider
        series = request.series or self.default_series
        model_index = request.model_index if request.model_index is not None else self.default_model_index
        endpoint_id = request.endpoint_id

        return resolve_model_endpoint(
            model_tree=self.llm_settings.model_tree,
            provider=provider,
            series=series,
            index=model_index,
            endpoint_id=endpoint_id,
            default_model=getattr(self.llm_settings, "default_model", None),
        )

    def _call_llm_once(self, req: SOAPRequest) -> Dict[str, Any]:
        model_name = self._resolve_request_model(req)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            scenario_number=req.scenario_number or "",
            scenario_summary_header=req.scenario_summary_header or "",
            ats_category=req.ats_category or "",
            ats_note=req.ats_note or "",
            dialogue_text=req.dialogue_text,
        )

        response = self.client.chat.completions.create(
            model=model_name,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content or ""
        parsed = self._extract_json_from_text(content)
        return self._normalize_result(parsed, req)

    def generate(self, request: SOAPRequest) -> SOAPResult:
        last_error: Optional[Exception] = None
        generation_start = time.perf_counter()

        for attempt in range(self.max_retries + 1):
            try:
                result = self._call_llm_once(request)
                validated = SOAPResult.model_validate(result)
                elapsed = time.perf_counter() - generation_start
                scenario = request.scenario_number or "-"
                print(
                    f"[SOAPGenerator] scenario={scenario} end_to_end_latency={elapsed:.3f}s"
                )
                return validated
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(0.8 * (attempt + 1))
                    continue
                break

        elapsed = time.perf_counter() - generation_start
        scenario = request.scenario_number or "-"
        print(f"[SOAPGenerator] scenario={scenario} failed_after={elapsed:.3f}s")
        raise SOAPGenerationError(f"SOAP generation failed: {last_error}") from last_error
