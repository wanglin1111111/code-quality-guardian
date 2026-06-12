"""SQL Optimizer 单元测试"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.sql_optimizer import SQLOptimizer


class TestSQLOptimizer:
    """SQLOptimizer 测试"""

    def setup_method(self):
        self.optimizer = SQLOptimizer("MySQL")

    def test_detect_select_star(self):
        report = self.optimizer.analyze("SELECT * FROM users")
        assert any("SELECT *" in i.title for i in report.issues)

    def test_detect_no_where(self):
        report = self.optimizer.analyze("SELECT id FROM users")
        assert any("全表扫描" in i.title for i in report.issues)

    def test_detect_like_leading_wildcard(self):
        report = self.optimizer.analyze("SELECT id FROM users WHERE name LIKE '%test%'")
        assert any("前导通配符" in i.title for i in report.issues)

    def test_detect_not_in(self):
        report = self.optimizer.analyze("SELECT id FROM users WHERE id NOT IN (1,2,3)")
        assert any("NOT IN" in i.title for i in report.issues)

    def test_detect_subquery(self):
        report = self.optimizer.analyze(
            "SELECT id FROM users WHERE id IN (SELECT user_id FROM orders)"
        )
        assert any("子查询" in i.title for i in report.issues)

    def test_detect_union(self):
        report = self.optimizer.analyze(
            "SELECT id FROM a UNION SELECT id FROM b"
        )
        assert any("UNION" in i.title for i in report.issues)

    def test_suggestion_not_empty(self):
        report = self.optimizer.analyze("SELECT * FROM users")
        for issue in report.issues:
            assert issue.suggestion != "", f"Issue '{issue.title}' has empty suggestion"

    def test_index_suggestions(self):
        report = self.optimizer.analyze(
            "SELECT id FROM users WHERE status = 'active' ORDER BY created_at"
        )
        assert len(report.index_suggestions) > 0

    def test_complexity_score_range(self):
        report = self.optimizer.analyze("SELECT 1")
        assert 1 <= report.complexity_score <= 10

    def test_complexity_increases_with_joins(self):
        simple = self.optimizer.analyze("SELECT id FROM users")
        complex_sql = self.optimizer.analyze(
            "SELECT a.id FROM a JOIN b ON a.id = b.a_id JOIN c ON b.id = c.b_id"
        )
        assert complex_sql.complexity_score >= simple.complexity_score

    def test_optimized_sql_contains_comments(self):
        report = self.optimizer.analyze("SELECT * FROM users WHERE name LIKE '%test%'")
        assert "优化建议" in report.optimized_sql or "SELECT col1" in report.optimized_sql

    def test_report_to_json(self):
        report = self.optimizer.analyze("SELECT * FROM users")
        json_str = report.to_json()
        assert '"original_sql"' in json_str

    def test_report_to_markdown(self):
        report = self.optimizer.analyze("SELECT * FROM users")
        md = report.to_markdown()
        assert "SQL 查询优化报告" in md

    def test_clean_sql_no_issues(self):
        report = self.optimizer.analyze(
            "SELECT id, name FROM users WHERE id = 1 LIMIT 10"
        )
        assert len(report.issues) == 0
