---
name: novel2video-promptengine
description: "Convert Chinese novel chapters into AI video generation assets: structured scene JSON, character consistency locks, storyboard timelines, and platform-specific prompts for 即梦, 可灵, Runway, LiblibAI, and OiiOii. Use when a user provides fiction/novel text and asks for 漫剧化, 分镜脚本, AI视频提示词, character lock prompts, or platform-ready prompts for text-to-video/image-to-video tools."
---

# Novel2Video PromptEngine

## Overview

Use this skill to turn novel chapters into copy-ready AI video production material. The bundled MVP works offline with a deterministic parser and can optionally use an OpenAI-compatible LLM endpoint for richer JSON extraction.

## Workflow

1. Save or receive the user's novel text.
2. Run the CLI from this skill directory:

```bash
python3 scripts/novel2video_cli.py --input chapter.txt --platforms jimeng,kling --format markdown --out report.md
```

3. For structured output, use JSON:

```bash
python3 scripts/novel2video_cli.py --input chapter.txt --platforms jimeng,kling --format json --out result.json
```

4. When the user needs a browser UI, install dependencies and start the local API:

```bash
python3 -m pip install -r scripts/requirements.txt
python3 scripts/api_server.py
```

Open `http://127.0.0.1:8787` after the server starts.

## Output Shape

The pipeline returns:

- `scenes`: parsed scene JSON with location, time, atmosphere, characters, key objects, camera language, dialogue, duration, action frames, and original text.
- `character_locks`: stable character appearance, style anchor, forbidden changes, and reference-image prompt.
- `storyboard`: timeline rows with shot number, screen content, duration, transition, sound/BGM cue, subtitle, and prompt reference.
- `platform_prompts`: one prompt list per platform, each containing `positive_prompt`, `negative_prompt`, `parameter_suggestion`, `aspect_ratio`, and `duration`.

For the exact schema, read `references/scene_schema.json`.

## Platform Templates

Prompt formats live in `scripts/templates/`:

- `jimeng.j2`: Chinese cinematic/new-guoman prompt, strong camera language.
- `kling.j2`: start -> transition -> end action structure for coherent motion.
- `runway.j2`: English cinematic prompt with photography terms.
- `liblibai.j2`: SD-style weighted prompt with LoRA/ControlNet suggestions.
- `oiioii.j2`: vertical short-video, chibi/stylized expression prompt.

Edit these templates when the target platform changes. Keep section headers exactly as `[positive_prompt]`, `[negative_prompt]`, `[parameter_suggestion]`, `[aspect_ratio]`, and `[duration]`.

## Optional LLM Parsing

Set these environment variables before using `--use-llm`:

```bash
export N2V_API_KEY="your-api-key"
export N2V_API_BASE="https://api.deepseek.com/v1"
export N2V_MODEL="deepseek-chat"
python3 scripts/novel2video_cli.py --input chapter.txt --use-llm --format json
```

`OPENAI_API_KEY` is also accepted when `N2V_API_KEY` is absent. Any OpenAI-compatible `/chat/completions` endpoint can be used.

## References

- Read `references/usage.md` for user-facing setup, API key, frontend, and template customization guidance.
- Read `references/prompting.md` when modifying the parser prompt or platform adaptation rules.
- Read `references/scene_schema.json` when validating output contracts.
