from __future__ import annotations

import os
from typing import Any, Literal

import httpx

from app.services.zhangxuefeng_research import (
    _fetch_baidu_evidence,
    _fetch_custom_evidence,
    _normalize_text,
    _unique_preserve_order,
)

HowToDoResearchKind = Literal[
    "calendar_time",
    "market_timing",
    "location_time",
    "factual_reference",
    "general",
]


TIME_KEYWORDS = (
    "今天",
    "明天",
    "后天",
    "本周",
    "下周",
    "清明",
    "节气",
    "换月",
    "哪天",
    "日期",
    "时间",
    "戊申日",
    "己亥日",
    "日辰",
)

MARKET_KEYWORDS = (
    "做空",
    "买跌",
    "买涨",
    "行情",
    "交易日",
    "出空",
    "止盈",
    "止损",
    "标的",
    "利润",
    "反弹",
)

LOCATION_KEYWORDS = (
    "西班牙",
    "Tarragona",
    "塔拉戈纳",
    "时区",
    "当地",
    "本地时间",
)

REFERENCE_KEYWORDS = (
    "原文",
    "出处",
    "资料",
    "官网",
    "规则",
    "政策",
    "历法",
    "黄历",
    "万年历",
)

SEARCH_RESULT_LIMIT = 5


def _infer_research_kind(question: str, history: list[dict[str, Any]] | None = None) -> HowToDoResearchKind:
    combined = " ".join(
        [
            _normalize_text(question),
            *[
                _normalize_text(item.get("content"))
                for item in (history or [])
                if _normalize_text(item.get("content"))
            ],
        ]
    ).strip()
    if any(keyword.lower() in combined.lower() for keyword in LOCATION_KEYWORDS):
        return "location_time"
    if any(keyword in combined for keyword in TIME_KEYWORDS):
        return "calendar_time"
    if any(keyword in combined for keyword in MARKET_KEYWORDS):
        return "market_timing"
    if any(keyword in combined for keyword in REFERENCE_KEYWORDS):
        return "factual_reference"
    return "general"


def _extract_cast_date(raw_result: dict[str, Any] | None) -> str:
    if not isinstance(raw_result, dict):
        return ""
    label = _normalize_text(raw_result.get("day_label"))
    if not label:
        return ""
    return label.split(" ")[0]


