from __future__ import annotations

import hashlib
import json
import random
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Any

from sqlalchemy.orm import Session

from app.services.llm_gateway import LLMGatewayError, generate_reply
from app.services.how_to_do_research import research_how_to_do_question
from app.services.text_sanitizer import strip_think_blocks


SECTION_LABELS = {
    "cast": "排盘",
    "chat": "占卜对话",
    "sundial": "日晷",
    "catalog": "六十四卦",
    "songs": "歌诀",
    "detail": "卦象详情",
}

CAST_MODE_LABELS = {
    "manual": "手动输入",
    "character": "汉字起卦",
    "coin": "硬币起卦",
}

FIVE_ELEMENTS = ["木", "火", "土", "金", "水"]

PALACE_ELEMENTS = {
    "乾宫": "金",
    "兑宫": "金",
    "离宫": "火",
    "震宫": "木",
    "巽宫": "木",
    "坎宫": "水",
    "艮宫": "土",
    "坤宫": "土",
}

BRANCH_ELEMENTS = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}

TRIGRAM_NAJIA = {
    "乾": {"inner": ["甲子", "甲寅", "甲辰"], "outer": ["壬午", "壬申", "壬戌"]},
    "兑": {"inner": ["丁巳", "丁卯", "丁丑"], "outer": ["丁亥", "丁酉", "丁未"]},
    "离": {"inner": ["己卯", "己丑", "己亥"], "outer": ["己酉", "己未", "己巳"]},
    "震": {"inner": ["庚子", "庚寅", "庚辰"], "outer": ["庚午", "庚申", "庚戌"]},
    "巽": {"inner": ["辛丑", "辛亥", "辛酉"], "outer": ["辛未", "辛巳", "辛卯"]},
    "坎": {"inner": ["戊寅", "戊辰", "戊午"], "outer": ["戊申", "戊戌", "戊子"]},
    "艮": {"inner": ["丙辰", "丙午", "丙申"], "outer": ["丙戌", "丙子", "丙寅"]},
    "坤": {"inner": ["乙未", "乙巳", "乙卯"], "outer": ["癸丑", "癸亥", "癸酉"]},
}

SIX_SPIRIT_ORDER = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
DAY_STEM_SPIRIT_START = {
    "甲": "青龙",
    "乙": "青龙",
    "丙": "朱雀",
    "丁": "朱雀",
    "戊": "勾陈",
    "己": "螣蛇",
    "庚": "白虎",
    "辛": "白虎",
    "壬": "玄武",
    "癸": "玄武",
}

GUIREN_BY_DAY_STEM = {
    "甲": ("丑", "未"),
    "戊": ("丑", "未"),
    "庚": ("丑", "未"),
    "乙": ("子", "申"),
    "己": ("子", "申"),
    "丙": ("亥", "酉"),
    "丁": ("亥", "酉"),
    "壬": ("卯", "巳"),
    "癸": ("卯", "巳"),
    "辛": ("寅", "午"),
}

YIMA_BY_DAY_BRANCH = {
    "申": "寅",
    "子": "寅",
    "辰": "寅",
    "寅": "申",
    "午": "申",
    "戌": "申",
    "亥": "巳",
    "卯": "巳",
    "未": "巳",
    "巳": "亥",
    "酉": "亥",
    "丑": "亥",
}

YANGREN_BY_DAY_STEM = {
    "甲": "卯",
    "乙": "寅",
    "丙": "午",
    "丁": "巳",
    "戊": "午",
    "己": "巳",
    "庚": "酉",
    "辛": "申",
    "壬": "子",
    "癸": "亥",
}

TRIGRAMS = [
    {"name": "乾", "symbol": "☰", "meaning": "天"},
    {"name": "兑", "symbol": "☱", "meaning": "泽"},
    {"name": "离", "symbol": "☲", "meaning": "火"},
    {"name": "震", "symbol": "☳", "meaning": "雷"},
    {"name": "巽", "symbol": "☴", "meaning": "风"},
    {"name": "坎", "symbol": "☵", "meaning": "水"},
    {"name": "艮", "symbol": "☶", "meaning": "山"},
    {"name": "坤", "symbol": "☷", "meaning": "地"},
]

HEXAGRAM_MAP = {
    "111111": (1, "乾"),
    "000000": (2, "坤"),
    "100010": (3, "屯"),
    "010001": (4, "蒙"),
    "111010": (5, "需"),
    "010111": (6, "讼"),
    "010000": (7, "师"),
    "000010": (8, "比"),
    "111011": (9, "小畜"),
    "110111": (10, "履"),
    "111000": (11, "泰"),
    "000111": (12, "否"),
    "101111": (13, "同人"),
    "111101": (14, "大有"),
    "001000": (15, "谦"),
    "000100": (16, "豫"),
    "100110": (17, "随"),
    "011001": (18, "蛊"),
    "110000": (19, "临"),
    "000011": (20, "观"),
    "100101": (21, "噬嗑"),
    "101001": (22, "贲"),
    "000001": (23, "剥"),
    "100000": (24, "复"),
    "100111": (25, "无妄"),
    "111001": (26, "大畜"),
    "100001": (27, "颐"),
    "011110": (28, "大过"),
    "010010": (29, "坎"),
    "101101": (30, "离"),
    "001110": (31, "咸"),
    "011100": (32, "恒"),
    "001111": (33, "遁"),
    "111100": (34, "大壮"),
    "000101": (35, "晋"),
    "101000": (36, "明夷"),
    "101011": (37, "家人"),
    "110101": (38, "睽"),
    "001010": (39, "蹇"),
    "010100": (40, "解"),
    "110001": (41, "损"),
    "100011": (42, "益"),
    "111110": (43, "夬"),
    "011111": (44, "姤"),
    "000110": (45, "萃"),
    "011000": (46, "升"),
    "010110": (47, "困"),
    "011010": (48, "井"),
    "101110": (49, "革"),
    "011101": (50, "鼎"),
    "100100": (51, "震"),
    "001001": (52, "艮"),
    "001011": (53, "渐"),
    "110100": (54, "归妹"),
    "101100": (55, "丰"),
    "001101": (56, "旅"),
    "011011": (57, "巽"),
    "110110": (58, "兑"),
    "010011": (59, "涣"),
    "110010": (60, "节"),
    "110011": (61, "中孚"),
    "001100": (62, "小过"),
    "101010": (63, "既济"),
    "010101": (64, "未济"),
}

HEXAGRAM_MEANINGS = {
    "乾": "元亨利贞，刚健中正", "坤": "厚德载物，柔顺承载", "屯": "起步艰难，先立根基", "蒙": "启蒙求教，先明边界",
    "需": "等待时机，蓄势再动", "讼": "有争执，先化解冲突", "师": "有组织有纪律，稳住阵脚", "比": "靠拢协作，重在同心",
    "小畜": "小有积蓄，先蓄再发", "履": "步步谨慎，先看规则", "泰": "上下相通，局势顺畅", "否": "上下不交，先收后进",
    "同人": "同心协力，利于共识", "大有": "资源丰厚，宜守成", "谦": "谦受益，低调稳进", "豫": "有喜有动，先定节奏",
    "随": "顺势而为，但别失主见", "蛊": "旧局待修，先整再动", "临": "临近成局，重在把握", "观": "先观察，再决定动作",
    "噬嗑": "有阻则断，需果断处理", "贲": "外在修饰，内核要稳", "剥": "剥落之势，宜保守", "复": "回到起点，重新来过",
    "无妄": "顺其自然，不宜妄动", "大畜": "蓄养力量，耐心等待", "颐": "养身养心，注意入口", "大过": "压力偏大，别硬扛",
    "坎": "险中求通，先保安全", "离": "明而有附，重在清晰", "咸": "感应相通，利于沟通", "恒": "持久之道，贵在稳定",
    "遁": "退一步海阔天空", "大壮": "势能上升，别冲过头", "晋": "进展上升，宜顺势", "明夷": "光被遮蔽，先藏锋",
    "家人": "内在秩序，先顾内里", "睽": "分歧并存，先求对齐", "蹇": "阻碍较多，宜绕行", "解": "困难解开，顺势松绑",
    "损": "有所舍弃，换取长远", "益": "增益之象，利于推进", "夬": "决断之时，别拖延", "姤": "相遇突发，谨慎处理",
    "萃": "聚集成势，利于集中", "升": "稳步上升，循序渐进", "困": "受困受限，先找出口", "井": "资源可用，重在维护",
    "革": "变革更新，先定方向", "鼎": "承载转化，适合定型", "震": "突发变动，先稳住", "艮": "止而不动，先收住",
    "渐": "循序渐进，不可急进", "归妹": "关系不稳，需慎重", "丰": "盛极一时，注意收敛", "旅": "在外求行，先安顿",
    "巽": "渗透推进，柔中有力", "兑": "交流顺畅，利于沟通", "涣": "离散化解，先疏后聚", "节": "有节有度，守住边界",
    "中孚": "诚信内在，沟通更稳", "小过": "小事可成，不宜过大", "既济": "事情已成，注意后续", "未济": "未成之局，先别定论",
}

TRIGRAM_DIRECTION_HINTS = {
    "乾": {"direction": "西北", "scene": "高处、金属边、柜顶、领导位、干燥明亮处"},
    "兑": {"direction": "正西", "scene": "口部高度、桌面、抽屉、金属器具旁、聊天休息处"},
    "离": {"direction": "正南", "scene": "灯下、电子设备旁、明亮处、充电区、热源附近"},
    "震": {"direction": "正东", "scene": "门边、走道、木柜、包袋边、活动频繁处"},
    "巽": {"direction": "东南", "scene": "角落、缝隙、书桌旁、木制家具边、风口附近"},
    "坎": {"direction": "正北", "scene": "低处、水边、洗手台、饮水区、阴暗潮湿处"},
    "艮": {"direction": "东北", "scene": "墙角、床边、柜角、堆放处、静止不动的角位"},
    "坤": {"direction": "西南", "scene": "地面、收纳箱、布艺处、母亲位、成堆杂物旁"},
}

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

HEXAGRAM_SPECS = {
    "乾": {"palace": "乾宫", "tag": "六冲"},
    "姤": {"palace": "乾宫", "tag": "一世"},
    "遁": {"palace": "乾宫", "tag": "二世"},
    "否": {"palace": "乾宫", "tag": "三世"},
    "观": {"palace": "乾宫", "tag": "四世"},
    "剥": {"palace": "乾宫", "tag": "五世"},
    "晋": {"palace": "乾宫", "tag": "游魂"},
    "大有": {"palace": "乾宫", "tag": "归魂"},
    "兑": {"palace": "兑宫", "tag": "六冲"},
    "困": {"palace": "兑宫", "tag": "一世"},
    "萃": {"palace": "兑宫", "tag": "二世"},
    "咸": {"palace": "兑宫", "tag": "三世"},
    "蹇": {"palace": "兑宫", "tag": "四世"},
    "谦": {"palace": "兑宫", "tag": "五世"},
    "小过": {"palace": "兑宫", "tag": "游魂"},
    "归妹": {"palace": "兑宫", "tag": "归魂"},
    "离": {"palace": "离宫", "tag": "六冲"},
    "旅": {"palace": "离宫", "tag": "一世"},
    "鼎": {"palace": "离宫", "tag": "二世"},
    "未济": {"palace": "离宫", "tag": "三世"},
    "蒙": {"palace": "离宫", "tag": "四世"},
    "涣": {"palace": "离宫", "tag": "五世"},
    "讼": {"palace": "离宫", "tag": "游魂"},
    "同人": {"palace": "离宫", "tag": "归魂"},
    "震": {"palace": "震宫", "tag": "六冲"},
    "豫": {"palace": "震宫", "tag": "一世"},
    "解": {"palace": "震宫", "tag": "二世"},
    "恒": {"palace": "震宫", "tag": "三世"},
    "升": {"palace": "震宫", "tag": "四世"},
    "井": {"palace": "震宫", "tag": "五世"},
    "大过": {"palace": "震宫", "tag": "游魂"},
    "随": {"palace": "震宫", "tag": "归魂"},
    "巽": {"palace": "巽宫", "tag": "六冲"},
    "小畜": {"palace": "巽宫", "tag": "一世"},
    "家人": {"palace": "巽宫", "tag": "二世"},
    "益": {"palace": "巽宫", "tag": "三世"},
    "无妄": {"palace": "巽宫", "tag": "四世"},
    "噬嗑": {"palace": "巽宫", "tag": "五世"},
    "颐": {"palace": "巽宫", "tag": "游魂"},
    "蛊": {"palace": "巽宫", "tag": "归魂"},
    "坎": {"palace": "坎宫", "tag": "六冲"},
    "节": {"palace": "坎宫", "tag": "一世"},
    "屯": {"palace": "坎宫", "tag": "二世"},
    "既济": {"palace": "坎宫", "tag": "三世"},
    "革": {"palace": "坎宫", "tag": "四世"},
    "丰": {"palace": "坎宫", "tag": "五世"},
    "明夷": {"palace": "坎宫", "tag": "游魂"},
    "师": {"palace": "坎宫", "tag": "归魂"},
    "艮": {"palace": "艮宫", "tag": "六冲"},
    "贲": {"palace": "艮宫", "tag": "一世"},
    "大畜": {"palace": "艮宫", "tag": "二世"},
    "损": {"palace": "艮宫", "tag": "三世"},
    "睽": {"palace": "艮宫", "tag": "四世"},
    "履": {"palace": "艮宫", "tag": "五世"},
    "中孚": {"palace": "艮宫", "tag": "游魂"},
    "渐": {"palace": "艮宫", "tag": "归魂"},
    "坤": {"palace": "坤宫", "tag": "六冲"},
    "复": {"palace": "坤宫", "tag": "一世"},
    "临": {"palace": "坤宫", "tag": "二世"},
    "泰": {"palace": "坤宫", "tag": "三世"},
    "大壮": {"palace": "坤宫", "tag": "四世"},
    "夬": {"palace": "坤宫", "tag": "五世"},
    "需": {"palace": "坤宫", "tag": "游魂"},
    "比": {"palace": "坤宫", "tag": "归魂"},
}

SHI_YING_MAP = {
    "六冲": (6, 3),
    "一世": (1, 4),
    "二世": (2, 5),
    "三世": (3, 6),
    "四世": (4, 1),
    "五世": (5, 2),
    "游魂": (4, 1),
    "归魂": (2, 6),
}

