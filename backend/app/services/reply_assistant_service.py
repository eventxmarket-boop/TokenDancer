from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.services.intimate_companion_service import detect_emotional_state
from app.services.llm_gateway import LLMGatewayError, generate_reply
from app.services.ocr_service import summarize_ocr_results
from app.services.text_sanitizer import strip_think_blocks


TARGET_PERSON_TYPES = {
    "crush": "暧昧 / crush",
    "partner": "伴侣",
    "ex": "前任",
    "colleague": "同事",
    "boss": "上司 / 领导",
    "client": "客户 / 对接方",
    "public_sector": "体制内 / 公务沟通",
    "mentor": "导师 / 前辈",
    "friend": "朋友",
    "family": "家人",
}

UNDERSTANDING_HINTS = (
    "什么意思",
    "怎么理解",
    "怎么想",
    "为什么",
    "雷区",
    "信号",
    "语气",
    "表达",
    "意图",
    "翻译",
    "看懂",
    "这句",
)

MAINTENANCE_HINTS = (
    "关系",
    "维护",
    "修复",
    "稳定",
    "长期",
    "安抚",
    "陪伴",
    "冲突",
    "修补",
    "相处",
    "日常",
    "继续",
)

MESSAGE_PUSH_HINTS = (
    "怎么回",
    "要不要发",
    "发出去",
    "发送前",
    "先练一遍",
    "推进",
    "表白",
    "约见",
    "破冰",
    "关键节点",
    "候选回复",
    "预演",
    "回复",
)

CRUSH_HINTS = ("暧昧", "crush", "喜欢", "表白", "约会", "约见", "追", "先发")
PARTNER_HINTS = ("伴侣", "男友", "女友", "老公", "老婆", "对象", "磨合")
EX_HINTS = ("前任", "复合", "分手", "过去关系", "旧情", "旧爱")
COLLEAGUE_HINTS = ("同事", "合作", "工作", "对接", "项目", "会议", "汇报")
BOSS_HINTS = ("上司", "领导", "老板", "汇报", "审批", "安排", "加班")
CLIENT_HINTS = ("客户", "甲方", "乙方", "对接", "合同", "需求", "报价", "交付")
FRIEND_HINTS = ("朋友", "同学", "闺蜜", "兄弟", "聚会", "聊天")
FAMILY_HINTS = ("家人", "妈妈", "爸爸", "父母", "家里", "亲戚")
PUBLIC_SECTOR_HINTS = ("体制内", "公务", "公文", "机关", "审批", "流程", "领导批示")
MENTOR_HINTS = ("导师", "前辈", "老师", "师兄", "师姐", "带教", "请教")

SCENE_TYPES = {
    "daily": "日常聊天",
    "conflict": "冷战 / 冲突",
    "push_forward": "推进关系",
    "work_report": "工作汇报",
    "follow_up": "跟进未回复",
    "formal_notice": "正式通知",
    "rejection": "拒绝 / 婉拒",
    "repair": "解释误会 / 修复",
}


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _clean_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


def _merge_unique_lines(*values: Any) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _clean_lines(value):
            if item and item not in seen:
                merged.append(item)
                seen.add(item)
    return merged


def _collect_text_pool(*values: Any) -> str:
    return " ".join(part for part in (_normalize_text(value) for value in values) if part)


def _infer_target_person_type(*values: Any) -> str:
    text = _collect_text_pool(*values)
    lower_text = text.lower()
    if any(keyword in lower_text for keyword in PUBLIC_SECTOR_HINTS):
        return "public_sector"
    if any(keyword in lower_text for keyword in MENTOR_HINTS):
        return "mentor"
    if any(keyword in lower_text for keyword in CRUSH_HINTS):
        return "crush"
    if any(keyword in lower_text for keyword in PARTNER_HINTS):
        return "partner"
    if any(keyword in lower_text for keyword in EX_HINTS):
        return "ex"
    if any(keyword in lower_text for keyword in BOSS_HINTS):
        return "boss"
    if any(keyword in lower_text for keyword in CLIENT_HINTS):
        return "client"
    if any(keyword in lower_text for keyword in COLLEAGUE_HINTS):
        return "colleague"
    if any(keyword in lower_text for keyword in FAMILY_HINTS):
        return "family"
    if any(keyword in lower_text for keyword in FRIEND_HINTS):
        return "friend"
    return "friend"


def _build_target_person_label(target_person_type: str) -> str:
    return TARGET_PERSON_TYPES.get(_normalize_text(target_person_type), _normalize_text(target_person_type) or "朋友")


def _build_scene_label(scene_type: str) -> str:
    scene = _normalize_text(scene_type)
    return SCENE_TYPES.get(scene, scene or "日常聊天")


def _infer_scene_type(*values: Any) -> str:
    text = _collect_text_pool(*values).lower()
    if any(keyword in text for keyword in ("冷战", "吵架", "误会", "道歉", "修复", "解释")):
        return "repair"
    if any(keyword in text for keyword in ("推进", "表白", "约见", "约会", "继续聊", "更进一步")):
        return "push_forward"
    if any(keyword in text for keyword in ("汇报", "方案", "进度", "结果", "审批", "请示")):
        return "work_report"
    if any(keyword in text for keyword in ("跟进", "未回复", "催", "什么时候", "进展")):
        return "follow_up"
    if any(keyword in text for keyword in ("通知", "告知", "正式", "邮件", "函", "公告")):
        return "formal_notice"
    if any(keyword in text for keyword in ("拒绝", "婉拒", "不方便", "不了", "算了")):
        return "rejection"
    if any(keyword in text for keyword in ("冲突", "吵架", "矛盾", "拉黑", "冷处理")):
        return "conflict"
    return "daily"


