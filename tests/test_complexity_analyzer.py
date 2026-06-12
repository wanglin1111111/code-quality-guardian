"""Complexity Analyzer 单元测试"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.complexity_analyzer import ComplexityAnalyzer


class TestComplexityAnalyzer:
    """ComplexityAnalyzer 测试"""

    def setup_method(self):
        self.analyzer = ComplexityAnalyzer("python")

    def test_simple_function_low_complexity(self):
        code = "def add(a, b):\n    return a + b\n"
        report = self.analyzer.analyze(code, "test.py")
        assert len(report.results) == 1
        assert report.results[0].cyclomatic <= 3

    def test_branching_increases_complexity(self):
        code = (
            "def check(x):\n"
            "    if x > 0:\n"
            "        if x > 10:\n"
            "            return 'big'\n"
            "        elif x > 5:\n"
            "            return 'medium'\n"
            "        else:\n"
            "            return 'small'\n"
            "    else:\n"
            "        return 'negative'\n"
        )
        report = self.analyze_code(code)
        assert report.results[0].cyclomatic > 2

    def test_loop_increases_complexity(self):
        code = "def process(items):\n    for item in items:\n        if item > 0:\n            print(item)\n"
        report = self.analyze_code(code)
        assert report.results[0].cyclomatic > 2

    def test_multiple_functions(self):
        code = "def foo():\n    pass\n\ndef bar():\n    pass\n"
        report = self.analyzer.analyze(code, "test.py")
        assert len(report.results) == 2

    def test_hotspot_detection(self):
        # Create a function with high complexity
        code = "def complex_fn(x):\n"
        for i in range(15):
            code += f"    if x > {i}:\n        pass\n"
        report = self.analyzer.analyze(code, "test.py")
        assert len(report.hotspot_functions) > 0

    def test_avg_cyclomatic(self):
        code = "def a():\n    pass\n\ndef b():\n    pass\n"
        report = self.analyzer.analyze(code, "test.py")
        assert report.avg_cyclomatic >= 0

    def test_empty_code(self):
        report = self.analyzer.analyze("", "empty.py")
        assert len(report.results) == 0
        assert report.avg_cyclomatic == 0

    def test_report_to_json(self):
        code = "def foo():\n    pass\n"
        report = self.analyzer.analyze(code, "test.py")
        json_str = report.to_json()
        assert '"file": "test.py"' in json_str
        assert '"avg_cyclomatic"' in json_str

    def test_report_to_markdown(self):
        code = "def foo():\n    pass\n"
        report = self.analyzer.analyze(code, "test.py")
        md = report.to_markdown()
        assert "复杂度分析报告" in md

    def test_risk_levels(self):
        code = "def simple():\n    return 1\n"
        report = self.analyzer.analyze(code, "test.py")
        assert report.results[0].risk_level in ("✅ 低", "⚠️ 中", "🔴 高")

    def analyze_code(self, code):
        return self.analyzer.analyze(code, "test.py")
