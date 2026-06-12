"""Test Generator 单元测试"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.test_generator import TestGenerator


class TestTestGenerator:
    """TestGenerator 测试"""

    def setup_method(self):
        self.gen = TestGenerator("python", "pytest")

    def test_generate_normal_cases(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b"
        suite = self.gen.generate(code, "add")
        assert len(suite.test_cases) > 0
        assert any(tc.category == "unit" for tc in suite.test_cases)

    def test_generate_edge_cases(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b"
        suite = self.gen.generate(code, "add")
        assert any(tc.category == "edge-case" for tc in suite.test_cases)

    def test_generate_exception_cases(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b"
        suite = self.gen.generate(code, "add")
        assert any(tc.category == "exception" for tc in suite.test_cases)

    def test_pytest_framework(self):
        code = "def greet(name: str) -> str:\n    return f'Hello {name}'"
        suite = self.gen.generate(code, "greet")
        test_code = suite.to_code()
        assert "import pytest" in test_code
        assert "def test_greet" in test_code

    def test_jest_framework(self):
        gen = TestGenerator("javascript", "jest")
        code = "function add(a, b) { return a + b; }"
        suite = gen.generate(code, "add")
        test_code = suite.to_code()
        assert "describe" in test_code
        assert "expect" in test_code

    def test_go_test_framework(self):
        gen = TestGenerator("go", "go-test")
        code = "func Add(a int, b int) int {\n\treturn a + b\n}"
        suite = gen.generate(code, "Add")
        test_code = suite.to_code()
        assert "testing" in test_code

    def test_coverage_estimate(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b"
        suite = self.gen.generate(code, "add")
        assert "%" in suite.coverage_estimate

    def test_parse_python_signature(self):
        code = "def process(data: dict, verbose: bool = False) -> list:"
        sig = self.gen._parse_signature(code)
        assert "data" in sig["params"]
        assert "verbose" in sig["params"]

    def test_parse_signature_self_excluded(self):
        code = "def method(self, x: int) -> str:"
        sig = self.gen._parse_signature(code)
        assert "self" not in sig["params"]
        assert "x" in sig["params"]

    def test_to_markdown(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b"
        suite = self.gen.generate(code, "add")
        md = suite.to_markdown()
        assert "测试用例生成报告" in md
        assert "add" in md