def _build_queries(
    question: str,
    category: str = "",
    cast_context: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> list[str]:
    normalized_question = _normalize_text(question)
    normalized_category = _normalize_text(category)
    raw_result = (cast_context or {}).get("raw_result") if isinstance(cast_context, dict) else {}
    cast_date = _extract_cast_date(raw_result if isinstance(raw_result, dict) else {})
    kind = _infer_research_kind(normalized_question, history)
    terms = _unique_preserve_order([normalized_question, normalized_category, cast_date])
    base = " ".join(item for item in terms if item).strip() or normalized_question

    if kind == "location_time":
        queries = [
            f"{base} 当地日期 时区",
            f"{base} 节气 日期",
            f"{base} 万年历 干支",
        ]
    elif kind == "calendar_time":
        queries = [
            f"{base} 节气 日期 万年历",
            f"{base} 干支 日期 黄历",
            f"{base} 当天 是什么日",
        ]
    elif kind == "market_timing":
        queries = [
            f"{base} 交易日 节气 日期",
            f"{base} 干支 日期 节气",
            f"{base} 市场 日历",
        ]
    elif kind == "factual_reference":
        queries = [
            f"{base} 官网 原文",
            f"{base} 规则 资料",
            f"{base} 历法 说明",
        ]
    else:
        queries = [
            f"{base} 节气 干支 日期",
            f"{base} 资料 说明",
            normalized_question,
        ]
    return _unique_preserve_order([_normalize_text(item) for item in queries if _normalize_text(item)])[:3]


def _domain_priority(url: str) -> int:
    normalized = url.lower()
    if ".gov.cn" in normalized or normalized.endswith("gov.cn"):
        return 120
    if ".org" in normalized:
        return 92
    if ".edu" in normalized:
        return 90
    if any(marker in normalized for marker in ("wannianli", "calendar", "timeanddate", "timezone", "exchange")):
        return 84
    if normalized:
        return 40
    return 0


def _score_result(item: dict[str, str]) -> int:
    title = _normalize_text(item.get("title"))
    snippet = _normalize_text(item.get("snippet"))
    url = _normalize_text(item.get("url"))
    combined = f"{title} {snippet}"
    score = _domain_priority(url)
    if any(keyword in combined for keyword in ("节气", "黄历", "万年历", "干支", "日历", "时区", "交易日", "清明")):
        score += 18
    if any(keyword in combined for keyword in ("官网", "官方", "公告", "说明")):
        score += 12
    if any(host in url.lower() for host in ("baidu.com", "zhihu.com", "weibo.com", "douyin.com")):
        score -= 24
    return score


def _rank_results(results: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in results:
        title = _normalize_text(item.get("title"))
        snippet = _normalize_text(item.get("snippet"))
        url = _normalize_text(item.get("url"))
        key = url or title or snippet
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append({"title": title, "snippet": snippet, "url": url})
    ranked = sorted(deduped, key=_score_result, reverse=True)
    return ranked[:SEARCH_RESULT_LIMIT]


def _summarize_results(results: list[dict[str, str]], kind: HowToDoResearchKind) -> dict[str, Any]:
    ranked = _rank_results(results)
    facts_summary: list[str] = []
    sources_hint: list[str] = []
    for item in ranked[:3]:
        title = _normalize_text(item.get("title"))
        snippet = _normalize_text(item.get("snippet"))
        url = _normalize_text(item.get("url"))
        line = " / ".join(part for part in [title, snippet] if part)
        if line:
            facts_summary.append(line)
        if url:
            host = url.split("/")[2] if "://" in url else url
            sources_hint.append(host.replace("www.", ""))

    if not facts_summary:
        fallback_by_kind = {
            "calendar_time": [
                "优先核实节气、黄历、万年历与具体日期，不要先按模糊印象判断。",
                "如果问的是某一天的助力，先确认那天对应的干支与节气前后位置。",
            ],
            "market_timing": [
                "先核实交易日、节气切换和具体日期，再把时间因素放回卦里判断。",
                "如果涉及做空或做多，先分清当天对你而言上涨是利还是害。",
            ],
            "location_time": [
                "先核实用户当地日期、时区和节气对应时间，再判断今天、明天或前一天。",
                "跨时区问题不能直接沿用服务器时间。",
            ],
            "factual_reference": [
                "先核实原始资料和规则出处，再把事实放回卦中解释。",
            ],
            "general": [
                "联网层没有拿到足够事实时，先以卦盘为主，不伪装成已核实过。",
            ],
        }
        facts_summary = fallback_by_kind.get(kind, fallback_by_kind["general"])

    return {
        "facts_summary": _unique_preserve_order(facts_summary),
        "sources_hint": _unique_preserve_order(sources_hint),
        "evidence": ranked,
    }


def _format_sources_hint(kind: HowToDoResearchKind, sources: list[str]) -> list[str]:
    if sources:
        return sources
    defaults = {
        "calendar_time": ["万年历", "节气历法资料", "黄历 / 干支资料"],
        "market_timing": ["市场日历", "万年历", "节气历法资料"],
        "location_time": ["timeanddate", "时区资料", "万年历"],
        "factual_reference": ["官方资料", "规则出处", "原始页面"],
        "general": ["官方资料", "日历 / 节气资料"],
    }
    return defaults.get(kind, defaults["general"])


async def research_how_to_do_question(
    question: str,
    category: str = "",
    cast_context: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    normalized_question = _normalize_text(question)
    if not normalized_question:
        return {
            "needs_research": False,
            "research_kind": "general",
            "facts_summary": [],
            "sources_hint": [],
            "search_queries": [],
            "evidence": [],
        }

    kind = _infer_research_kind(normalized_question, history)
    queries = _build_queries(normalized_question, category, cast_context, history)
    provider_mode = os.getenv("HOW_TO_DO_RESEARCH_MODE", "baidu").strip().lower()
    if provider_mode not in {"stub", "baidu", "custom"}:
        provider_mode = "baidu"

    evidence: list[dict[str, str]] = []
    try:
        if provider_mode == "stub":
            evidence = []
        elif provider_mode == "custom":
            for query in queries:
                evidence.extend(await _fetch_custom_evidence(query))
        else:
            for query in queries:
                evidence.extend(await _fetch_baidu_evidence(query))
    except (httpx.HTTPError, httpx.TimeoutException, RuntimeError, ValueError):
        evidence = []

    summary = _summarize_results(evidence, kind)
    return {
        "needs_research": True,
        "research_kind": kind,
        "facts_summary": summary["facts_summary"],
        "sources_hint": _format_sources_hint(kind, summary["sources_hint"]),
        "search_queries": queries,
        "evidence": summary["evidence"],
    }
