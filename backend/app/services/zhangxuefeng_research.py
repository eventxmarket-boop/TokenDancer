from __future__ import annotations

import html
import os
import re
from datetime import datetime
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Literal
from urllib.parse import quote_plus, urlparse

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

EDUCATION_FOCUS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "school_list": (
        "名单",
        "有哪些学校",
        "哪些学校",
        "院校名单",
        "能报什么学校",
        "可以报什么学校",
        "学校推荐",
        "专科学校",
        "本科院校",
    ),
    "score_line": (
        "分数线",
        "位次",
        "最低分",
        "投档线",
        "录取线",
        "多少分能上",
        "能上什么",
        "报什么",
    ),
    "major_detail": (
        "招生简章",
        "专业介绍",
        "培养方案",
        "就业质量报告",
        "学校怎么样",
        "院校怎么样",
        "官网",
        "招生网",
    ),
    "employment": (
        "就业率",
        "薪资",
        "岗位",
        "前景",
        "行业",
        "能不能选",
        "值不值",
    ),
    "policy": (
        "政策",
        "招生计划",
        "名额",
        "扩招",
        "缩招",
        "调整",
    ),
}

OFFICIAL_SOURCE_HINTS = [
    "教育考试院",
    "学校官网",
    "招生官网",
    "招生简章",
    "院校官网",
    "就业质量报告",
]

DEFAULT_SOURCE_HINTS = [
    "院校官网",
    "教育考试院",
    "学校招生简章",
    "专业培养方案",
]

BAIDU_SEARCH_URL = "https://www.baidu.com/s"
DEFAULT_TIMEOUT = 8.0
DEFAULT_MAX_RESULTS = 5


@dataclass(slots=True)
class ResearchResult:
    needs_research: bool
    question_class: QuestionClass
    facts_summary: list[str]
    sources_hint: list[str]
    search_query: str
    search_queries: list[str]
    evidence: list[dict[str, str]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "needs_research": self.needs_research,
            "question_class": self.question_class,
            "facts_summary": self.facts_summary,
            "sources_hint": self.sources_hint,
            "search_query": self.search_query,
            "search_queries": self.search_queries,
            "evidence": self.evidence,
        }


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _keyword_hits(text: str, keywords: tuple[str, ...]) -> int:
    normalized = _normalize_text(text)
    return sum(1 for keyword in keywords if keyword and keyword.lower() in normalized.lower())


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = _normalize_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


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


def _infer_education_focus(question: str) -> str:
    normalized = _normalize_text(question)
    for focus, keywords in EDUCATION_FOCUS_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return focus
    return "general"


