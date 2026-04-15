from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import quote_plus

import httpx

QuestionClass = Literal["fact_required", "framework_only", "hybrid"]


FACT_KEYWORDS = (
    "专业",
    "院校",
    "学校",
    "录取",
    "分数线",
    "位次",
    "保研",
    "就业率",
    "薪资",
    "政策",
    "招生",
    "排名",
    "学费",
    "城市",
    "地区",
)

FRAMEWORK_KEYWORDS = (
    "怎么选",
    "怎么办",
    "值不值",
    "靠谱吗",
    "适不适合",
    "要不要",
    "先就业",
    "考研",
    "家庭",
    "普通家庭",
    "取舍",
    "退路",
    "路径",
)

HYBRID_MARKERS = (
    "人工智能",
    "AI",
    "计算机",
    "金融",
    "临床",
    "新能源",
    "半导体",
    "医学",
    "文科",
    "双非",
)


@dataclass(slots=True)
class ResearchResult:
    needs_research: bool
    question_class: QuestionClass
    facts_summary: list[str]
    sources_hint: list[str]
    search_query: str
    evidence: list[dict[str, str]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "needs_research": self.needs_research,
            "question_class": self.question_class,
            "facts_summary": self.facts_summary,
            "sources_hint": self.sources_hint,
            "search_query": self.search_query,
            "evidence": self.evidence,
        }


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _keyword_hits(text: str, keywords: tuple[str, ...]) -> int:
    normalized = _normalize_text(text)
    return sum(1 for keyword in keywords if keyword and keyword.lower() in normalized.lower())


def classify_zhangxuefeng_question(user_message: str, history: list[dict[str, str]] | None = None) -> QuestionClass:
    text = _normalize_text(user_message)
    history_text = " ".join(
        _normalize_text(item.get("content", ""))
        for item in (history or [])
        if str(item.get("role", "")).strip() in {"user", "assistant"}
    )
    combined = f"{text} {history_text}".strip()

    fact_hits = _keyword_hits(combined, FACT_KEYWORDS)
    framework_hits = _keyword_hits(combined, FRAMEWORK_KEYWORDS)
    hybrid_hits = _keyword_hits(combined, HYBRID_MARKERS)

    if fact_hits >= 2 and framework_hits >= 1:
        return "hybrid"
    if hybrid_hits >= 1 and fact_hits >= 1:
        return "hybrid"
    if fact_hits >= 2:
        return "fact_required"
    if framework_hits >= 2:
        return "framework_only"

    if any(marker.lower() in combined.lower() for marker in HYBRID_MARKERS):
        return "hybrid"

    if any(keyword in combined for keyword in FACT_KEYWORDS):
        return "fact_required"

    return "framework_only"


def _build_sources_hint(question_class: QuestionClass) -> list[str]:
    base = ["院校官网", "教育考试院", "学校招生简章", "专业培养方案"]
    if question_class == "hybrid":
        return base + ["行业报告", "目标城市招聘信息", "近三年就业/升学去向"]
    return base


def _build_fact_summary(question: str, question_class: QuestionClass) -> list[str]:
    text = _normalize_text(question)
    summary = [
        "需要先核实最新事实，再做路径判断。",
        "不要把经验判断伪装成最新数据。",
    ]

    if any(keyword in text for keyword in ("人工智能", "AI", "计算机")):
        summary.extend(
            [
                "先核实目标院校的培养方案、课程设置和就业/升学去向。",
                "重点看岗位入口是否足够、城市机会是否承接得住。",
            ]
        )
    elif any(keyword in text for keyword in ("金融",)):
        summary.extend(
            [
                "先核实数学要求、就业岗位密度、目标城市金融岗位分布。",
                "重点看普通家庭能否承受试错成本和地域切换成本。",
            ]
        )
    elif any(keyword in text for keyword in ("临床", "医学")):
        summary.extend(
            [
                "先核实学制、规培、执业路径和地区录取差异。",
                "重点看毕业后是否有稳定入口，以及路径成本是否可承受。",
            ]
        )
    elif any(keyword in text for keyword in ("新能源", "半导体")):
        summary.extend(
            [
                "先核实产业分布、校企合作和岗位稳定性。",
                "重点看学校是否真的能把人送到岗位入口，而不是只看方向热度。",
            ]
        )
    elif any(keyword in text for keyword in ("文科",)):
        summary.extend(
            [
                "先核实目标专业的岗位入口和继续深造路径。",
                "重点看学校、城市和专业三者能否一起形成可落地的组合。",
            ]
        )
    else:
        summary.extend(
            [
                f"问题分类：{question_class}。",
                "需要核实院校官网、教育考试院、近三年就业/升学去向和政策变化。",
            ]
        )

    return summary


