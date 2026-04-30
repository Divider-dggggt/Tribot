from typing import Any, Dict, List, Optional

from .generator import SOAPGenerator
from .schemas import SOAPRequest


_generator: Optional[SOAPGenerator] = None


def init_soap_generator(
    config_path: str = "config.yaml",
    default_provider: str = "Doubao",
    default_series: str = "32K",
    default_model_index: int = 0,
    temperature: float = 0.1,
    max_retries: int = 2,
) -> SOAPGenerator:
    global _generator
    _generator = SOAPGenerator(
        config_path=config_path,
        default_provider=default_provider,
        default_series=default_series,
        default_model_index=default_model_index,
        temperature=temperature,
        max_retries=max_retries,
    )
    return _generator


def get_soap_generator() -> SOAPGenerator:
    global _generator
    if _generator is None:
        _generator = SOAPGenerator()
    return _generator


def generate_soap(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Other services in project can straighforwardly call。

    payload can include：
    {
        "scenario_number": "001",
        "scenario_summary_header": "Febrile infant",
        "ats_category": "ATS 2",
        "ats_note": "Urgent review",
        "dialogue_text": "...",
        "provider": "Doubao",
        "series": "32K",
        "model_index": 0
    }

    or explicitly indicate：
    {
        "dialogue_text": "...",
        "endpoint_id": "ep-20250425135605-wzd28"
    }
    """
    req = SOAPRequest.model_validate(payload)
    generator = get_soap_generator()
    result = generator.generate(req)
    return result.model_dump()


def generate_soap_batch(payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    generator = get_soap_generator()
    results: List[Dict[str, Any]] = []

    for payload in payloads:
        req = SOAPRequest.model_validate(payload)
        result = generator.generate(req)
        results.append(result.model_dump())

    return results


GENERATE_SOAP_TOOL_SPEC = {
    "name": "generate_soap",
    "description": (
        "Generate a structured SOAP note from triage dialogue. "
        "Supports selecting a model from config.yaml by provider/series/index "
        "or directly by endpoint_id."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "scenario_number": {"type": "string"},
            "scenario_summary_header": {"type": "string"},
            "ats_category": {"type": "string"},
            "ats_note": {"type": "string"},
            "dialogue_text": {"type": "string"},
            "provider": {
                "type": "string",
                "description": "e.g. Doubao or DeepSeek"
            },
            "series": {
                "type": "string",
                "description": "e.g. 32K, 256K, V3, R1"
            },
            "model_index": {
                "type": "integer",
                "description": "index in the configured model list",
                "default": 0
            },
            "endpoint_id": {
                "type": "string",
                "description": "Direct endpoint id, e.g. ep-xxxx"
            }
        },
        "required": ["dialogue_text"]
    }
}