def _extract_school_hint(question: str) -> str:
    normalized = _normalize_text(question)
    patterns = (
        r"[\u4e00-\u9fffA-Za-z0-9·（）()]{2,40}?(?:大学|学院|学校|专科学校|职业技术学院|高等专科学校)",
        r"[\u4e00-\u9fffA-Za-z0-9·（）()]{2,40}?(?:招生考试院|教育考试院)",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            return _normalize_text(match.group(0))
    return ""


def _extract_region_hint(question: str) -> str:
    normalized = _normalize_text(question)
    region_keywords = (
        "北京",
        "天津",
        "上海",
        "重庆",
        "河北",
        "山西",
        "辽宁",
        "吉林",
        "黑龙江",
        "江苏",
        "浙江",
        "安徽",
        "福建",
        "江西",
        "山东",
        "河南",
        "湖北",
        "湖南",
        "广东",
        "海南",
        "四川",
        "贵州",
        "云南",
        "陕西",
        "甘肃",
        "青海",
        "内蒙古",
        "广西",
        "宁夏",
        "新疆",
        "西藏",
    )
    for region in region_keywords:
        if region in normalized:
            return region
    return ""


def _extract_subject_hint(question: str) -> str:
    normalized = _normalize_text(question)
    subject_keywords = (
        "理科",
        "文科",
        "物理",
        "历史",
        "物化",
        "物化生",
        "物生地",
        "首选物理",
        "首选历史",
    )
    for subject in subject_keywords:
        if subject in normalized:
            return subject
    return ""


def _extract_score_hint(question: str) -> str:
    normalized = _normalize_text(question)
    match = re.search(r"\d{2,3}\s*分|\d{4,5}\s*位次", normalized)
    if match:
        return _normalize_text(match.group(0)).replace(" ", "")
    return ""


def build_search_queries(question: str, category: str) -> list[str]:
    normalized = _normalize_text(question)
    if not normalized:
        return []

    focus = _infer_education_focus(normalized)
    school_hint = _extract_school_hint(normalized)
    region_hint = _extract_region_hint(normalized)
    subject_hint = _extract_subject_hint(normalized)
    score_hint = _extract_score_hint(normalized)
    year = str(datetime.now().year)

    base_terms = _unique_preserve_order([region_hint, subject_hint, score_hint, school_hint])
    base_phrase = " ".join(base_terms).strip() or normalized

    if category == "framework_only":
        return [normalized]

    queries: list[str] = []
    if focus == "school_list":
        queries = [
            f"{base_phrase} 院校名单 site:gov.cn OR site:edu.cn",
            f"{base_phrase} 招生院校名单 教育考试院",
            f"{base_phrase} 专科 招生 院校 {year}",
        ]
    elif focus == "score_line":
        queries = [
            f"{base_phrase} 录取分数线 site:gov.cn OR site:edu.cn",
            f"{base_phrase} 历年 录取分数线 教育考试院",
            f"{base_phrase} 招生计划 院校官网",
        ]
    elif focus == "major_detail":
        queries = [
            f"{school_hint or base_phrase} 招生简章 site:edu.cn OR site:gov.cn",
            f"{school_hint or base_phrase} 专业介绍 site:edu.cn",
            f"{school_hint or base_phrase} 就业质量报告 site:edu.cn",
        ]
    elif focus == "employment":
        queries = [
            f"{base_phrase} 就业质量报告 site:edu.cn OR site:gov.cn",
            f"{base_phrase} 岗位 招聘 site:gov.cn OR site:edu.cn",
            f"{base_phrase} 招生简章 专业介绍",
        ]
    elif focus == "policy":
        queries = [
            f"{base_phrase} 招生计划 site:gov.cn OR site:edu.cn",
            f"{base_phrase} 教育考试院 政策",
            f"{base_phrase} 院校招生计划 官网",
        ]
    else:
        queries = [
            f"{base_phrase} site:gov.cn OR site:edu.cn",
            f"{base_phrase} 招生简章 教育考试院",
            f"{base_phrase} 专业介绍 官网",
        ]

    queries = [_normalize_text(query) for query in queries if _normalize_text(query)]
    return _unique_preserve_order(queries)[:3]


def _build_sources_hint(question: str, question_class: QuestionClass, results: list[dict[str, str]] | None = None) -> list[str]:
    if results:
        hints: list[str] = []
        for item in results[:3]:
            url = item.get("url", "").strip()
            host = urlparse(url).hostname or ""
            if host.endswith("gov.cn"):
                hints.append("教育考试院 / 政府官网")
            elif host.endswith("edu.cn") or host.endswith(".edu.cn"):
                hints.append("学校官网 / 招生网")
            elif host:
                hints.append(host.replace("www.", ""))
        return _unique_preserve_order(hints) or DEFAULT_SOURCE_HINTS

    focus = _infer_education_focus(question)
    if focus in {"school_list", "score_line", "major_detail", "employment", "policy"}:
        return DEFAULT_SOURCE_HINTS
    if question_class == "hybrid":
        return DEFAULT_SOURCE_HINTS + ["行业报告", "目标城市招聘信息", "近三年就业/升学去向"]
    return DEFAULT_SOURCE_HINTS


def _extract_data_tools_url(data_tools: str) -> str:
    if not data_tools:
        return ""

    normalized = data_tools.replace("\\u0026", "&")
    for key in ("mu", "url", "murl"):
        match = re.search(rf'"{key}":"([^"]+)"', normalized)
        if match:
            return html.unescape(match.group(1))
    return ""


class _BaiduSearchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.results: list[dict[str, str]] = []
        self._in_result = False
        self._result_depth = 0
        self._current: dict[str, str] | None = None
        self._current_field: str | None = None
        self._current_field_buffer: list[str] = []
        self._in_title = False
        self._field_depth = 0

    def _begin_result(self) -> None:
        self._in_result = True
        self._result_depth = 1
        self._current = {"title": "", "snippet": "", "url": ""}
        self._current_field = None
        self._current_field_buffer = []
        self._in_title = False
        self._field_depth = 0

    def _finish_field(self) -> None:
        if not self._current or not self._current_field:
            return
        value = _normalize_text("".join(self._current_field_buffer))
        if value:
            self._current[self._current_field] = value
        self._current_field = None
        self._current_field_buffer = []
        self._field_depth = 0

    def _finish_result(self) -> None:
        if not self._current:
            return
        title = _normalize_text(self._current.get("title", ""))
        snippet = _normalize_text(self._current.get("snippet", ""))
        url = _normalize_text(self._current.get("url", ""))
        if title or snippet or url:
            self.results.append({"title": title, "snippet": snippet, "url": url})
        self._current = None
        self._current_field = None
        self._current_field_buffer = []
        self._in_result = False
        self._in_title = False
        self._field_depth = 0
        self._result_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        class_names = set((attrs_dict.get("class") or "").split())

        if tag == "div":
            if not self._in_result and ("result" in class_names or "c-container" in class_names):
                self._begin_result()
                return
            if self._in_result:
                self._result_depth += 1
                if "c-abstract" in class_names and self._current is not None:
                    self._current_field = "snippet"
                    self._current_field_buffer = []
                    self._field_depth = 1
                elif self._current_field is not None:
                    self._field_depth += 1
            return

        if not self._in_result:
            return

        if tag == "h3":
            self._in_title = True
            return

        if tag == "a" and self._in_title and self._current is not None and not self._current.get("title"):
            data_tools = attrs_dict.get("data-tools", "")
            target_url = _extract_data_tools_url(data_tools) or attrs_dict.get("href", "")
            self._current["url"] = _normalize_text(target_url)
            self._current_field = "title"
            self._current_field_buffer = []
            self._field_depth = 1

    def handle_endtag(self, tag: str) -> None:
        if not self._in_result:
            return

        if tag == "a" and self._current_field == "title":
            self._finish_field()
            return

        if tag == "h3":
            self._in_title = False
            return

        if tag == "div":
            if self._current_field is not None:
                self._field_depth -= 1
                if self._field_depth <= 0:
                    self._finish_field()
            self._result_depth -= 1
            if self._result_depth <= 0:
                self._finish_result()

    def handle_data(self, data: str) -> None:
        if self._current_field is None:
            return
        text = html.unescape(data or "")
        if text:
            self._current_field_buffer.append(text)


def _parse_baidu_results(text: str, limit: int = DEFAULT_MAX_RESULTS) -> list[dict[str, str]]:
    parser = _BaiduSearchParser()
    parser.feed(text or "")
    parser.close()

    results = []
    for item in parser.results:
        title = _normalize_text(item.get("title", ""))
        snippet = _normalize_text(item.get("snippet", ""))
        url = _normalize_text(item.get("url", ""))
        if not title and not snippet:
            continue
        results.append({"title": title, "snippet": snippet, "url": url})
        if len(results) >= limit:
            break
    return results


def _parse_custom_results(response: httpx.Response, limit: int = DEFAULT_MAX_RESULTS) -> list[dict[str, str]]:
    try:
        payload = response.json()
    except ValueError:
        return _parse_baidu_results(response.text, limit=limit)

    items = payload.get("items") if isinstance(payload, dict) else []
    parsed: list[dict[str, str]] = []
    if isinstance(items, list):
        for item in items[:limit]:
            if isinstance(item, dict):
                parsed.append(
                    {
                        "title": _normalize_text(str(item.get("title", ""))),
                        "snippet": _normalize_text(str(item.get("snippet", ""))),
                        "url": _normalize_text(str(item.get("url", ""))),
                    }
                )
    return [item for item in parsed if item["title"] or item["snippet"]]


def _domain_priority(url: str) -> int:
    host = (urlparse(url).hostname or "").lower()
    if host.endswith("gov.cn"):
        return 120
    if host.endswith("edu.cn") or host.endswith(".edu.cn"):
        return 100
    if host.endswith(".edu") or ".edu." in host:
        return 95
    if any(keyword in host for keyword in ("zhaosheng", "admission", "zs", "zsb")):
        return 88
    if host:
        return 40
    return 0


def _score_result(item: dict[str, str]) -> int:
    url = item.get("url", "").strip()
    title = item.get("title", "").strip()
    snippet = item.get("snippet", "").strip()
    host = (urlparse(url).hostname or "").lower()
    score = _domain_priority(url)

    if any(marker in title or marker in snippet for marker in ("官网", "招生", "教育考试院", "就业质量报告", "专业介绍")):
        score += 12
    if any(marker in title or marker in snippet for marker in ("教育考试院", "招生考试院", "教育招生考试", "招生办公室")):
        score += 60
    if any(marker in host for marker in ("eea", "sneea", "zhaokao", "gaokao")):
        score += 20
    if "院校" in title or "学校" in title:
        score += 5
    if host.endswith("baidu.com") or host.endswith("zhihu.com") or host.endswith("weibo.com"):
        score -= 30
    if "广告" in snippet or "推广" in snippet:
        score -= 15

    return score


def rank_education_results(results: list[dict[str, str]]) -> list[dict[str, str]]:
    deduplicated: list[dict[str, str]] = []
    seen_keys: set[str] = set()
    for item in results:
        title = _normalize_text(item.get("title", ""))
        snippet = _normalize_text(item.get("snippet", ""))
        url = _normalize_text(item.get("url", ""))
        if not title and not snippet:
            continue
        key = _normalize_text(url or title)
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        deduplicated.append({"title": title, "snippet": snippet, "url": url})

    ranked = sorted(deduplicated, key=_score_result, reverse=True)
    filtered = [item for item in ranked if _score_result(item) >= 30]
    if not filtered:
        filtered = ranked
    return filtered[:DEFAULT_MAX_RESULTS]


def build_facts_summary(results: list[dict[str, str]], question: str) -> dict[str, Any]:
    normalized_question = _normalize_text(question)
    ranked = rank_education_results(results)
    if not ranked:
        return {
            "needs_research": True,
            "facts_summary": [],
            "sources_hint": _build_sources_hint(normalized_question, classify_zhangxuefeng_question(normalized_question), ranked),
            "search_query": normalized_question,
            "search_queries": [normalized_question] if normalized_question else [],
            "evidence": [],
        }

    summary_lines: list[str] = ["已优先保留官方或学校来源，先核实这些信息。"]
    source_lines: list[str] = []
    for item in ranked[:3]:
        title = _normalize_text(item.get("title", ""))
        snippet = _normalize_text(item.get("snippet", ""))
        url = _normalize_text(item.get("url", ""))
        if title or snippet:
            line = " / ".join(part for part in [title, snippet] if part)
            if line:
                summary_lines.append(line)
        host = (urlparse(url).hostname or "").replace("www.", "")
        if host.endswith("gov.cn"):
            source_lines.append("教育考试院 / 政府官网")
        elif host.endswith("edu.cn") or host.endswith(".edu.cn"):
            source_lines.append("学校官网 / 招生网")
        elif host:
            source_lines.append(host)

    return {
        "needs_research": True,
        "facts_summary": _unique_preserve_order(summary_lines),
        "sources_hint": _unique_preserve_order(source_lines) or DEFAULT_SOURCE_HINTS,
        "search_query": normalized_question,
        "search_queries": [normalized_question] if normalized_question else [],
        "evidence": ranked,
    }


async def _fetch_baidu_evidence(query: str) -> list[dict[str, str]]:
    timeout = float(os.getenv("ZHANGXUEFENG_RESEARCH_TIMEOUT", str(DEFAULT_TIMEOUT)) or DEFAULT_TIMEOUT)
    max_results = max(1, min(int(os.getenv("ZHANGXUEFENG_RESEARCH_MAX_RESULTS", str(DEFAULT_MAX_RESULTS)) or DEFAULT_MAX_RESULTS), 10))
    search_url = f"{BAIDU_SEARCH_URL}?wd={quote_plus(query)}&rn={max_results}&ie=utf-8&oq={quote_plus(query)}"
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=timeout), follow_redirects=True) as client:
        response = await client.get(
            search_url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; TokendancerPersonaBot/1.0)",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
        )
        response.raise_for_status()
        return _parse_baidu_results(response.text, limit=max_results)


