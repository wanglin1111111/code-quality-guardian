"""Log Analyzer 单元测试"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.log_analyzer import LogAnalyzer, LogReport


class TestLogAnalyzer:
    """LogAnalyzer 测试"""

    def setup_method(self):
        self.analyzer = LogAnalyzer()

    def test_detect_oom(self):
        log = "2024-01-01 10:00:00 ERROR java.lang.OutOfMemoryError: Java heap space"
        report = self.analyzer.analyze(log, log_file="test.log")
        assert any("内存溢出" in p.pattern for p in report.patterns)

    def test_detect_fatal_error(self):
        log = "2024-01-01 10:00:00 FATAL panic: runtime error"
        report = self.analyzer.analyze(log, log_file="test.log")
        assert any("致命错误" in p.pattern for p in report.patterns)

    def test_detect_connection_timeout(self):
        log = "2024-01-01 10:00:00 ERROR ConnectionTimeout: connection to db timed out"
        report = self.analyzer.analyze(log, log_file="test.log")
        assert any("连接超时" in p.pattern for p in report.patterns)

    def test_detect_warnings(self):
        log = "2024-01-01 10:00:00 WARN: deprecated API usage"
        report = self.analyzer.analyze(log, log_file="test.log")
        assert any("弃用" in p.pattern for p in report.patterns)

    def test_empty_log(self):
        report = self.analyzer.analyze("", log_file="empty.log")
        assert isinstance(report, LogReport)
        assert report.total_lines == 1
        assert len(report.patterns) == 0

    def test_returns_log_report(self):
        log = "2024-01-01 10:00:00 INFO normal log line"
        report = self.analyzer.analyze(log, log_file="test.log")
        assert isinstance(report, LogReport)

    def test_report_to_markdown(self):
        log = "2024-01-01 10:00:00 ERROR OutOfMemoryError\n2024-01-01 10:00:01 ERROR OutOfMemoryError"
        report = self.analyzer.analyze(log, log_file="test.log")
        md = report.to_markdown()
        assert "日志分析报告" in md

    def test_report_to_json(self):
        log = "2024-01-01 10:00:00 ERROR OutOfMemoryError"
        report = self.analyzer.analyze(log, log_file="test.log")
        json_str = report.to_json()
        assert '"log_file": "test.log"' in json_str

    def test_alert_rules_generated(self):
        log = "\n".join([
            f"2024-01-01 10:00:{i:02d} ERROR Exception: something failed"
            for i in range(10)
        ])
        report = self.analyzer.analyze(log, log_file="test.log")
        assert len(report.alert_rules) > 0

    def test_root_cause_for_oom(self):
        log = "2024-01-01 10:00:00 ERROR OutOfMemoryError: heap space"
        report = self.analyzer.analyze(log, log_file="test.log")
        assert any("内存溢出" in rc["title"] for rc in report.root_causes)

    def test_time_range_extraction(self):
        log = "2024-01-01 10:00:00 INFO start\n2024-01-01 10:05:00 INFO end"
        report = self.analyzer.analyze(log, log_file="test.log")
        assert "10:00:00" in report.time_range
        assert "10:05:00" in report.time_range

    def test_format_issues_missing_timestamp(self):
        log = "\n".join(["no timestamp here" for _ in range(30)])
        report = self.analyzer.analyze(log, log_file="test.log")
        assert len(report.format_issues) > 0
