#!/usr/bin/env python3
"""
Security Scanner — 安全漏洞扫描器
覆盖 OWASP Top 10 + CWE Top 25
功能：依赖安全检测、密钥扫描、注入攻击检测、权限校验
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta


@dataclass
class SecurityIssue:
    severity: str
    category: str
    line: int
    title: str
    description: str
    fix: str
    owasp: str = ""
    cwe: str = ""
    code_snippet: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class SecurityReport:
    file: str
    language: str
    timestamp: str
    issues: List[SecurityIssue]
    risk_score: int  # 0-10
    risk_level: str

    def to_markdown(self) -> str:
        lines = []
        lines.append("## 🛡️ 安全漏洞扫描报告\n")
        lines.append(f"**文件**: `{self.file}`")
        lines.append(f"**语言**: {self.language}")
        lines.append(f"**扫描时间**: {self.timestamp}")
        lines.append(f"**风险评分**: {self.risk_score}/10 ({self.risk_level})")
        lines.append("")

        if not self.issues:
            lines.append("✅ 未发现安全漏洞。")
            return "\n".join(lines)

        # Group by category
        categories = {}
        for issue in self.issues:
            categories.setdefault(issue.category, []).append(issue)

        for cat, issues in categories.items():
            cat_emoji = {
                "injection": "💉", "xss": "🔥", "csrf": "🎭",
                "auth": "🔑", "crypto": "🔐", "exposure": "📦",
                "config": "⚙️", "dependency": "📦", "hardcoded": "🔓"
            }.get(cat, "⚠️")
            lines.append(f"### {cat_emoji} {cat.upper()} 类漏洞\n")
            for idx, issue in enumerate(issues, 1):
                emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}.get(issue.severity, "•")
                lines.append(f"#### {idx}. {emoji} {issue.title} [{issue.severity}]")
                lines.append(f"**位置**: line {issue.line}")
                lines.append(f"**问题**: {issue.description}")
                if issue.code_snippet:
                    lines.append(f"**代码**:")
                    lines.append(f"```{self.language}")
                    lines.append(issue.code_snippet)
                    lines.append("```")
                lines.append(f"**修复**: {issue.fix}")
                if issue.owasp:
                    lines.append(f"**OWASP**: {issue.owasp}")
                if issue.cwe:
                    lines.append(f"**CWE**: {issue.cwe}")
                lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "file": self.file,
                "language": self.language,
                "timestamp": self.timestamp,
                "risk_score": self.risk_score,
                "risk_level": self.risk_level,
                "issues": [i.to_dict() for i in self.issues],
            },
            indent=2,
            ensure_ascii=False,
        )


class SecurityScanner:
    """安全漏洞扫描器 — OWASP Top 10 + CWE Top 25"""

    # OWASP Top 10 (2021) 规则
    OWASP_RULES = [
        # A01: Broken Access Control
        {
            "severity": "HIGH", "category": "auth",
            "pattern": r"(?:@RequestMapping|@GetMapping|@PostMapping|@PutMapping|@DeleteMapping)\s*\([^)]*\)\s*\n\s*(?:public|def)\s+\w+",
            "title": "缺少权限校验注解",
            "description": "API 端点缺少 @PreAuthorize 或等效权限校验，可能导致越权访问",
            "fix": "添加 @PreAuthorize(\"hasRole('ADMIN')\") 或等效权限校验",
            "owasp": "A01:2021 – Broken Access Control",
            "cwe": "CWE-285",
        },
        {
            "severity": "HIGH", "category": "auth",
            "pattern": r"if\s*\(.*(?:role|Role|permission|Permission)\s*[=!]",
            "title": "客户端侧权限校验",
            "description": "权限校验可能仅在客户端执行，服务端缺少验证",
            "fix": "确保服务端对所有敏感操作进行权限校验",
            "owasp": "A01:2021 – Broken Access Control",
            "cwe": "CWE-862",
        },
        # A02: Cryptographic Failures
        {
            "severity": "CRITICAL", "category": "hardcoded",
            "pattern": r"(?:password|passwd|pwd|secret|api_key|apikey|api_secret|token|private_key)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
            "title": "硬编码敏感信息",
            "description": "检测到密码、密钥或 Token 被硬编码在源代码中",
            "fix": "使用环境变量、密钥管理服务(Vault/AWS Secrets Manager)或配置文件",
            "owasp": "A02:2021 – Cryptographic Failures",
            "cwe": "CWE-798",
        },
        {
            "severity": "HIGH", "category": "crypto",
            "pattern": r"(?:MD5|SHA1)\s*\(",
            "title": "使用弱哈希算法",
            "description": "MD5/SHA1 已被证明不安全，存在碰撞攻击风险",
            "fix": "使用 SHA-256 或 bcrypt/Argon2 用于密码哈希",
            "owasp": "A02:2021 – Cryptographic Failures",
            "cwe": "CWE-327",
        },
        {
            "severity": "HIGH", "category": "crypto",
            "pattern": r"DES\b|3DES\b|RC4\b",
            "title": "使用弱加密算法",
            "description": "DES/3DES/RC4 加密算法已被破解或存在已知漏洞",
            "fix": "使用 AES-256-GCM 或 ChaCha20-Poly1305",
            "owasp": "A02:2021 – Cryptographic Failures",
            "cwe": "CWE-327",
        },
        # A03: Injection
        {
            "severity": "CRITICAL", "category": "injection",
            "pattern": r"(?:execute|query|exec)\s*\([^)]*\+[^)]*\)",
            "title": "SQL 注入风险（拼接查询）",
            "description": "使用字符串拼接构建 SQL 查询，存在注入风险",
            "fix": "使用参数化查询或 ORM（如 MyBatis / SQLAlchemy / Prisma）",
            "owasp": "A03:2021 – Injection",
            "cwe": "CWE-89",
        },
        {
            "severity": "HIGH", "category": "injection",
            "pattern": r"\.query\s*\([^)]*\$[^)]*\{[^)]*\}[^)]*\)",
            "title": "SQL 注入风险（模板字符串）",
            "description": "使用模板字符串构建 SQL 查询",
            "fix": "使用参数化查询",
            "owasp": "A03:2021 – Injection",
            "cwe": "CWE-89",
        },
        {
            "severity": "HIGH", "category": "injection",
            "pattern": r"eval\s*\(",
            "title": "代码注入风险（eval）",
            "description": "使用 eval() 执行动态代码，极其危险",
            "fix": "使用 json.loads() / ast.literal_eval() 替代 eval()",
            "owasp": "A03:2021 – Injection",
            "cwe": "CWE-95",
        },
        {
            "severity": "HIGH", "category": "injection",
            "pattern": r"exec\s*\(",
            "title": "代码注入风险（exec）",
            "description": "使用 exec() 执行动态代码",
            "fix": "重构为安全的动态导入方案",
            "owasp": "A03:2021 – Injection",
            "cwe": "CWE-95",
        },
        {
            "severity": "HIGH", "category": "injection",
            "pattern": r"subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True",
            "title": "命令注入风险",
            "description": "shell=True 允许 Shell 解释器执行，可能导致命令注入",
            "fix": "设置 shell=False，使用参数列表传递命令",
            "owasp": "A03:2021 – Injection",
            "cwe": "CWE-78",
        },
        # A04: Insecure Design
        {
            "severity": "MEDIUM", "category": "config",
            "pattern": r"DEBUG\s*=\s*True|debug\s*=\s*true|development\s+mode",
            "title": "调试模式在生产环境启用",
            "description": "DEBUG 模式在生产环境启用可能泄露敏感信息",
            "fix": "生产环境设置 DEBUG=False",
            "owasp": "A04:2021 – Insecure Design",
            "cwe": "CWE-489",
        },
        # A05: Security Misconfiguration
        {
            "severity": "HIGH", "category": "config",
            "pattern": r"(?:verify|check_ssl|verify_mode)\s*[=:]\s*False",
            "title": "SSL/TLS 验证被禁用",
            "description": "禁用 SSL 证书验证，容易受到中间人攻击",
            "fix": "始终启用 verify=True，或正确配置 CA 证书",
            "owasp": "A05:2021 – Security Misconfiguration",
            "cwe": "CWE-295",
        },
        {
            "severity": "MEDIUM", "category": "config",
            "pattern": r"CORS\s*[=:]\s*['\"]\*['\"]",
            "title": "CORS 配置为通配符",
            "description": "CORS 允许所有来源，可能导致跨站请求攻击",
            "fix": "限制 CORS 为可信域名列表",
            "owasp": "A05:2021 – Security Misconfiguration",
            "cwe": "CWE-942",
        },
        # A06: Vulnerable and Outdated Components
        {
            "severity": "MEDIUM", "category": "dependency",
            "pattern": r"import\s+(?:yaml|pickle|marshal|shelve)",
            "title": "使用不安全的数据反序列化库",
            "description": "yaml.load() / pickle.loads() 可执行任意代码",
            "fix": "yaml 使用 yaml.safe_load()，避免使用 pickle 处理不可信数据",
            "owasp": "A06:2021 – Vulnerable Components",
            "cwe": "CWE-502",
        },
        # A07: Auth Failures
        {
            "severity": "HIGH", "category": "auth",
            "pattern": r"(?:password|passwd)\s*[=!]=\s*(?:md5|sha1)\s*\(",
            "title": "弱密码哈希",
            "description": "使用 MD5/SHA1 进行密码哈希",
            "fix": "使用 bcrypt / Argon2 / PBKDF2",
            "owasp": "A07:2021 – Auth Failures",
            "cwe": "CWE-916",
        },
        {
            "severity": "MEDIUM", "category": "auth",
            "pattern": r"session\[.*\]\s*=",
            "title": "敏感数据存入 Session",
            "description": "Session 中可能存储了敏感信息，存在泄露风险",
            "fix": "Session 中只存 session_id，敏感数据存在服务端缓存",
            "owasp": "A07:2021 – Auth Failures",
            "cwe": "CWE-522",
        },
        # A08: Software and Data Integrity
        {
            "severity": "HIGH", "category": "crypto",
            "pattern": r"random\.(?:random|randint|choice)\s*\(",
            "title": "使用不安全的随机数生成器",
            "description": "random 模块不适合用于安全场景（密码、token）",
            "fix": "使用 secrets 模块（Python 3.6+）或 os.urandom()",
            "owasp": "A08:2021 – Integrity Failures",
            "cwe": "CWE-338",
        },
        # A09: Logging & Monitoring
        {
            "severity": "MEDIUM", "category": "exposure",
            "pattern": r"(?:password|token|secret|key)\s*[=:]\s*[^,)]*(?:,|\))",
            "title": "敏感信息可能被记录到日志",
            "description": "print / log 语句可能输出敏感数据",
            "fix": "在日志输出前过滤敏感字段",
            "owasp": "A09:2021 – Logging Failures",
            "cwe": "CWE-532",
        },
        # A10: SSRF
        {
            "severity": "HIGH", "category": "injection",
            "pattern": r"requests?\.(?:get|post|put|delete)\s*\(\s*(?:request\.|params\.|input\.)",
            "title": "可能的 SSRF 漏洞",
            "description": "URL 来自用户输入，可能导致服务端请求伪造",
            "fix": "验证 URL 域名白名单，限制为内部可信域名",
            "owasp": "A10:2021 – SSRF",
            "cwe": "CWE-918",
        },
        # XSS
        {
            "severity": "HIGH", "category": "xss",
            "pattern": r"innerHTML\s*=",
            "title": "XSS 风险（innerHTML）",
            "description": "直接设置 innerHTML 可能导致跨站脚本攻击",
            "fix": "使用 textContent 或 DOMPurify 清洗 HTML",
            "owasp": "A03:2021 – Injection",
            "cwe": "CWE-79",
        },
        {
            "severity": "HIGH", "category": "xss",
            "pattern": r"dangerouslySetInnerHTML",
            "title": "XSS 风险（React）",
            "description": "使用 dangerouslySetInnerHTML 渲染未清洗 HTML",
            "fix": "使用 DOMPurify 清洗后再渲染",
            "owasp": "A03:2021 – Injection",
            "cwe": "CWE-79",
        },
        # CSRF
        {
            "severity": "MEDIUM", "category": "csrf",
            "pattern": r"@(?:PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(",
            "title": "可能缺少 CSRF 防护",
            "description": "状态变更操作可能缺少 CSRF Token 校验",
            "fix": "启用 CSRF 防护（Spring Security CSRF Token / SameSite Cookie）",
            "owasp": "A01:2021 – Broken Access Control",
            "cwe": "CWE-352",
        },
    ]

    # CWE Top 25 补充规则
    CWE_RULES = [
        {
            "severity": "HIGH", "category": "injection",
            "pattern": r"os\.system\s*\(",
            "title": "OS 命令执行",
            "description": "os.system() 直接执行系统命令",
            "fix": "使用 subprocess.run() 并设置 shell=False",
            "cwe": "CWE-78",
        },
        {
            "severity": "HIGH", "category": "exposure",
            "pattern": r"(?:secret|token|password|key)\s*in\s+headers",
            "title": "敏感信息放在请求头",
            "description": "敏感信息可能通过 HTTP 头泄露",
            "fix": "使用 Authorization Bearer 或签名机制",
            "cwe": "CWE-200",
        },
        {
            "severity": "MEDIUM", "category": "config",
            "pattern": r"ALLOWED_HOSTS\s*=\s*\[\s*['\"]\*['\"]\]",
            "title": "Host 校验被禁用",
            "description": "ALLOWED_HOSTS=['*'] 可能导致 Host 头攻击",
            "fix": "指定具体的允许域名列表",
            "cwe": "CWE-601",
        },
        {
            "severity": "HIGH", "category": "crypto",
            "pattern": r"ECB\s*mode|MODE_ECB",
            "title": "不安全的加密模式",
            "description": "ECB 模式不隐藏数据模式，不安全",
            "fix": "使用 GCM 或 CBC + IV 模式",
            "cwe": "CWE-327",
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

    def __init__(self, language: str = "python"):
        self.language = language
        self.issues: List[SecurityIssue] = []
        # 预编译所有规则的正则表达式
        self._compiled_rules = (
            self._compile_rules(self.OWASP_RULES)
            + self._compile_rules(self.CWE_RULES)
        )

    def scan(self, code: str, file_path: str = "input") -> SecurityReport:
        """执行安全扫描"""
        self.issues = []
        lines = code.split("\n")

        # 应用所有规则
        for rule in self._compiled_rules:
            self._apply_rule(rule, lines)

        # 计算风险评分
        risk_score, risk_level = self._compute_risk()

        return SecurityReport(
            file=file_path,
            language=self.language,
            timestamp=datetime.now(timezone(timedelta(hours=8))).isoformat(),
            issues=self.issues,
            risk_score=risk_score,
            risk_level=risk_level,
        )

    def _apply_rule(self, rule: Dict, lines: List[str]):
        """应用单条规则"""
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            if rule["_compiled"].search(stripped):
                # 去重：同一行同一类别只保留最高严重性
                existing = [iss for iss in self.issues if iss.line == i and iss.category == rule["category"]]
                if existing and self._severity_rank(existing[0].severity) >= self._severity_rank(rule["severity"]):
                    continue

                self.issues.append(
                    SecurityIssue(
                        severity=rule["severity"],
                        category=rule["category"],
                        line=i,
                        title=rule["title"],
                        description=rule["description"],
                        fix=rule["fix"],
                        owasp=rule.get("owasp", ""),
                        cwe=rule.get("cwe", ""),
                        code_snippet=stripped,
                    )
                )

    def _severity_rank(self, sev: str) -> int:
        return {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(sev, 0)

    def _compute_risk(self) -> Tuple[int, str]:
        """计算综合风险评分"""
        if not self.issues:
            return 0, "安全"

        score = 0
        for issue in self.issues:
            if issue.severity == "CRITICAL":
                score += 3
            elif issue.severity == "HIGH":
                score += 2
            elif issue.severity == "MEDIUM":
                score += 1

        # 归一化到 0-10
        score = min(score, 10)

        if score >= 7:
            level = "🔴 高风险"
        elif score >= 4:
            level = "🟠 中风险"
        elif score >= 1:
            level = "🟡 低风险"
        else:
            level = "✅ 安全"

        return score, level


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="安全漏洞扫描器 — OWASP Top 10 + CWE Top 25")
    parser.add_argument("code_file", help="待扫描的源代码文件路径")
    parser.add_argument("language", nargs="?", default="python",
                        help="编程语言 (默认: python)")
    parser.add_argument("--json", action="store_true", dest="output_json",
                        help="以 JSON 格式输出")
    args = parser.parse_args()

    try:
        with open(args.code_file, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"错误: 文件 '{args.code_file}' 不存在")
        sys.exit(1)
    except PermissionError:
        print(f"错误: 无权读取文件 '{args.code_file}'")
        sys.exit(1)

    scanner = SecurityScanner(args.language)
    report = scanner.scan(code, args.code_file)

    if args.output_json:
        print(report.to_json())
    else:
        print(report.to_markdown())


if __name__ == "__main__":
    main()
