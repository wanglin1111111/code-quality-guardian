"""Code Reviewer 单元测试"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.code_reviewer import CodeReviewer, Severity, Category, ReviewPattern


class TestReviewPattern:
    """ReviewPattern 数据类测试"""

    def test_matches_positive(self):
        p = ReviewPattern(Severity.HIGH, Category.SECURITY, r"eval\(", "eval 注入风险")
        assert p.matches("result = eval(user_input)") is True

    def test_matches_negative(self):
        p = ReviewPattern(Severity.HIGH, Category.SECURITY, r"eval\(", "eval 注入风险")
        assert p.matches("result = json.loads(data)") is False

    def test_case_insensitive(self):
        p = ReviewPattern(Severity.HIGH, Category.SECURITY, r"eval\(", "eval 注入风险")
        assert p.matches("result = EVAL(x)") is True


class TestCodeReviewer:
    """CodeReviewer 引擎测试"""

    def setup_method(self):
        self.reviewer = CodeReviewer("python")

    def test_detect_sql_injection_fstring(self):
        code = 'query = f"SELECT * FROM users WHERE id = {user_id}"'
        report = self.reviewer.review(code, "test.py")
        assert any("SQL 注入" in i.description for i in report.issues)

    def test_detect_eval(self):
        code = "result = eval(user_input)"
        report = self.reviewer.review(code, "test.py")
        assert any("eval" in i.description for i in report.issues)

    def test_detect_hardcoded_secret(self):
        code = 'password = "EXAMPLE_PASSWORD"'
        report = self.reviewer.review(code, "test.py")
        assert any(i.severity == Severity.CRITICAL.value for i in report.issues)

    def test_detect_innerhtml_xss(self):
        code = "element.innerHTML = userInput;"
        report = self.reviewer.review(code, "test.js")
        assert any("XSS" in i.title for i in report.issues)

    def test_detect_bare_except(self):
        code = "try:\n    do_something()\nexcept:\n    pass"
        report = self.reviewer.review(code, "test.py")
        assert any("裸 except" in i.description for i in report.issues)

    def test_clean_code_high_score(self):
        code = 'def add(a: int, b: int) -> int:\n    """Add two numbers."""\n    return a + b\n'
        report = self.reviewer.review(code, "test.py")
        assert report.overall_score >= 8.0

    def test_no_issues_returns_perfect_score(self):
        code = "# just a comment\nx = 1\n"
        report = self.reviewer.review(code, "test.py")
        assert report.overall_score == 10.0

    def test_report_to_markdown(self):
        code = 'eval("1+1")'
        report = self.reviewer.review(code, "test.py")
        md = report.to_markdown()
        assert "代码质量审查报告" in md
        assert "test.py" in md

    def test_report_to_json(self):
        code = 'eval("1+1")'
        report = self.reviewer.review(code, "test.py")
        json_str = report.to_json()
        assert '"file": "test.py"' in json_str

    def test_comments_ignored(self):
        code = '# eval("this is a comment")'
        report = self.reviewer.review(code, "test.py")
        assert not any("eval" in i.description for i in report.issues)

    def test_severity_summary(self):
        code = 'eval("x")\nexec("y")\npassword = "EXAMPLE_PASSWORD"'
        report = self.reviewer.review(code, "test.py")
        summary = report.summary
        assert summary["CRITICAL"] >= 1
        assert summary["HIGH"] >= 1
