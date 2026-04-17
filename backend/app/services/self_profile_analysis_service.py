from __future__ import annotations

from typing import Any


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


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


def _resolve_create_mode(form_data: dict[str, Any]) -> str:
    mode = _normalize_text(form_data.get("create_mode")) or "standard"
    if mode not in {"light", "standard", "deep"}:
        return "standard"
    return mode


def _first_nonempty(*values: Any) -> str:
    for value in values:
        text = _normalize_text(value)
        if text:
            return text
    return ""


def _collect_sources(raw_materials: dict[str, Any]) -> list[str]:
    if not isinstance(raw_materials, dict):
        return []

    sources: list[str] = []
    for key, label in [
        ("chat_history_text", "聊天记录"),
        ("memory_notes_text", "记忆笔记"),
        ("text_materials_text", "文本材料"),
        ("image_notes_text", "图片说明"),
        ("photo_notes_text", "照片说明"),
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
        ("public_sources_text", "公开资料"),
        ("external_feedback_text", "他人评价"),
    ]:
        text = _normalize_text(raw_materials.get(key))
        if text:
            sources.append(f"{label}：{text[:64]}")

    uploaded_text_documents = raw_materials.get("uploaded_text_documents")
    if isinstance(uploaded_text_documents, list):
        for item in uploaded_text_documents[:3]:
            if isinstance(item, dict):
                filename = _normalize_text(item.get("filename") or item.get("name"))
                content = _normalize_text(item.get("content") or item.get("text"))
                snippet = filename or content[:32]
                if snippet:
                    sources.append(f"文件：{snippet}")

    uploaded_image_documents = raw_materials.get("uploaded_image_documents")
    if isinstance(uploaded_image_documents, list) and uploaded_image_documents:
        sources.append(f"图片材料：{len(uploaded_image_documents)} 张")

    ocr_results = raw_materials.get("ocr_extracted_texts")
    if isinstance(ocr_results, list):
        ocr_texts = []
        for item in ocr_results[:2]:
            if isinstance(item, dict):
                text = _normalize_text(item.get("ocr_text") or item.get("text") or item.get("content"))
            else:
                text = _normalize_text(item)
            if text:
                ocr_texts.append(text[:48])
        if ocr_texts:
            sources.append(f"OCR：{' / '.join(ocr_texts)}")

    return sources


