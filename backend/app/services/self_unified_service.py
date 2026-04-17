from __future__ import annotations

import re
from typing import Any

from app.schemas.self_unified import (
    SelfPersonaUnifiedDraft,
    SelfUnifiedBoundaryRules,
    SelfUnifiedDeepDiveItem,
    SelfUnifiedDecisionRules,
    SelfProfileAnalysisReport,
    SelfProfileInterviewItem,
    SelfProfileInterviewPack,
    SelfUnifiedIdentity,
    SelfUnifiedKnowledgeSourceItem,
    SelfUnifiedKnowledgeSources,
    SelfUnifiedQuestionRoute,
    SelfUnifiedTextBlock,
    SelfUnifiedValidationSample,
    SelfUnifiedVoice,
)
from app.services.self_profile_analysis_service import build_self_profile_analysis_report
from app.services.self_profile_interview_service import build_self_profile_interview_pack


class SelfUnifiedError(RuntimeError):
    pass


_DEFAULT_DEEP_DIVE_QUESTIONS = [
    "哪类问题你会特别坚定？",
    "哪类问题你会保留余地？",
    "你做过最典型的一次错误判断是什么？",
    "哪些原则是你后来才形成的？",
    "你会如何权衡长期和短期？",
    "你最讨厌哪种建议方式？",
    "什么场景下你会故意说得更直接？",
    "什么场景下你会更克制？",
    "你最常先看什么信息再下判断？",
    "什么信息不足时你会先追问？",
]

_DEFAULT_VALIDATION_SAMPLES = [
    "要不要接这个 offer？",
    "学什么技术更值？",
    "要不要先做 MVP？",
    "这件事应该止损还是继续推进？",
]

_QUESTION_ROUTE_DEFAULTS = [
    (
        "职业 / 求职 / 成长判断",
        {"self_decision_rules": 0.45, "self_identity": 0.25, "self_voice": 0.15, "self_knowledge_sources": 0.15},
        ["先看位置，再看代价，再看回报", "更重视长期选择和角色定位"],
    ),
    (
        "学习 / 技术 / 工具选择",
        {"self_knowledge_sources": 0.45, "self_decision_rules": 0.3, "self_identity": 0.15, "self_voice": 0.1},
        ["先查证，再比较，再做选择", "更重视已知事实和可验证材料"],
    ),
    (
        "产品 / 项目 / 执行",
        {"self_decision_rules": 0.4, "self_knowledge_sources": 0.3, "self_identity": 0.15, "self_voice": 0.15},
        ["先看目标与约束，再看推进方式", "更重视落地和节奏控制"],
    ),
    (
        "决策 / 取舍 / 风险判断",
        {"self_decision_rules": 0.55, "self_identity": 0.2, "self_knowledge_sources": 0.15, "self_voice": 0.1},
        ["先判断风险，再看收益", "更重视止损与边界"],
    ),
    (
        "关系 / 情绪 / 自我反思",
        {"self_identity": 0.4, "self_voice": 0.3, "self_boundary_rules": 0.2, "self_decision_rules": 0.1},
        ["先接住状态，再看边界", "更重视真实感受与表达方式"],
    ),
]


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _split_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


def _merge_unique_lines(*values: Any) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for value in values:
        for line in _split_lines(value):
            normalized = _normalize_text(line)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            merged.append(normalized)
    return merged


def _first_nonempty(*values: Any) -> str:
    for value in values:
        text = _normalize_text(value)
        if text:
            return text
    return ""


def _format_bullets(items: list[Any]) -> str:
    lines = [_normalize_text(item) for item in items if _normalize_text(item)]
    if not lines:
        return ""
    return "\n".join(f"- {line}" for line in lines)


def _extract_layer_text(
    form_data: dict[str, Any],
    keys: list[str],
    fallback_summary: str,
) -> SelfUnifiedTextBlock:
    summary = _first_nonempty(*(form_data.get(key) for key in keys))
    points = _merge_unique_lines(*(form_data.get(f"{key}_points") for key in keys))
    if not summary and points:
        summary = points[0]
    if not summary:
        summary = fallback_summary
    return SelfUnifiedTextBlock(summary=summary, points=points)


