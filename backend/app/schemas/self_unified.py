from __future__ import annotations

from pydantic import BaseModel, Field


class SelfUnifiedTextBlock(BaseModel):
    summary: str = ""
    points: list[str] = Field(default_factory=list)


class SelfUnifiedIdentity(BaseModel):
    role: str = ""
    long_term_goals: list[str] = Field(default_factory=list)
    value_anchors: list[str] = Field(default_factory=list)
    bottom_lines: list[str] = Field(default_factory=list)
    self_positioning: str = ""
    experience_tags: list[str] = Field(default_factory=list)


class SelfUnifiedDecisionRules(BaseModel):
    risk_preference: str = ""
    selection_principles: list[str] = Field(default_factory=list)
    decision_frames: list[str] = Field(default_factory=list)
    tradeoff_style: list[str] = Field(default_factory=list)
    stop_loss_rules: list[str] = Field(default_factory=list)
    push_rules: list[str] = Field(default_factory=list)
    non_binding_promises: list[str] = Field(default_factory=list)
    safety_buffer_rules: list[str] = Field(default_factory=list)


class SelfUnifiedVoice(BaseModel):
    tone: str = ""
    sentence_style: list[str] = Field(default_factory=list)
    expression_rhythm: str = ""
    humor_style: str = ""
    conclusion_style: str = ""
    direct_when: list[str] = Field(default_factory=list)
    soft_when: list[str] = Field(default_factory=list)


class SelfUnifiedKnowledgeSourceItem(BaseModel):
    label: str = ""
    kind: str = ""
    detail: str = ""
    freshness: str = ""
    priority: int = 0


class SelfUnifiedKnowledgeSources(BaseModel):
    static_materials: list[str] = Field(default_factory=list)
    recent_updates: list[str] = Field(default_factory=list)
    designated_sources: list[str] = Field(default_factory=list)
    dynamic_sources: list[SelfUnifiedKnowledgeSourceItem] = Field(default_factory=list)
    verify_first_question_types: list[str] = Field(default_factory=list)
    do_not_assume_facts: list[str] = Field(default_factory=list)


class SelfUnifiedBoundaryRules(BaseModel):
    forbidden_actions: list[str] = Field(default_factory=list)
    caution_notes: list[str] = Field(default_factory=list)
    do_not_invent_experiences: bool = True
    do_not_fake_familiarity: bool = True
    do_not_override_values: bool = True
    do_not_overstate_dynamic_facts: bool = True


class SelfUnifiedQuestionRoute(BaseModel):
    topic: str = ""
    weights: dict[str, float] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class SelfUnifiedDeepDiveItem(BaseModel):
    question: str = ""
    answer: str = ""
    follow_up_needed: bool = False


class SelfUnifiedValidationSample(BaseModel):
    question: str = ""
    expected_behavior: list[str] = Field(default_factory=list)
    expected_not: list[str] = Field(default_factory=list)
    notes: str = ""


class SelfProfileAnalysisReport(BaseModel):
    analysis_focus: str = ""
    identity_summary: dict[str, str] = Field(default_factory=dict)
    core_beliefs: list[str] = Field(default_factory=list)
    expression_style: list[str] = Field(default_factory=list)
    work_style: list[str] = Field(default_factory=list)
    timeline: list[str] = Field(default_factory=list)
    external_feedback: list[str] = Field(default_factory=list)
    missing_dimensions: list[str] = Field(default_factory=list)
    source_snapshot: list[str] = Field(default_factory=list)
    report_summary: str = ""


class SelfProfileInterviewItem(BaseModel):
    question: str = ""
    dimension: str = ""
    reason: str = ""
    answer: str = ""
    follow_up_needed: bool = False


class SelfProfileInterviewPack(BaseModel):
    question_count: int = 0
    answered_count: int = 0
    unanswered_count: int = 0
    questions: list[SelfProfileInterviewItem] = Field(default_factory=list)
    answer_notes: list[str] = Field(default_factory=list)


class SelfPersonaUnifiedDraft(BaseModel):
    create_mode: str = "standard"
    input_modes: list[str] = Field(default_factory=list)
    materials_summary: str = ""
    profile_analysis_report: SelfProfileAnalysisReport = Field(default_factory=SelfProfileAnalysisReport)
    profile_interview: SelfProfileInterviewPack = Field(default_factory=SelfProfileInterviewPack)
    self_identity: SelfUnifiedIdentity = Field(default_factory=SelfUnifiedIdentity)
    self_decision_rules: SelfUnifiedDecisionRules = Field(default_factory=SelfUnifiedDecisionRules)
    self_voice: SelfUnifiedVoice = Field(default_factory=SelfUnifiedVoice)
    self_knowledge_sources: SelfUnifiedKnowledgeSources = Field(default_factory=SelfUnifiedKnowledgeSources)
    self_boundary_rules: SelfUnifiedBoundaryRules = Field(default_factory=SelfUnifiedBoundaryRules)
    question_routing: list[SelfUnifiedQuestionRoute] = Field(default_factory=list)
    deep_dive_questions: list[str] = Field(default_factory=list)
    deep_dive_answers: list[SelfUnifiedDeepDiveItem] = Field(default_factory=list)
    validation_samples: list[SelfUnifiedValidationSample] = Field(default_factory=list)
    work_system: SelfUnifiedTextBlock = Field(default_factory=SelfUnifiedTextBlock)
    reply_persona: SelfUnifiedTextBlock = Field(default_factory=SelfUnifiedTextBlock)
    thinking_dna: SelfUnifiedTextBlock = Field(default_factory=SelfUnifiedTextBlock)
    memory_evidence: SelfUnifiedTextBlock = Field(default_factory=SelfUnifiedTextBlock)
    reflection_rules: SelfUnifiedTextBlock = Field(default_factory=SelfUnifiedTextBlock)


SelfUnifiedLayer = SelfUnifiedTextBlock
SelfPersonaUnifiedLayer = SelfUnifiedTextBlock
