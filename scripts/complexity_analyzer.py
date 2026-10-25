#!/usr/bin/env python3
"""
Complexity Analyzer — 代码复杂度分析工具
计算圈复杂度(Cyclomatic Complexity)和认知复杂度
"""

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class ComplexityResult:
    function_name: str
    line_start: int
    line_end: int
    cyclomatic: int
    cognitive: int
    lines_of_code: int
    risk_level: str

    def to_dict(self):
        return asdict(self)


@dataclass
class ComplexityReport:
    file: str
    language: str
    timestamp: str
    results: list[ComplexityResult]
    avg_cyclomatic: float
    avg_cognitive: float
    hotspot_functions: list[str]

    def to_markdown(self) -> str:
        lines = []
        lines.append("## 📐 代码复杂度分析报告\n")
        lines.append(f"**文件**: `{self.file}`")
        lines.append(f"**语言**: {self.language}")
        lines.append(f"**分析时间**: {self.timestamp}")
        lines.append(f"**函数数量**: {len(self.results)}")
        lines.append(f"**平均圈复杂度**: {self.avg_cyclomatic:.1f}")
        lines.append(f"**平均认知复杂度**: {self.avg_cognitive:.1f}")
        lines.append("")

        if self.hotspot_functions:
            lines.append("### 🔥 高复杂度热点函数\n")
            for fn in self.hotspot_functions:
                lines.append(f"- `{fn}`")
            lines.append("")

        lines.append("### 📊 详细分析\n")
        lines.append("| 函数 | 行范围 | 圈复杂度 | 认知复杂度 | 代码行数 | 风险 |")
        lines.append("|------|--------|----------|------------|----------|------|")
        for r in sorted(self.results, key=lambda x: -x.cyclomatic):
            risk_emoji = {"✅ 低": "✅", "⚠️ 中": "⚠️", "🔴 高": "🔴"}.get(r.risk_level, "")
            lines.append(
                f"| `{r.function_name}` | {r.line_start}-{r.line_end} | "
                f"{r.cyclomatic} | {r.cognitive} | {r.lines_of_code} | "
                f"{risk_emoji} {r.risk_level} |"
            )
        lines.append("")

        lines.append("### 📋 复杂度标准\n")
        lines.append("| 圈复杂度 | 风险等级 | 建议 |")
        lines.append("|----------|----------|------|")
        lines.append("| 1-5 | ✅ 低 | 可维护性良好 |")
        lines.append("| 6-10 | ⚠️ 中 | 建议简化逻辑 |")
        lines.append("| 11-20 | 🔴 高 | 需要重构 |")
        lines.append("| 20+ | 🔴 极高 | 紧急重构 |")

        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "file": self.file,
                "language": self.language,
                "timestamp": self.timestamp,
                "results": [r.to_dict() for r in self.results],
                "avg_cyclomatic": self.avg_cyclomatic,
                "avg_cognitive": self.avg_cognitive,
                "hotspot_functions": self.hotspot_functions,
            },
            indent=2,
            ensure_ascii=False,
        )