def _read_layer_text(form_data: dict[str, Any], layer_key: str, fallback_summary: str = "") -> SelfUnifiedTextBlock:
    raw_layer = form_data.get(layer_key)
    summary = ""
    points: list[str] = []
    if isinstance(raw_layer, dict):
        summary = _first_nonempty(raw_layer.get("summary"), raw_layer.get("title"))
        points = _merge_unique_lines(raw_layer.get("points"), raw_layer.get("items"), raw_layer.get("details"))
    else:
        summary = _first_nonempty(form_data.get(f"{layer_key}_summary"), form_data.get(layer_key))
        points = _merge_unique_lines(
            form_data.get(f"{layer_key}_points"),
            form_data.get(f"{layer_key}_items"),
            form_data.get(f"{layer_key}_details"),
        )
    if not summary and points:
        summary = points[0]
    if not summary:
        summary = fallback_summary
    return SelfUnifiedTextBlock(summary=summary, points=points)


def _summarize_raw_materials(raw_materials: dict[str, Any]) -> tuple[str, list[str]]:
    snippets: list[str] = []
    if not isinstance(raw_materials, dict):
        return "", snippets

    for key, label in [
        ("chat_history_text", "聊天记录"),
        ("memory_notes_text", "记忆笔记"),
        ("text_materials_text", "文本材料"),
        ("image_notes_text", "图片说明"),
        ("voice_notes_text", "语音说明"),
        ("diary_text", "日记"),
        ("letter_text", "信件"),
        ("conflict_text", "冲突片段"),
        ("draft_message_text", "待发送消息"),
        ("recent_context_text", "最近上下文"),
        ("reply_style_samples_text", "回复样本"),
        ("relationship_status_text", "关系状态"),
        ("interaction_patterns_text", "互动样本"),
        ("history_text", "历史材料"),
        ("expression_samples_text", "表达样本"),
    ]:
        text = _normalize_text(raw_materials.get(key))
        if text:
            snippets.append(f"{label}：{text[:48]}")

    uploaded_text_documents = raw_materials.get("uploaded_text_documents")
    if isinstance(uploaded_text_documents, list):
        for item in uploaded_text_documents[:2]:
            if isinstance(item, dict):
                filename = _normalize_text(item.get("filename") or item.get("name"))
                content = _normalize_text(item.get("content") or item.get("text"))
                piece = filename or content[:32]
                if piece:
                    snippets.append(f"文件：{piece}")

    uploaded_image_documents = raw_materials.get("uploaded_image_documents")
    if isinstance(uploaded_image_documents, list):
        snippets.append(f"图片材料：{len(uploaded_image_documents)} 张")
    ocr_results = raw_materials.get("ocr_extracted_texts")
    if isinstance(ocr_results, list):
        ocr_texts = [
            _normalize_text(item.get("ocr_text") if isinstance(item, dict) else item)
            for item in ocr_results
            if _normalize_text(item.get("ocr_text") if isinstance(item, dict) else item)
        ]
        if ocr_texts:
            snippets.append(f"OCR：{ocr_texts[0][:48]}")

    summary = " / ".join(snippets[:8])
    return summary, snippets


def _build_identity(form_data: dict[str, Any], materials_summary: str) -> SelfUnifiedIdentity:
    work_system = _read_layer_text(form_data, "work_system", "先把能证明判断方式的素材整理好。")
    return SelfUnifiedIdentity(
        role=_first_nonempty(
            form_data.get("self_identity_role"),
            form_data.get("identity_role"),
            work_system.summary,
            form_data.get("name"),
            "我",
        ),
        long_term_goals=_merge_unique_lines(
            form_data.get("self_identity_goals_text"),
            form_data.get("long_term_goals_text"),
            form_data.get("goals_text"),
            work_system.points,
        ),
        value_anchors=_merge_unique_lines(
            form_data.get("self_identity_values_text"),
            form_data.get("value_anchors_text"),
            form_data.get("values_text"),
        ),
        bottom_lines=_merge_unique_lines(
            form_data.get("self_identity_bottom_lines_text"),
            form_data.get("bottom_lines_text"),
            form_data.get("non_negotiables_text"),
        ),
        self_positioning=_first_nonempty(
            form_data.get("self_identity_positioning_text"),
            form_data.get("positioning_text"),
            materials_summary,
            "我是谁、我站在什么位置说话",
        ),
        experience_tags=_merge_unique_lines(
            form_data.get("self_identity_experience_tags_text"),
            form_data.get("experience_tags_text"),
            form_data.get("experience_text"),
        ),
    )


