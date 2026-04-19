from __future__ import annotations

from pathlib import Path
import yaml


def load_config(config_path: str) -> dict:
    cfg_path = Path(config_path).resolve()
    cfg_base = cfg_path.parent

    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    handbook_pdf = Path(cfg['paths']['handbook_pdf'])
    if not handbook_pdf.is_absolute():
        handbook_pdf = (cfg_base / handbook_pdf).resolve()
    cfg['paths']['handbook_pdf'] = str(handbook_pdf)

    artifacts_dir = Path(cfg['paths']['artifacts_dir'])
    if not artifacts_dir.is_absolute():
        artifacts_dir = (cfg_base / artifacts_dir).resolve()
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    cfg['paths']['artifacts_dir'] = str(artifacts_dir)
    return cfg
