#!/usr/bin/env python3
"""
Log Analyzer — 日志分析与异常检测引擎
功能：异常模式检测、根因分析、告警规则生成、日志格式化建议
"""

import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass


@dataclass
class LogPattern:
    pattern: str
    count: int
    severity: str  # CRITICAL / HIGH / MEDIUM / LOW
    first_seen: str
    last_seen: str
    sample_lines: list[str]

    def to_dict(self):
        return asdict(self)


@dataclass
class LogReport:
    log_file: str
    total_lines: int
    time_range: str
    patterns: list[LogPattern]
    root_causes: list[dict]
    alert_rules: list[str]
    format_issues: list[str]

    def to_markdown(self) -> str:
        lines = []
        lines.append("## 📊 日志分析报告\n")
        lines.append(f"**日志文件**: `{self.log_file}`")
        lines.append(f"**总行数**: {self.total_lines}")
        lines.append(f"**时间范围**: {self.time_range}")
        lines.append("")

        # 异常模式
        lines.append("### 🔍 异常模式检测\n")
        lines.append("| 严重性 | 模式 | 出现次数 | 首次 | 最近 |")
        lines.append("|--------|------|----------|------|------|")
        for p in self.patterns:
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}.get(p.severity, "•")
            lines.append(f"| {emoji} {p.severity} | `{p.pattern}` | {p.count} | {p.first_seen} | {p.last_seen} |")
        lines.append("")

        # 根因分析
        if self.root_causes:
            lines.append("### 🔎 根因分析\n")
            for idx, rc in enumerate(self.root_causes, 1):
                lines.append(f"**{idx}. {rc['title']}** (置信度: {rc['confidence']})")
                lines.append(f"- 关联错误: `{rc['pattern']}`")
                lines.append(f"- 可能原因: {rc['possible_cause']}")
                lines.append(f"- 建议行动: {rc['action']}")
                lines.append("")

        # 告警规则
        if self.alert_rules:
            lines.append("### 🚨 建议告警规则\n")
            for rule in self.alert_rules:
                lines.append(f"- {rule}")
            lines.append("")

        # 格式化建议
        if self.format_issues:
            lines.append("### 📝 日志格式化建议\n")
            for issue in self.format_issues:
                lines.append(f"- {issue}")
            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "log_file": self.log_file,
                "total_lines": self.total_lines,
                "time_range": self.time_range,
                "patterns": [p.to_dict() for p in self.patterns],
                "root_causes": self.root_causes,
                "alert_rules": self.alert_rules,
                "format_issues": self.format_issues,
            },
            indent=2,
            ensure_ascii=False,
        )


