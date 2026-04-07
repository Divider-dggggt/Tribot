from pathlib import Path
from app.services.soap_generator import init_soap_generator, generate_soap

_INITIALIZED = False

def generate_soap_summary(dialogue_text: str) -> str:
    global _INITIALIZED

    if not _INITIALIZED:
        script_dir = Path(__file__).resolve().parent
        config_path = script_dir / "config.yaml"
        init_soap_generator(config_path=str(config_path))
        _INITIALIZED = True

    result = generate_soap({
        "dialogue_text": dialogue_text
    })

    return result["brief_summary"]