def _build_decision_rules(form_data: dict[str, Any]) -> SelfUnifiedDecisionRules:
    thinking_dna = _read_layer_text(form_data, "thinking_dna", "先判断条件，再决定下一步。")
    return SelfUnifiedDecisionRules(
        risk_preference=_first_nonempty(
            form_data.get("self_decision_risk_preference_text"),
            form_data.get("risk_preference_text"),
            thinking_dna.summary,
            "先保底，再冲高",
        ),
        selection_principles=_merge_unique_lines(
            form_data.get("self_decision_principles_text"),
            form_data.get("decision_principles_text"),
            form_data.get("principles_text"),
            thinking_dna.points,
        ),
        decision_frames=_merge_unique_lines(
            form_data.get("self_decision_frames_text"),
            form_data.get("decision_frames_text"),
            form_data.get("frameworks_text"),
        ),
        tradeoff_style=_merge_unique_lines(
            form_data.get("self_decision_tradeoffs_text"),
            form_data.get("tradeoff_style_text"),
            form_data.get("tradeoffs_text"),
        ),
        stop_loss_rules=_merge_unique_lines(
            form_data.get("self_decision_stop_loss_text"),
            form_data.get("stop_loss_rules_text"),
            form_data.get("stop_loss_text"),
        ),
        push_rules=_merge_unique_lines(
            form_data.get("self_decision_push_rules_text"),
            form_data.get("push_rules_text"),
            form_data.get("push_text"),
        ),
        non_binding_promises=_merge_unique_lines(
            form_data.get("self_decision_non_binding_text"),
            form_data.get("non_binding_promises_text"),
        ),
        safety_buffer_rules=_merge_unique_lines(
            form_data.get("self_decision_safety_buffer_text"),
            form_data.get("safety_buffer_rules_text"),
        ),
    )


def _build_voice(form_data: dict[str, Any]) -> SelfUnifiedVoice:
    reply_persona = _read_layer_text(form_data, "reply_persona", "先给结论，再补理由。")
    return SelfUnifiedVoice(
        tone=_first_nonempty(
            form_data.get("self_voice_tone_text"),
            form_data.get("voice_tone_text"),
            reply_persona.summary,
            "清楚、克制、自然",
        ),
        sentence_style=_merge_unique_lines(
            form_data.get("self_voice_sentence_style_text"),
            form_data.get("sentence_style_text"),
            form_data.get("style_text"),
            reply_persona.points,
        ),
        expression_rhythm=_first_nonempty(
            form_data.get("self_voice_rhythm_text"),
            form_data.get("expression_rhythm_text"),
        ),
        humor_style=_first_nonempty(
            form_data.get("self_voice_humor_text"),
            form_data.get("humor_style_text"),
        ),
        conclusion_style=_first_nonempty(
            form_data.get("self_voice_conclusion_text"),
            form_data.get("conclusion_style_text"),
            "先给结论，再补理由",
        ),
        direct_when=_merge_unique_lines(
            form_data.get("self_voice_direct_when_text"),
            form_data.get("direct_when_text"),
        ),
        soft_when=_merge_unique_lines(
            form_data.get("self_voice_soft_when_text"),
            form_data.get("soft_when_text"),
        ),
    )