def build_self_profile_analysis_report(
    form_data: dict[str, Any],
    raw_materials: dict[str, Any],
    identity_layer: Any | None = None,
    decision_rules: Any | None = None,
    voice: Any | None = None,
    knowledge_sources: Any | None = None,
    boundary_rules: Any | None = None,
) -> dict[str, Any]:
    if not isinstance(form_data, dict):
        form_data = {}
    if not isinstance(raw_materials, dict):
        raw_materials = {}
    create_mode = _resolve_create_mode(form_data)

    identity_summary = {
        "role": _first_nonempty(
            getattr(identity_layer, "role", None),
            form_data.get("self_identity_role"),
            form_data.get("identity_role"),
            form_data.get("name"),
            "我",
        ),
        "positioning": _first_nonempty(
            getattr(identity_layer, "self_positioning", None),
            form_data.get("self_identity_positioning_text"),
            form_data.get("positioning_text"),
            "先把判断讲清楚，再决定怎么说",
        ),
        "goals": _first_nonempty(
            " / ".join(getattr(identity_layer, "long_term_goals", []) or []),
            form_data.get("self_identity_goals_text"),
            form_data.get("long_term_goals_text"),
        ),
        "values": _first_nonempty(
            " / ".join(getattr(identity_layer, "value_anchors", []) or []),
            form_data.get("self_identity_values_text"),
            form_data.get("value_anchors_text"),
        ),
    }

    core_beliefs = _merge_unique_lines(
        getattr(decision_rules, "selection_principles", None),
        getattr(decision_rules, "decision_frames", None),
        form_data.get("self_analysis_beliefs_text"),
        form_data.get("analysis_beliefs_text"),
        form_data.get("decision_principles_text"),
        form_data.get("principles_text"),
    )

    expression_style = _merge_unique_lines(
        getattr(voice, "sentence_style", None),
        getattr(voice, "direct_when", None),
        getattr(voice, "soft_when", None),
        form_data.get("self_analysis_expression_text"),
        form_data.get("expression_style_text"),
        form_data.get("style_text"),
    )

    work_style = _merge_unique_lines(
        form_data.get("self_analysis_work_style_text"),
        form_data.get("work_style_text"),
        form_data.get("work_system_points"),
        form_data.get("thinking_dna_points"),
    )

    timeline = _merge_unique_lines(
        raw_materials.get("history_text"),
        raw_materials.get("recent_context_text"),
        raw_materials.get("chat_history_text"),
        raw_materials.get("memory_notes_text"),
        raw_materials.get("diary_text"),
        raw_materials.get("letter_text"),
        raw_materials.get("text_materials_text"),
    )
    if not timeline:
        timeline = _merge_unique_lines(
            form_data.get("self_timeline_text"),
            form_data.get("timeline_text"),
            form_data.get("experience_text"),
        )

    external_feedback = _merge_unique_lines(
        form_data.get("self_external_feedback_text"),
        form_data.get("external_feedback_text"),
        form_data.get("feedback_text"),
        raw_materials.get("reply_style_samples_text"),
        raw_materials.get("expression_samples_text"),
    )

    source_snapshot = _collect_sources(raw_materials)
    source_snapshot.extend(
        _merge_unique_lines(
            getattr(knowledge_sources, "static_materials", None),
            getattr(knowledge_sources, "recent_updates", None),
            getattr(knowledge_sources, "designated_sources", None),
        )
    )

    missing_dimensions: list[str] = []
    if not identity_summary.get("goals"):
        missing_dimensions.append("长期目标")
    if not identity_summary.get("values"):
        missing_dimensions.append("价值锚点")
    if not core_beliefs:
        missing_dimensions.append("核心判断规则")
    if not expression_style:
        missing_dimensions.append("表达风格")
    if not work_style:
        missing_dimensions.append("工作 / 做事方式")
    if not timeline:
        missing_dimensions.append("阶段变化")
    if not external_feedback:
        missing_dimensions.append("他人评价")
    if not _merge_unique_lines(
        getattr(knowledge_sources, "designated_sources", None),
        form_data.get("self_public_sources_text"),
        form_data.get("public_sources_text"),
    ):
        missing_dimensions.append("公开资料源")

    boundary_notes = _merge_unique_lines(
        getattr(boundary_rules, "forbidden_actions", None),
        getattr(boundary_rules, "caution_notes", None),
    )

    analysis_focus = _first_nonempty(
        form_data.get("analysis_focus"),
        "素材驱动 / 判断优先 / 可持续更新",
    )

    if create_mode == "light":
        analysis_focus = _first_nonempty(
            analysis_focus,
            "先试轻量，先把骨架跑起来",
        )
    elif create_mode == "deep":
        analysis_focus = _first_nonempty(
            analysis_focus,
            "补全分析摘要、边界与验证样本",
        )

    report_summary_bits = [
        _first_nonempty(identity_summary.get("role"), identity_summary.get("positioning")),
        core_beliefs[0] if core_beliefs else "",
        expression_style[0] if expression_style else "",
        f"缺口：{' / '.join(missing_dimensions[:4])}" if missing_dimensions else "",
    ]
    if create_mode == "light":
        report_summary_bits = report_summary_bits[:3]
    elif create_mode == "deep":
        report_summary_bits.extend(
            [
                f"来源：{' / '.join(source_snapshot[:4])}" if source_snapshot else "",
                f"边界：{' / '.join(boundary_notes[:3])}" if boundary_notes else "",
            ]
        )
    report_summary = "；".join(bit for bit in report_summary_bits if bit)

    return {
        "analysis_focus": analysis_focus,
        "create_mode": create_mode,
        "depth_label": {"light": "轻量", "standard": "标准", "deep": "深度"}[create_mode],
        "identity_summary": identity_summary,
        "core_beliefs": core_beliefs,
        "expression_style": expression_style,
        "work_style": work_style,
        "timeline": timeline,
        "external_feedback": external_feedback,
        "missing_dimensions": missing_dimensions,
        "source_snapshot": source_snapshot[:16],
        "report_summary": report_summary,
        "boundary_notes": boundary_notes,
    }