DISPLAY_TAG_OVERRIDES = {
    "复": "六合",
}

GROUNDING_SNIPPETS = [
    "六爻更适合先看局势变化，再决定进退。",
    "有动爻时，先看变化位，再看整体趋势。",
    "变卦代表后势，不要只盯着本卦。",
    "时间起卦适合快速问事，手动起卦适合更明确的起卦过程。",
]

QUESTION_TYPE_RULES = [
    {
        "type": "做空交易",
        "keywords": ["做空", "买跌", "空单", "下跌", "反弹", "止盈", "止损", "出空", "换月", "行情", "标的"],
        "focus": ["先分清对用户而言上涨是利还是害", "重点看压制上涨与放大下跌的力量", "日辰月令对关键爻的助力要单独讲清"],
    },
    {
        "type": "普通求财",
        "keywords": ["财运", "求财", "赚钱", "利润", "转款", "到账", "收入", "回款"],
        "focus": ["重点看财爻、世应与应期", "判断钱能否落实以及何时到位", "分清眼前阻力与最终结果"],
    },
    {
        "type": "关系情感",
        "keywords": ["感情", "复合", "暧昧", "对象", "伴侣", "前任", "关系", "婚姻"],
        "focus": ["重点看世应、合冲与动爻态度", "判断关系是在靠近还是疏离", "结论要兼顾情绪安抚与边界提醒"],
    },
    {
        "type": "工作事务",
        "keywords": ["工作", "项目", "合作", "老板", "客户", "合同", "过户", "材料", "手续", "offer"],
        "focus": ["重点看父母爻、官鬼爻与文书流程", "判断事情能不能推进与卡点在哪", "建议要落到下一步动作"],
    },
    {
        "type": "催收纠纷",
        "keywords": ["催债", "施压", "纠纷", "起诉", "报警", "家人", "威胁", "债务"],
        "focus": ["重点看世应强弱与对方动作真假", "区分施压姿态和真实落地风险", "结论里要保留风险提醒"],
    },
    {
        "type": "居住去留",
        "keywords": ["住宿", "搬家", "续住", "租房", "居所", "去留"],
        "focus": ["重点看世爻、财爻与变卦后势", "判断维持现状还是更换更稳", "避免只给空泛情绪建议"],
    },
    {
        "type": "失物方位",
        "keywords": ["失物", "找东西", "找物", "寻物", "寻人", "方位", "方向", "在哪", "哪里", "何处", "位置"],
        "focus": ["重点看用神落位、世应、动爻和上下卦方位", "直接回答更偏哪个方向、哪类空间、是高是低、是明是暗", "不要讲空泛局势，先把位置线索说清楚"],
    },
]

CATEGORY_ROUTE_RULES = {
    "出行平安": {
        "type": "出行动向",
        "focus": ["重点看世爻、父母爻、官鬼爻与路途动象", "判断这一趟宜行还是宜缓，以及风险点在哪", "如果问时间，要把应期和窗口说清楚"],
    },
    "能否出行": {
        "type": "出行动向",
        "focus": ["重点看世爻、父母爻、官鬼爻与路途动象", "判断这一趟宜行还是宜缓，以及风险点在哪", "如果问时间，要把应期和窗口说清楚"],
    },
    "何时出行": {
        "type": "出行动向",
        "focus": ["重点看世爻、父母爻、官鬼爻与路途动象", "判断这一趟宜行还是宜缓，以及风险点在哪", "如果问时间，要把应期和窗口说清楚"],
    },
    "行人归来": {
        "type": "出行动向",
        "focus": ["重点看世应、驿马与动爻方向", "判断对方回不回、何时有消息、路上是否有阻", "结论里要直接说快慢和阻点"],
    },
    "出国远行": {
        "type": "出行动向",
        "focus": ["重点看世爻、父母爻、官鬼爻与路途动象", "判断这一趟宜行还是宜缓，以及风险点在哪", "如果问时间，要把应期和窗口说清楚"],
    },
    "求财": {
        "type": "普通求财",
        "focus": ["重点看财爻、世应与应期", "判断钱能否落实以及何时到位", "分清眼前阻力与最终结果"],
    },
    "投资买卖": {
        "type": "投资经营",
        "focus": ["重点看财爻、兄弟爻、官鬼爻和动爻方向", "判断这笔买卖是宜进、宜守还是宜收", "要把波动、风险和时机分开讲清楚"],
    },
    "开店经营": {
        "type": "投资经营",
        "focus": ["重点看财爻、父母爻、世爻与经营气势", "判断生意是能开、能守还是要缓", "要落到现金流、节奏和风险提醒"],
    },
    "求官": {
        "type": "职业仕途",
        "focus": ["重点看官鬼爻、父母爻、世爻与文书流程", "判断有没有机会、卡点在哪、是争取还是先守", "建议要落到动作而不是空泛鼓励"],
    },
    "求职": {
        "type": "职业仕途",
        "focus": ["重点看官鬼爻、父母爻、世爻与文书流程", "判断有没有机会、卡点在哪、是争取还是先守", "建议要落到动作而不是空泛鼓励"],
    },
    "升迁调动": {
        "type": "职业仕途",
        "focus": ["重点看官鬼爻、父母爻、世爻与文书流程", "判断有没有机会、卡点在哪、是争取还是先守", "建议要落到动作而不是空泛鼓励"],
    },
    "面试入职": {
        "type": "职业仕途",
        "focus": ["重点看官鬼爻、父母爻、世爻与文书流程", "判断有没有机会、卡点在哪、是争取还是先守", "建议要落到动作而不是空泛鼓励"],
    },
    "工作推进": {
        "type": "工作事务",
        "focus": ["重点看父母爻、官鬼爻与文书流程", "判断事情能不能推进与卡点在哪", "建议要落到下一步动作"],
    },
    "项目进度": {
        "type": "工作事务",
        "focus": ["重点看父母爻、官鬼爻与文书流程", "判断事情能不能推进与卡点在哪", "建议要落到下一步动作"],
    },
    "考试测验": {
        "type": "学业考试",
        "focus": ["重点看父母爻、官鬼爻、子孙爻与世爻状态", "判断能不能过、差在哪、补什么最要紧", "如果问成绩或结果，要讲清时间和发挥状态"],
    },
    "学业文书": {
        "type": "学业考试",
        "focus": ["重点看父母爻、官鬼爻、子孙爻与世爻状态", "判断能不能过、差在哪、补什么最要紧", "如果问成绩或结果，要讲清时间和发挥状态"],
    },
    "感情回应": {
        "type": "关系情感",
        "focus": ["重点看世应、合冲与动爻态度", "判断关系是在靠近还是疏离", "结论要兼顾情绪安抚与边界提醒"],
    },
    "感情复合": {
        "type": "关系情感",
        "focus": ["重点看世应、合冲与动爻态度", "判断关系是在靠近还是疏离", "结论要兼顾情绪安抚与边界提醒"],
    },
    "婚姻复合": {
        "type": "关系情感",
        "focus": ["重点看世应、合冲与动爻态度", "判断关系是在靠近还是疏离", "结论要兼顾情绪安抚与边界提醒"],
    },
    "表白推进": {
        "type": "关系情感",
        "focus": ["重点看世应、合冲与动爻态度", "判断关系是在靠近还是疏离", "结论要兼顾情绪安抚与边界提醒"],
    },
    "朋友关系": {
        "type": "关系情感",
        "focus": ["重点看世应、合冲与动爻态度", "判断关系是在靠近还是疏离", "结论要兼顾情绪安抚与边界提醒"],
    },
    "家宅关系": {
        "type": "家宅家庭",
        "focus": ["重点看世爻、父母爻、应爻与家宅位置", "判断是宜守、宜动还是先缓", "要把家庭关系和居住状态分开讲清楚"],
    },
    "父母长辈": {
        "type": "家宅家庭",
        "focus": ["重点看父母爻、世应与动爻态度", "判断长辈这边是支持、牵制还是担忧", "建议要兼顾现实礼数和情绪安抚"],
    },
    "子女教育": {
        "type": "家宅家庭",
        "focus": ["重点看子孙爻、父母爻、世应与动爻方向", "判断问题出在节奏、沟通还是环境", "建议要落到怎么管、怎么松、怎么稳"],
    },
    "搬家迁移": {
        "type": "居住去留",
        "focus": ["重点看世爻、财爻与变卦后势", "判断维持现状还是更换更稳", "避免只给空泛情绪建议"],
    },
    "健康疾病": {
        "type": "健康生育",
        "focus": ["重点看官鬼爻、子孙爻、世爻与父母爻", "判断问题是急是缓、在表还是在里", "表达上要谨慎安抚，不替代现实就医判断"],
    },
    "生产怀孕": {
        "type": "健康生育",
        "focus": ["重点看子孙爻、世爻、父母爻与官鬼爻", "判断当前是稳、需养还是有阻", "表达上要谨慎安抚，不替代现实医疗判断"],
    },
    "诉讼官非": {
        "type": "诉讼官非",
        "focus": ["重点看世应强弱、官鬼爻、父母爻与动爻攻守", "判断事情是虚惊、施压还是真有落地风险", "结论里要明确风险等级和应对顺序"],
    },
    "失物寻人": {
        "type": "失物方位",
        "focus": ["重点看用神落位、世应、动爻和上下卦方位", "直接回答更偏哪个方向、哪类空间、是高是低、是明是暗", "不要讲空泛局势，先把位置线索说清楚"],
    },
    "合作合伙": {
        "type": "合作交易",
        "focus": ["重点看世应、父母爻、兄弟爻与动爻攻守", "判断能不能成、谁更主动、后续会不会生变", "结论要落到合作边界和下一步动作"],
    },
    "交易签约": {
        "type": "合作交易",
        "focus": ["重点看世应、父母爻、兄弟爻与动爻攻守", "判断能不能成、谁更主动、后续会不会生变", "结论要落到合作边界和下一步动作"],
    },
    "借贷还款": {
        "type": "合作交易",
        "focus": ["重点看财爻、父母爻、世应和兑现时点", "判断钱能不能回、会不会拖、该催还是该缓", "要直接说兑现概率和阻点"],
    },
}

