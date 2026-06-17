"""Heuristic novel parser for the MVP pipeline.

The parser is intentionally deterministic so the skill can work without an
LLM key. When an LLM is configured, callers can replace this layer with the
OpenAI-compatible client in ``llm_client.py``.
"""

from __future__ import annotations

import re
from typing import Any


TIME_KEYWORDS = [
    "黎明",
    "清晨",
    "上午",
    "正午",
    "午后",
    "黄昏",
    "傍晚",
    "深夜",
    "午夜",
    "夜里",
    "雨夜",
]

LOCATION_HINTS = [
    "古庙",
    "天台",
    "宫殿",
    "大殿",
    "街道",
    "巷口",
    "客栈",
    "山谷",
    "战场",
    "书房",
    "房间",
    "码头",
    "森林",
    "屋顶",
    "院中",
    "桥上",
]

OBJECT_HINTS = [
    "玉佩",
    "血刃",
    "剑",
    "刀",
    "信笺",
    "簪子",
    "烛台",
    "酒杯",
    "戒指",
    "手机",
    "照片",
    "伞",
]

ACTION_VERBS = [
    "站",
    "走",
    "握",
    "抬",
    "低声",
    "猛然",
    "转身",
    "说",
    "喊",
    "冲",
    "拦",
    "拔",
    "跪",
    "笑",
    "哭",
    "看",
    "推",
    "藏",
    "伸",
    "抱",
]

NAME_BLACKLIST = {
    "黄昏",
    "深夜",
    "清晨",
    "下一刻",
    "古庙",
    "庙门",
    "烛光",
    "佛像",
    "玉佩",
    "阴影",
    "阴影中",
    "低声",
    "猛然",
    "抬手",
}


def parse_novel_text(text: str, visual_style: str = "新国漫3D渲染") -> dict[str, Any]:
    """Parse novel text into the PRD scene JSON shape."""

    chunks = _split_scene_chunks(text)
    scenes = []
    for index, chunk in enumerate(chunks, start=1):
        scene = _parse_scene(index, chunk, visual_style)
        scenes.append(scene)
    return {"visual_style": visual_style, "scenes": scenes}


def _split_scene_chunks(text: str) -> list[str]:
    cleaned = re.sub(r"\r\n?", "\n", text).strip()
    if not cleaned:
        raise ValueError("novel text is empty")

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", cleaned) if part.strip()]
    chunks: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= 650:
            chunks.append(paragraph)
            continue
        sentences = _split_sentences(paragraph)
        current: list[str] = []
        for sentence in sentences:
            if current and (_is_scene_turn(sentence) or sum(len(s) for s in current) > 420):
                chunks.append("".join(current).strip())
                current = []
            current.append(sentence)
        if current:
            chunks.append("".join(current).strip())
    return chunks[:24]


def _parse_scene(scene_id: int, chunk: str, visual_style: str) -> dict[str, Any]:
    character_names = _extract_character_names(chunk)
    characters = [_build_character(name, chunk) for name in character_names]
    if not characters:
        characters = [
            {
                "name": "主角",
                "action": _summarize_action(chunk),
                "emotion": _detect_emotion(chunk),
                "appearance_tag": "外貌待从原文补充",
                "camera_focus": "中景跟拍",
            }
        ]

    return {
        "scene_id": scene_id,
        "location": _detect_location(chunk),
        "time": _detect_time(chunk),
        "atmosphere": _detect_atmosphere(chunk),
        "characters": characters,
        "key_objects": _detect_key_objects(chunk),
        "camera_language": _detect_camera_language(chunk, characters),
        "dialogue": _extract_dialogue(chunk),
        "duration_estimate": _estimate_duration(chunk),
        "action_frames": _extract_action_frames(chunk, characters),
        "visual_style": visual_style,
        "original_text": chunk,
    }


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"([。！？!?；;])", text)
    sentences: list[str] = []
    for index in range(0, len(parts), 2):
        sentence = parts[index].strip()
        punctuation = parts[index + 1] if index + 1 < len(parts) else ""
        if sentence:
            sentences.append(sentence + punctuation)
    return sentences or [text]


def _is_scene_turn(sentence: str) -> bool:
    return bool(re.search(r"(下一刻|忽然|与此同时|随后|转眼|镜头|画面|另一边)", sentence))


def _extract_character_names(text: str) -> list[str]:
    verb_pattern = "|".join(map(re.escape, ACTION_VERBS))
    patterns = [
        rf"([\u4e00-\u9fa5]{{2,3}})(?=(?:从|在|向|对|把|将|猛然|突然|缓缓|{verb_pattern}))",
        r"([\u4e00-\u9fa5]{2,3})(?:低声|冷声|轻声|沉声)?说",
        r"“[^”]+。”?([\u4e00-\u9fa5]{2,3})",
    ]
    names: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            name = _normalize_character_name(match.group(1))
            if not name or name in NAME_BLACKLIST or name in OBJECT_HINTS or name in ACTION_VERBS:
                continue
            if name and name not in names:
                names.append(name)
    return names[:8]


def _normalize_character_name(name: str) -> str:
    cleaned = name.strip("，。！？；：: “”、")
    if len(cleaned) == 3 and cleaned.startswith(("的", "被", "将")):
        cleaned = cleaned[1:]
    trailing_tokens = ["低声", "猛然", "突然", "缓缓", "抬手", "站", "走", "握", "抬", "说", "喊", "看", "藏"]
    changed = True
    while changed:
        changed = False
        for token in trailing_tokens:
            if cleaned.endswith(token) and len(cleaned) > len(token) + 1:
                cleaned = cleaned[: -len(token)]
                changed = True
    if cleaned.endswith(("中", "里", "前", "后", "上", "下")) and cleaned[:-1] in NAME_BLACKLIST:
        return ""
    if cleaned in {"她", "他", "它", "他们", "她们"}:
        return ""
    return cleaned