class ComplexityAnalyzer:
    """代码复杂度分析工具"""

    # 复杂度阈值
    CYCLOMATIC_THRESHOLDS = {"low": 5, "medium": 10, "high": 20}
    COGNITIVE_THRESHOLDS = {"low": 8, "medium": 15, "high": 25}

    # 圈复杂度增量规则
    CYCLOMATIC_INCREMENT = {
        "if": 1,
        "elif": 1,
        "else": 0,
        "for": 1,
        "while": 1,
        "except": 1,
        "and": 1,
        "or": 1,
        "case": 1,
        "catch": 1,
        "?:": 1,  # ternary
        "&&": 1,
        "||": 1,
    }

    def __init__(self, language: str = "python"):
        self.language = language
        self.results: list[ComplexityResult] = []

    def analyze(self, code: str, file_path: str = "input") -> ComplexityReport:
        """执行复杂度分析"""
        self.results = []
        lines = code.split("\n")

        # 提取函数
        functions = self._extract_functions(lines)

        for fn_name, start, end in functions:
            fn_lines = lines[start - 1 : end]
            fn_code = "\n".join(fn_lines)
            loc = len([line for line in fn_lines if line.strip()])

            cc = self._cyclomatic_complexity(fn_code)
            cog = self._cognitive_complexity(fn_code)

            risk = self._risk_level(cc, cog)

            self.results.append(
                ComplexityResult(
                    function_name=fn_name,
                    line_start=start,
                    line_end=end,
                    cyclomatic=cc,
                    cognitive=cog,
                    lines_of_code=loc,
                    risk_level=risk,
                )
            )

        # 计算热点
        hotspots = [r.function_name for r in self.results if r.cyclomatic > 10]

        # 平均值
        avg_cc = sum(r.cyclomatic for r in self.results) / len(self.results) if self.results else 0
        avg_cog = sum(r.cognitive for r in self.results) / len(self.results) if self.results else 0

        return ComplexityReport(
            file=file_path,
            language=self.language,
            timestamp=datetime.now(timezone(timedelta(hours=8))).isoformat(),
            results=self.results,
            avg_cyclomatic=round(avg_cc, 1),
            avg_cognitive=round(avg_cog, 1),
            hotspot_functions=hotspots,
        )

    def _extract_functions(self, lines: list[str]) -> list[tuple[str, int, int]]:
        """提取函数定义及其行范围"""
        functions = []
        stack = []

        fn_patterns = {
            "python": r"^\s*def\s+(\w+)\s*\(",
            "javascript": r"^\s*(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\()",
            "typescript": r"^\s*(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\()",
            "java": r"^\s*(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(",
            "go": r"^\s*func\s+(?:\([^)]*\)\s+)?(\w+)\s*\(",
        }

        pattern = fn_patterns.get(self.language, fn_patterns["python"])

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue

            indent = len(line) - len(line.lstrip())

            # 检查是否为函数定义
            match = re.match(pattern, line)
            if match:
                fn_name = next((g for g in match.groups() if g), "unknown")
                stack.append((fn_name, i, indent))
                continue

            # 检查缩进回退（函数结束）
            while stack and indent <= stack[-1][2] and stripped not in ("}", ")", "]", ""):
                fn_name, start_line, _ = stack.pop()
                functions.append((fn_name, start_line, i - 1))
                break

        # 关闭剩余函数
        for fn_name, start_line, _ in reversed(stack):
            functions.append((fn_name, start_line, len(lines)))

        return functions

    def _cyclomatic_complexity(self, code: str) -> int:
        """计算圈复杂度（基础值1 + 分支数）"""
        cc = 1
        for keyword in self.CYCLOMATIC_INCREMENT:
            cc += code.count(keyword)
        return cc

    def _cognitive_complexity(self, code: str) -> int:
        """计算认知复杂度（简化版）"""
        cog = 0
        lines = code.split("\n")

        for line in lines:
            stripped = line.strip()

            # 嵌套 if 增加认知负担
            if re.match(r"\s+if\s", line):
                cog += 1 + line.count("  ")  # 缩进深度加成

            # for/while 循环
            if re.match(r"\s+(for|while)\s", line):
                cog += 1

            # 嵌套函数（lambda/闭包）
            if "lambda" in stripped:
                cog += 2

            # 逻辑运算符
            cog += line.count(" and ") + line.count(" or ")
            cog += line.count(" && ") + line.count(" || ")

        return cog

    def _risk_level(self, cc: int, cog: int) -> str:
        """风险等级评估"""
        if cc > self.CYCLOMATIC_THRESHOLDS["high"] or cog > self.COGNITIVE_THRESHOLDS["high"]:
            return "🔴 高"
        elif cc > self.CYCLOMATIC_THRESHOLDS["medium"] or cog > self.COGNITIVE_THRESHOLDS["medium"]:
            return "⚠️ 中"
        else:
            return "✅ 低"


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="代码复杂度分析工具")
    parser.add_argument("code_file", help="待分析的源代码文件路径")
    parser.add_argument("language", nargs="?", default="python", help="编程语言 (默认: python)")
    parser.add_argument("--json", action="store_true", dest="output_json", help="以 JSON 格式输出")
    args = parser.parse_args()

    try:
        with open(args.code_file, encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"错误: 文件 '{args.code_file}' 不存在")
        sys.exit(1)
    except PermissionError:
        print(f"错误: 无权读取文件 '{args.code_file}'")
        sys.exit(1)

    analyzer = ComplexityAnalyzer(args.language)
    report = analyzer.analyze(code, args.code_file)

    if args.output_json:
        print(report.to_json())
    else:
        print(report.to_markdown())


if __name__ == "__main__":
    main()