def _parse_search_results(text: str, limit: int = 3) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
        r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
        re.S,
    )
    for match in pattern.finditer(text):
        title = re.sub(r"<.*?>", "", match.group("title"))
        snippet = re.sub(r"<.*?>", "", match.group("snippet"))
        href = match.group("href").strip()
        if title.strip():
            results.append(
                {
                    "title": _normalize_text(title),
                    "snippet": _normalize_text(snippet),
                    "url": href,
                }
            )
        if len(results) >= limit:
            break
    return results


async def _fetch_web_evidence(question: str) -> list[dict[str, str]]:
    mode = os.getenv("ZHANGXUEFENG_RESEARCH_MODE", "stub").strip().lower()
    timeout = float(os.getenv("ZHANGXUEFENG_RESEARCH_TIMEOUT", "8") or 8)
    query = _normalize_text(question)
    if not query:
        return []

    if mode in {"stub", "off", "disabled"}:
        return []

    if mode in {"duckduckgo", "ddg"}:
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=timeout)) as client:
            response = await client.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            return _parse_search_results(response.text)

    search_url_template = os.getenv("ZHANGXUEFENG_RESEARCH_SEARCH_URL", "").strip()
    if search_url_template:
        search_url = search_url_template.format(query=quote_plus(query), raw_query=query)
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=timeout)) as client:
            response = await client.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            try:
                payload = response.json()
            except ValueError:
                return _parse_search_results(response.text)

            items = payload.get("items") if isinstance(payload, dict) else []
            parsed: list[dict[str, str]] = []
            if isinstance(items, list):
                for item in items[:3]:
                    if isinstance(item, dict):
                        parsed.append(
                            {
                                "title": _normalize_text(str(item.get("title", ""))),
                                "snippet": _normalize_text(str(item.get("snippet", ""))),
                                "url": _normalize_text(str(item.get("url", ""))),
                            }
                        )
            return [item for item in parsed if item["title"] or item["snippet"]]

    return []


def _deduplicate_lines(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        normalized = _normalize_text(line)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _build_fallback_summary(question: str, question_class: QuestionClass) -> list[str]:
    summary = _build_fact_summary(question, question_class)
    summary.append("当前环境未启用稳定的外部搜索源，以上先作为核实清单和判断框架。")
    return _deduplicate_lines(summary)


async def research_education_question(question: str, classification: QuestionClass | None = None) -> dict[str, Any]:
    normalized_question = _normalize_text(question)
    question_class = classification or classify_zhangxuefeng_question(normalized_question)
    needs_research = question_class in {"fact_required", "hybrid"}

    evidence: list[dict[str, str]] = []
    if needs_research:
        try:
            evidence = await _fetch_web_evidence(normalized_question)
        except (httpx.HTTPError, ValueError, RuntimeError):
            evidence = []

    facts_summary = _build_fact_summary(normalized_question, question_class)
    if evidence:
        for item in evidence:
            title = item.get("title", "").strip()
            snippet = item.get("snippet", "").strip()
            url = item.get("url", "").strip()
            text = " / ".join(part for part in [title, snippet, url] if part)
            if text:
                facts_summary.append(text)
        facts_summary = _deduplicate_lines(facts_summary)
    elif needs_research:
        facts_summary = _build_fallback_summary(normalized_question, question_class)

    return ResearchResult(
        needs_research=needs_research,
        question_class=question_class,
        facts_summary=facts_summary,
        sources_hint=_build_sources_hint(question_class),
        search_query=normalized_question,
        evidence=evidence,
    ).as_dict()
