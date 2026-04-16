from __future__ import annotations

import re
from typing import Any


GRIEF_HINTS = ("想念", "难过", "失落", "怀念", "告别", "离开", "难舍", "遗憾", "空落")
RECALL_HINTS = ("记得", "回忆", "以前", "那时候", "过去", "从前", "曾经", "重逢", "再见")
COMFORT_HINTS = ("怎么办", "难受", "想哭", "睡不着", "撑不住", "压力", "害怕")
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
    score += int(layer_weights.get(layer, 2) * float(retrieval_policy.get("layer_weight", 0.2) or 0.2) * 5)

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
    layered = _collect_layered_memories(memory_base)
    candidates: list[tuple[str, str]] = []
    for layer_name in LAYER_ORDER:
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
        _score_item(item, emotional_state, user_message, recent_context, layer, retrieval_policy)
        for layer, item in candidates
    ]
    scored.sort()
    max_items = int(retrieval_policy.get("max_memory_items") or 4)
    max_items = max(2, min(max_items, 5))
    selected = [item for _, _, item in scored[:max_items] if item]
    return list(dict.fromkeys(selected))


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
    if fallback_rules:
        parts.append("降级规则：")
        parts.extend(f"- {item}" for item in fallback_rules[:3])
    if protection_notes:
        parts.append("心理护栏：")
        parts.extend(f"- {item}" for item in protection_notes[:3])
    if safety_notes:
        parts.append("护栏状态：")
        parts.extend(f"- {item}" for item in safety_notes[:4])
    if avoid_triggers:
        parts.append("应避免触发：")
        parts.extend(f"- {item}" for item in avoid_triggers[:3])
    if boundaries:
        parts.append(f"边界提醒：{boundaries}")
    parts.append(f"当前用户消息：{_normalize_text(user_message)}")
    return "\n".join(parts).strip()


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
    memories = retrieve_ranked_reunion_memories(memory_base, emotional_state, user_message, retrieval_policy, history)
    return build_reunion_reply_context(
        persona_profile,
        memory_base,
        retrieval_policy if isinstance(retrieval_policy, dict) else {},
        safety_guardrails if isinstance(safety_guardrails, dict) else {},
        emotional_state,
        memories,
        user_message,
    )
