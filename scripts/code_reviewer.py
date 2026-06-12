#!/usr/bin/env python3
"""
Code Review Engine — 代码审查引擎
支持多维度扫描、严重性分级、修复建议生成
"""

import re
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Tuple
from enum import Enum
from datetime import datetime, timezone, timedelta


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Category(Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    STYLE = "style"
    DOCUMENTATION = "documentation"


SEVERITY_EMOJI = {
    Severity.CRITICAL: "🔴",
    Severity.HIGH: "🟠",
    Severity.MEDIUM: "🟡",
    Severity.LOW: "🔵",
    Severity.INFO: "⚪",
}

SEVERITY_SCORE = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 2,
    Severity.MEDIUM: 5,
    Severity.LOW: 8,
    Severity.INFO: 10,
}


@dataclass
class Issue:
    severity: str
    category: str
    line: int
    title: str
    description: str
    fix: str = ""
    code_before: str = ""
    code_after: str = ""
    owasp: str = ""
    cwe: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class ReviewReport:
    file: str
    language: str
    timestamp: str
    issues: List[Issue]
    dimensions: Dict[str, int]

    @property
    def summary(self) -> Dict[str, int]:
        counts = {s.value: 0 for s in Severity}
        for issue in self.issues:
            counts[issue.severity] += 1
        return counts

    @property
    def overall_score(self) -> float:
        if not self.issues:
            return 10.0
        total = sum(SEVERITY_SCORE[Severity(i.severity)] for i in self.issues)
        avg = total / len(self.issues)
        return round(avg, 1)

    def to_markdown(self) -> str:
        lines = []
        lines.append(f"## 🔍 代码质量审查报告\n")
        lines.append(f"**文件**: `{self.file}`")
        lines.append(f"**语言**: {self.language}")
        lines.append(f"**审查时间**: {self.timestamp}")
        s = self.summary
        lines.append(
            f"**严重性分布**: "
            f"🔴 CRITICAL: {s['CRITICAL']} | "
            f"🟠 HIGH: {s['HIGH']} | "
            f"🟡 MEDIUM: {s['MEDIUM']} | "
            f"🔵 LOW: {s['LOW']} | "
            f"⚪ INFO: {s['INFO']}"
        )
        lines.append("")

        # Group by severity
        for sev in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
            issues = [i for i in self.issues if i.severity == sev.value]
            if not issues:
                continue
            lines.append(f"### {SEVERITY_EMOJI[sev]} {sev.value} 级别问题\n")
            for idx, issue in enumerate(issues, 1):
                lines.append(f"#### {idx}. {issue.title} [{sev.value}]")
                lines.append(f"**位置**: line {issue.line}")
                lines.append(f"**问题**: {issue.description}")
                if issue.code_before:
                    lines.append(f"```\n{issue.code_before}\n```")
                if issue.code_after:
                    lines.append(f"**修复**:\n```\n{issue.code_after}\n```")
                if issue.owasp:
                    lines.append(f"**OWASP**: {issue.owasp}")
                if issue.cwe:
                    lines.append(f"**CWE**: {issue.cwe}")
                lines.append("")

        # Dimension scores
        lines.append("### 📊 维度评分\n")
        lines.append("| 维度 | 评分 | 说明 |")
        lines.append("|------|------|------|")
        dim_desc = {
            "security": "安全检查结果",
            "correctness": "逻辑正确性",
            "maintainability": "代码可维护性",
            "performance": "性能表现",
            "testing": "测试覆盖",
            "style": "代码风格",
        }
        for dim, score in self.dimensions.items():
            desc = dim_desc.get(dim, "")
            if score >= 8:
                status = "✅ 良好"
            elif score >= 5:
                status = "⚠️ 需改进"
            else:
                status = "❌ 严重问题"
            lines.append(f"| {dim} | {score}/10 | {status} |")

        lines.append(f"\n**综合评分**: {self.overall_score}/10")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "file": self.file,
                "language": self.language,
                "timestamp": self.timestamp,
                "summary": self.summary,
                "overall_score": self.overall_score,
                "issues": [i.to_dict() for i in self.issues],
                "dimensions": self.dimensions,
            },
            indent=2,
            ensure_ascii=False,
        )