def _infer_current_tone(*values: Any) -> str:
    text = _collect_text_pool(*values).lower()
    if any(keyword in text for keyword in ("正式", "邮件", "汇报", "通知", "公文")):
        return "formal"
    if any(keyword in text for keyword in ("推进", "主动", "约见", "表白")):
        return "forward"
    if any(keyword in text for keyword in ("克制", "边界", "婉拒", "不要太")):
        return "guarded"
    if any(keyword in text for keyword in ("体贴", "安抚", "陪伴", "温柔")):
        return "gentle"
    return "balanced"


def _is_work_person(target_person_type: str) -> bool:
    return _normalize_text(target_person_type) in {"colleague", "boss", "client", "public_sector", "mentor"}


def _build_tone_tags(target_person_type: str, scene_type: str, target_goal: str) -> list[str]:
    tags: list[str] = []
    if _is_work_person(target_person_type) or scene_type in {"work_report", "follow_up", "formal_notice"}:
        tags.extend(["职业化", "简明", "有边界"])
        if _normalize_text(target_person_type) in {"boss", "public_sector", "mentor"}:
            tags.append("正式")
    else:
        tags.extend(["自然", "体面"])
        if _normalize_text(target_person_type) in {"crush", "partner", "ex"}:
            tags.append("关系感")
    if any(keyword in _normalize_text(target_goal) for keyword in ("推进", "更进一步", "主动")):
        tags.append("推进")
    if any(keyword in _normalize_text(target_goal) for keyword in ("克制", "别太明显", "边界")):
        tags.append("克制")
    if any(keyword in _normalize_text(target_goal) for keyword in ("礼貌", "正式", "体面")):
        tags.append("礼貌")
    if not tags:
        tags = ["平衡"]
    return _merge_unique_lines(tags)


def _build_understanding_result(
    *,
    target_person_type: str,
    scene_type: str,
    message: str,
    current_context: str,
    relationship_status: str,
    target_goal: str,
    tone_hint: str,
    raw_materials: dict[str, Any],
) -> dict[str, Any]:
    text = _collect_text_pool(message, current_context, relationship_status, target_goal, tone_hint)
    lower_text = text.lower()
    emotional_state = detect_emotional_state(message, [{"role": "user", "content": current_context}])
    meaning_guess = "对方在表达一个需要你接住或继续回应的信号。"
    if _normalize_text(target_person_type) in {"boss", "public_sector", "colleague", "client", "mentor"}:
        meaning_guess = "这更像工作或正式沟通中的信息确认、进度跟进或态度试探。"
    elif _normalize_text(target_person_type) in {"crush", "partner", "ex"}:
        meaning_guess = "这句更像关系推进、确认态度，或者在试探你的回应节奏。"

    if scene_type == "work_report":
        meaning_guess = "对方更关心结果、进度、责任分工或下一步安排。"
    elif scene_type == "follow_up":
        meaning_guess = "对方在催进度或想确认你是否已经处理。"
    elif scene_type == "formal_notice":
        meaning_guess = "对方在做正式告知，需要你用更稳更清楚的方式接住。"
    elif scene_type == "rejection":
        meaning_guess = "这句大概率是在回避推进，或者在体面地收住边界。"
    elif scene_type == "repair":
        meaning_guess = "对方可能在解释误会、缓和情绪，或者尝试把关系拉回可沟通状态。"

    intent_guess = "先把信息接住，再决定是回应情绪、回应事实，还是推进下一步。"
    if any(keyword in lower_text for keyword in ("催", "跟进", "进度")):
        intent_guess = "对方主要想确认进度和你的态度。"
    elif any(keyword in lower_text for keyword in ("约", "见面", "推进", "表白")):
        intent_guess = "对方在试探你是否愿意继续推进。"
    elif any(keyword in lower_text for keyword in ("正式", "通知", "邮件", "公文")):
        intent_guess = "对方希望得到正式、克制、低歧义的回应。"

    risk_flags = _merge_unique_lines(
        _build_risk_flags(target_person_type, infer_reply_assistant_focus(message, current_context, relationship_status, target_goal, tone_hint, target_person_type=target_person_type), target_goal, message),
    )
    if scene_type == "work_report" and any(keyword in lower_text for keyword in ("可能", "大概", "也许")):
        risk_flags.append("工作场景里不要把不确定说得太虚")
    if scene_type == "rejection" and any(keyword in lower_text for keyword in ("太长", "解释太多")):
        risk_flags.append("拒绝场景里避免过度解释")

    relationship_state_guess = _normalize_text(relationship_status) or ("关系状态待补充" if not current_context else "当前关系状态需要结合上下文判断")
    scene_guess = _build_scene_label(scene_type)

    return {
        "meaning_guess": meaning_guess,
        "emotion_guess": emotional_state or ("平静" if "?" not in message else "试探"),
        "intent_guess": intent_guess,
        "relationship_state_guess": relationship_state_guess,
        "scene_guess": scene_guess,
        "risk_flags": _merge_unique_lines(risk_flags)[:6],
    }


