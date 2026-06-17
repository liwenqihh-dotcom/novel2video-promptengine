"""Novel2Video PromptEngine pipeline orchestration."""

from __future__ import annotations

import json
from typing import Any

from .consistency import build_character_locks
from .parser import parse_novel_text
from .templates import PLATFORM_DISPLAY_NAMES, normalize_platforms, render_platform_prompts


def generate_from_text(
    text: str,
    platforms: list[str] | tuple[str, ...] | None = None,
    visual_style: str = "新国漫3D渲染，2.5D漫剧风格",
    use_llm: bool = False,
) -> dict[str, Any]:
    """Generate scene JSON, character locks, storyboard, and platform prompts."""

    if use_llm:
        from .llm_client import parse_with_openai_compatible_llm

        parsed = parse_with_openai_compatible_llm(text, visual_style=visual_style)
    else:
        parsed = parse_novel_text(text, visual_style=visual_style)

    scenes = parsed["scenes"]
    character_locks = build_character_locks(scenes, visual_style=visual_style)
    platform_keys = normalize_platforms(platforms)
    platform_prompts = render_platform_prompts(scenes, character_locks, platform_keys)
    storyboard = build_storyboard(scenes, platform_prompts)

    return {
        "engine": "Novel2Video-PromptEngine",
        "version": "0.1.0",
        "visual_style": visual_style,
        "scenes": scenes,
        "character_locks": character_locks,
        "storyboard": storyboard,
        "platform_prompts": platform_prompts,
    }


def build_storyboard(
    scenes: list[dict[str, Any]],
    platform_prompts: dict[str, list[dict[str, str]]],
) -> list[dict[str, str]]:
    storyboard: list[dict[str, str]] = []
    for scene in scenes:
        scene_id = scene["scene_id"]
        first_prompt = _first_prompt_for_scene(scene_id, platform_prompts)
        storyboard.append(
            {
                "shot_no": f"{scene_id:03d}",
                "scene_id": str(scene_id),
                "screen_content": _screen_content(scene),
                "duration": scene.get("duration_estimate", "5s"),
                "transition": _suggest_transition(scene_id, scene),
                "sound": _suggest_sound(scene),
                "subtitle": scene.get("dialogue") or _subtitle_from_scene(scene),
                "prompt_ref": first_prompt,
            }
        )
    return storyboard


def generate_markdown_report(result: dict[str, Any]) -> str:
    lines: list[str] = ["# Novel2Video Prompt Report", ""]
    lines.append("## 角色一致性锁定")
    for name, lock in result.get("character_locks", {}).items():
        lines.extend(
            [
                f"### {name}",
                f"- 基础形象：{lock['base_image']}",
                f"- 风格锚点：{lock['style_anchor']}",
                f"- 禁止项：{lock['forbidden']}",
                f"- 参考图提示词：{lock['reference_image_prompt']}",
                "",
            ]
        )

    lines.extend(["## 分镜脚本", "", "| 镜号 | 画面内容 | 时长 | 转场 | 音效/BGM | 字幕 |", "| --- | --- | --- | --- | --- | --- |"])
    for shot in result.get("storyboard", []):
        lines.append(
            "| {shot_no} | {screen_content} | {duration} | {transition} | {sound} | {subtitle} |".format(
                **{key: _escape_table(str(value)) for key, value in shot.items()}
            )
        )
    lines.append("")

    lines.append("## 平台专属 Prompt")
    for platform, prompts in result.get("platform_prompts", {}).items():
        display = PLATFORM_DISPLAY_NAMES.get(platform, platform)
        lines.extend(["", f"### {display}"])
        for prompt in prompts:
            lines.extend(
                [
                    "",
                    f"#### 镜头 {prompt.get('scene_id')}",
                    "**正向提示词**",
                    "```text",
                    prompt.get("positive_prompt", ""),
                    "```",
                    "**负面提示词**",
                    "```text",
                    prompt.get("negative_prompt", ""),
                    "```",
                    f"- 参数建议：{prompt.get('parameter_suggestion', '')}",
                    f"- 画幅比例：{prompt.get('aspect_ratio', '')}",
                    f"- 时长：{prompt.get('duration', '')}",
                ]
            )
    return "\n".join(lines).strip() + "\n"


def result_to_json(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)


def _first_prompt_for_scene(scene_id: int, platform_prompts: dict[str, list[dict[str, str]]]) -> str:
    for prompts in platform_prompts.values():
        for prompt in prompts:
            if prompt.get("scene_id") == str(scene_id):
                return prompt.get("positive_prompt", "")[:120]
    return ""


def _screen_content(scene: dict[str, Any]) -> str:
    camera = scene.get("camera_language", {})
    character_actions = "；".join(
        f"{character.get('name')} {character.get('action')}" for character in scene.get("characters", [])
    )
    return (
        f"{scene.get('time')}，{scene.get('location')}，{scene.get('atmosphere')}。"
        f"{character_actions}。{camera.get('shot_type')}，{camera.get('camera_move')}，{camera.get('lighting')}"
    )


def _suggest_transition(scene_id: int, scene: dict[str, Any]) -> str:
    if scene_id == 1:
        return "淡入"
    if "狂风" in scene.get("original_text", "") or "下一刻" in scene.get("original_text", ""):
        return "闪白硬切"
    return "硬切"


def _suggest_sound(scene: dict[str, Any]) -> str:
    text = scene.get("original_text", "")
    if "狂风" in text:
        return "风声骤起，鼓点增强"
    if "烛光" in text:
        return "低频氛围乐，烛火细响"
    return "悬疑氛围垫乐"


def _subtitle_from_scene(scene: dict[str, Any]) -> str:
    characters = scene.get("characters", [])
    if characters:
        return f"{characters[0].get('name')}的命运在此刻转向。"
    return "剧情继续推进。"


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
