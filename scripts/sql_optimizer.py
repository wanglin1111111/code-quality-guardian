#!/usr/bin/env python3
"""
SQL Optimizer — SQL 查询分析与优化建议引擎
支持 MySQL / PostgreSQL / SQLite
功能：慢查询识别、执行计划分析、索引建议、重写优化
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timezone, timedelta


@dataclass
class SQLIssue:
    severity: str  # HIGH / MEDIUM / LOW
    title: str
    description: str
    suggestion: str
    optimized_sql: str = ""
    line: int = 0

    def to_dict(self):
        return asdict(self)


@dataclass
class SQLReport:
    original_sql: str
    db_type: str
    timestamp: str
    issues: List[SQLIssue]
    optimized_sql: str
    index_suggestions: List[str]
    complexity_score: int  # 1-10

    def to_markdown(self) -> str:
        lines = []
        lines.append("## 🚀 SQL 查询优化报告\n")
        lines.append(f"**数据库类型**: {self.db_type}")
        lines.append(f"**分析时间**: {self.timestamp}")
        lines.append(f"**复杂度评分**: {self.complexity_score}/10")
        lines.append("")

        if self.issues:
            lines.append("### ⚠️ 发现的问题\n")
            for idx, issue in enumerate(self.issues, 1):
                emoji = {"HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}.get(issue.severity, "•")
                lines.append(f"#### {idx}. {emoji} {issue.title} [{issue.severity}]")
                if issue.line:
                    lines.append(f"**位置**: line {issue.line}")
                lines.append(f"**问题**: {issue.description}")
                lines.append(f"**建议**: {issue.suggestion}")
                if issue.optimized_sql:
                    lines.append(f"**优化SQL**:")
                    lines.append(f"```sql")
                    lines.append(issue.optimized_sql)
                    lines.append("```")
                lines.append("")

        if self.index_suggestions:
            lines.append("### 📇 索引建议\n")
            for idx, idx_sug in enumerate(self.index_suggestions, 1):
                lines.append(f"{idx}. `{idx_sug}`")
            lines.append("")

        if self.optimized_sql:
            lines.append("### ✅ 优化后的 SQL\n")
            lines.append("```sql")
            lines.append(self.optimized_sql)
            lines.append("```\n")

        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "original_sql": self.original_sql,
                "db_type": self.db_type,
                "timestamp": self.timestamp,
                "issues": [i.to_dict() for i in self.issues],
                "optimized_sql": self.optimized_sql,
                "index_suggestions": self.index_suggestions,
                "complexity_score": self.complexity_score,
            },
            indent=2,
            ensure_ascii=False,
        )


class SQLOptimizer:
    """SQL 查询分析与优化引擎"""

    # 问题检测规则
    RULES = [
        # 严重问题
        {
            "id": "select_star",
            "severity": "MEDIUM",
            "pattern": r"SELECT\s+\*\s+FROM",
            "title": "使用 SELECT *",
            "description": "SELECT * 会查询所有列，增加 I/O 和网络开销，且可能导致无法使用覆盖索引",
            "suggestion": "将 SELECT * 替换为明确指定所需字段名，减少不必要的数据传输",
            "category": "performance",
        },
        {
            "id": "cartesian_product",
            "severity": "HIGH",
            "pattern": r"FROM\s+\w+(?:\s+\w+)?(?:\s*,\s*\w+){2,}",
            "title": "可能存在笛卡尔积",
            "description": "多个表之间缺少 JOIN 条件，可能导致笛卡尔积，数据量爆炸",
            "suggestion": "为每个表之间添加明确的 JOIN 条件，避免隐式笛卡尔积",
            "category": "correctness",
        },
        {
            "id": "no_where_clause",
            "severity": "MEDIUM",
            "pattern": r"^(?!.*WHERE)(?!.*HAVING)(?!.*LIMIT)(?!.*JOIN)(?!.*WHERE).*SELECT.*FROM",
            "title": "全表扫描",
            "description": "查询缺少 WHERE 条件，可能导致全表扫描",
            "suggestion": "添加 WHERE 条件过滤数据，或添加 LIMIT 限制返回行数",
            "category": "performance",
        },
        {
            "id": "like_leading_wildcard",
            "severity": "MEDIUM",
            "pattern": r"LIKE\s+['\"](?:%[^%]*|_)|(?:%[^%]*)",
            "title": "前导通配符查询",
            "description": "LIKE '%xxx' 无法使用 B-tree 索引，导致全表扫描",
            "suggestion": "考虑使用全文索引 (FULLTEXT) 或反向索引，避免前缀通配符",
            "category": "performance",
        },
        {
            "id": "or_in_where",
            "severity": "LOW",
            "pattern": r"WHERE\s+\w+\s*=\s*[^C]+\s+OR\s+\w+\s*=",
            "title": "OR 条件可能影响索引使用",
            "description": "WHERE 子句中使用多个 OR 条件可能导致索引失效",
            "suggestion": "将 OR 条件改为 IN 列表，或使用 UNION ALL 拆分多个查询",
            "category": "performance",
        },
        {
            "id": "function_on_column",
            "severity": "MEDIUM",
            "pattern": r"WHERE\s+\w+\s*\([^)]*\w+[^)]*\)",
            "title": "在索引列上使用函数",
            "description": "在 WHERE 条件中对索引列使用函数会导致索引失效",
            "suggestion": "避免在索引列上使用函数，可预先计算并存储结果",
            "category": "performance",
        },
        {
            "id": "not_in",
            "severity": "MEDIUM",
            "pattern": r"NOT\s+IN\s*\(",
            "title": "使用 NOT IN",
            "description": "NOT IN 对 NULL 值行为不确定，且通常无法使用索引",
            "suggestion": "将 NOT IN 改为 NOT EXISTS 或 LEFT JOIN ... WHERE ... IS NULL",
            "category": "performance",
        },
        {
            "id": "subquery_in_where",
            "severity": "MEDIUM",
            "pattern": r"WHERE\s+\w+\s+(?:IN|NOT IN|EXISTS|NOT EXISTS)\s*\(\s*SELECT",
            "title": "子查询可能效率低下",
            "description": "WHERE 子句中的子查询可能被多次执行，建议改为 JOIN",
            "suggestion": "将子查询重构为 JOIN，或使用 CTE (WITH 语句) 优化",
            "category": "performance",
        },
        {
            "id": "distinct_with_join",
            "severity": "LOW",
            "pattern": r"SELECT\s+DISTINCT.*JOIN",
            "title": "DISTINCT + JOIN 可能暗示设计问题",
            "description": "DISTINCT 与 JOIN 一起使用可能是重复数据的修复手段，建议检查 JOIN 条件",
            "suggestion": "检查 JOIN 条件是否正确，考虑使用 EXISTS 子查询替代",
            "category": "correctness",
        },
        {
            "id": "order_by_without_limit",
            "severity": "LOW",
            "pattern": r"ORDER\s+BY\s+\w+(?!.*LIMIT)",
            "title": "ORDER BY 无 LIMIT",
            "description": "ORDER BY 但没有 LIMIT 会对全量结果排序，开销大",
            "suggestion": "添加 LIMIT 限制排序结果数量，减少排序开销",
            "category": "performance",
        },
        {
            "id": "union_all_vs_union",
            "severity": "LOW",
            "pattern": r"\bUNION\s(?!ALL)",
            "title": "使用 UNION 而非 UNION ALL",
            "description": "UNION 会去重（排序+比较），如果不需要去重使用 UNION ALL",
            "suggestion": "如不需去重，将 UNION 改为 UNION ALL 以提升性能",
            "category": "performance",
        },
    ]

    @classmethod
    def _compile_rules(cls, rules: list) -> list:
        """为规则列表预编译正则表达式"""
        compiled = []
        for rule in rules:
            compiled_rule = dict(rule)
            compiled_rule["_compiled"] = re.compile(rule["pattern"], re.IGNORECASE)
            compiled.append(compiled_rule)
        return compiled

    def __init__(self, db_type: str = "MySQL"):
        self.db_type = db_type
        self.issues: List[SQLIssue] = []
        self.sql = ""
        self._compiled_rules = self._compile_rules(self.RULES)

    def analyze(self, sql: str) -> SQLReport:
        """执行 SQL 分析"""
        self.sql = sql.strip().rstrip(";")
        self.issues = []

        # 执行规则检测
        self._apply_rules()

        # 提取表名
        tables = self._extract_tables()

        # 生成索引建议
        index_suggestions = self._suggest_indexes(tables)

        # 生成优化 SQL
        optimized = self._generate_optimized_sql()

        # 计算复杂度
        complexity = self._compute_complexity()

        return SQLReport(
            original_sql=self.sql,
            db_type=self.db_type,
            timestamp=datetime.now(timezone(timedelta(hours=8))).isoformat(),
            issues=self.issues,
            optimized_sql=optimized,
            index_suggestions=index_suggestions,
            complexity_score=complexity,
        )

    def _apply_rules(self):
        """应用检测规则"""
        lines = self.sql.split("\n")
        for line_num, line in enumerate(lines, 1):
            for rule in self._compiled_rules:
                if rule["_compiled"].search(line):
                    self.issues.append(
                        SQLIssue(
                            severity=rule["severity"],
                            title=rule["title"],
                            description=rule["description"],
                            suggestion=rule.get("suggestion", ""),
                            line=line_num,
                        )
                    )

    def _extract_tables(self) -> List[str]:
        """提取 SQL 中的表名"""
        tables = []
        # FROM 子句
        from_match = re.findall(r"FROM\s+(\w+)", self.sql, re.IGNORECASE)
        tables.extend(from_match)
        # JOIN 子句
        join_match = re.findall(r"JOIN\s+(\w+)", self.sql, re.IGNORECASE)
        tables.extend(join_match)
        return list(set(tables))

    def _suggest_indexes(self, tables: List[str]) -> List[str]:
        """生成索引建议"""
        suggestions = []
        sql_upper = self.sql.upper()

        # WHERE 条件列
        where_columns = re.findall(r"WHERE\s+(\w+)\s*[=<>]", self.sql, re.IGNORECASE)
        for col in where_columns:
            suggestions.append(f"CREATE INDEX idx_{col} ON {tables[0] if tables else 'table_name'} ({col});")

        # ORDER BY 列
        order_columns = re.findall(r"ORDER\s+BY\s+(\w+)", self.sql, re.IGNORECASE)
        for col in order_columns:
            if col not in where_columns:
                suggestions.append(f"CREATE INDEX idx_{col}_order ON {tables[0] if tables else 'table_name'} ({col});")

        # JOIN 条件列
        join_cols = re.findall(r"ON\s+\w+\.(\w+)\s*=\s*\w+\.(\w+)", self.sql, re.IGNORECASE)
        for t1_col, t2_col in join_cols:
            suggestions.append(f"CREATE INDEX idx_{t2_col} ON {tables[1] if len(tables) > 1 else 'table2'} ({t2_col});")

        return list(set(suggestions))[:5]  # 最多返回5条建议

    def _generate_optimized_sql(self) -> str:
        """生成优化后的 SQL"""
        optimized = self.sql

        # SELECT * → SELECT col1, col2...
        star_match = re.search(r"SELECT\s+\*\s+FROM", optimized, re.IGNORECASE)
        if star_match:
            # 保留原始，添加注释说明
            optimized = re.sub(
                r"(SELECT\s+\*\s+FROM)",
                r"SELECT col1, col2, col3 /* TODO: 替换为具体需要的字段 */ FROM",
                optimized,
                flags=re.IGNORECASE,
            )

        # 前导通配符 LIKE → 建议全文索引
        if re.search(r"LIKE\s+['\"]%", optimized, re.IGNORECASE):
            optimized += "\n-- 考虑使用全文索引 (FULLTEXT) 替代 LIKE '%xxx%'"

        # 添加注释
        optimized += "\n-- 优化建议："
        for issue in self.issues:
            if issue.severity in ("HIGH", "MEDIUM"):
                optimized += f"\n-- [{issue.severity}] {issue.title}: {issue.suggestion}"

        return optimized

    def _compute_complexity(self) -> int:
        """计算 SQL 复杂度（1-10）"""
        score = 1
        # JOIN 数量
        joins = len(re.findall(r"\bJOIN\b", self.sql, re.IGNORECASE))
        score += min(joins * 2, 4)
        # 子查询
        subqueries = len(re.findall(r"\(\s*SELECT", self.sql, re.IGNORECASE))
        score += min(subqueries * 2, 3)
        # UNION
        if re.search(r"\bUNION\b", self.sql, re.IGNORECASE):
            score += 1
        # GROUP BY
        if re.search(r"\bGROUP\s+BY\b", self.sql, re.IGNORECASE):
            score += 1
        return min(score, 10)


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="SQL 查询分析与优化建议引擎")
    parser.add_argument("sql_file", help="包含 SQL 的文件路径")
    parser.add_argument("--db-type", default="MySQL",
                        choices=["MySQL", "PostgreSQL", "SQLite"],
                        help="数据库类型 (默认: MySQL)")
    parser.add_argument("--json", action="store_true", dest="output_json",
                        help="以 JSON 格式输出")
    args = parser.parse_args()

    try:
        with open(args.sql_file, "r", encoding="utf-8") as f:
            sql = f.read()
    except FileNotFoundError:
        print(f"错误: 文件 '{args.sql_file}' 不存在")
        sys.exit(1)
    except PermissionError:
        print(f"错误: 无权读取文件 '{args.sql_file}'")
        sys.exit(1)

    optimizer = SQLOptimizer(args.db_type)
    report = optimizer.analyze(sql)

    if args.output_json:
        print(report.to_json())
    else:
        print(report.to_markdown())


if __name__ == "__main__":
    main()
