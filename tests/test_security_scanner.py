"""Security Scanner 单元测试"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.security_scanner import SecurityScanner


class TestSecurityScanner:
    """SecurityScanner 测试"""

    def setup_method(self):
        self.scanner = SecurityScanner("python")

    def test_detect_hardcoded_password(self):
        code = 'api_key = "sk-1234567890abcdef"'
        report = self.scanner.scan(code, "test.py")
        assert any("硬编码" in i.title for i in report.issues)

    def test_detect_eval_injection(self):
        code = "result = eval(user_input)"
        report = self.scanner.scan(code, "test.py")
        assert any("eval" in i.title.lower() for i in report.issues)

    def test_detect_exec_injection(self):
        code = "exec(dynamic_code)"
        report = self.scanner.scan(code, "test.py")
        assert any("exec" in i.title.lower() for i in report.issues)

    def test_detect_shell_injection(self):
        code = "subprocess.run(cmd, shell=True)"
        report = self.scanner.scan(code, "test.py")
        assert any("命令注入" in i.title for i in report.issues)

    def test_detect_weak_hash(self):
        code = "hash = MD5(password)"
        report = self.scanner.scan(code, "test.py")
        assert any("弱哈希" in i.title for i in report.issues)

    def test_detect_ssl_disabled(self):
        code = "requests.get(url, verify=False)"
        report = self.scanner.scan(code, "test.py")
        assert any("SSL" in i.title for i in report.issues)

    def test_detect_insecure_random(self):
        code = "token = random.randint(0, 999999)"
        report = self.scanner.scan(code, "test.py")
        assert any("随机数" in i.title for i in report.issues)

    def test_detect_xss_innerhtml(self):
        code = "el.innerHTML = htmlContent;"
        report = self.scanner.scan(code, "test.js")
        assert any("XSS" in i.title for i in report.issues)

    def test_safe_code_low_risk(self):
        code = "x = 1 + 2\nprint(x)\n"
        report = self.scanner.scan(code, "test.py")
        assert report.risk_score <= 2

    def test_report_to_json(self):
        code = 'eval("x")'
        report = self.scanner.scan(code, "test.py")
        json_str = report.to_json()
        assert '"risk_score"' in json_str

    def test_report_to_markdown(self):
        code = 'eval("x")'
        report = self.scanner.scan(code, "test.py")
        md = report.to_markdown()
        assert "安全漏洞扫描报告" in md

    def test_comments_ignored(self):
        code = '# eval("this is commented out")'
        report = self.scanner.scan(code, "test.py")
        assert not any("eval" in i.title.lower() for i in report.issues)

    def test_risk_level_high(self):
        code = 'password = "secret123"\neval(user_input)\nexec(code)\nsubprocess.run(cmd, shell=True)'
        report = self.scanner.scan(code, "test.py")
        assert report.risk_score >= 7
        assert "高风险" in report.risk_level
