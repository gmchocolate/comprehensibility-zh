"""Repository contract checks only; these tests never run an AI model or human study."""

import json
import re
import unittest
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PREFIXES = "ABCDEF"
EXPECTED_PER_GROUP = 6


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class RepositoryTests(unittest.TestCase):
    def test_required_files_exist(self):
        paths = [
            "README.md", "SKILL.md", "LICENSE", "CONTRIBUTING.md",
            "CHANGELOG.md", "docs/DESIGN.md", "docs/EVALUATION.md",
            "docs/RESEARCH.md", "docs/PROJECT_SPEC.md",
            "examples/examples.md", "tests/fixtures.json",
            ".github/workflows/validate.yml",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file())

    def test_skill_frontmatter_and_modes(self):
        text = read("SKILL.md")
        self.assertTrue(text.startswith("---\n"))
        parts = text.split("---\n", 2)
        self.assertGreaterEqual(len(parts), 3)
        header = parts[1]
        self.assertRegex(header, r"(?m)^name:\s*comprehensibility-zh\s*$")
        desc = re.search(r"(?m)^description:\s*(.+)$", header)
        self.assertIsNotNone(desc)
        self.assertLessEqual(len(desc.group(1).strip()), 1024)
        self.assertRegex(header, r"(?m)^license:\s*MIT\s*$")
        for mode in ("review", "light", "standard", "deep"):
            with self.subTest(mode=mode):
                self.assertIn(f"`{mode}`", text)

    def test_rule_catalog_is_complete_and_unique(self):
        design = read("docs/DESIGN.md")
        ids = re.findall(r"(?m)^\|\s*([A-F]\d{2})\s*\|", design)
        self.assertEqual(len(ids), len(set(ids)), "Rule IDs must be unique")
        expected = {f"{prefix}{index:02}" for prefix in EXPECTED_PREFIXES
                    for index in range(1, EXPECTED_PER_GROUP + 1)}
        self.assertEqual(set(ids), expected, "The design must define all 36 rules")

    def test_fixture_schema_and_rule_alignment(self):
        data = json.loads(read("tests/fixtures.json"))
        self.assertIn("cases", data)
        cases = data["cases"]
        self.assertEqual(len(cases), len(EXPECTED_PREFIXES) * EXPECTED_PER_GROUP)
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)), "Fixture IDs must be unique")
        counts = Counter(case["category"] for case in cases)
        self.assertEqual(dict(counts), {prefix: EXPECTED_PER_GROUP
                                        for prefix in EXPECTED_PREFIXES})
        design_ids = set(re.findall(r"(?m)^\|\s*([A-F]\d{2})\s*\|", read("docs/DESIGN.md")))
        self.assertEqual(set(ids), design_ids)
        required = {"id", "category", "audience", "source",
                    "phenomenon", "expected_behavior", "must_not"}
        for case in cases:
            with self.subTest(case=case.get("id")):
                self.assertTrue(required.issubset(case))
                self.assertRegex(case["id"], r"^[A-F]\d{2}$")
                self.assertEqual(case["id"][0], case["category"])
                for field in required:
                    self.assertIsInstance(case[field], str)
                    self.assertTrue(case[field].strip(), field)

    def test_local_markdown_links_exist(self):
        # This checks file targets, not Markdown anchors or URL destinations.
        for source in ROOT.rglob("*.md"):
            text = source.read_text(encoding="utf-8")
            for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
                destination = match.group(1).strip().split("#", 1)[0]
                if not destination or "://" in destination or destination.startswith(("mailto:", "#")):
                    continue
                file_target = (source.parent / unquote(destination)).resolve()
                with self.subTest(source=str(source.relative_to(ROOT)), target=destination):
                    self.assertTrue(file_target.is_relative_to(ROOT))
                    self.assertTrue(file_target.exists(), f"Broken link from {source}: {destination}")

    def test_critical_semantic_boundaries_are_documented(self):
        skill = read("SKILL.md")
        examples = read("examples/examples.md")
        for term in ("事实", "否定", "条件", "歧义", "作者", "链接", "权限", "尚未通过"):
            with self.subTest(term=term):
                self.assertIn(term, skill)
        for term in ("张老师", "李老师", "HTTP 429", "十个工作日", "只有", "尚未通过"):
            with self.subTest(example=term):
                self.assertIn(term, examples)

    def test_research_claims_have_clear_limits(self):
        for path in ["README.md", "SKILL.md", "docs/RESEARCH.md", "docs/EVALUATION.md"]:
            with self.subTest(path=path):
                text = read(path)
                self.assertRegex(text, r"(真人|读者).{0,20}(实验|理解)")
        for path in ["README.md", "SKILL.md", "docs/DESIGN.md", "docs/PROJECT_SPEC.md"]:
            with self.subTest(path=path):
                self.assertNotIn("30 条检查", read(path))

    def test_static_tests_are_not_presented_as_model_evaluation(self):
        workflow = read(".github/workflows/validate.yml")
        self.assertIn("unittest discover", workflow)
        eval_doc = read("docs/EVALUATION.md")
        self.assertIn("不会运行语言模型", eval_doc)
        self.assertIn("没有中文真人理解实验结果", eval_doc)


if __name__ == "__main__":
    unittest.main()
