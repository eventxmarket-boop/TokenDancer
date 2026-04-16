from __future__ import annotations

import re
from typing import Any


GRIEF_HINTS = ("想念", "难过", "失落", "怀念", "告别", "离开", "难舍", "遗憾", "空落")
RECALL_HINTS = ("记得", "回忆", "以前", "那时候", "过去", "从前", "曾经", "重逢", "再见")
COMFORT_HINTS = ("怎么办", "难受", "想哭", "睡不着", "撑不住", "压力", "害怕")
DISTRESS_HINTS = ("活不下去", "不想活", "自杀", "崩溃", "撑不住了", "绝望", "消失")
DEPENDENCY_HINTS = ("一直陪我", "只要你在", "你别走", "不要离开", "只有你", "永远陪着我")
CERTAINTY_HINTS = ("一定", "肯定", "现在就在", "一直都知道", "此刻正在看着你")
SUPERNATURAL_HINTS = ("灵魂", "死后", "来世", "天上", "看着你", "守护着你")
LAYER_ORDER = ("episodic", "semantic", "procedural")


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _clean_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


def _guided_answer_lines(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [
            _normalize_text(item)
            for item in value.values()
            if _normalize_text(item)
        ]
    return _clean_lines(value)


def _split_keywords(text: str) -> list[str]:
    return [item for item in re.split(r"[\s,，。！？!?、/|]+", _normalize_text(text)) if len(item) >= 2]


def _collect_layered_memories(memory_base: dict[str, Any]) -> dict[str, list[str]]:
    if not isinstance(memory_base, dict):
        memory_base = {}

    episodic = _clean_lines(memory_base.get("episodic_memories"))
    semantic = _clean_lines(memory_base.get("semantic_memories"))
    procedural = _clean_lines(memory_base.get("procedural_memories"))

    if not episodic:
        episodic = _clean_lines(memory_base.get("shared_memories"))
    if not semantic:
        semantic = _clean_lines(memory_base.get("legacy_summary"))
    if not procedural:
        procedural = _clean_lines(memory_base.get("voice_notes")) + _clean_lines(memory_base.get("photo_notes"))

    episodic = list(dict.fromkeys(episodic))
    semantic = list(dict.fromkeys(semantic))
    procedural = list(dict.fromkeys(procedural))
    return {
        "episodic": episodic,
        "semantic": semantic,
        "procedural": procedural,
    }


def _collect_legacy_reunion_candidates(memory_base: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for key in (
        "chat_history_summary",
        "diary_notes",
        "letter_notes",
        "photo_notes",
        "voice_notes",
        "memory_fragments",
        "shared_memories",
        "legacy_summary",
    ):
        candidates.extend(_clean_lines(memory_base.get(key)))
    return list(dict.fromkeys(candidates))


def _topic_keywords(text: str) -> set[str]:
    tokens = set(_split_keywords(text))
    for hint in RECALL_HINTS + GRIEF_HINTS + COMFORT_HINTS:
        if hint in _normalize_text(text):
            tokens.add(hint)
    return tokens


def _has_high_distress(text: str, emotional_state: str) -> bool:
    normalized = _normalize_text(text)
    if any(hint in normalized for hint in DISTRESS_HINTS):
        return True
    if emotional_state == "怀念 / 失落" and any(hint in normalized for hint in ("撑不住", "崩溃", "绝望", "想消失")):
        return True
    return False


def _history_topic_stability(history: list[dict[str, str]], user_message: str) -> tuple[int, int]:
    recent_texts = [
        _normalize_text(message.get("content"))
        for message in history[-4:]
        if _normalize_text(message.get("content"))
    ]
    if not recent_texts:
        return 0, 0

    current_tokens = _topic_keywords(user_message)
    if not current_tokens:
        current_tokens = set(_split_keywords(user_message))

    overlap_count = 0
    repeated_count = 0
    for text in recent_texts:
        tokens = _topic_keywords(text)
        if current_tokens & tokens:
            overlap_count += 1
        if any(keyword in text for keyword in RECALL_HINTS + GRIEF_HINTS + COMFORT_HINTS):
            repeated_count += 1
    return overlap_count, repeated_count


def _memory_volume(memory_base: dict[str, Any]) -> int:
    layered = _collect_layered_memories(memory_base)
    return sum(len(layered.get(layer, [])) for layer in LAYER_ORDER)


def progressive_recall_stage(
    memory_base: dict[str, Any],
    emotional_state: str,
    user_message: str,
    retrieval_policy: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
) -> str:
    retrieval_policy = retrieval_policy or {}
    history = history or []
    normalized_message = _normalize_text(user_message)
    if _has_high_distress(normalized_message, emotional_state):
        return "light"

    volume = _memory_volume(memory_base)
    guided_fields = _guided_answer_lines((memory_base or {}).get("guided_memory_answers"))
    topic_overlap, repeated_count = _history_topic_stability(history, normalized_message)
    history_depth = len([message for message in history[-4:] if _normalize_text(message.get("content"))])
    explicit_recall = any(hint in normalized_message for hint in RECALL_HINTS)
    explicit_memory = any(hint in normalized_message for hint in GRIEF_HINTS)

    if emotional_state == "怀念 / 失落":
        if (
            history_depth <= 2
            and topic_overlap <= 0
            and repeated_count <= 0
            and len(guided_fields) <= 1
        ):
            return "light"
        if volume >= 8 and (
            explicit_recall
            or explicit_memory
            or repeated_count >= 2
            or len(guided_fields) >= 3
            or history_depth >= 4
        ):
            return "deep"
        if topic_overlap >= 1 or repeated_count >= 1 or len(guided_fields) >= 2:
            return "medium"
        return "medium"

    if emotional_state == "回忆 / 复盘":
        if volume >= 7 and history_depth >= 3 and (explicit_recall or topic_overlap >= 2):
            return "deep"
        if topic_overlap >= 1 or repeated_count >= 1 or len(guided_fields) >= 2:
            return "medium"
        return "light"

    if emotional_state == "需要安抚":
        if volume >= 6 and history_depth >= 3 and repeated_count >= 1:
            return "medium"
        return "light"

    if history_depth >= 4 and (topic_overlap >= 2 or repeated_count >= 2):
        return "medium"
    if volume >= 8 and (explicit_recall or len(guided_fields) >= 3):
        return "deep"
    return "light"


def select_reunion_memory_layers(stage: str, emotional_state: str) -> tuple[str, ...]:
    stage = _normalize_text(stage) or "light"
    if stage == "light":
        if emotional_state == "怀念 / 失落":
            return ("procedural", "semantic", "episodic")
        return ("procedural", "semantic")
    if stage == "medium":
        if emotional_state == "需要安抚":
            return ("procedural", "episodic", "semantic")
        if emotional_state == "回忆 / 复盘":
            return ("episodic", "semantic", "procedural")
        return ("episodic", "procedural", "semantic")
    return ("episodic", "semantic", "procedural")


def _layer_stage_bonus(layer: str, stage: str) -> int:
    stage = _normalize_text(stage) or "light"
    stage_weights = {
        "light": {"procedural": 4, "semantic": 3, "episodic": 1},
        "medium": {"episodic": 4, "procedural": 3, "semantic": 3},
        "deep": {"episodic": 5, "semantic": 4, "procedural": 3},
    }
    return stage_weights.get(stage, stage_weights["light"]).get(layer, 0)


def rank_reunion_memories_by_stage(
    memory_base: dict[str, Any],
    emotional_state: str,
    user_message: str,
    retrieval_policy: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
    stage: str | None = None,
) -> list[str]:
    retrieval_policy = retrieval_policy or {}
    history = history or []
    layered = _collect_layered_memories(memory_base)
    recall_stage = _normalize_text(stage or retrieval_policy.get("recall_stage")) or progressive_recall_stage(
        memory_base,
        emotional_state,
        user_message,
        retrieval_policy,
        history,
    )
    ordered_layers = select_reunion_memory_layers(recall_stage, emotional_state)
    candidates: list[tuple[str, str]] = []
    for layer_name in ordered_layers:
        for item in layered.get(layer_name, []):
            candidates.append((layer_name, item))

    candidates.extend(("semantic", item) for item in _collect_legacy_reunion_candidates(memory_base))
    if not candidates:
        return []

    recent_context = " ".join(
        _normalize_text(message.get("content"))
        for message in history[-4:]
        if _normalize_text(message.get("content"))
    )

    scored = [
        _score_item(item, emotional_state, user_message, recent_context, layer, retrieval_policy, recall_stage)
        for layer, item in candidates
    ]
    scored.sort()
    max_items = int(retrieval_policy.get("max_memory_items") or 4)
    if recall_stage == "light":
        max_items = min(max_items, 2)
    elif recall_stage == "medium":
        max_items = min(max_items, 3)
    else:
        max_items = min(max_items, 4)
    max_items = max(1, min(max_items, 5))
    selected = [item for _, _, item in scored[:max_items] if item]
    return list(dict.fromkeys(selected))


def _detect_layer_from_item(item: str) -> str:
    text = _normalize_text(item)
    if not text:
        return "semantic"

    episodic_hints = (
        "那天",
        "那次",
        "当时",
        "以前",
        "曾经",
        "一起",
        "见面",
        "门口",
        "回家",
        "过年",
        "生日",
        "散步",
        "记得",
        "重逢",
        "再见",
        "告别",
        "纪念",
        "照片",
        "截图",
    )
    semantic_hints = (
        "一直",
        "总是",
        "觉得",
        "看法",
        "提醒",
        "希望",
        "重要",
        "习惯",
        "价值",
        "长期",
        "稳定",
        "关系",
        "对你",
    )
    procedural_hints = (
        "怎么叫",
        "称呼",
        "口头禅",
        "安慰",
        "照顾",
        "关心",
        "提醒",
        "叮嘱",
        "语气",
        "节奏",
        "表达",
        "先别急",
        "慢慢来",
    )

    scores = {
        "episodic": 0,
        "semantic": 0,
        "procedural": 0,
    }
    if any(hint in text for hint in episodic_hints):
        scores["episodic"] += 3
    if any(hint in text for hint in semantic_hints):
        scores["semantic"] += 3
    if any(hint in text for hint in procedural_hints):
        scores["procedural"] += 3

    if "以前" in text or "那时" in text or "一起" in text or "门口" in text:
        scores["episodic"] += 1
    if "总是" in text or "一直" in text or "觉得" in text:
        scores["semantic"] += 1
    if "先别急" in text or "慢慢来" in text or "注意休息" in text:
        scores["procedural"] += 1

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return ranked[0][0]


def detect_reunion_emotional_state(user_message: str, history: list[dict[str, str]]) -> str:
    text = " ".join(
        [
            _normalize_text(user_message),
            " ".join(
                _normalize_text(message.get("content"))
                for message in history[-4:]
                if _normalize_text(message.get("content"))
            ),
        ]
    )

    if any(hint in text for hint in GRIEF_HINTS):
        return "怀念 / 失落"
    if any(hint in text for hint in RECALL_HINTS):
        return "回忆 / 复盘"
    if any(hint in text for hint in COMFORT_HINTS):
        return "需要安抚"
    return "日常回顾"


def _score_item(
    item: str,
    emotional_state: str,
    user_message: str,
    recent_context: str,
    layer: str,
    retrieval_policy: dict[str, Any],
    recall_stage: str = "",
) -> tuple[int, int, str]:
    text = _normalize_text(item)
    score = 0
    query = _normalize_text(user_message)
    context = _normalize_text(recent_context)
    tokens = _split_keywords(query)

    emotional_keywords = {
        "怀念 / 失落": GRIEF_HINTS,
        "回忆 / 复盘": RECALL_HINTS,
        "需要安抚": COMFORT_HINTS,
        "日常回顾": (),
    }.get(emotional_state, ())

    if any(keyword in text for keyword in emotional_keywords):
        score += int(3 * float(retrieval_policy.get("emotion_weight", 0.35) or 0.35))
    if any(token in text for token in tokens):
        score += int(2 * float(retrieval_policy.get("topic_weight", 0.35) or 0.35)) + 1
    if any(keyword in context for keyword in _split_keywords(text)):
        score += 2

    layer_weights = {
        "episodic": 3,
        "semantic": 2,
        "procedural": 2,
    }
    if emotional_state == "怀念 / 失落":
        layer_weights.update({"procedural": 4, "episodic": 3, "semantic": 1})
    elif emotional_state == "回忆 / 复盘":
        layer_weights.update({"episodic": 4, "semantic": 3, "procedural": 1})
    elif emotional_state == "需要安抚":
        layer_weights.update({"procedural": 4, "semantic": 2, "episodic": 2})
    if recall_stage == "light":
        layer_weights.update({"procedural": 5, "semantic": 3, "episodic": 1})
    elif recall_stage == "medium":
        layer_weights.update({"episodic": 4, "procedural": 3, "semantic": 3})
    elif recall_stage == "deep":
        layer_weights.update({"episodic": 5, "semantic": 4, "procedural": 3})
    score += int(layer_weights.get(layer, 2) * float(retrieval_policy.get("layer_weight", 0.2) or 0.2) * 5)
    stage_bonus = _layer_stage_bonus(layer, recall_stage)
    score += stage_bonus

    if len(text) <= 24:
        score += 1
    if layer == "procedural" and any(keyword in text for keyword in ("先别急", "慢慢来", "注意休息", "我在")):
        score += 2
    if layer == "episodic" and any(keyword in text for keyword in ("以前", "当时", "那天", "一起")):
        score += 2
    if layer == "semantic" and any(keyword in text for keyword in ("一直", "总是", "觉得", "提醒")):
        score += 2
    return (-score, len(text), text)


def retrieve_ranked_reunion_memories(
    memory_base: dict[str, Any],
    emotional_state: str,
    user_message: str,
    retrieval_policy: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
) -> list[str]:
    retrieval_policy = retrieval_policy or {}
    history = history or []
    return rank_reunion_memories_by_stage(
        memory_base,
        emotional_state,
        user_message,
        retrieval_policy,
        history,
    )


def retrieve_relevant_memories(
    memory_base: dict[str, Any],
    emotional_state: str,
    user_message: str,
    retrieval_policy: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
) -> list[str]:
    return retrieve_ranked_reunion_memories(memory_base, emotional_state, user_message, retrieval_policy, history)


def build_reunion_reply_context(
    persona_profile: dict[str, Any],
    memory_base: dict[str, Any],
    retrieval_policy: dict[str, Any],
    safety_guardrails: dict[str, Any],
    emotional_state: str,
    memories: list[str],
    user_message: str,
    tone_rules: dict[str, Any] | None = None,
) -> str:
    tone = _normalize_text(persona_profile.get("tone"))
    remembrance_style = _normalize_text(persona_profile.get("remembrance_style"))
    comfort_style = _normalize_text(persona_profile.get("comfort_style"))
    boundaries = _normalize_text(persona_profile.get("boundaries"))
    name = _normalize_text(persona_profile.get("name"))
    relationship_type = _normalize_text(persona_profile.get("relationship_type"))
    retrieval_mode = _normalize_text(retrieval_policy.get("mode"))
    progressive_recall = bool(retrieval_policy.get("progressive_recall", True))
    priority_rules = _clean_lines(retrieval_policy.get("priority_rules"))
    fallback_rules = _clean_lines(retrieval_policy.get("fallback_rules"))
    max_memory_items = int(retrieval_policy.get("max_memory_items") or 4)
    recall_stage = _normalize_text(retrieval_policy.get("recall_stage")) or "light"
    emotion_weight = retrieval_policy.get("emotion_weight", 0.35)
    topic_weight = retrieval_policy.get("topic_weight", 0.35)
    layer_weight = retrieval_policy.get("layer_weight", 0.2)
    safety_weight = retrieval_policy.get("safety_weight", 0.1)
    protection_notes = _clean_lines(safety_guardrails.get("emotional_protection"))
    avoid_triggers = _clean_lines(safety_guardrails.get("avoid_triggers"))
    history_summary = _normalize_text(memory_base.get("chat_history_summary"))
    episodic_count = len(_clean_lines(memory_base.get("episodic_memories")))
    semantic_count = len(_clean_lines(memory_base.get("semantic_memories")))
    procedural_count = len(_clean_lines(memory_base.get("procedural_memories")))
    safety_notes = []
    if bool(safety_guardrails.get("avoid_dependency_language", True)):
        safety_notes.append("避免强化依赖感")
    if bool(safety_guardrails.get("avoid_claiming_certainty", True)):
        safety_notes.append("避免把未确认内容说成确定事实")
    if bool(safety_guardrails.get("avoid_afterlife_claims", True)):
        safety_notes.append("不做超自然或来世类宣称")
    if bool(safety_guardrails.get("de_escalate_distress", True)):
        safety_notes.append("高 distress 时先降温、再安抚")

    temperature_map = {
        "怀念 / 失落": "克制、温柔、允许慢慢回忆",
        "回忆 / 复盘": "平稳、清楚、顺着往前讲",
        "需要安抚": "先稳住情绪，再慢慢说",
        "日常回顾": "轻一点、慢一点、保留记忆感",
    }
    temperature = temperature_map.get(emotional_state, "轻一点、慢一点、保留记忆感")

    parts = [
        f"当前情绪状态：{emotional_state}",
        f"建议回应温度：{temperature}",
        f"回忆档位：{recall_stage}",
    ]
    if relationship_type or name:
        parts.append(f"重逢身份：{relationship_type or name}")
    if tone:
        parts.append(f"说话风格：{tone}")
    if remembrance_style:
        parts.append(f"回忆方式：{remembrance_style}")
    if comfort_style:
        parts.append(f"安抚方式：{comfort_style}")
    if retrieval_mode:
        parts.append(f"记忆检索模式：{retrieval_mode}")
    parts.append(f"是否渐进式回忆：{'是' if progressive_recall else '否'}")
    parts.append(f"召回上限：{max_memory_items}")
    parts.append(f"层级数量：E{episodic_count} / S{semantic_count} / P{procedural_count}")
    parts.append(
        "检索权重："
        f"情绪 {emotion_weight} / 话题 {topic_weight} / 层级 {layer_weight} / 护栏 {safety_weight}"
    )
    if history_summary:
        parts.append(f"聊天记录摘要：{history_summary}")
    if priority_rules:
        parts.append("优先规则：")
        parts.extend(f"- {item}" for item in priority_rules[:4])
    if memories:
        parts.append("可调用回忆：")
        parts.extend(f"- {item}" for item in memories[:max_memory_items])
    if tone_rules:
        for key, value in tone_rules.items():
            if not value:
                continue
            if isinstance(value, list):
                parts.append(f"{key}：")
                parts.extend(f"- {item}" for item in value[:4])
            else:
                parts.append(f"{key}：{value}")
    if fallback_rules:
        parts.append("降级规则：")
        parts.extend(f"- {item}" for item in fallback_rules[:3])
    if protection_notes:
        parts.append("心理护栏：")
        parts.extend(f"- {item}" for item in protection_notes[:3])
    if safety_notes:
        parts.append("护栏状态：")
        parts.extend(f"- {item}" for item in safety_notes[:4])
    if any(keyword in _normalize_text(user_message) for keyword in CERTAINTY_HINTS):
        parts.append("表达提醒：不要把未确认的想法说成确定事实")
    if any(keyword in _normalize_text(user_message) for keyword in DEPENDENCY_HINTS):
        parts.append("表达提醒：不要强化依赖感或占据现实关系位置")
    if any(keyword in _normalize_text(user_message) for keyword in SUPERNATURAL_HINTS):
        parts.append("表达提醒：不要做超自然或来世类宣称")
    if avoid_triggers:
        parts.append("应避免触发：")
        parts.extend(f"- {item}" for item in avoid_triggers[:3])
    if boundaries:
        parts.append(f"边界提醒：{boundaries}")
    parts.append(f"当前用户消息：{_normalize_text(user_message)}")
    return "\n".join(parts).strip()


def build_reunion_tone_rules(
    stage: str,
    emotional_state: str,
    safety_guardrails: dict[str, Any],
) -> dict[str, list[str]]:
    stage = _normalize_text(stage) or "light"
    emotional_state = _normalize_text(emotional_state) or "日常回顾"
    protection_notes = _clean_lines(safety_guardrails.get("emotional_protection")) if isinstance(safety_guardrails, dict) else []
    avoid_triggers = _clean_lines(safety_guardrails.get("avoid_triggers")) if isinstance(safety_guardrails, dict) else []
    tone_map = {
        "light": [
            "先接住当前情绪，再轻轻带到记忆边缘",
            "只放一小段记忆，不展开太多背景",
            "语气低饱和，像轻轻碰到回忆",
        ],
        "medium": [
            "围绕当前主题逐步召回一两条相关记忆",
            "先说清当下，再补一点过去",
            "保持克制，不把回忆一下子铺满",
        ],
        "deep": [
            "允许更完整地回到共同经历，但仍要控制数量",
            "把记忆说得更清楚一些，但不抢叙事",
            "保留温度，避免把重逢说成情绪洪水",
        ],
    }
    return {
        "回忆档位提示": tone_map.get(stage, tone_map["light"]),
        "情绪校准": [
            f"当前情绪：{emotional_state}",
            "优先安稳，再轻量回忆",
        ],
        "护栏提醒": protection_notes[:3] or ["先接住情绪，再慢慢回忆"],
        "避免项": avoid_triggers[:3] or ["不强化依赖", "不做确定性代言", "不做超自然宣称"],
    }


def build_reunion_guarded_reply_context(
    persona_profile: dict[str, Any],
    memory_base: dict[str, Any],
    retrieval_policy: dict[str, Any],
    safety_guardrails: dict[str, Any],
    emotional_state: str,
    memories: list[str],
    user_message: str,
) -> str:
    stage = _normalize_text(retrieval_policy.get("recall_stage")) or "light"
    tone_rules = build_reunion_tone_rules(stage, emotional_state, safety_guardrails)
    return build_reunion_reply_context(
        persona_profile,
        memory_base,
        retrieval_policy,
        safety_guardrails,
        emotional_state,
        memories,
        user_message,
        tone_rules=tone_rules,
    )


def build_reunion_persona_context(
    persona: dict[str, Any],
    history: list[dict[str, str]],
    user_message: str,
) -> str:
    persona_profile = persona.get("reunion_persona_profile") or {}
    memory_base = persona.get("reunion_memory_base") or {}
    retrieval_policy = persona.get("reunion_memory_retrieval_policy") or {}
    safety_guardrails = persona.get("reunion_safety_guardrails") or {}
    if not isinstance(persona_profile, dict) or not isinstance(memory_base, dict):
        return ""

    emotional_state = detect_reunion_emotional_state(user_message, history)
    recall_stage = progressive_recall_stage(memory_base, emotional_state, user_message, retrieval_policy, history)
    staged_policy = {**retrieval_policy, "recall_stage": recall_stage}
    memories = retrieve_ranked_reunion_memories(memory_base, emotional_state, user_message, staged_policy, history)
    return build_reunion_guarded_reply_context(
        persona_profile,
        memory_base,
        staged_policy if isinstance(staged_policy, dict) else {},
        safety_guardrails if isinstance(safety_guardrails, dict) else {},
        emotional_state,
        memories,
        user_message,
    )
