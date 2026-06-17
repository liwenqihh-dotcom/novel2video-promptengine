# Novel2Video PromptEngine 使用文档

## 1. 本地 CLI

在 Skill 根目录运行：

```bash
python3 scripts/novel2video_cli.py --input chapter.txt --platforms jimeng,kling --format markdown --out report.md
```

常用参数：

- `--input`: UTF-8 小说文本文件。
- `--text`: 直接传入短文本。
- `--platforms`: 平台列表，支持 `jimeng,kling,runway,liblibai,oiioii`。
- `--format`: `markdown` 或 `json`。
- `--style`: 统一美术风格锚点。
- `--use-llm`: 使用 OpenAI-compatible LLM 解析。

## 2. API Key 配置

默认启发式解析不需要 API Key。需要 LLM 解析时配置：

```bash
export N2V_API_KEY="your-api-key"
export N2V_API_BASE="https://api.deepseek.com/v1"
export N2V_MODEL="deepseek-chat"
```

兼容变量：

- `OPENAI_API_KEY`: 当 `N2V_API_KEY` 未设置时使用。
- `N2V_API_BASE`: 任意 OpenAI-compatible `/chat/completions` 服务的 `/v1` 地址。
- `N2V_MODEL`: 模型名。

运行：

```bash
python3 scripts/novel2video_cli.py --input chapter.txt --use-llm --format json --out result.json
```

## 3. 前端界面

安装依赖：

```bash
python3 -m pip install -r scripts/requirements.txt
```

启动：

```bash
python3 scripts/api_server.py
```

访问：

```text
http://127.0.0.1:8787
```

界面包含小说输入、平台选择、分镜时间轴、平台 Prompt Tab、复制 JSON 和复制 Prompt。

## 4. 自定义模板

模板位于：

```text
scripts/templates/
```

每个平台模板必须保留这些段落名：

```text
[positive_prompt]
[negative_prompt]
[parameter_suggestion]
[aspect_ratio]
[duration]
```

可用变量：

- `scene_id`
- `location`
- `time`
- `atmosphere`
- `style`
- `character_summary`
- `lock_summary`
- `action_summary`
- `emotion_summary`
- `object_summary`
- `dialogue`
- `shot_type`
- `camera_move`
- `lighting`
- `duration`
- `start_frame`
- `peak_frame`
- `end_frame`

模板是 Jinja2 兼容语法；未安装 Jinja2 时，MVP 会使用内置的简单变量替换器处理 `{{ variable }}`。

## 5. API 调用

请求：

```bash
curl -s http://127.0.0.1:8787/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"text":"黄昏时分，苏晚站在古庙前。","platforms":["jimeng","kling"]}'
```

响应包含：

- `scenes`
- `character_locks`
- `storyboard`
- `platform_prompts`