def _build_character(name: str, text: str) -> dict[str, str]:
    sentence = _sentence_for_name(name, text)
    return {
        "name": name,
        "action": _extract_action_for_name(name, sentence),
        "emotion": _detect_emotion(sentence or text),
        "appearance_tag": _extract_appearance(sentence or text),
        "camera_focus": _detect_camera_focus(sentence or text),
    }


def _sentence_for_name(name: str, text: str) -> str:
    for sentence in _split_sentences(text):
        if name in sentence:
            return sentence
    return text


def _extract_action_for_name(name: str, sentence: str) -> str:
    if not sentence:
        return "根据剧情推进完成关键动作"
    after_name = sentence.split(name, 1)[-1]
    after_name = after_name.strip("，。！？；：: ")
    if not after_name:
        return _summarize_action(sentence)
    return after_name[:42]


def _extract_appearance(text: str) -> str:
    patterns = [
        r"[\u4e00-\u9fa5]{0,4}色长发",
        r"[\u4e00-\u9fa5]{0,4}色短发",
        r"[\u4e00-\u9fa5]{0,4}色[\u4e00-\u9fa5]{0,4}裙",
        r"[\u4e00-\u9fa5]{0,4}色[\u4e00-\u9fa5]{0,4}袍",
        r"[\u4e00-\u9fa5]{0,4}色[\u4e00-\u9fa5]{0,4}衣",
        r"丹凤眼",
        r"桃花眼",
        r"泪痣",
        r"银发",
        r"黑发",
        r"红衣",
        r"白衣",
    ]
    found: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text):
            if match not in found:
                found.append(match)
    return "，".join(found) if found else "外貌待从原文补充"


def _detect_emotion(text: str) -> str:
    emotion_rules = [
        ("愤怒", "隐忍的愤怒"),
        ("绝望", "绝望"),
        ("恐惧", "恐惧"),
        ("惊", "震惊"),
        ("笑", "克制的笑意"),
        ("哭", "悲伤"),
        ("低声", "压抑冷静"),
        ("狂风", "紧张警觉"),
    ]
    for keyword, label in emotion_rules:
        if keyword in text:
            return label
    return "情绪克制，暗含张力"


def _detect_camera_focus(text: str) -> str:
    if any(keyword in text for keyword in ["眼", "泪", "低声", "说", "指节"]):
        return "面部与手部特写"
    if any(keyword in text for keyword in ["走出", "转身", "冲", "拦住"]):
        return "中景动作跟拍"
    return "中景人物关系"


def _detect_location(text: str) -> str:
    location_pattern = (
        r"((?:破败的|荒废的|古老的|幽暗的|寂静的|现代都市|雨中的)?"
        r"[\u4e00-\u9fa5]{0,8}(?:"
        + "|".join(map(re.escape, LOCATION_HINTS))
        + r"))"
    )
    match = re.search(location_pattern, text)
    if match:
        return match.group(1).strip("，。里中内外上下前后")
    return "未明确地点"


def _detect_time(text: str) -> str:
    for keyword in TIME_KEYWORDS:
        if keyword in text:
            return keyword
    return "未明确时间"


def _detect_atmosphere(text: str) -> str:
    labels: list[str] = []
    rules = [
        ("破败", "荒凉"),
        ("烛光", "幽暗"),
        ("狂风", "紧张"),
        ("血", "危险"),
        ("雨", "潮湿压抑"),
        ("笑", "暧昧"),
        ("战", "史诗感"),
    ]
    for keyword, label in rules:
        if keyword in text and label not in labels:
            labels.append(label)
    return "，".join(labels) if labels else "剧情张力"


def _detect_key_objects(text: str) -> list[str]:
    found = [item for item in OBJECT_HINTS if item in text]
    return found or ["无明确道具"]


def _detect_camera_language(text: str, characters: list[dict[str, str]]) -> dict[str, str]:
    if any(keyword in text for keyword in ["眼", "指节", "低声说"]):
        shot_type = "特写"
    elif len(characters) >= 2:
        shot_type = "中景"
    else:
        shot_type = "全景"

    if any(keyword in text for keyword in ["走出", "转身", "冲", "拦住", "撞开"]):
        camera_move = "跟拍后推镜头"
    elif any(keyword in text for keyword in ["握紧", "眼底", "低声"]):
        camera_move = "缓慢推镜头"
    else:
        camera_move = "固定镜头"

    if "烛光" in text:
        lighting = "烛光摇曳，侧逆光"
    elif "黄昏" in text:
        lighting = "黄昏暖色逆光"
    elif "夜" in text:
        lighting = "低照度冷色月光"
    else:
        lighting = "电影感柔光"

    return {"shot_type": shot_type, "camera_move": camera_move, "lighting": lighting}


def _extract_dialogue(text: str) -> str:
    dialogues = re.findall(r"“([^”]+)”", text)
    return " / ".join(dialogues)


def _estimate_duration(text: str) -> str:
    if len(text) > 420 or "“" in text:
        return "8s"
    return "5s"


def _summarize_action(text: str) -> str:
    sentence = _split_sentences(text)[0]
    return sentence[:46]


def _extract_action_frames(text: str, characters: list[dict[str, str]]) -> dict[str, str]:
    actions = [character["action"] for character in characters if character.get("action")]
    summary = _summarize_action(text)
    start = actions[0] if actions else summary
    peak = actions[1] if len(actions) > 1 else summary
    end = actions[-1] if actions else summary
    return {"start": start, "peak": peak, "end": end}