class LogAnalyzer:
    """日志分析与异常检测引擎"""

    # 异常模式库（优先级从高到低）
    ERROR_PATTERNS = [
        # CRITICAL
        (r"OutOfMemoryError|OOM|memory\s+exhausted", "CRITICAL", "内存溢出"),
        (r"StackOverflowError|stack\s+overflow", "CRITICAL", "栈溢出"),
        (r"Segmentation fault|SIGSEGV|core\s+dumped", "CRITICAL", "段错误"),
        (r"Fatal\s+error|PANIC|panic:", "CRITICAL", "致命错误"),
        (r"deadlock|Deadlock\s+detected", "CRITICAL", "死锁"),
        (r"data\s+corruption|checksum\s+mismatch|CRC\s+error", "CRITICAL", "数据损坏"),
        # HIGH（具体分类必须先于通用 ERROR\s+\w+，否则会被吞成“运行时异常”）
        (r"ConnectionRefused|ConnectionTimeout|connect\s+timeout", "HIGH", "连接超时"),
        (r"PermissionDenied|403\s+Forbidden|access\s+denied", "HIGH", "权限拒绝"),
        (r"DatabaseError|SQLException|duplicate\s+key|constraint", "HIGH", "数据库错误"),
        (r"DiskFull|No space left|ENOSPC", "HIGH", "磁盘满"),
        (r"certificate\s+(?:verify|expir|invalid)", "HIGH", "证书问题"),
        (r"Error:\s*\w+Error|ERROR\s+\w+|exception|Exception", "HIGH", "运行时异常"),
        # MEDIUM
        (r"Warning:|WARN\s+\w+|warn\s+\w+", "MEDIUM", "警告"),
        (r"timeout|timed?\s*out", "MEDIUM", "超时"),
        (r"retry|retrying", "MEDIUM", "重试"),
        (r"rate\s+limit|429\s+Too\s+Many", "MEDIUM", "限流"),
        (r"deprecated|DeprecationWarning", "MEDIUM", "弃用警告"),
        (r"slow\s+query|SlowQuery|query\s+took", "MEDIUM", "慢查询"),
        # LOW
        (r"DEBUG\s+\w+|debug\s+\w+", "LOW", "调试信息"),
        (r"INFO\s+\w+", "LOW", "普通信息"),
    ]

    # 告警规则模板
    ALERT_RULE_TEMPLATES = [
        "每分钟出现超过 5 次 {pattern} → 触发 P1 告警",
        "连续 3 分钟出现 {pattern} → 触发 P2 告警",
        "{pattern} 与上次出现间隔 < 30 秒 → 触发 P1 告警（可能风暴）",
        "{pattern} 首次出现 → 记录事件，3 分钟内无重复则自动解除",
    ]

    def __init__(self):
        self.patterns_found: list[LogPattern] = []
        self.total_lines = 0
        self.time_range = ""
        self.format_issues: list[str] = []

    def analyze(self, log_content: str, log_file: str = "input", log_format: str = "plain") -> LogReport:
        """执行日志分析，返回 LogReport 对象"""
        self.total_lines = len(log_content.split("\n"))
        self.patterns_found = []

        lines = log_content.split("\n")

        # 提取时间范围
        self.time_range = self._extract_time_range(lines)

        # 检测时间格式
        self._check_format(lines, log_format)

        # 模式匹配与统计
        pattern_data = defaultdict(lambda: {"count": 0, "first": "", "last": "", "samples": []})

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            for pattern, _severity, label in self.ERROR_PATTERNS:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    key = f"{label}"
                    pattern_data[key]["count"] += 1
                    if not pattern_data[key]["first"]:
                        pattern_data[key]["first"] = self._extract_timestamp(line_stripped)
                    pattern_data[key]["last"] = self._extract_timestamp(line_stripped)
                    if len(pattern_data[key]["samples"]) < 3:
                        pattern_data[key]["samples"].append(line_stripped[:80])
                    break  # 每行只匹配第一个

        # 转换为 LogPattern 对象
        for label, data in sorted(pattern_data.items(), key=lambda x: -x[1]["count"]):
            sev = next((sev_value for _pattern, sev_value, lbl in self.ERROR_PATTERNS if lbl == label), "MEDIUM")
            self.patterns_found.append(
                LogPattern(
                    pattern=label,
                    count=data["count"],
                    severity=sev,
                    first_seen=data["first"] or "unknown",
                    last_seen=data["last"] or "unknown",
                    sample_lines=data["samples"],
                )
            )

        # 根因分析
        root_causes = self._root_cause_analysis()

        # 生成告警规则
        alert_rules = self._generate_alert_rules()

        return LogReport(
            log_file=log_file,
            total_lines=self.total_lines,
            time_range=self.time_range,
            patterns=list(self.patterns_found),
            root_causes=root_causes,
            alert_rules=alert_rules,
            format_issues=list(self.format_issues),
        )

    def _extract_time_range(self, lines: list[str]) -> str:
        """从日志中提取时间范围"""
        timestamps = []
        for line in lines[:100]:
            ts = self._extract_timestamp(line)
            if ts and ts != "unknown":
                timestamps.append(ts)
        if len(timestamps) >= 2:
            return f"{timestamps[0]} ~ {timestamps[-1]}"
        elif timestamps:
            return timestamps[0]
        return "unknown"

    def _extract_timestamp(self, line: str) -> str:
        """提取行中的时间戳"""
        patterns = [
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}",
            r"\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}",
            r"\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}",
        ]
        for p in patterns:
            match = re.search(p, line)
            if match:
                return match.group()
        return "unknown"

    def _check_format(self, lines: list[str], log_format: str):
        """检查日志格式问题"""
        if log_format == "plain":
            # 检查是否缺少时间戳
            no_timestamp = sum(1 for line in lines[:50] if self._extract_timestamp(line) == "unknown")
            if no_timestamp > 20:
                self.format_issues.append("超过 40% 的行缺少时间戳，建议统一添加 ISO 格式时间戳")
            # 检查是否缺少级别标识
            no_level = sum(1 for line in lines[:50] if not re.search(r"(ERROR|WARN|INFO|DEBUG)", line, re.IGNORECASE))
            if no_level > 30:
                self.format_issues.append("缺少日志级别标识，建议添加 ERROR/WARN/INFO 前缀")

    def _root_cause_analysis(self) -> list[dict]:
        """根因分析"""
        causes = []

        # OOM 根因
        oom = next((p for p in self.patterns_found if "内存溢出" in p.pattern), None)
        if oom:
            causes.append(
                {
                    "title": "内存溢出 (OOM)",
                    "confidence": "高",
                    "pattern": oom.pattern,
                    "possible_cause": "大量数据处理、内存泄漏、JVM 堆配置不足",
                    "action": "检查堆内存配置、分析堆转储、排查大对象缓存",
                }
            )

        # 连接超时根因
        timeout = next((p for p in self.patterns_found if "连接超时" in p.pattern), None)
        if timeout:
            causes.append(
                {
                    "title": "网络连接不稳定",
                    "confidence": "中高",
                    "pattern": timeout.pattern,
                    "possible_cause": "下游服务过载、网络抖动、连接池耗尽",
                    "action": "检查下游服务状态、增加重试机制、扩展连接池",
                }
            )

        # 权限拒绝根因
        perm = next((p for p in self.patterns_found if "权限拒绝" in p.pattern), None)
        if perm:
            causes.append(
                {
                    "title": "权限配置问题",
                    "confidence": "高",
                    "pattern": perm.pattern,
                    "possible_cause": "服务账号权限变更、文件权限、API 密钥过期",
                    "action": "验证服务账号权限、检查 IAM 策略轮换",
                }
            )

        # 异常频率根因
        errors = next((p for p in self.patterns_found if "运行时异常" in p.pattern), None)
        if errors and errors.count > 10:
            causes.append(
                {
                    "title": "高频运行时异常",
                    "confidence": "中高",
                    "pattern": errors.pattern,
                    "possible_cause": "边界条件未处理、外部依赖不稳定、数据格式异常",
                    "action": "添加异常捕获、加强输入验证、增加熔断机制",
                }
            )

        return causes

    def _generate_alert_rules(self) -> list[str]:
        """生成告警规则"""
        rules = []
        for p in self.patterns_found[:5]:  # 最多5条规则
            for template in self.ALERT_RULE_TEMPLATES[:1]:  # 每条模式1条规则
                rules.append(template.format(pattern=p.pattern))
        return rules


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="日志分析与异常检测引擎")
    parser.add_argument("log_file", help="日志文件路径")
    parser.add_argument("--format", default="plain", choices=["plain", "json", "syslog"], help="日志格式 (默认: plain)")
    parser.add_argument("--json", action="store_true", dest="output_json", help="以 JSON 格式输出")
    args = parser.parse_args()

    try:
        with open(args.log_file, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 文件 '{args.log_file}' 不存在")
        sys.exit(1)
    except PermissionError:
        print(f"错误: 无权读取文件 '{args.log_file}'")
        sys.exit(1)

    analyzer = LogAnalyzer()
    report = analyzer.analyze(content, log_file=args.log_file, log_format=args.format)

    if args.output_json:
        print(report.to_json())
    else:
        print(report.to_markdown())


if __name__ == "__main__":
    main()