class CodeReviewer:
    """代码审查引擎 — 多维度扫描 + 严重性分级 + 修复建议"""

    # 安全漏洞模式库
    SECURITY_PATTERNS = [
        # SQL 注入
        (
            Severity.HIGH, Category.SECURITY,
            r"f['\"].*SELECT.*\{",
            "SQL 注入风险：使用 f-string 拼接 SQL",
            "使用参数化查询或 ORM",
            "A03:2021 – Injection",
            "CWE-89",
        ),
        (
            Severity.HIGH, Category.SECURITY,
            r"\.execute\([^,)]*\+",
            "SQL 注入风险：字符串拼接构造查询",
            "使用参数化查询",
            "A03:2021 – Injection",
            "CWE-89",
        ),
        (
            Severity.HIGH, Category.SECURITY,
            r"eval\(",
            "代码注入风险：使用 eval()",
            "避免使用 eval，使用 ast.literal_eval 或 json.loads",
            "A03:2021 – Injection",
            "CWE-95",
        ),
        (
            Severity.HIGH, Category.SECURITY,
            r"exec\(",
            "代码注入风险：使用 exec()",
            "重构为安全的动态导入方案",
            "A03:2021 – Injection",
            "CWE-95",
        ),
        (
            Severity.CRITICAL, Category.SECURITY,
            r"(password|passwd|pwd|secret|api_key|apikey|token)\s*=\s*['\"][^'\"]+['\"]",
            "硬编码敏感信息：检测到密码/密钥/Token",
            "使用环境变量或密钥管理服务",
            "A02:2021 – Cryptographic Failures",
            "CWE-798",
        ),
        (
            Severity.HIGH, Category.SECURITY,
            r"subprocess\.(call|run|Popen)\([^)]*shell\s*=\s*True",
            "命令注入风险：shell=True 启用 Shell 解释",
            "设置 shell=False，使用参数列表",
            "A03:2021 – Injection",
            "CWE-78",
        ),
        (
            Severity.HIGH, Category.SECURITY,
            r"requests?\.(get|post|put|delete)\([^)]*verify\s*=\s*False",
            "SSL 验证被禁用",
            "始终启用 verify=True 或配置证书",
            "A02:2021 – Cryptographic Failures",
            "CWE-295",
        ),
        # XSS 相关（JS/TS/前端）
        (
            Severity.HIGH, Category.SECURITY,
            r"innerHTML\s*=",
            "XSS 风险：直接设置 innerHTML",
            "使用 textContent 或 DOMPurify 清洗",
            "A03:2021 – Injection",
            "CWE-79",
        ),
        (
            Severity.HIGH, Category.SECURITY,
            r"dangerouslySetInnerHTML",
            "XSS 风险：React 危险属性",
            "使用 DOMPurify 清洗后渲染",
            "A03:2021 – Injection",
            "CWE-79",
        ),
    ]

    # 性能问题模式
    PERFORMANCE_PATTERNS = [
        (
            Severity.MEDIUM, Category.PERFORMANCE,
            r"for .+ in .+:\s*\n\s*\.append\(",
            "循环内重复操作：建议使用列表推导式或 map",
            "",
        ),
        (
            Severity.MEDIUM, Category.PERFORMANCE,  # type: ignore
            r"SELECT \* FROM",
            "避免 SELECT *，指定所需字段",
            "",
        ),
        (
            Severity.MEDIUM, Category.PERFORMANCE,
            r"\.get\(.*\)\s*in\s+.*:\s*\n.*\.get\(",
            "N+1 查询模式：循环中重复查询数据库",
            "使用批量查询或 JOIN",
        ),
    ]

    # 代码质量模式
    QUALITY_PATTERNS = [
        (
            Severity.LOW, Category.MAINTAINABILITY,
            r"def .{50,}\(",
            "函数名过长（>50字符），可读性差",
            "缩短函数名，使用清晰简洁的命名",
        ),
        (
            Severity.LOW, Category.STYLE,
            r"print\(",
            "调试代码：包含 print 语句",
            "使用 logging 模块替代 print",
        ),
        (
            Severity.INFO, Category.DOCUMENTATION,
            r"def \w+\([^)]*\):\s*\n(?!\s*[\"']{3})",
            "函数缺少文档字符串",
            "添加 docstring 描述函数功能、参数和返回值",
        ),
        (
            Severity.MEDIUM, Category.MAINTAINABILITY,
            r"if .+:\s*\n(?:.*\n){15,}.*else:",
            "if 分支过长（>15行），建议提取为独立函数",
            "将分支逻辑提取为独立函数",
        ),
        (
            Severity.LOW, Category.CORRECTNESS,
            r"except:",
            "裸 except 捕获所有异常，隐藏错误",
            "指定具体异常类型",
        ),
        (
            Severity.MEDIUM, Category.CORRECTNESS,
            r"except\s+\w+:\s*\n\s*pass",
            "空异常处理（pass），可能隐藏错误",
            "至少记录日志或重新抛出",
        ),
    ]

    def __init__(self, language: str = "python"):
        self.language = language
        self.issues: List[Issue] = []
        self.file_path = ""

    def review(self, code: str, file_path: str = "input") -> ReviewReport:
        """执行完整代码审查"""
        self.file_path = file_path
        self.issues = []
        lines = code.split("\n")

        # 执行各维度扫描
        self._scan_security(code, lines)
        self._scan_performance(code, lines)
        self._scan_quality(code, lines)

        # 计算维度评分
        dimensions = self._compute_dimensions()

        return ReviewReport(
            file=self.file_path,
            language=self.language,
            timestamp=datetime.now(timezone(timedelta(hours=8))).isoformat(),
            issues=self.issues,
            dimensions=dimensions,
        )

    def _scan_security(self, code: str, lines: List[str]):
        """安全扫描"""
        for sev, cat, pattern, desc, fix, owasp, cwe in self.SECURITY_PATTERNS:
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(pattern, stripped, re.IGNORECASE):
                    self.issues.append(
                        Issue(
                            severity=sev.value,
                            category=cat.value,
                            line=i,
                            title=self._shorten(desc, 40),
                            description=desc,
                            fix=fix,
                            code_before=stripped,
                            code_after=fix if fix else "",
                            owasp=owasp or "",
                            cwe=cwe or "",
                        )
                    )

    def _scan_performance(self, code: str, lines: List[str]):
        """性能扫描"""
        for item in self.PERFORMANCE_PATTERNS:
            if len(item) == 3:
                sev, cat, pattern = item
                desc = ""
                fix = ""
            else:
                sev, cat, pattern, desc, fix = item
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(pattern, stripped, re.IGNORECASE):
                    self.issues.append(
                        Issue(
                            severity=sev.value,
                            category=cat.value,
                            line=i,
                            title=self._shorten(desc, 40) if desc else "性能问题",
                            description=desc or f"潜在性能问题: {pattern}",
                            fix=fix,
                            code_before=stripped,
                        )
                    )

    def _scan_quality(self, code: str, lines: List[str]):
        """代码质量扫描"""
        for item in self.QUALITY_PATTERNS:
            if len(item) == 3:
                sev, cat, pattern = item
                desc = ""
                fix = ""
            else:
                sev, cat, pattern, desc, fix = item
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(pattern, stripped, re.IGNORECASE):
                    self.issues.append(
                        Issue(
                            severity=sev.value,
                            category=cat.value,
                            line=i,
                            title=self._shorten(desc, 40) if desc else "代码质量问题",
                            description=desc or f"代码风格问题: {pattern}",
                            fix=fix,
                            code_before=stripped,
                        )
                    )

    def _compute_dimensions(self) -> Dict[str, int]:
        """计算各维度评分"""
        dims = {
            "security": 10,
            "correctness": 10,
            "maintainability": 10,
            "performance": 10,
            "testing": 10,
            "style": 10,
        }

        for issue in self.issues:
            s = SEVERITY_SCORE[Severity(issue.severity)]
            cat = issue.category
            if cat == "security" and s < dims["security"]:
                dims["security"] = s
            elif cat == "performance" and s < dims["performance"]:
                dims["performance"] = s
            elif cat == "maintainability" and s < dims["maintainability"]:
                dims["maintainability"] = s
            elif cat == "correctness" and s < dims["correctness"]:
                dims["correctness"] = s
            elif cat == "style" and s < dims["style"]:
                dims["style"] = s

        return dims

    @staticmethod
    def _shorten(text: str, max_len: int = 40) -> str:
        return text[:max_len] + "..." if len(text) > max_len else text


def main():
    import sys

    if len(sys.argv) < 2:
        print("用法: python code_reviewer.py <code_file> [language]")
        sys.exit(1)

    file_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "python"

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    reviewer = CodeReviewer(language)
    report = reviewer.review(code, file_path)

    # 输出
    if len(sys.argv) > 3 and sys.argv[3] == "--json":
        print(report.to_json())
    else:
        print(report.to_markdown())


if __name__ == "__main__":
    main()