async def _fetch_custom_evidence(query: str) -> list[dict[str, str]]:
    search_url_template = os.getenv("ZHANGXUEFENG_RESEARCH_SEARCH_URL", "").strip()
    if not search_url_template:
        return []

    timeout = float(os.getenv("ZHANGXUEFENG_RESEARCH_TIMEOUT", str(DEFAULT_TIMEOUT)) or DEFAULT_TIMEOUT)
    search_url = search_url_template.format(query=quote_plus(query), raw_query=query)
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=timeout), follow_redirects=True) as client:
        response = await client.get(
            search_url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; TokendancerPersonaBot/1.0)",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
        )
        response.raise_for_status()
        return _parse_custom_results(response)


def _build_fallback_summary(question: str, question_class: QuestionClass) -> list[str]:
    focus = _infer_education_focus(question)
    if focus == "school_list":
        summary = [
            "先核实目标地区的招生院校名单，再看是否有官方批次与招生简章。",
            "不要把信息流里的推荐直接当成名单，优先看学校官网和教育考试院。",
        ]
    elif focus == "score_line":
        summary = [
            "先核实近三年的录取分数线和位次，再判断能不能报。",
            "不要只看单一年份，要同时看批次、位次和招生计划变化。",
        ]
    elif focus == "major_detail":
        summary = [
            "先核实招生简章、专业介绍和培养方案，再判断值不值。",
            "优先看学校官网和就业质量报告，不要先看营销文案。",
        ]
    elif focus == "employment":
        summary = [
            "先核实就业质量报告、岗位入口和城市机会，再做判断。",
            "方向热不热不是唯一标准，关键是毕业后有没有稳定入口。",
        ]
    elif focus == "policy":
        summary = [
            "先核实教育考试院和学校官网的招生计划，再看政策变化。",
            "不要把旧政策当最新版本，先确认时间和批次。",
        ]
    else:
        summary = [
            "需要先核实最新事实，再做路径判断。",
            "不要把经验判断伪装成最新数据。",
        ]

    if question_class == "hybrid":
        summary.append("混合问题要先拿到事实，再用判断框架做取舍。")
    return _unique_preserve_order(summary)


