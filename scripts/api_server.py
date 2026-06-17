#!/usr/bin/env python3
"""FastAPI app for the Novel2Video PromptEngine MVP."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing API dependencies. Install them with: "
        "python3 -m pip install -r scripts/requirements.txt"
    ) from exc

from novel2video_promptengine.pipeline import generate_from_text, generate_markdown_report


class GenerateRequest(BaseModel):
    text: str
    platforms: list[str] = Field(default_factory=lambda: ["jimeng", "kling"])
    style: str = "新国漫3D渲染，2.5D漫剧风格"
    output_format: str = "json"
    use_llm: bool = False


app = FastAPI(title="Novel2Video PromptEngine", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/generate")
def generate(request: GenerateRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    try:
        result = generate_from_text(
            request.text,
            platforms=request.platforms,
            visual_style=request.style,
            use_llm=request.use_llm,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if request.output_format == "markdown":
        return {"markdown": generate_markdown_report(result), "result": result}
    return result


STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing uvicorn. Install dependencies with: "
            "python3 -m pip install -r scripts/requirements.txt"
        ) from exc
    uvicorn.run("api_server:app", host="127.0.0.1", port=8787, reload=os.environ.get("N2V_RELOAD") == "1")