ANSWER_SKELETONS = {
    "出行动向": {
        "professional_terms": ["世应", "动爻", "驿马", "官鬼", "应期"],
        "core_conclusion": "先直接说此行宜动、宜缓还是先不动，并点明是眼前有阻还是后面转顺。",
        "interaction_focus": "重点讲世爻、父母爻、官鬼爻和动爻之间的牵动，必要时带一句驿马或合冲。",
        "time_focus": "时间段要说成近、中、后三个层次，不要只甩一个模糊日子。",
        "action_focus": "建议落到要不要出发、要不要改期、要不要先补条件。",
        "closing_question_style": "最后反问用户：更想问成行时间，还是更想问这一路哪里最容易出岔子？",
    },
    "普通求财": {
        "professional_terms": ["财爻", "世应", "月令", "旬空", "应期"],
        "core_conclusion": "先直接说财能不能落袋，是眼前就见、要等一等，还是容易落空。",
        "interaction_focus": "重点讲财爻、世爻、应爻和阻力位，不要把满盘六亲都铺开。",
        "time_focus": "时间推演优先说应期、出空、合起、填实这类节点。",
        "action_focus": "建议落到该催、该守、该缓还是该分批看。",
        "closing_question_style": "最后反问用户：你更在意这笔钱能不能到，还是更在意它大概什么时候到？",
    },
    "做空交易": {
        "professional_terms": ["财爻", "兄弟爻", "官鬼", "月令", "回头克"],
        "core_conclusion": "先直接说空头更占优、偏震荡，还是反手风险更大。",
        "interaction_focus": "重点讲财爻、兄弟爻、官鬼和动爻之间谁在压谁，不要按普通求财口径解释。",
        "time_focus": "把换月、出空、节气或具体交易日说成明确窗口。",
        "action_focus": "建议落到宜持有、宜减仓、宜止盈还是先观望。",
        "closing_question_style": "最后反问用户：你下一步更想看具体时间窗口，还是更想看这单的风险边界？",
    },
    "投资经营": {
        "professional_terms": ["财爻", "兄弟爻", "父母爻", "世爻", "应期"],
        "core_conclusion": "先直接说这笔经营或投资更偏可做、可守，还是先别急着进。",
        "interaction_focus": "重点讲财路、成本、阻力和后劲，不要只讲情绪判断。",
        "time_focus": "说清楚当前窗口是试探期、承压期还是放量期。",
        "action_focus": "建议落到先投多少、先试多久、哪里要设防守线。",
        "closing_question_style": "最后反问用户：你更想继续看投入时机，还是想看这件事后面能不能放大？",
    },
    "职业仕途": {
        "professional_terms": ["官鬼", "父母爻", "世爻", "应爻", "文书"],
        "core_conclusion": "先直接说这件事有没有机会，是可争、可等，还是暂时卡住。",
        "interaction_focus": "重点讲官鬼爻、父母爻、世应和流程位，不要空谈运气。",
        "time_focus": "时间上优先说消息窗口、流程推进点和转机点。",
        "action_focus": "建议落到该主动争取、补材料、等消息还是换方向。",
        "closing_question_style": "最后反问用户：你更想看这次有没有结果，还是更想看卡点到底在谁身上？",
    },
    "工作事务": {
        "professional_terms": ["父母爻", "官鬼", "世应", "动爻", "合冲"],
        "core_conclusion": "先直接说这件事能不能推得动，是卡在流程、人，还是节奏。",
        "interaction_focus": "重点讲父母爻、官鬼爻和世应关系，必要时点明谁是阻点。",
        "time_focus": "时间上说清楚眼前卡点、下一窗口和拖久后的变化。",
        "action_focus": "建议落到先催哪一步、先补什么、先跟谁对齐。",
        "closing_question_style": "最后反问用户：你更想继续看推进时机，还是想看这件事最该先处理哪一个卡点？",
    },
    "学业考试": {
        "professional_terms": ["父母爻", "官鬼", "子孙", "世爻", "应期"],
        "core_conclusion": "先直接说这次更偏能过、悬着，还是要再补一口气。",
        "interaction_focus": "重点讲父母爻、官鬼爻、子孙爻和世爻状态，不要满盘平均发力。",
        "time_focus": "时间上优先说临考、发榜、结果兑现的节点。",
        "action_focus": "建议落到该补哪块、稳心态还是改策略。",
        "closing_question_style": "最后反问用户：你更想看最后结果，还是更想看接下来最该补哪一块？",
    },
    "关系情感": {
        "professional_terms": ["世应", "合冲", "动爻", "月令", "应期"],
        "core_conclusion": "先直接说关系是在靠近、僵着，还是在慢慢往外走。",
        "interaction_focus": "重点讲世应、合冲和动爻态度，少讲空泛心灵鸡汤。",
        "time_focus": "时间上说清楚近期态度变化和后面能不能回暖。",
        "action_focus": "建议落到该推进、该缓一缓、该表态还是该收边界。",
        "closing_question_style": "最后反问用户：你更想继续看对方现在的态度，还是更想看这段关系后面还有没有推进点？",
    },
    "家宅家庭": {
        "professional_terms": ["父母爻", "世应", "家宅位", "动爻", "合冲"],
        "core_conclusion": "先直接说这件事更偏宜守、宜动，还是先缓一缓。",
        "interaction_focus": "重点讲父母爻、世应和家宅相关动位，把情绪和现实分开讲。",
        "time_focus": "时间上说清楚眼前矛盾会不会放大，后面有没有转松。",
        "action_focus": "建议落到先沟通、先观察，还是先换动作。",
        "closing_question_style": "最后反问用户：你更想继续看家里这层关系，还是更想看现实环境这层变化？",
    },
    "居住去留": {
        "professional_terms": ["世爻", "父母爻", "财爻", "变卦", "六冲"],
        "core_conclusion": "先直接说更偏搬、更偏守，还是方向已定但时机未到。",
        "interaction_focus": "重点讲世爻、父母爻、财爻和变卦后势，不要模棱两可。",
        "time_focus": "时间上说清楚现在、再等一阵、真正适合动的时候分别是什么感觉。",
        "action_focus": "建议落到先看房、先观察，还是先稳住别急动。",
        "closing_question_style": "最后反问用户：你更想继续看搬的时机，还是更想看现在这个住处真正让你不舒服的点？",
    },
    "健康生育": {
        "professional_terms": ["官鬼", "子孙", "父母爻", "世爻", "旺衰"],
        "core_conclusion": "先直接说这事更偏急、偏缓，还是以调养观察为主。",
        "interaction_focus": "重点讲官鬼、子孙、父母爻和世爻强弱，不渲染恐惧。",
        "time_focus": "时间上说清楚是短期波动还是要看一个恢复周期。",
        "action_focus": "建议落到休养、复查、调整节奏，并提醒以现实医疗判断为先。",
        "closing_question_style": "最后反问用户：你更想继续看恢复节奏，还是更想看这件事眼下最该避开的风险点？",
    },
    "诉讼官非": {
        "professional_terms": ["世应", "官鬼", "父母爻", "动爻", "攻守"],
        "core_conclusion": "先直接说对方更像施压、真要落地，还是虚张声势中带一点风险。",
        "interaction_focus": "重点讲世应强弱、官鬼爻和父母爻的攻守关系。",
        "time_focus": "时间上说清楚近期会不会升级、什么时候容易见真章。",
        "action_focus": "建议落到先留证据、先沟通、先守边界还是先做现实准备。",
        "closing_question_style": "最后反问用户：你更想继续看对方会不会真的动作，还是更想看你这边该先怎么防？",
    },
    "失物方位": {
        "professional_terms": ["用神", "世应", "动爻", "上下卦", "方位"],
        "core_conclusion": "先直接说主方向，再补1到3个环境线索，比如高低、明暗、角落或柜边。",
        "interaction_focus": "重点讲用神落位、世应和上下卦方位，不讲大而空的局势。",
        "time_focus": "时间上只简单说眼下找得到、晚一点更显，还是已经被移动过。",
        "action_focus": "建议落到先找哪个方向、先翻哪类位置、是不是要回想谁动过。",
        "closing_question_style": "最后反问用户：你要不要把这个东西的大概形状和最后一次出现的位置再告诉我一下？",
    },
    "合作交易": {
        "professional_terms": ["世应", "父母爻", "兄弟爻", "财爻", "兑现"],
        "core_conclusion": "先直接说能不能成、能不能回，还是会拖、会变。",
        "interaction_focus": "重点讲世应、财爻、父母爻和兄弟爻的牵制关系。",
        "time_focus": "时间上说清楚是近期能落、要拖，还是会反复。",
        "action_focus": "建议落到该谈条件、该催款、该留证还是该先观望。",
        "closing_question_style": "最后反问用户：你更想继续看成不成，还是更想看后面最容易卡在哪个环节？",
    },
    "催收纠纷": {
        "professional_terms": ["世应", "官鬼", "父母爻", "动爻", "虚实"],
        "core_conclusion": "先直接说对方更偏施压还是真会落地动作。",
        "interaction_focus": "重点讲世应强弱、官鬼动向和父母爻的现实落地能力。",
        "time_focus": "时间上说清楚短期会不会升级，还是过阵子就缓。",
        "action_focus": "建议落到先稳、先防、先留痕，不空谈。",
        "closing_question_style": "最后反问用户：你更想继续看对方动作真假，还是更想看你这边该先怎么稳住？",
    },
    "通用问事": {
        "professional_terms": ["动爻", "世应", "月令", "旬空", "变卦"],
        "core_conclusion": "先直接说这件事眼下更偏顺、偏阻，还是先观望。",
        "interaction_focus": "重点讲盘里最关键的两三组关系，不硬套旧模板。",
        "time_focus": "时间上只讲最关键的变化窗口。",
        "action_focus": "建议落到下一步最该做什么。",
        "closing_question_style": "最后反问用户：你更想把这件事往结果上看，还是往时间点上看得更细一点？",
    },
}

GENERIC_TEMPLATE_MARKERS = [
    "这卦先看",
    "眼下不必先慌",
    "先顺着局势判断进退",
    "事情不是完全没有路",
    "只是不必先慌",
    "怎么应对：先按眼前最关键的一步处理",
]

QUESTION_TYPE_RELEVANCE_MARKERS = {
    "出行动向": ["出行", "归来", "改期", "成行", "路上", "驿马", "启程"],
    "普通求财": ["财", "钱", "到账", "兑现", "入袋", "应期", "回款"],
    "做空交易": ["做空", "下跌", "反弹", "空单", "减仓", "止盈", "止损"],
    "投资经营": ["投资", "经营", "投入", "回本", "现金流", "试单", "开店"],
    "职业仕途": ["面试", "入职", "录用", "机会", "岗位", "文书", "消息"],
    "工作事务": ["推进", "项目", "流程", "对齐", "卡点", "补材料", "进度"],
    "学业考试": ["考试", "成绩", "分数", "高考", "上岸", "录取", "发挥", "复习"],
    "关系情感": ["关系", "态度", "靠近", "复合", "表白", "回应", "边界"],
    "家宅家庭": ["家里", "家庭", "长辈", "孩子", "沟通", "家宅", "关系"],
    "居住去留": ["搬家", "续住", "住处", "看房", "换地方", "居住", "时机"],
    "健康生育": ["恢复", "复查", "休养", "身体", "怀孕", "生产", "调养"],
    "诉讼官非": ["施压", "落地", "证据", "官非", "风险", "升级", "纠纷"],
    "失物方位": ["东", "西", "南", "北", "方向", "角落", "柜", "抽屉", "高处", "低处"],
    "合作交易": ["合作", "签约", "催款", "回款", "兑现", "成不成", "环节"],
    "催收纠纷": ["催收", "施压", "动作", "真假", "留痕", "防守", "升级"],
}

DIRECT_DECISION_MARKERS = ["更偏", "偏", "宜", "不宜", "能", "不能", "会", "不会", "先缓", "先别", "可", "不太"]
LOCATION_ANSWER_MARKERS = ["东", "西", "南", "北", "东北", "东南", "西北", "西南", "正东", "正西", "正南", "正北", "柜", "抽屉", "床", "桌", "角落", "包里", "高处", "低处", "门口"]
SCOPE_NUDGE_VARIANTS = [
    "如果你想让我看得更细致一点，可以再补一句细节，我继续帮你分析。",
    "要是你想让我判断得更明确一点，可以继续补背景，我再顺着这卦往下看。",
    "如果你觉得这里还不够具体，可以把关键细节接着告诉我，我再帮你细分析一层。",
    "要是你想把这件事看得更准确一点，可以继续补两句细节，我再往下判断。",
]

MAX_HOW_TO_DO_COMPLETION_RETRIES = 1

LINE_GUIDANCE = [
    "起点和底盘，先看稳不稳。",
    "基础承接位，先看配合。",
    "变化开始显现，别硬顶。",
    "外部推动与阻力，要看清。",
    "核心主位，决定当前走势。",
    "收尾与结果，别把话说满。",
]

