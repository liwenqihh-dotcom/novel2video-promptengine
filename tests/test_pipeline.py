import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from novel2video_promptengine.pipeline import generate_from_text, generate_markdown_report


SAMPLE_NOVEL = """
黄昏时分，破败的古庙里只剩摇晃的烛光。
苏晚站在佛像前，月白色襦裙被夜风吹起，她握紧玉佩，指节发白，眼底压着隐忍的愤怒。
萧寒从阴影中走出，银色长发掠过肩头，低声说：“把玉佩交出来。”

下一刻，庙门被狂风撞开。苏晚猛然转身，将玉佩藏进袖中，萧寒抬手拦住她的去路。
""".strip()


class PipelineTests(unittest.TestCase):
    def test_generates_scene_json_character_locks_and_mvp_prompts(self):
        result = generate_from_text(SAMPLE_NOVEL, platforms=["jimeng", "kling"])

        self.assertIn("scenes", result)
        self.assertGreaterEqual(len(result["scenes"]), 1)
        first_scene = result["scenes"][0]
        self.assertEqual(first_scene["scene_id"], 1)
        self.assertIn("古庙", first_scene["location"])
        self.assertIn("camera_language", first_scene)
        self.assertTrue(first_scene["characters"])

        character_locks = result["character_locks"]
        self.assertIn("苏晚", character_locks)
        self.assertIn("萧寒", character_locks)
        self.assertIn("月白色襦裙", character_locks["苏晚"]["base_image"])
        self.assertIn("银色长发", character_locks["萧寒"]["base_image"])

        prompts = result["platform_prompts"]
        self.assertEqual({"jimeng", "kling"}, set(prompts.keys()))
        jimeng_prompt = prompts["jimeng"][0]
        kling_prompt = prompts["kling"][0]
        for prompt in (jimeng_prompt, kling_prompt):
            self.assertIn("positive_prompt", prompt)
            self.assertIn("negative_prompt", prompt)
            self.assertIn("parameter_suggestion", prompt)
            self.assertIn("aspect_ratio", prompt)
            self.assertIn("duration", prompt)
        self.assertIn("新国漫", jimeng_prompt["positive_prompt"])
        self.assertIn("起始", kling_prompt["positive_prompt"])

    def test_markdown_report_contains_copy_ready_sections(self):
        result = generate_from_text(SAMPLE_NOVEL, platforms=["jimeng", "kling"])
        markdown = generate_markdown_report(result)

        self.assertIn("# Novel2Video Prompt Report", markdown)
        self.assertIn("## 分镜脚本", markdown)
        self.assertIn("### 即梦", markdown)
        self.assertIn("### 可灵", markdown)
        self.assertIn("```text", markdown)

    def test_result_is_json_serializable(self):
        result = generate_from_text(SAMPLE_NOVEL, platforms=["jimeng", "kling"])
        encoded = json.dumps(result, ensure_ascii=False)
        self.assertIn("苏晚", encoded)


if __name__ == "__main__":
    unittest.main()