def _build_tone_profile(target_person_type: str, scene_type: str, target_goal: str, tone_hint: str) -> dict[str, Any]:
    tags = _build_tone_tags(target_person_type, scene_type, target_goal)
    if _is_work_person(target_person_type) or scene_type in {"work_report", "follow_up", "formal_notice"}:
        label = "职业化 / 正式"
        guidance = "优先简明、清楚、不过度承诺；对上级、客户和体制内沟通时保持正式与低情绪。"
    elif _normalize_text(target_person_type) in {"crush", "partner", "ex"}:
        label = "关系感 / 克制"
        guidance = "优先接住情绪和关系温度，同时保留边界，不要太油，也不要太硬。"
    else:
        label = "自然 / 体面"
        guidance = "优先自然、礼貌、可继续接话。"
    if _normalize_text(tone_hint):
        guidance = f"{guidance} 用户补充的语气偏好：{_normalize_text(tone_hint)}。"
    return {
        "label": label,
        "style_tags": tags,
        "guidance": guidance,
    }


def _build_reply_candidates_runtime(
    *,
    target_person_type: str,
    scene_type: str,
    target_goal: str,
    tone_hint: str,
) -> list[dict[str, Any]]:
    target_label = _build_target_person_label(target_person_type)
    scene_label = _build_scene_label(scene_type)
    goal = _normalize_text(target_goal) or "先把话接住。"
    tone_text = _normalize_text(tone_hint) or "自然、清楚"
    is_work = _is_work_person(target_person_type) or scene_type in {"work_report", "follow_up", "formal_notice"}
    candidates = [
        {
            "label": "更稳版",
            "text": f"{target_label}这条我先接住，{goal}；如果你愿意，我可以顺着这个方向继续帮你整理。",
            "style_tags": ["稳妥", "有边界"] if not is_work else ["职业化", "稳妥"],
            "reason": "先把信息接住，再给对方明确但不过度的回应。",
        },
        {
            "label": "更自然版",
            "text": f"我明白你的意思了，{scene_label}下可以先这样回：先回应对方，再把你的目标带进去。",
            "style_tags": ["自然", "顺口"] if not is_work else ["简明", "顺滑"],
            "reason": "保留日常交流感，适合即时发送。",
        },
        {
            "label": "更主动版",
            "text": f"可以顺着往前推进一步，重点是把你的意图讲清楚，同时保留{tone_text}的语气。",
            "style_tags": ["推进", "清楚"],
            "reason": "适合你希望把关系或事项往前推一点的时候。",
        },
        {
            "label": "更克制版",
            "text": f"先别把话说满，留一点回旋空间，等对方再接一句再决定下一步。",
            "style_tags": ["克制", "留余地"],
            "reason": "适合不想太快表态、先观察对方反应的时候。",
        },
    ]
    if is_work:
        candidates.append(
            {
                "label": "更正式版",
                "text": f"收到，我先按这个方向处理，后续我把进展整理后再同步你。",
                "style_tags": ["正式", "职业化"],
                "reason": "适合老板、客户、甲方或体制内沟通。",
            }
        )
    return candidates


def _build_predicted_replies_runtime(target_person_type: str, scene_type: str, message: str) -> list[dict[str, Any]]:
    target_label = _build_target_person_label(target_person_type)
    scene_label = _build_scene_label(scene_type)
    if _is_work_person(target_person_type) or scene_type in {"work_report", "follow_up", "formal_notice"}:
        return [
            {"label": "正面回应", "text": f"{target_label}可能会认可你的态度，并继续追问进展或下一步安排。", "risk_level": "低"},
            {"label": "模糊回应", "text": f"{target_label}可能会先说收到，但暂时不展开更多信息。", "risk_level": "中"},
            {"label": "防御回应", "text": f"{target_label}可能会觉得你还没说清楚，继续要求你补充细节。", "risk_level": "中"},
        ]
    if _normalize_text(target_person_type) in {"crush", "partner", "ex"}:
        return [
            {"label": "正面回应", "text": f"{target_label}可能会顺着你的话继续聊，甚至把关系或情绪往前带一点。", "risk_level": "低"},
            {"label": "模糊回应", "text": f"{target_label}可能会先观察你的语气，再决定要不要继续展开。", "risk_level": "中"},
            {"label": "冷处理", "text": f"{target_label}可能会短回或延后回复，先看你的节奏是不是太快。", "risk_level": "中"},
        ]
    return [
        {"label": "正面回应", "text": f"{target_label}大概率会继续接话，把当前{scene_label}推进下去。", "risk_level": "低"},
        {"label": "模糊回应", "text": f"{target_label}可能会先表达态度，但不立刻给完全结论。", "risk_level": "中"},
        {"label": "防御回应", "text": f"{target_label}可能会觉得信息还不够，先补一个问题或确认一下。", "risk_level": "中"},
    ]


def _build_fallback_reply_assistant_response(
    *,
    message: str,
    target_person_type: str,
    target_person_label: str,
    scene_type: str,
    current_context: str,
    target_goal: str,
    tone_hint: str,
    relationship_status: str,
    raw_materials: dict[str, Any],
) -> dict[str, Any]:
    understanding_result = _build_understanding_result(
        target_person_type=target_person_type,
        scene_type=scene_type,
        message=message,
        current_context=current_context,
        relationship_status=relationship_status,
        target_goal=target_goal,
        tone_hint=tone_hint,
        raw_materials=raw_materials,
    )
    tone_profile = _build_tone_profile(target_person_type, scene_type, target_goal, tone_hint)
    reply_candidates = _build_reply_candidates_runtime(
        target_person_type=target_person_type,
        scene_type=scene_type,
        target_goal=target_goal,
        tone_hint=tone_hint,
    )
    predicted_replies = _build_predicted_replies_runtime(target_person_type, scene_type, message)
    recommended_reply = reply_candidates[0]["text"] if reply_candidates else ""
    material_summary = _material_summary(raw_materials)
    context_summary = _collect_text_pool(current_context, relationship_status, target_goal, tone_hint)
    return {
        "mode": "reply_assistant",
        "target_person_type": _normalize_text(target_person_type) or "friend",
        "target_person_label": _normalize_text(target_person_label) or _build_target_person_label(target_person_type),
        "scene_type": _normalize_text(scene_type) or "daily",
        "scene_label": _build_scene_label(scene_type),
        "understanding_result": understanding_result,
        "reply_candidates": reply_candidates,
        "predicted_replies": predicted_replies,
        "risk_flags": understanding_result.get("risk_flags", []),
        "tone_profile": tone_profile,
        "recommended_reply": recommended_reply,
        "material_summary": material_summary,
        "context_summary": context_summary,
    }