SIX_SPIRITS = ["玄武", "白虎", "螣蛇", "勾陈", "朱雀", "青龙"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
RELATIONS = ["父母", "兄弟", "子孙", "妻财", "官鬼"]

PALACE_GUA_CATALOG = [
    (
        "乾宫",
        [
            ("乾为天", "六冲", "乾"),
            ("天风姤", "一世", "姤"),
            ("天山遁", "二世", "遁"),
            ("天地否", "三世", "否"),
            ("风地观", "四世", "观"),
            ("山地剥", "五世", "剥"),
            ("火地晋", "游魂", "晋"),
            ("火天大有", "归魂", "大有"),
        ],
    ),
    (
        "兑宫",
        [
            ("兑为泽", "六冲", "兑"),
            ("泽水困", "一世", "困"),
            ("泽地萃", "二世", "萃"),
            ("泽山咸", "三世", "咸"),
            ("水山蹇", "四世", "蹇"),
            ("地山谦", "五世", "谦"),
            ("雷山小过", "游魂", "小过"),
            ("雷泽归妹", "归魂", "归妹"),
        ],
    ),
    (
        "离宫",
        [
            ("离为火", "六冲", "离"),
            ("火山旅", "一世", "旅"),
            ("火风鼎", "二世", "鼎"),
            ("火水未济", "三世", "未济"),
            ("山水蒙", "四世", "蒙"),
            ("风水涣", "五世", "涣"),
            ("天水讼", "游魂", "讼"),
            ("天火同人", "归魂", "同人"),
        ],
    ),
    (
        "震宫",
        [
            ("震为雷", "六冲", "震"),
            ("雷地豫", "一世", "豫"),
            ("雷水解", "二世", "解"),
            ("雷风恒", "三世", "恒"),
            ("地风升", "四世", "升"),
            ("水风井", "五世", "井"),
            ("泽风大过", "游魂", "大过"),
            ("泽雷随", "归魂", "随"),
        ],
    ),
    (
        "巽宫",
        [
            ("巽为风", "六冲", "巽"),
            ("风天小畜", "一世", "小畜"),
            ("风火家人", "二世", "家人"),
            ("风雷益", "三世", "益"),
            ("天雷无妄", "四世", "无妄"),
            ("火雷噬嗑", "五世", "噬嗑"),
            ("山雷颐", "游魂", "颐"),
            ("山风蛊", "归魂", "蛊"),
        ],
    ),
    (
        "坎宫",
        [
            ("坎为水", "六冲", "坎"),
            ("水泽节", "一世", "节"),
            ("水雷屯", "二世", "屯"),
            ("水火既济", "三世", "既济"),
            ("泽火革", "四世", "革"),
            ("雷火丰", "五世", "丰"),
            ("地火明夷", "游魂", "明夷"),
            ("地水师", "归魂", "师"),
        ],
    ),
    (
        "艮宫",
        [
            ("艮为山", "六冲", "艮"),
            ("山火贲", "一世", "贲"),
            ("山天大畜", "二世", "大畜"),
            ("山泽损", "三世", "损"),
            ("火泽睽", "四世", "睽"),
            ("天泽履", "五世", "履"),
            ("风泽中孚", "游魂", "中孚"),
            ("风山渐", "归魂", "渐"),
        ],
    ),
    (
        "坤宫",
        [
            ("坤为地", "六冲", "坤"),
            ("地雷复", "一世", "复"),
            ("地泽临", "二世", "临"),
            ("地天泰", "三世", "泰"),
            ("雷天大壮", "四世", "大壮"),
            ("泽天夬", "五世", "夬"),
            ("水天需", "游魂", "需"),
            ("水地比", "归魂", "比"),
        ],
    ),
]

HEXAGRAM_NAME_TO_BINARY = {name: binary for binary, (_, name) in HEXAGRAM_MAP.items()}

ALL_GUA_CATALOG = []
for palace_index, (palace, guas) in enumerate(PALACE_GUA_CATALOG):
    for order, (name, tag, meaning_key) in enumerate(guas, start=1):
        number = palace_index * 8 + order
        binary = HEXAGRAM_NAME_TO_BINARY.get(meaning_key, "")
        ALL_GUA_CATALOG.append(
            {
                "number": number,
                "name": name,
                "meaning": HEXAGRAM_MEANINGS.get(meaning_key, "顺势而行"),
                "binary": binary,
                "palace": palace,
                "tag": tag,
            }
        )


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _clean_divination_output(text: str) -> str:
    cleaned = strip_think_blocks(str(text or ""))
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.replace("**", "").replace("__", "").replace("`", "")
    cleaned = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*\*\s+", "- ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    paragraphs = [item.strip() for item in re.split(r"\n{2,}", cleaned) if item.strip()]
    deduped: list[str] = []
    seen: set[str] = set()
    for paragraph in paragraphs:
        key = re.sub(r"\s+", "", paragraph)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(paragraph)
    return "\n\n".join(deduped).strip()


def _build_divination_grounding(base_result: dict[str, Any]) -> dict[str, Any]:
    raw = base_result.get("raw_result", {}) or {}
    line_details = raw.get("line_details") or []
    transformed_line_details = raw.get("transformed_line_details") or []
    return {
        "question": _normalize_text(base_result.get("question")),
        "summary": _normalize_text(base_result.get("summary")),
        "cards": base_result.get("cards", []),
        "hexagram": {
            "name": raw.get("hexagram_name"),
            "meaning": raw.get("hexagram_meaning"),
            "palace": raw.get("hexagram_palace"),
            "tag": raw.get("hexagram_tag"),
            "panel_title": raw.get("panel_title"),
            "panel_subtitle": raw.get("panel_subtitle"),
            "upper_trigram": raw.get("upper_trigram"),
            "lower_trigram": raw.get("lower_trigram"),
            "changing_lines": raw.get("changing_lines", []),
            "transformed_hexagram": raw.get("transformed_hexagram"),
        },
        "time_context": {
            "day_label": raw.get("day_label"),
            "ganzhi_line": raw.get("ganzhi_line"),
            "shensha": raw.get("shensha", {}),
        },
        "line_details": [
            {
                "position": item.get("position"),
                "six_spirit": item.get("six_spirit"),
                "relation": item.get("relation"),
                "stem_branch": item.get("stem_branch"),
                "bar_text": item.get("bar_text"),
                "change_mark": item.get("change_mark"),
                "shi_ying": item.get("shi_ying"),
                "hidden_spirit": item.get("hidden_spirit"),
            }
            for item in line_details
        ],
        "transformed_line_details": [
            {
                "position": item.get("position"),
                "six_spirit": item.get("six_spirit"),
                "relation": item.get("relation"),
                "stem_branch": item.get("stem_branch"),
                "bar_text": item.get("bar_text"),
                "change_mark": item.get("change_mark"),
                "shi_ying": item.get("shi_ying"),
                "hidden_spirit": item.get("hidden_spirit"),
            }
            for item in transformed_line_details
        ],
    }


def _build_symbol_snapshot(grounding: dict[str, Any]) -> dict[str, Any]:
    line_details = grounding.get("line_details") or []
    transformed_line_details = grounding.get("transformed_line_details") or []
    key_lines: list[dict[str, Any]] = []
    for item in line_details:
        if item.get("change_mark") or item.get("shi_ying") or item.get("hidden_spirit"):
            key_lines.append(
                {
                    "position": item.get("position"),
                    "relation": item.get("relation"),
                    "six_spirit": item.get("six_spirit"),
                    "stem_branch": item.get("stem_branch"),
                    "shi_ying": item.get("shi_ying"),
                    "change_mark": item.get("change_mark"),
                    "hidden_spirit": item.get("hidden_spirit"),
                }
            )
    if not key_lines:
        key_lines = [
            {
                "position": item.get("position"),
                "relation": item.get("relation"),
                "six_spirit": item.get("six_spirit"),
                "stem_branch": item.get("stem_branch"),
                "shi_ying": item.get("shi_ying"),
                "change_mark": item.get("change_mark"),
                "hidden_spirit": item.get("hidden_spirit"),
            }
            for item in line_details[:3]
        ]
    return {
        "hexagram_name": _normalize_text((grounding.get("hexagram") or {}).get("name")),
        "hexagram_tag": _normalize_text((grounding.get("hexagram") or {}).get("tag")),
        "hexagram_palace": _normalize_text((grounding.get("hexagram") or {}).get("palace")),
        "changing_lines": list((grounding.get("hexagram") or {}).get("changing_lines") or []),
        "transformed_hexagram": (grounding.get("hexagram") or {}).get("transformed_hexagram") or {},
        "key_lines": key_lines,
        "transformed_key_lines": [
            {
                "position": item.get("position"),
                "relation": item.get("relation"),
                "six_spirit": item.get("six_spirit"),
                "stem_branch": item.get("stem_branch"),
                "shi_ying": item.get("shi_ying"),
                "change_mark": item.get("change_mark"),
            }
            for item in transformed_line_details
            if item.get("position") in {entry.get("position") for entry in key_lines}
        ],
    }


def _build_relation_network_summary(grounding: dict[str, Any]) -> dict[str, Any]:
    line_details = grounding.get("line_details") or []
    moving_lines = [
        item for item in line_details if _normalize_text(item.get("change_mark"))
    ]
    shi_line = next((item for item in line_details if _normalize_text(item.get("shi_ying")) == "世"), {})
    ying_line = next((item for item in line_details if _normalize_text(item.get("shi_ying")) == "应"), {})
    return {
        "moving_line_count": len(moving_lines),
        "moving_line_positions": [item.get("position") for item in moving_lines],
        "shi_line": {
            "position": shi_line.get("position"),
            "relation": shi_line.get("relation"),
            "stem_branch": shi_line.get("stem_branch"),
            "six_spirit": shi_line.get("six_spirit"),
        },
        "ying_line": {
            "position": ying_line.get("position"),
            "relation": ying_line.get("relation"),
            "stem_branch": ying_line.get("stem_branch"),
            "six_spirit": ying_line.get("six_spirit"),
        },
        "network_focus": [
            "先看动爻牵动哪些位置与六亲关系。",
            "再看五行生克、合冲刑害如何在盘里串起来。",
            "再看世应是否形成主导互动。",
            "最后看变卦是否强化或反转当前主线。",
        ],
    }


def _build_core_conflict_summary(grounding: dict[str, Any]) -> dict[str, Any]:
    line_details = grounding.get("line_details") or []
    moving_lines = [
        {
            "position": item.get("position"),
            "relation": item.get("relation"),
            "stem_branch": item.get("stem_branch"),
            "six_spirit": item.get("six_spirit"),
            "change_mark": item.get("change_mark"),
            "shi_ying": item.get("shi_ying"),
        }
        for item in line_details
        if _normalize_text(item.get("change_mark"))
    ]
    if not moving_lines:
        moving_lines = [
            {
                "position": item.get("position"),
                "relation": item.get("relation"),
                "stem_branch": item.get("stem_branch"),
                "six_spirit": item.get("six_spirit"),
                "change_mark": item.get("change_mark"),
                "shi_ying": item.get("shi_ying"),
            }
            for item in line_details[:2]
        ]
    return {
        "dominant_conflicts": moving_lines,
        "instruction": "先从动爻、世应、变卦里提取主导矛盾，不要把所有关系一股脑平铺出来。",
    }


def _build_time_evolution_summary(grounding: dict[str, Any]) -> dict[str, Any]:
    time_context = grounding.get("time_context", {}) or {}
    changing_lines = list((grounding.get("hexagram") or {}).get("changing_lines") or [])
    return {
        "cast_time": {
            "day_label": _normalize_text(time_context.get("day_label")),
            "ganzhi_line": _normalize_text(time_context.get("ganzhi_line")),
        },
        "phase_hints": [
            "先以起卦时点为零点，不要脱离这个时间坐标。",
            "把月建、日辰、旬空当成外部状态参数，看它们怎么改写盘内力量。",
            "有动爻时要把变化趋势放进时间线里看。",
            "如果用户追问某天、某节气、某前后窗口，再把该时间点作为额外变量代入。",
        ],
        "changing_lines": changing_lines,
    }


def _build_symbol_system_summary(grounding: dict[str, Any]) -> dict[str, Any]:
    hexagram = grounding.get("hexagram", {}) or {}
    return {
        "source_symbols": [
            "本卦与变卦的爻象",
            "六亲、世应、六神、地支",
            "动爻与变爻信息",
            "月建、日辰、旬空、神煞",
        ],
        "hexagram_identity": {
            "name": _normalize_text(hexagram.get("name")),
            "tag": _normalize_text(hexagram.get("tag")),
            "palace": _normalize_text(hexagram.get("palace")),
            "upper_trigram": _normalize_text(hexagram.get("upper_trigram")),
            "lower_trigram": _normalize_text(hexagram.get("lower_trigram")),
        },
        "instruction": "先把盘面看成一套符号数据，不要一上来就直接映射到吉凶结论。",
    }


def _build_state_evolution_summary(grounding: dict[str, Any]) -> dict[str, Any]:
    time_context = grounding.get("time_context", {}) or {}
    return {
        "external_state_inputs": [
            _normalize_text(time_context.get("ganzhi_line")),
            "月建 / 日辰 / 旬空",
            "动爻、化进化退、回头生克",
        ],
        "state_engine_rules": [
            "先区分静爻和动爻，动爻是变化源。",
            "再看旺衰、旬空、月破是否让某些符号变强或暂时失效。",
            "最后看动爻变爻之间是回头生、回头克，还是趋势延续。",
        ],
        "instruction": "把系统看成随时间变化的状态机，而不是静态截图。",
    }


def _build_answer_skeleton(question_type: str) -> dict[str, Any]:
    skeleton = ANSWER_SKELETONS.get(question_type) or ANSWER_SKELETONS["通用问事"]
    return {
        "tone": "专业、稳、有人味，术语要点到为止，不要像教科书。",
        "length_rule": "首轮尽量控制在 220 到 360 字；追问补充尽量控制在 140 到 260 字。",
        "section_contract": {
            "核心结论": skeleton["core_conclusion"],
            "关键互动分析": skeleton["interaction_focus"],
            "时间推演": skeleton["time_focus"],
            "实际意义": skeleton["action_focus"],
        },
        "professional_terms": skeleton["professional_terms"],
        "closing_question_style": skeleton["closing_question_style"],
        "instruction": "结尾必须自然反问一句，引导用户补最关键的下一条信息。",
    }


def _extract_relevance_markers(question_type: str, question: str) -> list[str]:
    markers = list(QUESTION_TYPE_RELEVANCE_MARKERS.get(question_type, []))
    normalized_question = _normalize_text(question)
    dynamic_pairs = [
        ("高考", ["高考", "分数", "成绩"]),
        ("考研", ["考研", "复试", "上岸"]),
        ("考试", ["考试", "成绩", "发挥"]),
        ("录取", ["录取", "上岸"]),
        ("搬家", ["搬家", "续住", "住处"]),
        ("续住", ["续住", "搬家", "住处"]),
        ("找东西", ["方向", "位置", "角落"]),
        ("失物", ["方向", "位置", "角落"]),
        ("签约", ["签约", "条件", "落地"]),
    ]
    for needle, extras in dynamic_pairs:
        if needle in normalized_question:
            markers.extend(extras)
    if re.search(r"\d+\s*分", normalized_question):
        markers.extend(["分数", "成绩"])
    return list(dict.fromkeys(marker for marker in markers if marker))


def _looks_like_generic_template(answer: str) -> bool:
    normalized = _normalize_text(answer)
    hit_count = sum(1 for marker in GENERIC_TEMPLATE_MARKERS if marker in normalized)
    return hit_count >= 2


def _answer_needs_repair(
    *,
    question: str,
    protocol: dict[str, Any],
    answer: str,
) -> tuple[bool, str]:
    normalized_answer = _normalize_text(answer)
    if not normalized_answer:
        return True, "回答为空"

    question_type = _normalize_text(protocol.get("question_type"))
    meta = protocol.get("question_type_meta", {}) or {}
    contract = protocol.get("answer_contract", {}) or {}
    reasons: list[str] = []

    if meta.get("coverage") == "high" and _looks_like_generic_template(normalized_answer):
        reasons.append("回答落成了通用空壳模板")

    relevance_markers = _extract_relevance_markers(question_type, question)
    lacks_relevance = bool(meta.get("coverage") == "high" and relevance_markers and not any(marker in normalized_answer for marker in relevance_markers))
    if lacks_relevance and (_looks_like_generic_template(normalized_answer) or len(normalized_answer) <= 120):
        reasons.append("没有回应当前分类最核心的语义")

    first_paragraph = re.split(r"\n{2,}|\n", normalized_answer, maxsplit=1)[0]
    if contract.get("binary_decision") and not any(marker in first_paragraph for marker in DIRECT_DECISION_MARKERS):
        reasons.append("二选一或是非题没有先给明确倾向")

    if contract.get("direction_first") and not any(marker in first_paragraph for marker in LOCATION_ANSWER_MARKERS):
        reasons.append("方位题没有先直接回答方向或环境")

    return bool(reasons), "；".join(reasons)


async def _continue_llm_completion(
    *,
    db: Session | None,
    base_messages: list[dict[str, str]],
    existing_content: str,
) -> tuple[str, str]:
    appended = existing_content.strip()
    model_used = ""
    for _ in range(MAX_HOW_TO_DO_COMPLETION_RETRIES):
        follow_messages = [
            *base_messages,
            {"role": "assistant", "content": appended},
            {
                "role": "user",
                "content": "你刚才的回答被截断了。不要重复前文，只从刚才停住的那一句继续往下说，把剩下内容补完并自然收住。",
            },
        ]
        reply = await generate_reply(follow_messages, db=db)
        continued = str(reply.get("content") or "").strip()
        if not continued:
            break
        model_used = str(reply.get("model") or model_used)
        appended = f"{appended}\n\n{continued}".strip()
        finish_reason = str(reply.get("finish_reason") or "")
        if not _should_continue_generation(appended, finish_reason):
            break
    return appended, model_used


async def _repair_divination_answer(
    *,
    db: Session | None,
    question: str,
    protocol: dict[str, Any],
    grounding: dict[str, Any],
    rejected_answer: str,
    repair_reason: str,
    research_context: str = "",
    conversation_history: list[dict[str, str]] | None = None,
    is_followup: bool = False,
) -> tuple[str, str]:
    system_prompt = (
        "你是 Tokendancer 的六爻解卦师。上一版回答因为跑题或过于空泛而被判定无效。"
        "这一次必须严格围绕当前问题类型、当前卦盘和当前问念重答。"
        "先按符号层、关系层、状态层看卦，再映射到用户问题。"
        "不要再输出通用模板句，不要再说'先看主势'、'先顺着局势判断进退'这类空话。"
        "如果是高覆盖分类，必须回应这一类问题最该看的卦位、术语和现实判断。"
        "如果是二选一或是非题，第一句直接给明确倾向。"
        "如果是失物或方位题，第一句直接给方向和环境线索。"
        "语气要像稳定的专业解卦师，带少量术语，但不要像系统面板。"
        "不要输出 markdown、编号清单、代码块。"
    )
    user_prompt = json.dumps(
        {
            "question": question,
            "question_type": protocol.get("question_type"),
            "repair_reason": repair_reason,
            "rejected_answer": rejected_answer,
            "grounding": grounding,
            "protocol": protocol,
            "research_context": research_context,
            "conversation_history": conversation_history or [],
            "mode": "followup" if is_followup else "first_reply",
            "output_goal": "基于同一卦盘重写一版紧扣分类、紧扣问句、紧扣卦位的有效答案。",
        },
        ensure_ascii=False,
        indent=2,
    )
    reply = await generate_reply(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        db=db,
    )
    content = str(reply.get("content") or "").strip()
    model_used = str(reply.get("model") or "")
    finish_reason = str(reply.get("finish_reason") or "")
    if _should_continue_generation(content, finish_reason):
        content, continued_model = await _continue_llm_completion(
            db=db,
            base_messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            existing_content=content,
        )
        model_used = continued_model or model_used
    return content.strip(), model_used


def _build_direction_reference(grounding: dict[str, Any]) -> dict[str, Any]:
    hexagram = grounding.get("hexagram", {}) or {}
    transformed = hexagram.get("transformed_hexagram") or {}
    upper = _normalize_text(hexagram.get("upper_trigram"))
    lower = _normalize_text(hexagram.get("lower_trigram"))
    transformed_upper = _normalize_text(transformed.get("upper_trigram"))
    transformed_lower = _normalize_text(transformed.get("lower_trigram"))

    current_bias = [
        {
            "trigram": name,
            "direction": TRIGRAM_DIRECTION_HINTS.get(name, {}).get("direction", ""),
            "scene": TRIGRAM_DIRECTION_HINTS.get(name, {}).get("scene", ""),
        }
        for name in [upper, lower]
        if name
    ]
    transformed_bias = [
        {
            "trigram": name,
            "direction": TRIGRAM_DIRECTION_HINTS.get(name, {}).get("direction", ""),
            "scene": TRIGRAM_DIRECTION_HINTS.get(name, {}).get("scene", ""),
        }
        for name in [transformed_upper, transformed_lower]
        if name
    ]
    return {
        "bagua_direction_map": TRIGRAM_DIRECTION_HINTS,
        "current_hexagram_bias": current_bias,
        "transformed_hexagram_bias": transformed_bias,
        "instruction": "如果用户问方位、位置、找东西或寻人，先直接给方向和环境线索，再解释依据。",
    }


def _infer_answer_contract(
    question: str,
    question_type: str,
    conversation_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    normalized_question = _normalize_text(question)
    recent_history = " ".join(_normalize_text(item.get("content")) for item in (conversation_history or [])[-4:])
    combined = f"{normalized_question} {recent_history}".strip()
    follow_up_expand = normalized_question in {"继续", "展开", "接着说", "详细说", "细说", "继续说"} or (
        len(normalized_question) <= 8 and any(token in normalized_question for token in ["继续", "展开", "细说"])
    )
    binary_decision = any(
        token in combined
        for token in ["要不要", "该不该", "能不能", "会不会", "搬还是不搬", "续住还是搬家", "比较好还是", "到底要不要", "直接说"]
    )
    direction_first = question_type == "失物方位" or any(
        token in combined for token in ["方位", "方向", "在哪里", "在哪", "何处", "位置", "找东西", "失物"]
    )
    return {
        "follow_up_expand": follow_up_expand,
        "binary_decision": binary_decision,
        "direction_first": direction_first,
        "response_rules": [
            "默认只展开最关键的结论和依据，不重复前面已经说过的大段内容。",
            "如果是二选一或是非题，核心结论第一句必须直接给明确倾向。",
            "如果是失物方位题，核心结论第一句必须直接回答更偏哪个方向，再补1到3个环境线索。",
            "如果用户只是说继续或展开，默认补上一轮没说透的部分，不重讲完整五段。",
        ],
        "length_rule": "首轮尽量控制在 260 到 420 字；追问补充尽量控制在 180 到 300 字。",
    }


def _compact_history_for_prompt(conversation_history: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    compacted: list[dict[str, str]] = []
    for item in (conversation_history or [])[-6:]:
        role = _normalize_text(item.get("role")) or "user"
        content = _normalize_text(item.get("content"))
        if not content:
            continue
        if role == "assistant":
            paragraphs = [part.strip() for part in re.split(r"\n{2,}", content) if part.strip()]
            content = " / ".join(paragraphs[:2])[:220]
        else:
            content = content[:180]
        compacted.append({"role": role, "content": content})
    return compacted


def _assistant_reply_count(conversation_history: list[dict[str, Any]] | None) -> int:
    return sum(
        1
        for item in (conversation_history or [])
        if _normalize_text(item.get("role")) == "assistant" and _normalize_text(item.get("content"))
    )


def _should_append_followup_question(
    question: str,
    conversation_history: list[dict[str, Any]] | None = None,
    cast_context: dict[str, Any] | None = None,
) -> bool:
    reply_index = _assistant_reply_count(conversation_history) + 1
    if reply_index >= 4:
        return False
    if reply_index > 3:
        return False
    seed_source = "||".join(
        [
            _normalize_text(question),
            _normalize_text(((cast_context or {}).get("raw_result") or {}).get("hexagram_name")),
            str(reply_index),
        ]
    )
    rng = random.Random(_stable_seed(seed_source))
    return rng.random() < 0.6


def _should_append_scope_nudge(
    question: str,
    conversation_history: list[dict[str, Any]] | None = None,
    cast_context: dict[str, Any] | None = None,
) -> bool:
    reply_index = _assistant_reply_count(conversation_history) + 1
    if reply_index > 2:
        return False
    seed_source = "||".join(
        [
            _normalize_text(question),
            _normalize_text(((cast_context or {}).get("raw_result") or {}).get("hexagram_name")),
            str(reply_index),
            "scope-nudge",
        ]
    )
    rng = random.Random(_stable_seed(seed_source))
    return rng.random() < 0.5


def _append_scope_nudge(text: str, nudge: str) -> str:
    normalized = text.strip()
    if not normalized or not nudge.strip():
        return normalized
    paragraphs = [item.strip() for item in re.split(r"\n{2,}", normalized) if item.strip()]
    if not paragraphs:
        return nudge.strip()
    last = paragraphs[-1]
    if "？" in last or last.endswith("?"):
        paragraphs.insert(len(paragraphs) - 1, nudge.strip())
    else:
        paragraphs.append(nudge.strip())
    return "\n\n".join(paragraphs).strip()


def _should_continue_generation(content: str, finish_reason: str) -> bool:
    normalized = _normalize_text(content)
    if not normalized:
        return False
    if finish_reason.lower() in {"length", "max_tokens"}:
        return True
    if content.endswith(("，", "、", "：", "（", "(", "/", "-", "—")):
        return True
    tail = normalized[-12:]
    if any(marker in tail for marker in ("月令", "日建", "再看", "时间推演", "关键互动分析", "实际意义", "风险提醒")) and not normalized.endswith(("。", "！", "？")):
        return True
    return False


def _remove_trailing_question(text: str) -> str:
    paragraphs = [item.strip() for item in re.split(r"\n{2,}", text) if item.strip()]
    if not paragraphs:
        return text.strip()
    last = paragraphs[-1]
    if "？" in last or last.endswith("?"):
        parts = re.split(r"(?<=[。！？!?])", last)
        kept_parts: list[str] = []
        for part in parts:
            trimmed = part.strip()
            if not trimmed:
                continue
            if "？" in trimmed or trimmed.endswith("?"):
                break
            kept_parts.append(trimmed)
        if kept_parts:
            paragraphs[-1] = "".join(kept_parts).strip()
        else:
            paragraphs = paragraphs[:-1]
    return "\n\n".join(paragraphs).strip()


def _format_how_to_do_research_context(research: dict[str, Any] | None) -> str:
    if not isinstance(research, dict):
        return ""
    summary_lines = [
        _normalize_text(line)
        for line in (research.get("facts_summary") or [])
        if _normalize_text(line)
    ]
    sources_hint = [
        _normalize_text(line)
        for line in (research.get("sources_hint") or [])
        if _normalize_text(line)
    ]
    search_queries = [
        _normalize_text(line)
        for line in (research.get("search_queries") or [])
        if _normalize_text(line)
    ]
    research_kind = _normalize_text(research.get("research_kind"))
    parts: list[str] = []
    if research_kind:
        parts.append(f"联网研究类型：{research_kind}")
    adaptive_reason = _normalize_text(research.get("adaptive_reason"))
    if adaptive_reason:
        parts.append(f"联网补充原因：{adaptive_reason}")
    if search_queries:
        parts.append("联网检索词：")
        parts.extend(f"- {line}" for line in search_queries[:3])
    if summary_lines:
        parts.append("联网核实摘要：")
        parts.extend(f"- {line}" for line in summary_lines[:4])
    if sources_hint:
        parts.append("联网参考来源：")
        parts.extend(f"- {line}" for line in sources_hint[:4])
    return "\n".join(parts).strip()


def _infer_question_type(question: Any = "", category: Any = "", *texts: Any) -> dict[str, Any]:
    normalized_category = _normalize_text(category)
    if normalized_category and normalized_category in CATEGORY_ROUTE_RULES:
        route = CATEGORY_ROUTE_RULES[normalized_category]
        return {
            "type": route["type"],
            "focus": list(route["focus"]),
            "matched": True,
            "matched_keywords": [normalized_category],
            "coverage": "high",
            "match_source": "category",
        }

    haystack = " ".join(
        _normalize_text(text)
        for text in [question, category, *texts]
        if _normalize_text(text)
    )
    for rule in QUESTION_TYPE_RULES:
        if any(keyword in haystack for keyword in rule["keywords"]):
            return {
                "type": rule["type"],
                "focus": list(rule["focus"]),
                "matched": True,
                "matched_keywords": [keyword for keyword in rule["keywords"] if keyword in haystack][:5],
                "coverage": "high",
                "match_source": "keywords",
            }
    return {
        "type": "通用问事",
        "focus": ["先判断用户真正关心的结果是什么", "只展开最关键的3到4个卦象关系", "结论必须落到可执行建议"],
        "matched": False,
        "matched_keywords": [],
        "coverage": "low",
        "match_source": "fallback",
    }


def _build_interpretation_protocol(
    question: str,
    category: str,
    grounding: dict[str, Any],
    conversation_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    question_type = _infer_question_type(
        question,
        category,
        *(item.get("content") for item in (conversation_history or [])),
    )
    time_context = grounding.get("time_context", {}) or {}
    hexagram = grounding.get("hexagram", {}) or {}
    return {
        "framework_name": "符号解析 -> 关系建模 -> 主线提取 -> 时间推演 -> 问题映射 -> 决策输出",
        "framework_layers": {
            "hexagram_native_layer": [
                "先把卦象当成符号系统处理，不先急着断吉凶。",
                "先做符号解析、关系建模、主线提取和时间推演。",
                "先理解卦本身怎么动，再映射到用户问题。",
            ],
            "question_mapping_layer": [
                "识别用户问的到底是什么问题。",
                "先定义什么对用户是利，什么对用户是害。",
                "最后才把卦势映射成结论、风险和建议。",
            ],
            "symbol_relation_state_layer": [
                "符号层：先识别本卦、变卦、六亲、世应、六神、地支这些基础符号。",
                "关系层：再看生克、合冲、刑害怎么把关键爻连起来。",
                "状态层：最后看月建、日辰、旬空、动变如何改写强弱和趋势。",
            ],
        },
        "question_type": question_type["type"],
        "question_focus": question_type["focus"],
        "question_type_meta": {
            "matched": question_type.get("matched", False),
            "coverage": question_type.get("coverage", "low"),
            "matched_keywords": question_type.get("matched_keywords", []),
            "instruction": "如果没命中现成问题类型，不要硬套旧模板，而要回到卦象结构本身重新建立判断标准。",
        },
        "problem_definition": {
            "core_question": _normalize_text(question),
            "category": _normalize_text(category),
            "instruction": "先锁定用户真正想问的结果，再建立利弊判断标准。",
        },
        "symbol_system": _build_symbol_system_summary(grounding),
        "symbol_parsing": _build_symbol_snapshot(grounding),
        "relation_modeling": _build_relation_network_summary(grounding),
        "core_conflict_extraction": _build_core_conflict_summary(grounding),
        "time_evolution": _build_time_evolution_summary(grounding),
        "state_evolution": _build_state_evolution_summary(grounding),
        "direction_reference": _build_direction_reference(grounding),
        "answer_contract": _infer_answer_contract(question, question_type["type"], conversation_history),
        "answer_skeleton": _build_answer_skeleton(question_type["type"]),
        "time_alignment": {
            "must_follow_cast_time": True,
            "day_label": _normalize_text(time_context.get("day_label")),
            "ganzhi_line": _normalize_text(time_context.get("ganzhi_line")),
            "instruction": "先按起卦时间对应的日辰、月令、节气判断，不要自行改用别的日期。",
        },
        "analysis_steps": [
            "第一步先做卦象本体层分析：符号解析、关系建模、主线提取、时间推演。",
            "第二步再做问题映射层分析：识别问题类型，定义利弊标准，再映射结论。",
            "如果问题类型命中不足，退回到符号层、关系层、状态层重新建模，再用联网事实补足现实背景。",
            "只围绕本卦、动爻、变卦、六神、六亲、世应、六合六冲、旬空、神煞做判断。",
            "从盘里挑最关键的3到4组关系展开，不要把满盘信息平铺给用户。",
            "最后必须落到操作建议、风险提醒和边界说明。",
        ],
        "answer_shape": [
            "核心结论",
            "关键互动分析",
            "时间推演 / 阶段特征",
            "实际意义 / 怎么应对",
            "风险提醒 / 安一句心",
        ],
        "style_rules": [
            "像真正解卦师，不像系统面板。",
            "先安抚，再判断。",
            "二选一问题要直接说倾向，不要模棱两可。",
            "失物方位问题要先说方向和环境，不要先讲大道理。",
            "用户追问继续时，只补新信息，不把前文完整重说。",
            "术语要有，但别堆；每次抓 2 到 4 个最关键术语就够了。",
            "单条回答不要过长，结尾要自然反问一句。",
            "不要暴露内部推理、搜索、校准过程。",
            "不要输出 markdown 标记、标题井号、代码块、表格。",
        ],
        "current_hexagram": {
            "name": hexagram.get("name"),
            "tag": hexagram.get("tag"),
            "palace": hexagram.get("palace"),
            "changing_lines": hexagram.get("changing_lines", []),
            "transformed_hexagram": hexagram.get("transformed_hexagram"),
        },
    }


def _stable_seed(*parts: Any) -> int:
    joined = "||".join(_normalize_text(part) for part in parts if _normalize_text(part))
    if not joined:
        joined = "liu-yao"
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _make_rng(*parts: Any) -> random.Random:
    return random.Random(_stable_seed(*parts))


def _line_value_from_back_count(back_count: int) -> int:
    mapping = {0: 6, 1: 7, 2: 8, 3: 9}
    return mapping.get(back_count, 8)


def _true_random_line_value() -> int:
    rng = random.SystemRandom()
    back_count = sum(rng.randint(0, 1) for _ in range(3))
    return _line_value_from_back_count(back_count)


def _parse_cast_datetime(value: str) -> datetime:
    normalized = _normalize_text(value)
    tz = ZoneInfo("Asia/Shanghai")
    if not normalized:
        return datetime.now(tz)
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(normalized, fmt).replace(tzinfo=tz)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=tz)
    except ValueError:
        return datetime.now(tz)


def _sexagenary_name(index: int) -> str:
    return f"{STEMS[index % 10]}{BRANCHES[index % 12]}"


def _year_ganzhi(dt: datetime) -> str:
    adjusted_year = dt.year - 1 if (dt.month, dt.day) < (2, 4) else dt.year
    return _sexagenary_name((adjusted_year - 1984) % 60)


def _month_branch_index(dt: datetime) -> int:
    mapping = {
        1: 1,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 6,
        7: 7,
        8: 8,
        9: 9,
        10: 10,
        11: 11,
        12: 0,
    }
    branch_index = mapping.get(dt.month, 1)
    if dt.month == 1 and (dt.month, dt.day) < (2, 4):
        branch_index = 1
    return branch_index


def _month_ganzhi(dt: datetime) -> str:
    year_stem = _year_ganzhi(dt)[0]
    first_stem_map = {
        "甲": "丙",
        "己": "丙",
        "乙": "戊",
        "庚": "戊",
        "丙": "庚",
        "辛": "庚",
        "丁": "壬",
        "壬": "壬",
        "戊": "甲",
        "癸": "甲",
    }
    first_stem = first_stem_map[year_stem]
    branch_index = _month_branch_index(dt)
    month_offset = (branch_index - 2) % 12
    stem_index = (STEMS.index(first_stem) + month_offset) % 10
    return f"{STEMS[stem_index]}{BRANCHES[branch_index]}"


def _day_ganzhi(dt: datetime) -> str:
    jdn = dt.toordinal() + 1721424
    return _sexagenary_name((jdn + 49) % 60)


def _hour_branch_index(dt: datetime) -> int:
    return ((dt.hour + 1) // 2) % 12


def _hour_ganzhi(dt: datetime) -> str:
    day_stem = _day_ganzhi(dt)[0]
    first_stem_map = {
        "甲": "甲",
        "己": "甲",
        "乙": "丙",
        "庚": "丙",
        "丙": "戊",
        "辛": "戊",
        "丁": "庚",
        "壬": "庚",
        "戊": "壬",
        "癸": "壬",
    }
    first_stem = first_stem_map[day_stem]
    branch_index = _hour_branch_index(dt)
    stem_index = (STEMS.index(first_stem) + branch_index) % 10
    return f"{STEMS[stem_index]}{BRANCHES[branch_index]}"


def _xunkong(dt: datetime) -> str:
    day_index = (dt.toordinal() + 1721424 + 49) % 60
    groups = [
        ("戌", "亥"),
        ("申", "酉"),
        ("午", "未"),
        ("辰", "巳"),
        ("寅", "卯"),
        ("子", "丑"),
    ]
    empty_a, empty_b = groups[day_index // 10]
    return f"旬空{empty_a}{empty_b}"


def _ganzhi_line(dt: datetime) -> str:
    year = _year_ganzhi(dt)
    month = _month_ganzhi(dt)
    day = _day_ganzhi(dt)
    hour = _hour_ganzhi(dt)
    return f"{year}年{month}月{day}日{hour}时({_xunkong(dt)})"


def _line_text(position: int, yin_yang: str, is_changing: bool) -> str:
    prefix = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"][position - 1]
    return f"{prefix}：{'阳' if yin_yang == '阳' else '阴'}{'（动）' if is_changing else ''}"


def _shi_ying_positions(hexagram_name: str) -> tuple[int, int]:
    spec = HEXAGRAM_SPECS.get(hexagram_name, {})
    tag = spec.get("tag", "")
    return SHI_YING_MAP.get(tag, (0, 0))


def _display_tag_for(hexagram_name: str, raw_tag: str) -> str:
    return DISPLAY_TAG_OVERRIDES.get(hexagram_name, raw_tag)


def _generates(source: str, target: str) -> bool:
    return {
        "木": "火",
        "火": "土",
        "土": "金",
        "金": "水",
        "水": "木",
    }.get(source) == target


def _controls(source: str, target: str) -> bool:
    return {
        "木": "土",
        "土": "水",
        "水": "火",
        "火": "金",
        "金": "木",
    }.get(source) == target


def _bar_text(yin_yang: str) -> str:
    return "▅▅▅" if yin_yang == "阳" else "▅ ▅"


def _relation_for(palace_element: str, line_element: str) -> str:
    if palace_element == line_element:
        return "兄弟"
    if _generates(line_element, palace_element):
        return "父母"
    if _generates(palace_element, line_element):
        return "子孙"
    if _controls(palace_element, line_element):
        return "妻财"
    if _controls(line_element, palace_element):
        return "官鬼"
    return "兄弟"


def _hexagram_trigrams(hexagram_name: str) -> tuple[str, str]:
    binary = HEXAGRAM_NAME_TO_BINARY.get(hexagram_name, "")
    if len(binary) != 6:
        return "乾", "乾"
    lower_binary = binary[:3]
    upper_binary = binary[3:]
    lower = TRIGRAMS[_trigram_index([{"yin_yang": "阳" if ch == "1" else "阴"} for ch in lower_binary])]["name"]
    upper = TRIGRAMS[_trigram_index([{"yin_yang": "阳" if ch == "1" else "阴"} for ch in upper_binary])]["name"]
    return lower, upper


def _hexagram_static_lines(hexagram_name: str) -> list[dict[str, Any]]:
    spec = HEXAGRAM_SPECS.get(hexagram_name, {"palace": "乾宫", "tag": ""})
    palace_element = PALACE_ELEMENTS.get(spec["palace"], "金")
    lower, upper = _hexagram_trigrams(hexagram_name)
    lower_najia = TRIGRAM_NAJIA[lower]["inner"]
    upper_najia = TRIGRAM_NAJIA[upper]["outer"]
    static_lines: list[dict[str, Any]] = []
    for position in range(1, 7):
        stem_branch = lower_najia[position - 1] if position <= 3 else upper_najia[position - 4]
        branch = stem_branch[-1]
        line_element = BRANCH_ELEMENTS.get(branch, "土")
        static_lines.append(
            {
                "position": position,
                "stem_branch": stem_branch,
                "element": line_element,
                "relation": _relation_for(palace_element, line_element),
            }
        )
    return static_lines


def _six_spirits_for_day(day_stem: str) -> list[str]:
    start = DAY_STEM_SPIRIT_START.get(day_stem, "青龙")
    start_index = SIX_SPIRIT_ORDER.index(start)
    return [SIX_SPIRIT_ORDER[(start_index + offset) % len(SIX_SPIRIT_ORDER)] for offset in range(6)]


def _hidden_spirits_for(hexagram_name: str, line_infos: list[dict[str, Any]]) -> dict[int, str]:
    spec = HEXAGRAM_SPECS.get(hexagram_name, {"palace": "乾宫"})
    pure_hexagram = next(
        (
            meaning_key
            for palace, guas in PALACE_GUA_CATALOG
            if palace == spec["palace"]
            for _, _, meaning_key in guas[:1]
        ),
        hexagram_name,
    )
    palace_lines = _hexagram_static_lines(pure_hexagram)
    current_relations = {item["relation"] for item in line_infos}
    missing_relations = set(RELATIONS) - current_relations
    hidden_map: dict[int, str] = {}
    for current, palace_line in zip(line_infos, palace_lines):
        if palace_line["relation"] in missing_relations and palace_line["relation"] != current["relation"]:
            hidden_map[current["position"]] = f"{palace_line['relation']}{palace_line['stem_branch']}{palace_line['element']}"
    return hidden_map


def _shensha_for(dt: datetime, line_details: list[dict[str, Any]], shi_position: int) -> dict[str, str]:
    day_gz = _day_ganzhi(dt)
    day_stem = day_gz[0]
    day_branch = day_gz[1]
    guiren_a, guiren_b = GUIREN_BY_DAY_STEM.get(day_stem, ("—", "—"))
    guashen = "—"
    if 1 <= shi_position <= len(line_details):
        guashen = line_details[shi_position - 1]["stem_branch"][-1]
    return {
        "卦身": guashen,
        "贵人": f"{guiren_a}、{guiren_b}",
        "驿马": YIMA_BY_DAY_BRANCH.get(day_branch, "—"),
        "羊刃": YANGREN_BY_DAY_STEM.get(day_stem, "—"),
    }


def _build_line_detail(
    position: int,
    line: dict[str, Any],
    static_line: dict[str, Any],
    six_spirit: str,
    shi_position: int = 0,
    ying_position: int = 0,
    hidden_spirit: str = "",
) -> dict[str, Any]:
    change_mark = ""
    if line["is_changing"]:
        change_mark = "o" if line["yin_yang"] == "阳" else "x"
    return {
        "position": position,
        "position_name": line["position_name"],
        "text": line["text"],
        "guidance": line["guidance"],
        "is_changing": line["is_changing"],
        "yin_yang": line["yin_yang"],
        "bar_text": _bar_text(line["yin_yang"]),
        "change_mark": change_mark,
        "six_spirit": six_spirit,
        "relation": static_line["relation"],
        "stem_branch": static_line["stem_branch"],
        "nayin": "",
        "hidden_spirit": hidden_spirit,
        "shi_ying": "世" if position == shi_position else "应" if position == ying_position else "",
    }


def _binary_from_lines(lines: list[dict[str, Any]]) -> str:
    return "".join("1" if item["yin_yang"] == "阳" else "0" for item in lines)


def _trigram_index(lines: list[dict[str, Any]]) -> int:
    binary = "".join("1" if item["yin_yang"] == "阳" else "0" for item in lines)
    mapping = {"111": 0, "110": 1, "101": 2, "100": 3, "011": 4, "010": 5, "001": 6, "000": 7}
    return mapping.get(binary, 0)


def _hexagram_lookup(binary: str) -> tuple[int, str]:
    return HEXAGRAM_MAP.get(binary, (1, "乾"))


def _hexagram_meaning(name: str) -> str:
    return HEXAGRAM_MEANINGS.get(name, "顺势而行，先观察再动作")


def _build_mutual_hexagram(lines: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(lines) < 5:
        return None
    upper_bits = "".join("1" if item["yin_yang"] == "阳" else "0" for item in lines[2:5])
    lower_bits = "".join("1" if item["yin_yang"] == "阳" else "0" for item in lines[1:4])
    if len(upper_bits) != 3 or len(lower_bits) != 3:
        return None
    upper = TRIGRAMS[_trigram_index([{"yin_yang": "阳" if ch == "1" else "阴"} for ch in upper_bits])]
    lower = TRIGRAMS[_trigram_index([{"yin_yang": "阳" if ch == "1" else "阴"} for ch in lower_bits])]
    hexagram_number, name = _hexagram_lookup(upper_bits + lower_bits)
    return {
        "hexagram_number": hexagram_number,
        "name": name,
        "meaning": _hexagram_meaning(name),
        "upper_trigram": upper["name"],
        "lower_trigram": lower["name"],
    }


def _build_lines(seed: str, mode: str, cast_mode: str, question: str, source_text: str = "", manual_lines: list[int] | None = None) -> list[dict[str, Any]]:
    rng = _make_rng(seed, mode, cast_mode, question, source_text)
    lines: list[dict[str, Any]] = []
    manual_lines = manual_lines or []
    for position in range(1, 7):
      # 6/7/8/9 代表老阴、少阳、少阴、老阳
        if cast_mode == "manual":
            if position <= len(manual_lines) and manual_lines[position - 1] in {6, 7, 8, 9}:
                value = manual_lines[position - 1]
            else:
                value = _true_random_line_value()
        elif cast_mode == "character":
            base = sum(ord(ch) for ch in source_text or question or seed) + position * 17
            value = [6, 7, 8, 9][base % 4]
        else:
            value = _true_random_line_value()
        is_yang = value in {7, 9}
        is_changing = value in {6, 9}
        lines.append(
            {
                "position": position,
                "position_name": ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"][position - 1],
                "value": value,
                "is_changing": is_changing,
                "yin_yang": "阳" if is_yang else "阴",
                "text": _line_text(position, "阳" if is_yang else "阴", is_changing),
                "guidance": LINE_GUIDANCE[position - 1],
            }
        )
    return lines


def _build_cast_result(question: str, category: str, cast_mode: str, cast_seed: str, source_text: str = "", manual_lines: list[int] | None = None) -> dict[str, Any]:
    seed_value = cast_seed or datetime.now().isoformat(timespec="seconds")
    cast_dt = _parse_cast_datetime(seed_value)
    lines = _build_lines(seed_value, "cast", cast_mode, question, source_text, manual_lines=manual_lines)
    binary = _binary_from_lines(lines)
    hexagram_number, name = _hexagram_lookup(binary)
    upper = TRIGRAMS[_trigram_index(lines[3:])]
    lower = TRIGRAMS[_trigram_index(lines[:3])]
    changing_lines = [item["position"] for item in lines if item["is_changing"]]
    mutual_hexagram = _build_mutual_hexagram(lines)
    hexagram_spec = HEXAGRAM_SPECS.get(name, {"palace": "未知宫", "tag": ""})
    shi_position, ying_position = _shi_ying_positions(name)
    now = cast_dt
    day_ganzhi = _day_ganzhi(now)
    day_stem = day_ganzhi[0]
    six_spirits = _six_spirits_for_day(day_stem)
    static_lines = _hexagram_static_lines(name)
    hidden_spirits = _hidden_spirits_for(name, static_lines)
    transformed_hexagram = None
    transformed_line_details: list[dict[str, Any]] = []
    if changing_lines:
        transformed_lines = [
            {
                **item,
                "is_changing": False,
                "yin_yang": ("阴" if item["yin_yang"] == "阳" else "阳") if item["value"] in {6, 9} else item["yin_yang"],
                "text": _line_text(
                    item["position"],
                    ("阴" if item["yin_yang"] == "阳" else "阳") if item["value"] in {6, 9} else item["yin_yang"],
                    False,
                ),
            }
            for item in lines
        ]
        transformed_binary = _binary_from_lines(transformed_lines)
        transformed_number, transformed_name = _hexagram_lookup(transformed_binary)
        transformed_upper = TRIGRAMS[_trigram_index(transformed_lines[3:])]
        transformed_lower = TRIGRAMS[_trigram_index(transformed_lines[:3])]
        transformed_spec = HEXAGRAM_SPECS.get(transformed_name, {"palace": "未知宫", "tag": ""})
        transformed_hexagram = {
            "hexagram_number": transformed_number,
            "name": transformed_name,
            "meaning": _hexagram_meaning(transformed_name),
            "upper_trigram": transformed_upper["name"],
            "lower_trigram": transformed_lower["name"],
            "panel_title": f"{transformed_lower['meaning']}{transformed_upper['meaning']}{transformed_name}",
            "panel_subtitle": (
                f"{transformed_spec['palace'].replace('宫', '')}·{_display_tag_for(transformed_name, transformed_spec['tag'])}"
                if transformed_spec["tag"]
                else transformed_spec["palace"].replace("宫", "")
            ),
        }
        transformed_static_lines = _hexagram_static_lines(transformed_name)
        transformed_hidden_spirits = _hidden_spirits_for(transformed_name, transformed_static_lines)
        transformed_shi, transformed_ying = _shi_ying_positions(transformed_name)
        transformed_line_details = [
            _build_line_detail(
                position,
                item,
                transformed_static_lines[position - 1],
                six_spirits[position - 1],
                transformed_shi,
                transformed_ying,
                transformed_hidden_spirits.get(position, ""),
            )
            for position, item in enumerate(transformed_lines, start=1)
        ]

    summary = (
        f"本卦为{name}卦（第{hexagram_number}卦），{_hexagram_meaning(name)}。"
        f" 起卦方式为{CAST_MODE_LABELS.get(cast_mode, '硬币起卦')}。"
    )
    if changing_lines:
        summary += f" 动爻在第{'、'.join(f'{item}爻' for item in changing_lines)}，"
        if transformed_hexagram:
            summary += f"变卦为{transformed_hexagram['name']}卦。"
    else:
        summary += " 暂无动爻，先看本卦整体趋势。"
    summary += " 六爻更适合先看变化，再定进退。"

    cards = [
        {"label": "起卦方式", "value": CAST_MODE_LABELS.get(cast_mode, "硬币起卦")},
        {"label": "本卦", "value": f"{name}卦"},
        {"label": "上下卦", "value": f"{upper['name']} / {lower['name']}"},
        {"label": "互卦", "value": f"{mutual_hexagram['name']}卦" if mutual_hexagram else "无"},
        {"label": "动爻", "value": "、".join(f"{item}爻" for item in changing_lines) if changing_lines else "无"},
        {"label": "变卦", "value": f"{transformed_hexagram['name']}卦" if transformed_hexagram else "无"},
        {"label": "问念", "value": question or "未填写"},
        {"label": "分类", "value": category or "未分类"},
    ]
    line_details = [
        _build_line_detail(
            position,
            item,
            static_lines[position - 1],
            six_spirits[position - 1],
            shi_position,
            ying_position,
            hidden_spirits.get(position, ""),
        )
        for position, item in enumerate(lines, start=1)
    ]
    shen_sha = _shensha_for(now, line_details, shi_position)
    day_label = now.strftime("%Y年%m月%d日%H:%M:%S %A")
    day_label = day_label.replace("Monday", "周一").replace("Tuesday", "周二").replace("Wednesday", "周三").replace("Thursday", "周四").replace("Friday", "周五").replace("Saturday", "周六").replace("Sunday", "周日")
    panel_title = f"{lower['meaning']}{upper['meaning']}{name}"
    panel_subtitle = (
        f"{hexagram_spec['palace'].replace('宫', '')}·{_display_tag_for(name, hexagram_spec['tag'])}"
        if hexagram_spec["tag"]
        else hexagram_spec["palace"].replace("宫", "")
    )
    time_line = f"{now.strftime('%Y年%m月%d日%H:%M:%S')} {day_label.split(' ')[-1]}农历三月初二"
    ganzhi_line = _ganzhi_line(now)
    suggestions = [
        "先看动爻在哪一层，再判断该守还是该推。",
        "有变卦时，优先看变化方向，不要只盯本卦。",
        "六爻更适合看当前局势，先定节奏再动作。",
    ]

    return {
        "method_label": "排盘",
        "question": question,
        "summary": summary,
        "cards": cards,
        "suggestions": suggestions,
        "raw_result": {
            "cast_mode": cast_mode,
            "hexagram_number": hexagram_number,
            "hexagram_name": name,
            "hexagram_meaning": _hexagram_meaning(name),
            "upper_trigram": upper["name"],
            "lower_trigram": lower["name"],
            "mutual_hexagram": mutual_hexagram,
            "binary": binary,
            "changing_lines": changing_lines,
            "lines": lines,
            "line_details": line_details,
            "transformed_hexagram": transformed_hexagram,
            "transformed_line_details": transformed_line_details,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "day_label": time_line,
            "ganzhi_line": ganzhi_line,
            "panel_title": panel_title,
            "panel_subtitle": panel_subtitle,
            "hexagram_tag": hexagram_spec["tag"],
            "hexagram_palace": hexagram_spec["palace"],
            "category": category or "未分类",
            "shensha": shen_sha,
        },
    }


def _build_catalog_result() -> dict[str, Any]:
    cards = [
        {"label": f"{item['number']} {item['name']}", "value": item["meaning"]}
        for item in ALL_GUA_CATALOG
    ]
    return {
        "method_label": "六十四卦",
        "question": "",
        "summary": "六十四卦库，点开任意一卦即可查看名称与卦意。",
        "cards": cards,
        "suggestions": ["可直接在卦库中搜索卦名。", "需要查看完整内容时，继续向下浏览。"],
        "raw_result": {"catalog": ALL_GUA_CATALOG},
    }


def _build_reference_result() -> dict[str, Any]:
    now = datetime.now()
    return {
        "method_label": "日晷",
        "question": "",
        "summary": "当前时间、日期、节气与时辰参考，放在这里先看时势。",
        "cards": [
            {"label": "当前时间", "value": now.strftime("%Y-%m-%d %H:%M:%S")},
            {"label": "中国时区", "value": "Asia/Shanghai"},
            {"label": "节气参考", "value": "当前节气与下一节气可由前端展示。"},
            {"label": "更新时间", "value": now.strftime("%Y-%m-%d %H:%M:%S")},
            {"label": "提示", "value": "日晷页只看时势，不替代排盘。"},
        ],
        "suggestions": ["如果要进一步判断，回到排盘页看本卦、互卦和变卦。"],
        "raw_result": {
            "sundial": {"timestamp": now.isoformat(timespec="seconds")},
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "date_text": date.today().isoformat(),
        },
    }


def _build_calendar_result() -> dict[str, Any]:
    today = date.today()
    summary = f"当前日期为 {today.isoformat()}，可作为时间参考。"
    return {
        "method_label": "日历",
        "question": "",
        "summary": summary,
        "cards": [
            {"label": "公历日期", "value": today.isoformat()},
            {"label": "星期", "value": today.strftime("%A")},
            {"label": "建议", "value": "可直接用今天时间起卦。"},
        ],
        "suggestions": ["如果要问今天的局势，可切回起卦页直接用当前时间。"],
        "raw_result": {"date": today.isoformat(), "weekday": today.strftime("%A")},
    }


def _build_clock_result() -> dict[str, Any]:
    now = datetime.now()
    summary = f"当前时间为 {now.strftime('%Y-%m-%d %H:%M:%S')}。"
    return {
        "method_label": "时钟",
        "question": "",
        "summary": summary,
        "cards": [
            {"label": "当前时间", "value": now.strftime("%Y-%m-%d %H:%M:%S")},
            {"label": "当前小时", "value": now.strftime("%H:00")},
            {"label": "建议", "value": "可直接按当前时间起卦。"},
        ],
        "suggestions": ["想用时间起卦时，直接切回起卦页。"],
        "raw_result": {"timestamp": now.isoformat(timespec="seconds")},
    }


def _build_records_result() -> dict[str, Any]:
    return {
        "method_label": "记录",
        "question": "",
        "summary": "记录由前端本地保存，方便回看最近的六爻结果。",
        "cards": [
            {"label": "记录位置", "value": "浏览器本地"},
            {"label": "说明", "value": "不会影响其他页面。"},
        ],
        "suggestions": ["可在前端保存最近的起卦记录。"],
        "raw_result": {"storage": "local"},
    }


def _build_songs_result() -> dict[str, Any]:
    built_in_songs = [
        {
            "title": "浑天甲子歌",
            "content": "干金甲子外壬午，坎水戊寅外戊申。震木庚子外庚午，艮土丙辰外丙戌。坤土乙未外癸丑，巽木辛丑外辛未。离火己卯外己酉，兑金丁巳外丁亥。",
        },
        {
            "title": "天干与内脏关系对应",
            "content": "甲肝乙胆丙小肠，丁心戊胃己脾乡。庚是大肠辛属肺，壬系膀胱癸肾藏。三焦亦是壬中寄，包络同归入癸方。",
        },
        {
            "title": "天干与人体对应关系",
            "content": "甲头乙项丙肩求，丁心戊肋己属腹。庚是脐轮辛为股，壬癸足足一身由。",
        },
        {
            "title": "地支与内脏关系对应",
            "content": "子属膀胱水道耳，丑为胞肚及脾乡。寅胆发脉并两手，卯本十指内肝方。辰土为皮肩胸肋，巳面齿咽下尻肛。午火精神司眼目，未土胃脘隔脊梁。申金大肠经络肺，酉中精血小肠藏。戌土命门腿足，亥水为头及肾囊。",
        },
        {
            "title": "地支与人体关系对应",
            "content": "午头巳未两肩均，左右二腕为辰申。卯酉双肋寅戌腿，丑亥属脚子为阴。",
        },
        {
            "title": "八卦与人体对应关系",
            "content": "干首坤腹坎耳俦，震足巽股艮手留。兑口离目分八卦，凡看病此中求。",
        },
        {
            "title": "八记忆卦口诀",
            "content": "干三连，坤六断。震仰盂，艮覆碗。兑上缺，巽下断。离中虚，坎中满。",
        },
        {
            "title": "年上月初，五虎遁",
            "content": "甲己之年丙作首，乙庚之岁戊为头。丙辛之岁寻庚上，丁壬壬寅顺水流。若问戊何处癸起，甲寅之上好追求。",
        },
        {
            "title": "日起时，五鼠遁",
            "content": "甲己还加甲，乙庚丙作初。丙辛从戊起，丁壬庚子居。癸起壬子，周而复始求。",
        },
        {
            "title": "寻找世认宫歌",
            "content": "天同二世天变五。地同四世地变初。本宫六世三世异。人同游魂人变归。一二三六外卦宫。四五游魂内卦变更。归魂内卦是本宫。",
        },
    ]
    return {
        "method_label": "歌诀",
        "question": "",
        "summary": "这里放六爻的速记和口诀，方便快速理解卦意。",
        "cards": [{"label": item["title"], "value": item["content"]} for item in built_in_songs],
        "suggestions": ["如果不需要这块，后续可以直接删除。"],
        "raw_result": {"snippets": built_in_songs},
    }


async def _interpret_with_llm(
    question: str,
    base_result: dict[str, Any],
    db: Session | None,
    research_context: str = "",
    should_append_question: bool = True,
    should_append_scope_nudge: bool = False,
) -> tuple[str, str]:
    grounding = _build_divination_grounding(base_result)
    protocol = _build_interpretation_protocol(
        question=question,
        category=_normalize_text((base_result.get("raw_result") or {}).get("category")),
        grounding=grounding,
    )
    system_prompt = (
        "你是 Tokendancer 的六爻解卦师。"
        "所有判断都必须只依据眼前这张卦盘，不许脱离卦象给通用建议，不许编造盘里没有的信息。"
        "解读时要先完成卦象本体层分析：符号解析、关系建模、主线提取、时间推演；再进入问题映射层：定义利弊标准、映射到用户问题、给出决策。"
        "解读时要从本卦、动爻、变卦、六神、六亲、世应、卦宫、六合六冲、旬空与神煞这些已提供的信息出发，抓最关键的关系来判断。"
        "语气要像真正解卦的人，沉稳、安抚、有人味，哪怕结果不理想，也先安人心，再落判断。"
        "不要输出 markdown，不要出现 **、#、表格代码块、系统解释或'作为AI'。"
        "先按起卦时间对应的日辰、月令、节气来解，不要自己改日期。"
        "不要直接把卦等同于吉凶，要先理解卦本身的动力学机制，再解释它对用户问题意味着什么。"
        "先按符号层、关系层、状态层去理解盘面：先识别符号，再看生克合冲，最后看月建日辰旬空和动变如何改写趋势。"
        "如果问题没有明确命中已有模板，不要套错模板；要回到卦象结构本身重新建立这件事的利弊标准，并结合联网补充处理现实背景。"
        "如果用户问的是二选一、是非题，核心结论第一句就直接给明确倾向。"
        "如果用户问的是找东西、失物、方位、位置，核心结论第一句就直接给方位判断，再补空间线索和依据。"
        "输出结构固定为五段：核心结论、关键互动分析、时间推演、实际意义、风险提醒。"
        "每段都用人话写，不要长篇铺陈，但要让人看得出判断确实从卦里来。"
        "回答要像同一个稳定的专业 skill：带一点六爻术语，但语气要拟人，不要生硬。"
        "单条回答不要过长，首轮控制在中短篇幅。"
        "最后必须自然追问一句，把用户引到最值得继续追断的下一点上。"
        "整篇避免重复，控制节奏，不要把同一层意思来回说。"
    )
    user_prompt = json.dumps(
        {
            "question": question,
            "base_result": grounding,
            "interpretation_protocol": protocol,
            "research_context": research_context,
            "grounding_snippets": GROUNDING_SNIPPETS,
            "output_goal": "给出一版更像解卦师的首轮解读，先识别问题类型，再结合日辰月令和关键爻关系展开，最后落到建议",
        },
        ensure_ascii=False,
        indent=2,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    reply = await generate_reply(messages, db=db)
    content = str(reply.get("content") or "").strip()
    model_used = str(reply.get("model") or "")
    finish_reason = str(reply.get("finish_reason") or "")
    if _should_continue_generation(content, finish_reason):
        content, continued_model = await _continue_llm_completion(
            db=db,
            base_messages=messages,
            existing_content=content,
        )
        model_used = continued_model or model_used
    needs_repair, repair_reason = _answer_needs_repair(
        question=question,
        protocol=protocol,
        answer=content,
    )
    if needs_repair:
        repair_context = research_context
        try:
            repair_payload = await research_how_to_do_question(
                question=question,
                category=_normalize_text((base_result.get("raw_result") or {}).get("category")),
                cast_context={"raw_result": base_result.get("raw_result", {})},
                history=[],
                forced_kind="adaptive_context",
            )
            repair_context = "\n\n".join(
                part for part in [research_context, _format_how_to_do_research_context(repair_payload)] if part
            ).strip()
        except Exception:
            repair_context = research_context
        repaired_text, repaired_model = await _repair_divination_answer(
            db=db,
            question=question,
            protocol=protocol,
            grounding=grounding,
            rejected_answer=content,
            repair_reason=repair_reason,
            research_context=repair_context,
            is_followup=False,
        )
        repaired_needs_fix, _ = _answer_needs_repair(
            question=question,
            protocol=protocol,
            answer=repaired_text,
        )
        if repaired_text and not repaired_needs_fix:
            content = repaired_text
            model_used = repaired_model or model_used
    if not should_append_question:
        content = _remove_trailing_question(content)
    if should_append_scope_nudge:
        nudge_seed = _stable_seed(question, grounding.get("hexagram", {}).get("name"), "scope-nudge-variant")
        nudge = SCOPE_NUDGE_VARIANTS[nudge_seed % len(SCOPE_NUDGE_VARIANTS)]
        content = _append_scope_nudge(content, nudge)
    return content.strip(), model_used


async def _chat_with_llm(
    user_message: str,
    cast_context: dict[str, Any],
    conversation_history: list[dict[str, Any]],
    db: Session | None,
    research_context: str = "",
    should_append_question: bool = True,
    should_append_scope_nudge: bool = False,
) -> tuple[str, str]:
    raw_context = cast_context.get("raw_result") if isinstance(cast_context, dict) else {}
    grounding = cast_context if "time_context" in cast_context and "hexagram" in cast_context else {
        "question": _normalize_text(cast_context.get("question")) if isinstance(cast_context, dict) else "",
        "summary": _normalize_text(cast_context.get("summary")) if isinstance(cast_context, dict) else "",
        "hexagram": {
            "name": _normalize_text(raw_context.get("hexagram_name")) if isinstance(raw_context, dict) else "",
            "tag": _normalize_text(raw_context.get("hexagram_tag")) if isinstance(raw_context, dict) else "",
            "palace": _normalize_text(raw_context.get("hexagram_palace")) if isinstance(raw_context, dict) else "",
            "changing_lines": raw_context.get("changing_lines", []) if isinstance(raw_context, dict) else [],
            "transformed_hexagram": raw_context.get("transformed_hexagram") if isinstance(raw_context, dict) else {},
        },
        "time_context": {
            "day_label": _normalize_text(raw_context.get("day_label")) if isinstance(raw_context, dict) else "",
            "ganzhi_line": _normalize_text(raw_context.get("ganzhi_line")) if isinstance(raw_context, dict) else "",
            "shensha": raw_context.get("shensha", {}) if isinstance(raw_context, dict) else {},
        },
        "line_details": raw_context.get("line_details", []) if isinstance(raw_context, dict) else [],
        "transformed_line_details": raw_context.get("transformed_line_details", []) if isinstance(raw_context, dict) else [],
    }
    protocol = _build_interpretation_protocol(
        question=user_message,
        category=_normalize_text(cast_context.get("category")) if isinstance(cast_context, dict) else "",
        grounding=grounding,
        conversation_history=conversation_history,
    )
    system_prompt = (
        "你是 Tokendancer 的六爻续断解卦师。"
        "这段对话已经绑定到同一卦、同一件事，后续回答只允许围绕当前这卦和原问题延伸，不能被聊天带偏。"
        "如果用户追问超出本卦可覆盖的范围，你要温和收回到本卦，只就这件事继续断，不把新话题当成新卦处理。"
        "续断时也要先完成卦象本体层分析，再做问题映射，不要跳过结构分析直接给结论。"
        "回答必须以当前卦盘为根：本卦、动爻、变卦、六神、六亲、世应、六合六冲、旬空与神煞，择要而断。"
        "语气要像经验老到的解卦师，稳、软、安抚，不说系统话，不给泛泛心理建议。"
        "不要输出 markdown，不要出现 **、#、代码块、系统解释。"
        "先按这一卦对应的起卦时间和盘面继续断，不要擅自改时间。"
        "续断时也要先按符号层、关系层、状态层回到盘面本身，再回答用户新追问。"
        "如果用户追问的是盘里原本没有现成模板的话题，就用卦象结构重新建模，再吸收联网补充，而不是乱套旧模板。"
        "如果用户只是说继续、展开、细说，默认只补上一轮没说透的关键点，不要把之前完整答案重讲一遍。"
        "如果用户问的是二选一、是非题，核心结论第一句就直接给明确倾向。"
        "如果用户问的是找东西、失物、方位、位置，核心结论第一句就直接给方位判断，再补空间线索和依据。"
        "默认保持简洁，续断优先短一些，除非用户明确要求展开很多。"
        "回答要保留一点专业术语，但口气要像会看卦的人在当面说，不要像系统报告。"
        "最后也要自然反问一句，把追问收回到最关键的下一点。"
    )
    trimmed_history = _compact_history_for_prompt(conversation_history)
    user_prompt = json.dumps(
        {
            "cast_context": grounding,
            "interpretation_protocol": protocol,
            "research_context": research_context,
            "conversation_history": trimmed_history,
            "latest_user_message": user_message,
            "grounding_snippets": GROUNDING_SNIPPETS,
            "output_goal": "基于同一卦继续追断，先识别追问关注点，再只围绕本卦关键关系回答",
        },
        ensure_ascii=False,
        indent=2,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    reply = await generate_reply(messages, db=db)
    content = str(reply.get("content") or "").strip()
    model_used = str(reply.get("model") or "")
    finish_reason = str(reply.get("finish_reason") or "")
    if _should_continue_generation(content, finish_reason):
        content, continued_model = await _continue_llm_completion(
            db=db,
            base_messages=messages,
            existing_content=content,
        )
        model_used = continued_model or model_used
    needs_repair, repair_reason = _answer_needs_repair(
        question=user_message,
        protocol=protocol,
        answer=content,
    )
    if needs_repair:
        repair_context = research_context
        try:
            repair_payload = await research_how_to_do_question(
                question=user_message,
                category=_normalize_text(cast_context.get("category")) if isinstance(cast_context, dict) else "",
                cast_context=cast_context if isinstance(cast_context, dict) else {},
                history=conversation_history if isinstance(conversation_history, list) else [],
                forced_kind="adaptive_context",
            )
            repair_context = "\n\n".join(
                part for part in [research_context, _format_how_to_do_research_context(repair_payload)] if part
            ).strip()
        except Exception:
            repair_context = research_context
        repaired_text, repaired_model = await _repair_divination_answer(
            db=db,
            question=user_message,
            protocol=protocol,
            grounding=grounding,
            rejected_answer=content,
            repair_reason=repair_reason,
            research_context=repair_context,
            conversation_history=trimmed_history,
            is_followup=True,
        )
        repaired_needs_fix, _ = _answer_needs_repair(
            question=user_message,
            protocol=protocol,
            answer=repaired_text,
        )
        if repaired_text and not repaired_needs_fix:
            content = repaired_text
            model_used = repaired_model or model_used
    if not should_append_question:
        content = _remove_trailing_question(content)
    if should_append_scope_nudge:
        nudge_seed = _stable_seed(user_message, grounding.get("hexagram", {}).get("name"), "scope-nudge-variant")
        nudge = SCOPE_NUDGE_VARIANTS[nudge_seed % len(SCOPE_NUDGE_VARIANTS)]
        content = _append_scope_nudge(content, nudge)
    return content.strip(), model_used


def _fallback_interpretation(base_result: dict[str, Any]) -> str:
    raw = base_result.get("raw_result", {}) or {}
    hexagram_name = _normalize_text(raw.get("hexagram_name")) or "此卦"
    transformed = raw.get("transformed_hexagram") or {}
    transformed_name = _normalize_text(transformed.get("name"))
    changing_lines = raw.get("changing_lines") or []
    changing_text = "、".join(f"{item}爻" for item in changing_lines) if changing_lines else "暂无动爻"
    return (
        f"核心结论：这卦先看{hexagram_name}的主势，眼下不必先慌，先顺着局势判断进退。\n\n"
        f"卦象拆解：本卦主当前局面，{('动在' + changing_text) if changing_lines else '暂无动爻，重点看整体卦势'}"
        f"{f'，后势转到{transformed_name}' if transformed_name else ''}，说明事情不是完全没有路，只是节奏要拿稳。\n\n"
        "怎么应对：先按眼前最关键的一步处理，不急着把话说满，也不要一次做过头。\n\n"
        "卦上提醒：结果未定时，稳住比硬冲更要紧，先把心放平，路会看得更清。"
    ).strip()


async def generate_how_to_do_runtime(request: dict[str, Any], db: Session | None = None) -> dict[str, Any]:
    section = _normalize_text(request.get("section")) or "cast"
    cast_mode = _normalize_text(request.get("cast_mode")) or "coin"
    question = _normalize_text(request.get("question"))
    category = _normalize_text(request.get("category"))
    cast_seed = _normalize_text(request.get("cast_seed"))
    manual_lines = request.get("manual_lines") or []
    character_text = _normalize_text(request.get("character_text"))
    use_ai = bool(request.get("use_ai", True))
    user_message = _normalize_text(request.get("user_message"))
    conversation_history = request.get("conversation_history") or []
    cast_context = request.get("cast_context") or {}

    if section == "catalog":
        base_result = _build_catalog_result()
    elif section in {"reference", "calendar", "clock", "sundial"}:
        base_result = _build_reference_result()
    elif section == "songs":
        base_result = _build_songs_result()
    elif section == "chat":
        if not cast_context:
            raise ValueError("缺少卦象上下文")
        if not user_message:
            raise ValueError("请输入追问内容")
        research_payload: dict[str, Any] = {}
        research_context = ""
        if use_ai:
            try:
                research_payload = await research_how_to_do_question(
                    question=user_message,
                    category=_normalize_text(cast_context.get("category")) if isinstance(cast_context, dict) else "",
                    cast_context=cast_context if isinstance(cast_context, dict) else {},
                    history=conversation_history if isinstance(conversation_history, list) else [],
                )
                research_context = _format_how_to_do_research_context(research_payload)
            except Exception:
                research_payload = {}
                research_context = ""
        fallback = (
            "核心结论：这次追问仍然要回到本卦本身看，先别被新的情绪和说法带偏。\n\n"
            f"卦上看：{_normalize_text(cast_context.get('summary')) or '眼前局势仍以本卦主势为准。'}\n\n"
            "怎么应对：把这次追问放回同一件事里判断，先顺势，不急着另起判断。\n\n"
            "安一句心：卦还在，路也还在，先按这一步看清再说。"
        ).strip()
        ai_interpretation = fallback
        model_used = ""
        should_append_question = _should_append_followup_question(
            user_message,
            conversation_history=conversation_history if isinstance(conversation_history, list) else [],
            cast_context=cast_context if isinstance(cast_context, dict) else {},
        )
        should_append_scope_nudge = _should_append_scope_nudge(
            user_message,
            conversation_history=conversation_history if isinstance(conversation_history, list) else [],
            cast_context=cast_context if isinstance(cast_context, dict) else {},
        )
        if use_ai and db is not None:
            try:
                ai_text, model_used = await _chat_with_llm(
                    user_message,
                    cast_context,
                    conversation_history,
                    db,
                    research_context=research_context,
                    should_append_question=should_append_question,
                    should_append_scope_nudge=should_append_scope_nudge,
                )
                if ai_text:
                    ai_interpretation = _clean_divination_output(ai_text)
            except LLMGatewayError:
                model_used = ""
            except Exception:
                model_used = ""
        response_raw_result = dict(cast_context) if isinstance(cast_context, dict) else {}
        if research_payload:
            response_raw_result["latest_research"] = research_payload
        return {
            "section": section,
            "method_label": SECTION_LABELS["chat"],
            "question": user_message,
            "summary": "",
            "cards": [],
            "ai_interpretation": ai_interpretation,
            "suggestions": [],
            "raw_result": response_raw_result,
            "catalog": [],
            "model_used": model_used,
        }
    elif section == "cast":
        source_text = character_text or question
        base_result = _build_cast_result(question, category, cast_mode, cast_seed, source_text=source_text, manual_lines=manual_lines)
    elif section == "detail":
        base_result = _build_cast_result(question, category, cast_mode, cast_seed, source_text=character_text or question, manual_lines=manual_lines)
    else:
        raise ValueError(f"不支持的模块: {section}")

    ai_interpretation = _fallback_interpretation(base_result)
    model_used = ""
    research_payload: dict[str, Any] = {}
    research_context = ""
    if use_ai and question:
        try:
            research_payload = await research_how_to_do_question(
                question=question,
                category=category,
                cast_context={"raw_result": base_result.get("raw_result", {})},
                history=[],
            )
            research_context = _format_how_to_do_research_context(research_payload)
        except Exception:
            research_payload = {}
            research_context = ""
    if use_ai and db is not None and section == "cast":
        should_append_question = _should_append_followup_question(
            question,
            conversation_history=[],
            cast_context={"raw_result": base_result.get("raw_result", {})},
        )
        should_append_scope_nudge = _should_append_scope_nudge(
            question,
            conversation_history=[],
            cast_context={"raw_result": base_result.get("raw_result", {})},
        )
        try:
            ai_text, model_used = await _interpret_with_llm(
                question,
                base_result,
                db,
                research_context=research_context,
                should_append_question=should_append_question,
                should_append_scope_nudge=should_append_scope_nudge,
            )
            if ai_text:
                ai_interpretation = _clean_divination_output(ai_text)
        except LLMGatewayError:
            model_used = ""
        except Exception:
            model_used = ""
    if research_payload:
        raw_result = dict(base_result.get("raw_result", {}) or {})
        raw_result["research"] = research_payload
        base_result["raw_result"] = raw_result

    return {
        "section": section,
        "method_label": base_result.get("method_label", SECTION_LABELS.get(section, "我该怎么做")),
        "question": question,
        "summary": _normalize_text(base_result.get("summary")),
        "cards": base_result.get("cards", []),
        "ai_interpretation": ai_interpretation,
        "suggestions": base_result.get("suggestions", []),
        "raw_result": base_result.get("raw_result", {}),
        "catalog": base_result.get("raw_result", {}).get("catalog", []),
        "model_used": model_used,
    }