def _build_knowledge_sources(
    form_data: dict[str, Any],
    raw_materials: dict[str, Any],
    materials_summary: str,
) -> SelfUnifiedKnowledgeSources:
    memory_evidence = _read_layer_text(form_data, "memory_evidence", "把材料和记忆痕迹整理出来。")
    static_materials = _merge_unique_lines(
        materials_summary,
        form_data.get("self_knowledge_static_text"),
        form_data.get("knowledge_static_text"),
        memory_evidence.summary,
        memory_evidence.points,
    )
    recent_updates = _merge_unique_lines(
        form_data.get("self_knowledge_recent_text"),
        form_data.get("knowledge_recent_text"),
    )
    designated_sources = _merge_unique_lines(
        form_data.get("self_knowledge_sources_text"),
        form_data.get("knowledge_sources_text"),
        form_data.get("self_public_sources_text"),
        form_data.get("public_sources_text"),
    )
    dynamic_source_lines = _merge_unique_lines(
        form_data.get("self_knowledge_dynamic_text"),
        form_data.get("dynamic_sources_text"),
    )
    dynamic_sources: list[SelfUnifiedKnowledgeSourceItem] = []
    for index, line in enumerate(dynamic_source_lines):
        dynamic_sources.append(
            SelfUnifiedKnowledgeSourceItem(
                label=line[:32],
                kind="dynamic",
                detail=line,
                freshness="recent",
                priority=index + 1,
            )
        )
    verify_first_question_types = _merge_unique_lines(
        form_data.get("self_knowledge_verify_text"),
        form_data.get("knowledge_verify_text"),
    )
    do_not_assume_facts = _merge_unique_lines(
        form_data.get("self_knowledge_do_not_assume_text"),
        form_data.get("knowledge_do_not_assume_text"),
        "不把动态事实说死",
    )
    if raw_materials.get("uploaded_text_documents"):
        designated_sources.append("上传文档")
    if raw_materials.get("uploaded_image_documents"):
        designated_sources.append("图片 / OCR")
    return SelfUnifiedKnowledgeSources(
        static_materials=static_materials,
        recent_updates=recent_updates,
        designated_sources=_merge_unique_lines(designated_sources),
        dynamic_sources=dynamic_sources,
        verify_first_question_types=verify_first_question_types
        or [
            "具体院校 / 专业 / 工具 / 项目",
            "近期事实变化",
            "最新政策 / 价格 / 版本",
        ],
        do_not_assume_facts=do_not_assume_facts,
    )


def _build_boundary_rules(form_data: dict[str, Any]) -> SelfUnifiedBoundaryRules:
    reflection_rules = _read_layer_text(form_data, "reflection_rules", "保留边界，不替自己下结论。")
    forbidden_actions = _merge_unique_lines(
        form_data.get("self_boundary_rules_text"),
        form_data.get("boundary_rules_text"),
        reflection_rules.summary,
        reflection_rules.points,
        "不编造没发生过的经历",
        "不假装熟悉并不了解的领域",
        "不为了像而乱加人设",
        "不把不确定的动态事实说死",
    )
    caution_notes = _merge_unique_lines(
        form_data.get("self_boundary_notes_text"),
        form_data.get("boundary_notes_text"),
    )
    return SelfUnifiedBoundaryRules(
        forbidden_actions=forbidden_actions,
        caution_notes=caution_notes,
    )


def _build_question_routing() -> list[SelfUnifiedQuestionRoute]:
    routes: list[SelfUnifiedQuestionRoute] = []
    for topic, weights, notes in _QUESTION_ROUTE_DEFAULTS:
        routes.append(SelfUnifiedQuestionRoute(topic=topic, weights=weights, notes=notes))
    return routes


def _build_deep_dive_items(form_data: dict[str, Any]) -> tuple[list[str], list[SelfUnifiedDeepDiveItem]]:
    answers_text = _first_nonempty(
        form_data.get("self_deep_dive_answers_text"),
        form_data.get("deep_dive_answers_text"),
    )
    answers = _split_lines(answers_text)
    deep_dive_answers: list[SelfUnifiedDeepDiveItem] = []
    for index, prompt in enumerate(_DEFAULT_DEEP_DIVE_QUESTIONS):
        deep_dive_answers.append(
            SelfUnifiedDeepDiveItem(
                question=prompt,
                answer=answers[index] if index < len(answers) else "",
                follow_up_needed=index >= len(answers),
            )
        )
    return _DEFAULT_DEEP_DIVE_QUESTIONS, deep_dive_answers