def _extract_json_object(content: str) -> dict[str, Any] | None:
    text = strip_think_blocks(_normalize_text(content))
    if not text:
        return None
    if text.startswith("```"):
      text = text.strip("`")
      if text.lower().startswith("json"):
          text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _normalize_reply_assistant_response(payload: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    response = dict(fallback)
    if not isinstance(payload, dict):
        return response

    response["mode"] = _normalize_text(payload.get("mode")) or response["mode"]
    response["target_person_type"] = _normalize_text(payload.get("target_person_type")) or response["target_person_type"]
    response["target_person_label"] = _normalize_text(payload.get("target_person_label")) or response["target_person_label"]
    response["scene_type"] = _normalize_text(payload.get("scene_type")) or response["scene_type"]
    response["scene_label"] = _normalize_text(payload.get("scene_label")) or response["scene_label"]
    response["recommended_reply"] = _normalize_text(payload.get("recommended_reply")) or response["recommended_reply"]
    response["material_summary"] = _normalize_text(payload.get("material_summary")) or response["material_summary"]
    response["context_summary"] = _normalize_text(payload.get("context_summary")) or response["context_summary"]

    understanding_result = payload.get("understanding_result")
    if isinstance(understanding_result, dict):
        response["understanding_result"] = {
            "meaning_guess": _normalize_text(understanding_result.get("meaning_guess")) or response["understanding_result"]["meaning_guess"],
            "emotion_guess": _normalize_text(understanding_result.get("emotion_guess")) or response["understanding_result"]["emotion_guess"],
            "intent_guess": _normalize_text(understanding_result.get("intent_guess")) or response["understanding_result"]["intent_guess"],
            "relationship_state_guess": _normalize_text(understanding_result.get("relationship_state_guess")) or response["understanding_result"]["relationship_state_guess"],
            "scene_guess": _normalize_text(understanding_result.get("scene_guess")) or response["understanding_result"]["scene_guess"],
            "risk_flags": _merge_unique_lines(understanding_result.get("risk_flags"), response["understanding_result"].get("risk_flags")),
        }

    reply_candidates = payload.get("reply_candidates")
    if isinstance(reply_candidates, list) and reply_candidates:
        normalized_candidates: list[dict[str, Any]] = []
        for item in reply_candidates:
            if not isinstance(item, dict):
                continue
            normalized_candidates.append(
                {
                    "label": _normalize_text(item.get("label")),
                    "text": _normalize_text(item.get("text")),
                    "style_tags": _merge_unique_lines(item.get("style_tags")),
                    "reason": _normalize_text(item.get("reason")),
                }
            )
        if normalized_candidates:
            response["reply_candidates"] = normalized_candidates

    predicted_replies = payload.get("predicted_replies")
    if isinstance(predicted_replies, list) and predicted_replies:
        normalized_predicted: list[dict[str, Any]] = []
        for item in predicted_replies:
            if not isinstance(item, dict):
                continue
            normalized_predicted.append(
                {
                    "label": _normalize_text(item.get("label")),
                    "text": _normalize_text(item.get("text")),
                    "risk_level": _normalize_text(item.get("risk_level")),
                }
            )
        if normalized_predicted:
            response["predicted_replies"] = normalized_predicted

    risk_flags = payload.get("risk_flags")
    if isinstance(risk_flags, list):
        response["risk_flags"] = _merge_unique_lines(risk_flags, response["risk_flags"])

    tone_profile = payload.get("tone_profile")
    if isinstance(tone_profile, dict):
        response["tone_profile"] = {
            "label": _normalize_text(tone_profile.get("label")) or response["tone_profile"]["label"],
            "style_tags": _merge_unique_lines(tone_profile.get("style_tags")) or response["tone_profile"]["style_tags"],
            "guidance": _normalize_text(tone_profile.get("guidance")) or response["tone_profile"]["guidance"],
        }

    return response


async def generate_reply_assistant_runtime(
    request: dict[str, Any],
    db: Session | None = None,
) -> dict[str, Any]:
    message = _normalize_text(request.get("message"))
    if not message:
        raise ValueError("message 不能为空")

    target_person_type = _normalize_text(request.get("target_person_type")) or "friend"
    target_person_label = _normalize_text(request.get("target_person_label")) or _build_target_person_label(target_person_type)
    scene_type = _normalize_text(request.get("scene_type")) or _infer_scene_type(
        message,
        request.get("current_context"),
        request.get("target_goal"),
        request.get("relationship_status"),
        request.get("conversation_context"),
    )
    current_context = _normalize_text(request.get("current_context"))
    target_goal = _normalize_text(request.get("target_goal"))
    tone_hint = _normalize_text(request.get("tone_hint"))
    relationship_status = _normalize_text(request.get("relationship_status"))
    conversation_context = _normalize_text(request.get("conversation_context"))
    raw_materials = request.get("raw_materials") if isinstance(request.get("raw_materials"), dict) else {}

    fallback = _build_fallback_reply_assistant_response(
        message=message,
        target_person_type=target_person_type,
        target_person_label=target_person_label,
        scene_type=scene_type,
        current_context=current_context,
        target_goal=target_goal,
        tone_hint=tone_hint,
        relationship_status=relationship_status,
        raw_materials=raw_materials,
    )

    if db is None:
        return fallback

    system_prompt = (
        "你是 Tokendancer 的直用型回复助手“我该怎么回”。"
        "你的任务是：用户直接贴一句话或一段聊天，你要给出理解、回复候选、风险提示和下一句预测。"
        "只输出严格 JSON 对象，不要输出 markdown，不要输出代码块，不要输出解释性前言。"
        "JSON 必须包含 mode、target_person_type、target_person_label、scene_type、scene_label、understanding_result、reply_candidates、predicted_replies、risk_flags、tone_profile、recommended_reply、material_summary、context_summary。"
        "understanding_result 必须包含 meaning_guess、emotion_guess、intent_guess、relationship_state_guess、scene_guess、risk_flags。"
        "reply_candidates 必须是对象数组，每项至少包含 label、text、style_tags、reason。"
        "predicted_replies 必须是对象数组，每项至少包含 label、text、risk_level。"
        "tone_profile 必须包含 label、style_tags、guidance。"
        "工作沟通场景要更正式、简明、可执行，不要过度承诺。"
        "亲密关系场景要更自然、体面、保留边界，不要太油。"
    )

    user_prompt = json.dumps(
        {
            "message": message,
            "target_person_type": target_person_type,
            "target_person_label": target_person_label,
            "scene_type": scene_type,
            "scene_label": _build_scene_label(scene_type),
            "current_context": current_context,
            "target_goal": target_goal,
            "tone_hint": tone_hint,
            "relationship_status": relationship_status,
            "conversation_context": conversation_context,
            "material_summary": fallback.get("material_summary", ""),
            "fallback": fallback,
        },
        ensure_ascii=False,
        indent=2,
    )

    try:
        reply = await generate_reply(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            db=db,
        )
    except LLMGatewayError:
        return fallback

    parsed = _extract_json_object(str(reply.get("content", "")))
    response = _normalize_reply_assistant_response(parsed or {}, fallback)
    response["material_summary"] = response.get("material_summary") or fallback.get("material_summary", "")
    response["context_summary"] = response.get("context_summary") or fallback.get("context_summary", "")
    return response


def infer_reply_assistant_focus(*values: Any, target_person_type: str = "") -> dict[str, float | str]:
    text = _collect_text_pool(*values)
    lower_text = text.lower()
    inferred_target = _normalize_text(target_person_type) or _infer_target_person_type(text)

    understanding_hits = sum(1 for hint in UNDERSTANDING_HINTS if hint in lower_text)
    maintenance_hits = sum(1 for hint in MAINTENANCE_HINTS if hint in lower_text)
    message_push_hits = sum(1 for hint in MESSAGE_PUSH_HINTS if hint in lower_text)

    if inferred_target == "crush":
        message_push_hits += 3
    elif inferred_target in {"partner", "family", "friend"}:
        maintenance_hits += 2
    elif inferred_target == "ex":
        understanding_hits += 1
        maintenance_hits += 1
    elif inferred_target in {"colleague", "boss", "client"}:
        understanding_hits += 2
        message_push_hits += 1

    if not text:
        return {
            "analysis_focus": "balanced",
            "understanding_weight": 0.25,
            "maintenance_weight": 0.25,
            "message_push_weight": 0.25,
        }

    if understanding_hits == 0 and maintenance_hits == 0 and message_push_hits == 0:
        return {
            "analysis_focus": "balanced",
            "understanding_weight": 0.33,
            "maintenance_weight": 0.33,
            "message_push_weight": 0.34,
        }

    understanding_score = 0.35 + (understanding_hits * 0.12)
    maintenance_score = 0.35 + (maintenance_hits * 0.12)
    message_push_score = 0.35 + (message_push_hits * 0.12)
    if inferred_target == "crush":
        message_push_score += 0.15
    if inferred_target in {"partner", "family"}:
        maintenance_score += 0.1
    if inferred_target in {"colleague", "boss", "client"}:
        understanding_score += 0.08
    total = understanding_score + maintenance_score + message_push_score
    understanding_weight = round(understanding_score / total, 2)
    maintenance_weight = round(maintenance_score / total, 2)
    message_push_weight = round(message_push_score / total, 2)

    ordered_weights = sorted(
        [("understanding", understanding_weight), ("maintenance", maintenance_weight), ("message_push", message_push_weight)],
        key=lambda item: item[1],
        reverse=True,
    )
    if len(ordered_weights) >= 2 and (ordered_weights[0][1] - ordered_weights[1][1]) < 0.08:
        focus = "balanced"
    else:
        focus = ordered_weights[0][0]

    return {
        "analysis_focus": focus,
        "understanding_weight": understanding_weight,
        "maintenance_weight": maintenance_weight,
        "message_push_weight": message_push_weight,
    }


def build_reply_assistant_profile(
    *,
    target_person_type: str,
    target_person_label: str,
    target_person_name: str,
    reply_mode: str,
    relationship_status: str,
    reply_goal: str,
    tone: str,
    focus: dict[str, float | str],
) -> dict[str, Any]:
    return {
        "target_person_type": _normalize_text(target_person_type),
        "target_person_label": _normalize_text(target_person_label) or _build_target_person_label(target_person_type),
        "target_person_name": _normalize_text(target_person_name),
        "reply_mode": _normalize_text(reply_mode),
        "relationship_status": _normalize_text(relationship_status),
        "reply_goal": _normalize_text(reply_goal),
        "tone": _normalize_text(tone),
        "analysis_focus": _normalize_text(focus.get("analysis_focus")),
        "understanding_weight": float(focus.get("understanding_weight") or 0.0),
        "maintenance_weight": float(focus.get("maintenance_weight") or 0.0),
        "message_push_weight": float(focus.get("message_push_weight") or 0.0),
    }


def _candidate_reply_prefix(target_label: str, focus: dict[str, float | str], reply_mode: str) -> str:
    focus_label = _normalize_text(focus.get("analysis_focus")) or "balanced"
    if reply_mode == "material_distill":
        return f"基于{target_label}的材料"
    if focus_label == "message_push":
        return f"针对{target_label}的推进回复"
    if focus_label == "maintenance":
        return f"针对{target_label}的稳态回复"
    if focus_label == "understanding":
        return f"针对{target_label}的理解回复"
    return f"针对{target_label}的平衡回复"


def _build_reply_candidates(target_label: str, reply_goal: str, tone: str, focus: dict[str, float | str]) -> list[str]:
    goal = _normalize_text(reply_goal) or "先把话接住，再给更合适的回应。"
    tone_text = _normalize_text(tone) or "自然、克制"
    prefix = _candidate_reply_prefix(target_label, focus, "")
    templates = [
        f"稳妥版：{prefix}，先接住对方，再把你的意思说清楚。目标：{goal}。",
        f"自然版：{prefix}，语气保持{tone_text}，先顺着回应，再看下一步。目标：{goal}。",
        f"主动版：{prefix}，可以在尊重对方的前提下多推进一步。目标：{goal}。",
        f"克制版：{prefix}，先留一点余地，避免太快下结论。目标：{goal}。",
    ]
    return _merge_unique_lines(templates)


def _build_predicted_replies(target_person_type: str, focus: dict[str, float | str], user_message: str) -> list[str]:
    target_label = _build_target_person_label(target_person_type)
    focus_label = _normalize_text(focus.get("analysis_focus")) or "balanced"
    message = _normalize_text(user_message)
    templates = [
        f"{target_label}可能会先接住你的意思，再看你是不是在认真回应。",
        f"{target_label}可能会补充细节，继续确认你的态度。",
    ]
    if focus_label == "message_push":
        templates.append(f"{target_label}可能会更关注你要不要继续推进，语气会更在意节奏。")
    elif focus_label == "maintenance":
        templates.append(f"{target_label}可能会更看重你是不是稳住关系、不是只说一句就结束。")
    elif focus_label == "understanding":
        templates.append(f"{target_label}可能会先看你是否真的理解了这句话的意思。")
    else:
        templates.append(f"{target_label}可能会先观察你的回复是否兼顾理解和分寸。")
    if message:
        templates.append(f"围绕「{message[:24]}」这类内容，对方可能会先回应情绪或态度，再补信息。")
    return _merge_unique_lines(templates)[:4]


def _build_risk_flags(target_person_type: str, focus: dict[str, float | str], reply_goal: str, user_message: str) -> list[str]:
    text = _collect_text_pool(target_person_type, focus.get("analysis_focus"), reply_goal, user_message)
    lower_text = text.lower()
    flags: list[str] = []
    if any(keyword in lower_text for keyword in ("催", "逼", "马上", "立刻", "现在就", "秒回")):
        flags.append("推进过快")
    if any(keyword in lower_text for keyword in ("吵架", "生气", "冷战", "拉黑", "崩溃", "绝望")):
        flags.append("情绪较高")
    if any(keyword in lower_text for keyword in ("不确定", "猜", "可能", "也许")):
        flags.append("信息不足")
    if _normalize_text(focus.get("analysis_focus")) == "message_push":
        flags.append("注意发送前再确认关系状态")
    if not flags:
        flags.append("先确认目标，再发送")
    return _merge_unique_lines(flags)


def _build_message_push_cues(target_person_type: str, reply_goal: str, tone: str, user_message: str) -> list[str]:
    target_label = _build_target_person_label(target_person_type)
    goal = _normalize_text(reply_goal)
    cues = [
        f"先判断{target_label}更在意情绪还是信息。",
        "先给一版更稳的，再给一版更主动的。",
        "发出前先预演对方可能的下一句。",
    ]
    if goal:
        cues.append(f"当前目标：{goal}")
    if _normalize_text(tone):
        cues.append(f"语气要求：{_normalize_text(tone)}")
    if _normalize_text(user_message):
        cues.append(f"原话片段：{_normalize_text(user_message)[:28]}")
    return _merge_unique_lines(cues)


def _material_summary(raw_materials: dict[str, Any]) -> str:
    if not isinstance(raw_materials, dict):
        return ""
    snippets: list[str] = []
    text_pool = _merge_unique_lines(
        raw_materials.get("chat_history_text"),
        raw_materials.get("memory_notes_text"),
        raw_materials.get("text_materials_text"),
        raw_materials.get("draft_message_text"),
        raw_materials.get("recent_context_text"),
        raw_materials.get("reply_style_samples_text"),
        raw_materials.get("relationship_status_text"),
        raw_materials.get("interaction_patterns_text"),
        raw_materials.get("history_text"),
        raw_materials.get("expression_samples_text"),
        raw_materials.get("image_notes_text"),
        raw_materials.get("voice_notes_text"),
    )
    if text_pool:
        snippets.append(text_pool[0])
    image_documents = raw_materials.get("uploaded_image_documents") if isinstance(raw_materials.get("uploaded_image_documents"), list) else []
    if image_documents:
        snippets.append(f"图片{len(image_documents)}张")
    text_documents = raw_materials.get("uploaded_text_documents") if isinstance(raw_materials.get("uploaded_text_documents"), list) else []
    if text_documents:
        snippets.append(f"文件{len(text_documents)}份")
    ocr_results = raw_materials.get("ocr_extracted_texts") if isinstance(raw_materials.get("ocr_extracted_texts"), list) else []
    if ocr_results:
        snippets.append(summarize_ocr_results([item for item in ocr_results if isinstance(item, dict)]))
    return " / ".join(snippets[:3])


def build_reply_assistant_memory_base(
    *,
    target_person_type: str,
    target_person_label: str,
    target_person_name: str,
    reply_mode: str,
    relationship_status: str,
    reply_goal: str,
    tone: str,
    raw_materials: dict[str, Any],
    focus: dict[str, float | str],
) -> dict[str, Any]:
    reply_text_pool = _merge_unique_lines(
        raw_materials.get("chat_history_text"),
        raw_materials.get("memory_notes_text"),
        raw_materials.get("text_materials_text"),
        raw_materials.get("draft_message_text"),
        raw_materials.get("recent_context_text"),
        raw_materials.get("reply_style_samples_text"),
        raw_materials.get("interaction_patterns_text"),
        raw_materials.get("history_text"),
        raw_materials.get("expression_samples_text"),
        raw_materials.get("image_notes_text"),
        raw_materials.get("voice_notes_text"),
        [item.get("ocr_text") for item in raw_materials.get("ocr_extracted_texts", []) if isinstance(item, dict)],
    )

    understanding_layer = {
        "target_person_type": _normalize_text(target_person_type),
        "target_person_label": _normalize_text(target_person_label) or _build_target_person_label(target_person_type),
        "target_person_name": _normalize_text(target_person_name),
        "reply_mode": _normalize_text(reply_mode),
        "relationship_status": _normalize_text(relationship_status),
        "reply_goal": _normalize_text(reply_goal),
        "tone": _normalize_text(tone),
        "analysis_focus": _normalize_text(focus.get("analysis_focus")),
    }
    reply_candidates = _build_reply_candidates(
        understanding_layer["target_person_label"],
        reply_goal,
        tone,
        focus,
    )
    predicted_replies = _build_predicted_replies(target_person_type, focus, reply_goal)
    risk_flags = _build_risk_flags(target_person_type, focus, reply_goal, _collect_text_pool(raw_materials.get("draft_message_text"), raw_materials.get("chat_history_text")))
    message_push_cues = _build_message_push_cues(target_person_type, reply_goal, tone, raw_materials.get("draft_message_text"))
    reply_context = _material_summary(raw_materials)
    relationship_memory = _merge_unique_lines(
        raw_materials.get("memory_notes_text"),
        raw_materials.get("chat_history_text"),
        raw_materials.get("text_materials_text"),
        raw_materials.get("ocr_extracted_texts"),
    )
    interaction_samples = _merge_unique_lines(
        raw_materials.get("chat_history_text"),
        raw_materials.get("recent_context_text"),
        raw_materials.get("draft_message_text"),
    )
    style_samples = _merge_unique_lines(
        raw_materials.get("reply_style_samples_text"),
        raw_materials.get("interaction_patterns_text"),
        raw_materials.get("expression_samples_text"),
    )
    if not relationship_memory:
        relationship_memory = reply_text_pool[:4]
    if not interaction_samples:
        interaction_samples = reply_text_pool[:3]
    if not style_samples:
        style_samples = reply_candidates[:3]

    return {
        "understanding_layer": understanding_layer,
        "reply_candidates": reply_candidates,
        "predicted_replies": predicted_replies,
        "risk_flags": risk_flags,
        "message_push_cues": message_push_cues,
        "relationship_memory": relationship_memory[:6],
        "interaction_samples": interaction_samples[:6],
        "style_samples": style_samples[:6],
        "reply_context": reply_context,
        "analysis_focus": _normalize_text(focus.get("analysis_focus")),
        "understanding_weight": float(focus.get("understanding_weight") or 0.0),
        "maintenance_weight": float(focus.get("maintenance_weight") or 0.0),
        "message_push_weight": float(focus.get("message_push_weight") or 0.0),
        "raw_materials": raw_materials,
    }


def select_reply_assistant_memory_layers(
    memory_base: dict[str, Any],
    emotional_state: str,
    user_message: str,
    *,
    history: list[dict[str, str]] | None = None,
) -> dict[str, list[str] | str]:
    pool = {
        "relationship_memory": _merge_unique_lines(memory_base.get("relationship_memory")),
        "interaction_samples": _merge_unique_lines(memory_base.get("interaction_samples")),
        "style_samples": _merge_unique_lines(memory_base.get("style_samples")),
        "reply_candidates": _merge_unique_lines(memory_base.get("reply_candidates")),
        "predicted_replies": _merge_unique_lines(memory_base.get("predicted_replies")),
        "message_push_cues": _merge_unique_lines(memory_base.get("message_push_cues")),
    }
    recent_history = [
        _normalize_text(message.get("content"))
        for message in (history or [])[-4:]
        if _normalize_text(message.get("content"))
    ]
    trigger_text = _collect_text_pool(emotional_state, user_message, " ".join(recent_history))
    trigger_lower = trigger_text.lower()
    stage = "balanced"
    if any(keyword in trigger_lower for keyword in ("难过", "失落", "焦虑", "压力", "委屈", "崩溃", "心累")):
        stage = "light"
    elif any(keyword in trigger_lower for keyword in MESSAGE_PUSH_HINTS):
        stage = "push"
    elif any(keyword in trigger_lower for keyword in UNDERSTANDING_HINTS):
        stage = "understanding"
    elif any(keyword in trigger_lower for keyword in MAINTENANCE_HINTS):
        stage = "maintenance"

    if stage == "light":
        selected = pool["style_samples"][:2] or pool["reply_candidates"][:2] or pool["relationship_memory"][:1]
    elif stage == "push":
        selected = pool["message_push_cues"][:2] + pool["reply_candidates"][:1] + pool["predicted_replies"][:1]
    elif stage == "understanding":
        selected = pool["interaction_samples"][:2] + pool["relationship_memory"][:1] + pool["reply_candidates"][:1]
    elif stage == "maintenance":
        selected = pool["relationship_memory"][:2] + pool["style_samples"][:1] + pool["reply_candidates"][:1]
    else:
        selected = pool["relationship_memory"][:2] + pool["interaction_samples"][:1] + pool["style_samples"][:1]

    selected = [item for item in selected if item]
    if not selected:
        selected = pool["reply_candidates"][:2] or pool["predicted_replies"][:2]

    max_memory_items = {"light": 2, "understanding": 3, "maintenance": 3, "push": 3}.get(stage, 3)
    return {
        "recall_stage": stage,
        "max_memory_items": max_memory_items,
        "selected_memories": selected[:max_memory_items],
        "relationship_memory": pool["relationship_memory"],
        "interaction_samples": pool["interaction_samples"],
        "style_samples": pool["style_samples"],
        "reply_candidates": pool["reply_candidates"],
        "predicted_replies": pool["predicted_replies"],
        "message_push_cues": pool["message_push_cues"],
    }


def build_reply_assistant_context(
    persona: dict[str, Any],
    history: list[dict[str, str]],
    user_message: str,
) -> str:
    profile = persona.get("reply_assistant_profile") or {}
    memory_base = persona.get("reply_assistant_memory_base") or persona.get("relationship_management_memory_base") or persona.get("intimate_memory_base") or persona.get("memory_base") or {}
    if not isinstance(profile, dict) or not isinstance(memory_base, dict):
        return ""

    emotional_state = detect_emotional_state(user_message, history)
    focus = infer_reply_assistant_focus(
        profile.get("target_person_type"),
        profile.get("reply_mode"),
        profile.get("relationship_status"),
        profile.get("reply_goal"),
        user_message,
        " ".join(message.get("content", "") for message in history[-4:]),
        memory_base.get("reply_context"),
        memory_base.get("relationship_memory"),
        memory_base.get("interaction_samples"),
        memory_base.get("style_samples"),
        memory_base.get("reply_candidates"),
        memory_base.get("message_push_cues"),
        target_person_type=profile.get("target_person_type", ""),
    )
    selected = select_reply_assistant_memory_layers(memory_base, emotional_state, user_message, history=history)
    target_label = _normalize_text(profile.get("target_person_label")) or _build_target_person_label(profile.get("target_person_type"))
    lines: list[str] = [
        "回复辅助路径：我该怎么回",
        f"对象类型：{target_label}",
        f"分析重心：{focus['analysis_focus']}",
        f"理解权重：{focus['understanding_weight']}",
        f"维护权重：{focus['maintenance_weight']}",
        f"消息推进权重：{focus.get('message_push_weight', 0.0)}",
        f"当前情绪状态：{emotional_state}",
        f"当前用户消息：{_normalize_text(user_message)}",
    ]
    reply_mode = _normalize_text(profile.get("reply_mode"))
    relationship_status = _normalize_text(profile.get("relationship_status"))
    reply_goal = _normalize_text(profile.get("reply_goal"))
    tone = _normalize_text(profile.get("tone"))
    if reply_mode:
        lines.append(f"回复模式：{reply_mode}")
    if relationship_status:
        lines.append(f"关系状态：{relationship_status}")
    if reply_goal:
        lines.append(f"当前目标：{reply_goal}")
    if tone:
        lines.append(f"语气要求：{tone}")
    if selected.get("selected_memories"):
        lines.append("当前召回：")
        lines.extend(f"- {item}" for item in selected["selected_memories"][:4])
    if selected.get("reply_candidates"):
        lines.append("候选回复：")
        lines.extend(f"- {item}" for item in selected["reply_candidates"][:4])
    if selected.get("predicted_replies"):
        lines.append("对方可能回复：")
        lines.extend(f"- {item}" for item in selected["predicted_replies"][:4])
    if selected.get("message_push_cues"):
        lines.append("消息推进线索：")
        lines.extend(f"- {item}" for item in selected["message_push_cues"][:4])
    risk_flags = _merge_unique_lines(memory_base.get("risk_flags"))
    if risk_flags:
        lines.append("风险提示：")
        lines.extend(f"- {item}" for item in risk_flags[:4])
    return "\n".join(lines).strip()
