"""Character consistency utilities."""

from __future__ import annotations

from typing import Any


def build_character_locks(
    scenes: list[dict[str, Any]],
    visual_style: str = "新国漫3D渲染，2.5D漫剧风格",
) -> dict[str, dict[str, str]]:
    """Build stable cross-scene character descriptions."""

    appearances: dict[str, list[str]] = {}
    emotions: dict[str, list[str]] = {}

    for scene in scenes:
        for character in scene.get("characters", []):
            name = character.get("name", "").strip()
            if not name:
                continue
            appearances.setdefault(name, [])
            emotions.setdefault(name, [])
            appearance = character.get("appearance_tag", "").strip()
            if appearance and appearance != "外貌待从原文补充":
                for part in _split_tags(appearance):
                    if part not in appearances[name]:
                        appearances[name].append(part)
            emotion = character.get("emotion", "").strip()
            if emotion and emotion not in emotions[name]:
                emotions[name].append(emotion)

    locks: dict[str, dict[str, str]] = {}
    for name in appearances:
        base_image = "，".join(appearances[name]) or "五官清晰，服装主色调需从原文保持一致"
        emotional_range = "，".join(emotions.get(name, [])[:4]) or "克制、有剧情张力"
        locks[name] = {
            "name": name,
            "base_image": base_image,
            "style_anchor": visual_style,
            "forbidden": "不改变发型、瞳色、服装主色调、年龄感和体型比例",
            "emotion_range": emotional_range,
            "reference_image_prompt": (
                f"{name}，{base_image}，{visual_style}，三视图角色设定，"
                "干净背景，面部特征清晰，适合作为视频角色参考图"
            ),
        }
    return locks


def format_lock_summary(character_locks: dict[str, dict[str, str]], names: list[str] | None = None) -> str:
    selected_names = names or list(character_locks.keys())
    parts: list[str] = []
    for name in selected_names:
        lock = character_locks.get(name)
        if not lock:
            continue
        parts.append(f"{name}: {lock['base_image']}; 禁止: {lock['forbidden']}")
    return " | ".join(parts) if parts else "保持角色外貌、服装和年龄感一致"


def _split_tags(value: str) -> list[str]:
    return [part.strip() for part in value.replace("、", "，").split("，") if part.strip()]