def _build_validation_samples(form_data: dict[str, Any]) -> list[SelfUnifiedValidationSample]:
    sample_lines = _split_lines(
        _first_nonempty(
            form_data.get("self_validation_samples_text"),
            form_data.get("validation_samples_text"),
        )
    )
    if not sample_lines:
        sample_lines = list(_DEFAULT_VALIDATION_SAMPLES)

    samples: list[SelfUnifiedValidationSample] = []
    for index, question in enumerate(sample_lines[:6]):
        samples.append(
            SelfUnifiedValidationSample(
                question=question,
                expected_behavior=[
                    "先给判断",
                    "符合本人决策习惯",
                    "不说违背价值观的话",
                ],
                expected_not=[
                    "不编造经历",
                    "不把动态事实说死",
                ],
                notes=f"验证样本 {index + 1}",
            )
        )
    return samples


def _format_text_block(title: str, summary: str, points: list[str]) -> SelfUnifiedTextBlock:
    lines = [summary] if summary else []
    lines.extend(points)
    text = "\n".join(line for line in lines if line).strip()
    if not text:
        return SelfUnifiedTextBlock()
    return SelfUnifiedTextBlock(summary=summary or text, points=points)


def _route_question(question: str, persona: dict[str, Any] | None = None) -> SelfUnifiedQuestionRoute:
    normalized = _normalize_text(question)
    topic = "关系 / 情绪 / 自我反思"
    if any(keyword in normalized for keyword in ["offer", "转方向", "升职", "跳槽", "职业", "工作", "求职", "学校", "毕业", "面试"]):
        topic = "职业 / 求职 / 成长判断"
    elif any(keyword in normalized for keyword in ["技术", "工具", "框架", "代码", "学习", "系统", "模型", "版本"]):
        topic = "学习 / 技术 / 工具选择"
    elif any(keyword in normalized for keyword in ["项目", "产品", "mvp", "执行", "推进", "上线", "排期"]):
        topic = "产品 / 项目 / 执行"
    elif any(keyword in normalized for keyword in ["止损", "风险", "取舍", "该不该", "要不要", "选择"]):
        topic = "决策 / 取舍 / 风险判断"

    route_lookup = {item.topic: item for item in _build_question_routing()}
    base = route_lookup.get(topic) or SelfUnifiedQuestionRoute(topic=topic)
    return base


