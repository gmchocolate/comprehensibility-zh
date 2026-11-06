"""Metadata and fixture schema checks; NOT an AI model evaluation."""
import json
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RepositoryTests(unittest.TestCase):
    def test_skill_frontmatter(self):
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        header = content.split("---", 2)[1]
        self.assertRegex(header, r"(?m)^name:\s*comprehensibility-zh\s*$")
        self.assertRegex(header, r"(?m)^description:\s*\S+")
        self.assertLessEqual(len("comprehensibility-zh"), 64)
        self.assertLessEqual(len(next(line.split(":",1)[1].strip() for line in header.splitlines() if line.startswith("description:"))), 1024)
        for mode in ("review", "light", "standard", "deep"):
            self.assertIn(mode, content)

    def test_referenced_files_exist(self):
        for path in ["README.md", "SKILL.md", "LICENSE", "CONTRIBUTING.md", "CHANGELOG.md", "docs/DESIGN.md", "docs/EVALUATION.md", "docs/RESEARCH.md", "docs/PROJECT_SPEC.md", "examples/examples.md", "tests/fixtures.json"]:
            self.assertTrue((ROOT / path).is_file(), path)

    def test_fixture_schema_and_diversity(self):
        data = json.loads((ROOT / "tests/fixtures.json").read_text(encoding="utf-8"))
        cases = data["cases"]
        self.assertGreaterEqual(len(cases), 30)
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        counts = Counter(case["category"] for case in cases)
        for category in "ABCDEF":
            self.assertGreaterEqual(counts[category], 5)
        for case in cases:
            self.assertRegex(case["id"], r"^[A-F]\d{2}$")
            self.assertTrue(set(["id","category","audience","source","phenomenon","expected_behavior","must_not"]).issubset(case))
            self.assertTrue(all(isinstance(case[k], str) and case[k].strip() for k in ["audience", "source", "phenomenon", "expected_behavior", "must_not"]))
            self.assertEqual(case["id"][0], case["category"])

    def test_protected_basenames_mentioned(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for word in ["事实", "否定", "条件", "归因", "代码", "文件", "歧义", "读者"]:
            self.assertIn(word, skill)

if __name__ == "__main__":
    unittest.main()
