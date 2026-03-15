from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SOAPSubjective(BaseModel):
    chief_complaint: str = ""
    history_of_present_illness: List[str] = Field(default_factory=list)
    associated_symptoms: List[str] = Field(default_factory=list)
    negatives: List[str] = Field(default_factory=list)
    relevant_history: List[str] = Field(default_factory=list)


class SOAPObjective(BaseModel):
    vitals: Dict[str, Any] = Field(default_factory=dict)
    exam_findings: List[str] = Field(default_factory=list)
    observed_general_state: List[str] = Field(default_factory=list)


class SOAPBody(BaseModel):
    subjective: SOAPSubjective
    objective: SOAPObjective
    assessment: List[str] = Field(default_factory=list)
    plan: List[str] = Field(default_factory=list)


class SOAPRequest(BaseModel):
    scenario_number: Optional[str] = ""
    scenario_summary_header: Optional[str] = ""
    ats_category: Optional[str] = ""
    ats_note: Optional[str] = ""
    dialogue_text: str

    # 可选模型选择参数
    provider: Optional[str] = None     # 例如 "Doubao" / "DeepSeek"
    series: Optional[str] = None       # 例如 "32K" / "256K" / "V3" / "R1"
    model_index: int = 0               # 对应列表下标
    endpoint_id: Optional[str] = None  # 直接传 ep-xxxx 时可覆盖 provider/series/index


class SOAPResult(BaseModel):
    scenario_number: str = ""
    summary_header: str = ""
    soap: SOAPBody