def build_self_unified_draft(form_data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(form_data, dict):
        raise SelfUnifiedError("form_data must be an object")

    create_mode = _normalize_text(form_data.get("create_mode")) or "standard"
    input_modes = form_data.get("input_modes")
    if isinstance(input_modes, list):
        normalized_input_modes = [_normalize_text(item) for item in input_modes if _normalize_text(item)]
    else:
        normalized_input_modes = _split_lines(input_modes)
    if not normalized_input_modes:
        normalized_input_modes = [_normalize_text(form_data.get("input_mode")) or "manual_profile"]

    raw_materials = form_data.get("raw_materials") if isinstance(form_data.get("raw_materials"), dict) else {}
    raw_materials = raw_materials or {}
    materials_summary, _ = _summarize_raw_materials(raw_materials)

    # Backwards compatibility: old five-layer signals still populate the new four-layer structure.
    identity_layer = _build_identity(form_data, materials_summary)
    decision_rules = _build_decision_rules(form_data)
    voice = _build_voice(form_data)
    knowledge_sources = _build_knowledge_sources(form_data, raw_materials, materials_summary)
    boundary_rules = _build_boundary_rules(form_data)
    profile_analysis_report = build_self_profile_analysis_report(
        form_data,
        raw_materials,
        identity_layer=identity_layer,
        decision_rules=decision_rules,
        voice=voice,
        knowledge_sources=knowledge_sources,
        boundary_rules=boundary_rules,
    )
    profile_interview = build_self_profile_interview_pack(form_data, profile_analysis_report)
    question_routing = _build_question_routing()
    interview_questions = profile_interview.get("questions") or []
    deep_dive_questions = [item.get("question", "") for item in interview_questions if _normalize_text(item.get("question"))]
    deep_dive_answers = [
        SelfUnifiedDeepDiveItem(
            question=_normalize_text(item.get("question")),
            answer=_normalize_text(item.get("answer")),
            follow_up_needed=bool(item.get("follow_up_needed")),
        )
        for item in interview_questions
        if _normalize_text(item.get("question"))
    ]
    validation_samples = _build_validation_samples(form_data)

    legacy_work_system = _format_text_block(
        "做事方式",
        _first_nonempty(_read_layer_text(form_data, "work_system").summary, identity_layer.self_positioning),
        _merge_unique_lines(_read_layer_text(form_data, "work_system").points, identity_layer.long_term_goals),
    )
    legacy_reply_persona = _format_text_block(
        "回复方式",
        _first_nonempty(_read_layer_text(form_data, "reply_persona").summary, voice.tone),
        _merge_unique_lines(_read_layer_text(form_data, "reply_persona").points, voice.sentence_style),
    )
    legacy_thinking_dna = _format_text_block(
        "思考方式",
        _first_nonempty(
            _read_layer_text(form_data, "thinking_dna").summary,
            decision_rules.selection_principles[0] if decision_rules.selection_principles else "",
        ),
        _merge_unique_lines(_read_layer_text(form_data, "thinking_dna").points, decision_rules.decision_frames),
    )
    legacy_memory_evidence = _format_text_block(
        "材料层",
        _first_nonempty(
            _read_layer_text(form_data, "memory_evidence").summary,
            materials_summary,
            knowledge_sources.static_materials[0] if knowledge_sources.static_materials else "",
        ),
        _merge_unique_lines(_read_layer_text(form_data, "memory_evidence").points, knowledge_sources.static_materials),
    )
    legacy_reflection_rules = _format_text_block(
        "边界规则",
        _first_nonempty(
            _read_layer_text(form_data, "reflection_rules").summary,
            boundary_rules.forbidden_actions[0] if boundary_rules.forbidden_actions else "",
        ),
        _merge_unique_lines(_read_layer_text(form_data, "reflection_rules").points, boundary_rules.caution_notes),
    )

    profile = _format_bullets(
        [
            f"身份：{identity_layer.role}",
            f"定位：{identity_layer.self_positioning}",
            f"长期目标：{' / '.join(identity_layer.long_term_goals[:3])}" if identity_layer.long_term_goals else "",
            f"价值锚点：{' / '.join(identity_layer.value_anchors[:3])}" if identity_layer.value_anchors else "",
        ]
    )
    mindset = _format_bullets(
        [
            f"风险偏好：{decision_rules.risk_preference}",
            *decision_rules.selection_principles[:3],
            *decision_rules.decision_frames[:3],
        ]
    )
    heuristics = _format_bullets(
        [
            *decision_rules.stop_loss_rules[:3],
            *decision_rules.push_rules[:3],
            *decision_rules.non_binding_promises[:3],
            *boundary_rules.forbidden_actions[:3],
        ]
    )
    expression = _format_bullets(
        [
            f"语气：{voice.tone}",
            f"结论方式：{voice.conclusion_style}",
            *voice.sentence_style[:4],
        ]
    )
    guardrails = _format_bullets(
        [
            *boundary_rules.forbidden_actions[:4],
            *boundary_rules.caution_notes[:4],
            *knowledge_sources.do_not_assume_facts[:3],
            profile_analysis_report.get("report_summary", ""),
        ]
    )

    self_persona_unified = SelfPersonaUnifiedDraft(
        create_mode=create_mode,
        input_modes=normalized_input_modes,
        materials_summary=materials_summary,
        profile_analysis_report=SelfProfileAnalysisReport(**profile_analysis_report),
        profile_interview=SelfProfileInterviewPack(**profile_interview),
        self_identity=identity_layer,
        self_decision_rules=decision_rules,
        self_voice=voice,
        self_knowledge_sources=knowledge_sources,
        self_boundary_rules=boundary_rules,
        question_routing=question_routing,
        deep_dive_questions=deep_dive_questions,
        deep_dive_answers=deep_dive_answers,
        validation_samples=validation_samples,
        work_system=legacy_work_system,
        reply_persona=legacy_reply_persona,
        thinking_dna=legacy_thinking_dna,
        memory_evidence=legacy_memory_evidence,
        reflection_rules=legacy_reflection_rules,
    )

    return {
        "profile": profile or "自我主线",
        "mindset": mindset or "先判断，再表达",
        "heuristics": heuristics or "保留边界，不编造事实",
        "expression": expression or "先给结论，再给理由",
        "guardrails": guardrails or "不编造经历，不假装熟悉，不说死动态事实",
        "name": _normalize_text(form_data.get("name")) or "我的人格",
        "create_mode": create_mode,
        "input_modes": normalized_input_modes,
        "material_summary": materials_summary,
        "analysis_focus": _normalize_text(profile_analysis_report.get("analysis_focus")) or "素材驱动 / 判断优先 / 可持续更新",
        "profile_analysis_report": profile_analysis_report,
        "profile_interview": profile_interview,
        "raw_materials": raw_materials,
        "self_persona_unified": self_persona_unified.model_dump(),
    }


def route_self_question(question: str, persona: dict[str, Any] | None = None) -> dict[str, Any]:
    route = _route_question(question, persona)
    return route.model_dump()


def build_self_unified_context(persona: dict[str, Any], history: list[dict[str, str]], user_message: str) -> str:
    payload = persona.get("self_persona_unified") or {}
    if not isinstance(payload, dict):
        payload = {}
    route = route_self_question(user_message, persona)
    create_mode = _normalize_text(payload.get("create_mode")) or "standard"
    depth_label = {"light": "轻量", "standard": "标准", "deep": "深度"}.get(create_mode, "标准")
    analysis_report = payload.get("profile_analysis_report") or {}
    profile_interview = payload.get("profile_interview") or {}
    self_identity = payload.get("self_identity") or {}
    self_decision_rules = payload.get("self_decision_rules") or {}
    self_voice = payload.get("self_voice") or {}
    self_knowledge_sources = payload.get("self_knowledge_sources") or {}
    boundary_rules = payload.get("self_boundary_rules") or {}
    materials_summary = _normalize_text(payload.get("materials_summary"))

    route_weights = route.get("weights") or {}
    prioritized_layers = sorted(route_weights.items(), key=lambda item: item[1], reverse=True)
    layer_summary = ", ".join(f"{key}:{value:.2f}" for key, value in prioritized_layers)
    notes = route.get("notes") or []

    parts = [
        f"蒸馏档位：{depth_label}",
        f"问题路由：{route.get('topic') or '关系 / 情绪 / 自我反思'}",
        f"权重倾向：{layer_summary}" if layer_summary else "",
        f"材料摘要：{materials_summary}" if materials_summary else "",
        f"身份定位：{_normalize_text(self_identity.get('self_positioning')) or _normalize_text(self_identity.get('role'))}",
        f"决策偏好：{_normalize_text(self_decision_rules.get('risk_preference')) or '先保底再判断'}",
        f"表达倾向：{_normalize_text(self_voice.get('tone')) or '清楚、克制、自然'}",
        f"知识源优先：{' / '.join(_split_lines(self_knowledge_sources.get('verify_first_question_types'))[:3])}",
        f"边界规则：{' / '.join(_split_lines(boundary_rules.get('forbidden_actions'))[:3])}",
        f"分析报告：{_normalize_text(analysis_report.get('report_summary'))}",
        f"分析缺口：{' / '.join(_split_lines(analysis_report.get('missing_dimensions'))[:4])}",
        f"追问补洞：{_normalize_text(profile_interview.get('question_count'))} 个问题，已答 {_normalize_text(profile_interview.get('answered_count'))} 个",
    ]
    if notes:
        parts.append("路由提示：")
        parts.extend(f"- {note}" for note in notes if note)
    parts.append(
        {
            "light": "回答要求：先给判断，再给理由；尽量短一点，先保留骨架，动态事实先查知识源；不要编造经历；不确定时先说明缺口。",
            "standard": "回答要求：先给判断，再给理由；动态事实先查知识源；不要编造经历；不确定时先说明缺口。",
            "deep": "回答要求：先给判断，再给理由；必要时补充摘要与验证；动态事实先查知识源；不要编造经历；不确定时先说明缺口。",
        }.get(create_mode, "回答要求：先给判断，再给理由；动态事实先查知识源；不要编造经历；不确定时先说明缺口。")
    )
    return "\n".join(piece for piece in parts if piece).strip()


def build_self_persona_draft(form_data: dict[str, Any]) -> dict[str, Any]:
    return build_self_unified_draft(form_data)


def format_self_unified_for_prompt(persona: dict[str, Any]) -> str:
    payload = persona.get("self_persona_unified") or {}
    if not isinstance(payload, dict):
        return ""

    parts: list[str] = []
    create_mode = _normalize_text(payload.get("create_mode")) or "standard"
    depth_label = {"light": "轻量", "standard": "标准", "deep": "深度"}.get(create_mode, "标准")
    profile_analysis_report = payload.get("profile_analysis_report") or {}
    profile_interview = payload.get("profile_interview") or {}
    identity = payload.get("self_identity") or {}
    decision_rules = payload.get("self_decision_rules") or {}
    voice = payload.get("self_voice") or {}
    knowledge_sources = payload.get("self_knowledge_sources") or {}
    boundary_rules = payload.get("self_boundary_rules") or {}

    def _append_section(title: str, value: Any) -> None:
        text = _normalize_text(value)
        if text:
            parts.append(f"## {title}\n{text}")

    _append_section("蒸馏档位", depth_label)
    _append_section("自我身份层", identity.get("self_positioning") or identity.get("role"))
    _append_section("自我判断层", decision_rules.get("risk_preference"))
    _append_section("自我表达层", voice.get("tone"))
    _append_section("自我知识源层", " / ".join(_split_lines(knowledge_sources.get("static_materials"))[:6]))
    _append_section("自我边界", " / ".join(_split_lines(boundary_rules.get("forbidden_actions"))[:6]))
    _append_section("人物分析报告", profile_analysis_report.get("report_summary"))
    if isinstance(profile_interview, dict):
        interview_lines = []
        for item in (profile_interview.get("questions") or [])[:8]:
            if not isinstance(item, dict):
                continue
            question = _normalize_text(item.get("question"))
            answer = _normalize_text(item.get("answer"))
            if question:
                interview_lines.append(f"- {question}" + (f"｜{answer}" if answer else ""))
        _append_section("追问补洞", "\n".join(interview_lines))
    return "\n\n".join(parts).strip()


def format_self_unified_layers(persona: dict[str, Any]) -> dict[str, Any]:
    payload = persona.get("self_persona_unified") or {}
    if not isinstance(payload, dict):
        return {}
    return {
        "create_mode": payload.get("create_mode") or "standard",
        "profile_analysis_report": payload.get("profile_analysis_report") or {},
        "profile_interview": payload.get("profile_interview") or {},
        "self_identity": payload.get("self_identity") or {},
        "self_decision_rules": payload.get("self_decision_rules") or {},
        "self_voice": payload.get("self_voice") or {},
        "self_knowledge_sources": payload.get("self_knowledge_sources") or {},
        "self_boundary_rules": payload.get("self_boundary_rules") or {},
        "question_routing": payload.get("question_routing") or [],
        "deep_dive_questions": payload.get("deep_dive_questions") or [],
        "validation_samples": payload.get("validation_samples") or [],
    }