async def research_education_question(question: str, classification: QuestionClass | None = None) -> dict[str, Any]:
    normalized_question = _normalize_text(question)
    question_class = classification or classify_zhangxuefeng_question(normalized_question)
    needs_research = question_class in {"fact_required", "hybrid"}
    provider_mode = os.getenv("ZHANGXUEFENG_RESEARCH_MODE", "baidu").strip().lower()
    if provider_mode not in {"stub", "baidu", "custom"}:
        provider_mode = "baidu"

    search_queries = build_search_queries(normalized_question, question_class)
    evidence: list[dict[str, str]] = []
    if needs_research:
        try:
            if provider_mode == "stub":
                evidence = []
            elif provider_mode == "custom":
                for query in search_queries or [normalized_question]:
                    evidence.extend(await _fetch_custom_evidence(query))
            else:
                for query in search_queries or [normalized_question]:
                    evidence.extend(await _fetch_baidu_evidence(query))
        except (httpx.HTTPError, ValueError, RuntimeError, httpx.TimeoutException):
            evidence = []

    ranked_evidence = rank_education_results(evidence)
    if ranked_evidence:
        summary_payload = build_facts_summary(ranked_evidence, normalized_question)
        facts_summary = summary_payload["facts_summary"]
        sources_hint = summary_payload["sources_hint"]
    elif needs_research:
        facts_summary = []
        sources_hint = _build_sources_hint(normalized_question, question_class, [])
        # 保留一份可回退的判断清单，但不伪装成已经查到事实。
        summary_payload = {
            "needs_research": True,
            "facts_summary": facts_summary,
            "sources_hint": sources_hint,
            "search_query": normalized_question,
            "search_queries": search_queries,
            "evidence": [],
        }
    else:
        summary_payload = build_facts_summary([], normalized_question)
        facts_summary = summary_payload["facts_summary"]
        sources_hint = summary_payload["sources_hint"]

    result = ResearchResult(
        needs_research=needs_research,
        question_class=question_class,
        facts_summary=facts_summary,
        sources_hint=sources_hint,
        search_query=search_queries[0] if search_queries else normalized_question,
        search_queries=search_queries,
        evidence=ranked_evidence,
    )
    payload = result.as_dict()
    if not payload["facts_summary"] and needs_research:
        payload["sources_hint"] = _build_sources_hint(normalized_question, question_class, ranked_evidence)
    return payload
