"""Platform prompt template rendering."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .consistency import format_lock_summary


PLATFORM_ALIASES = {
    "jimeng": "jimeng",
    "即梦": "jimeng",
    "dreamina": "jimeng",
    "kling": "kling",
    "可灵": "kling",
    "runway": "runway",
    "liblibai": "liblibai",
    "liblib": "liblibai",
    "oiioii": "oiioii",
    "oii": "oiioii",
}

PLATFORM_DISPLAY_NAMES = {
    "jimeng": "即梦",
    "kling": "可灵",
    "runway": "Runway",
    "liblibai": "LiblibAI",
    "oiioii": "OiiOii",
}


def normalize_platforms(platforms: list[str] | tuple[str, ...] | None) -> list[str]:
    if not platforms:
        return ["jimeng", "kling"]
    normalized: list[str] = []
    for raw in platforms:
        key = PLATFORM_ALIASES.get(raw.strip().lower(), PLATFORM_ALIASES.get(raw.strip()))
        if not key:
            raise ValueError(f"unsupported platform: {raw}")
        if key not in normalized:
            normalized.append(key)
    return normalized


def render_platform_prompts(
    scenes: list[dict[str, Any]],
    character_locks: dict[str, dict[str, str]],
    platforms: list[str] | tuple[str, ...] | None = None,
    templates_dir: Path | None = None,
) -> dict[str, list[dict[str, str]]]:
    """Render copy-ready prompts for each requested platform."""

    platform_keys = normalize_platforms(platforms)
    template_root = templates_dir or Path(__file__).resolve().parents[1] / "templates"
    rendered: dict[str, list[dict[str, str]]] = {}
    for platform in platform_keys:
        template_path = template_root / f"{platform}.j2"
        if not template_path.exists():
            raise FileNotFoundError(f"missing template: {template_path}")
        template = template_path.read_text(encoding="utf-8")
        rendered[platform] = []
        for scene in scenes:
            context = _build_template_context(scene, character_locks)
            text = _render_template(template, context)
            sections = _parse_sections(text)
            sections["platform"] = platform
            sections["platform_display_name"] = PLATFORM_DISPLAY_NAMES[platform]
            sections["scene_id"] = str(scene["scene_id"])
            rendered[platform].append(sections)
    return rendered


def _build_template_context(scene: dict[str, Any], character_locks: dict[str, dict[str, str]]) -> dict[str, Any]:
    characters = scene.get("characters", [])
    names = [character.get("name", "") for character in characters if character.get("name")]
    action_frames = scene.get("action_frames", {})
    return {
        "scene_id": scene.get("scene_id", ""),
        "location": scene.get("location", "未明确地点"),
        "time": scene.get("time", "未明确时间"),
        "atmosphere": scene.get("atmosphere", "剧情张力"),
        "style": scene.get("visual_style", "新国漫3D渲染"),
        "character_summary": _character_summary(characters),
        "lock_summary": format_lock_summary(character_locks, names),
        "action_summary": "；".join(
            character.get("action", "") for character in characters if character.get("action")
        )
        or "根据剧情推进完成关键动作",
        "emotion_summary": "，".join(
            character.get("emotion", "") for character in characters if character.get("emotion")
        )
        or "情绪克制",
        "object_summary": "，".join(scene.get("key_objects", [])) or "无明确道具",
        "dialogue": scene.get("dialogue") or "无对白",
        "shot_type": scene.get("camera_language", {}).get("shot_type", "中景"),
        "camera_move": scene.get("camera_language", {}).get("camera_move", "固定镜头"),
        "lighting": scene.get("camera_language", {}).get("lighting", "电影感柔光"),
        "duration": scene.get("duration_estimate", "5s"),
        "start_frame": action_frames.get("start", "角色进入画面，情绪蓄势"),
        "peak_frame": action_frames.get("peak", "动作达到高潮，镜头聚焦表情和道具"),
        "end_frame": action_frames.get("end", "角色动作收束，留下悬念"),
    }


def _character_summary(characters: list[dict[str, str]]) -> str:
    parts = []
    for character in characters:
        parts.append(
            f"{character.get('name', '角色')}：{character.get('appearance_tag', '外貌待补充')}，"
            f"{character.get('emotion', '情绪克制')}，{character.get('camera_focus', '中景')}"
        )
    return "；".join(parts) if parts else "主角完成剧情动作"


def _render_template(template: str, context: dict[str, Any]) -> str:
    try:
        from jinja2 import Template
    except ModuleNotFoundError:
        return _render_lite_jinja(template, context)
    return Template(template).render(**context)


def _render_lite_jinja(template: str, context: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        value: Any = context
        for part in key.split("."):
            if isinstance(value, dict):
                value = value.get(part, "")
            else:
                value = getattr(value, part, "")
        return str(value)

    return re.sub(r"{{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*}}", replace, template)


def _parse_sections(rendered_text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_key: str | None = None
    buffer: list[str] = []
    for line in rendered_text.splitlines():
        marker = re.fullmatch(r"\[([a-z_]+)\]", line.strip())
        if marker:
            if current_key is not None:
                sections[current_key] = "\n".join(buffer).strip()
            current_key = marker.group(1)
            buffer = []
            continue
        if current_key is not None:
            buffer.append(line)
    if current_key is not None:
        sections[current_key] = "\n".join(buffer).strip()

    required = ["positive_prompt", "negative_prompt", "parameter_suggestion", "aspect_ratio", "duration"]
    for key in required:
        sections.setdefault(key, "")
    return sections
