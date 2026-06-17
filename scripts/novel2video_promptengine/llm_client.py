"""Optional OpenAI-compatible LLM parser."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


SYSTEM_PROMPT = """
你是一位资深漫剧导演和AI视频提示词工程师。请将用户提供的小说文本处理为严格JSON。
要求：
1. 按时间、地点、情绪突变切分场景。
2. 为每个场景设计景别、运镜、光影。
3. 将连续动作拆为start/peak/end三段。
4. 提取角色外貌、动作、情绪、道具、对白。
5. 保持统一美术风格。
只输出JSON，不输出解释性文字。
""".strip()


def parse_with_openai_compatible_llm(text: str, visual_style: str) -> dict[str, Any]:
    api_key = os.environ.get("N2V_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set N2V_API_KEY or OPENAI_API_KEY before using --use-llm.")

    api_base = os.environ.get("N2V_API_BASE", "https://api.deepseek.com/v1").rstrip("/")
    model = os.environ.get("N2V_MODEL", "deepseek-chat")
    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "请按Novel2Video场景Schema解析以下小说文本。"
                    f"统一美术风格：{visual_style}\n\n{text}"
                ),
            },
        ],
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        f"{api_base}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc

    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    parsed.setdefault("visual_style", visual_style)
    if "scenes" not in parsed:
        raise RuntimeError("LLM response missing 'scenes'.")
    return parsed
