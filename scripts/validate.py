#!/usr/bin/env python3
"""code-quality-guardian 技能验证脚本。

断言"产出=合规成立"而非"动作已执行"：
- GOOD 样例：含全部合规要素，且无违规 → exit 0
- BAD 样例：命中任一违规模式 → exit 1

退出码契约：0=通过，1=存在错误，2=文件错误。
"""

import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_FILE_ERROR = 2


def read_sample(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        print(f"文件不存在: {path}", file=sys.stderr)
        sys.exit(EXIT_FILE_ERROR)
    return p.read_text(encoding="utf-8")


GOOD_REQUIREMENTS = [
    ("注入|SQL|命令|injection", "缺少注入类检查"),
    ("(硬编码|secret|密钥|凭据)", "缺少硬编码密钥检查"),
    ("反序列化|pickle|yaml", "缺少反序列化检查"),
    ("(路径穿越|traversal|\\.\\.)", "缺少路径穿越检查"),
    ("(越权|IDOR|鉴权|授权)", "缺少越权/鉴权检查"),
    ("参数化|占位符|shell=False|safe_load|白名单", "缺少安全修复模式建议"),
]

BAD_VIOLATIONS = [
    ("shell\\s*=\\s*True.{0,20}(拼接|format|%s|\\+|f['\\\"])", "命中违规：shell=True 拼接命令"),
    ("(SELECT|INSERT|UPDATE|DELETE).{0,30}(f['\\\"]|\\.format|%s.{0,10}%)", "命中违规：SQL 字符串拼接"),
    ("(password|api_key|secret|token)\\s*=\\s*['\\\"][A-Za-z0-9]{16,}", "命中违规：硬编码密钥"),
    ("pickle\\.loads?\\(|yaml\\.load\\((?![^)]*Loader)", "命中违规：不安全反序列化"),
    ("eval\\(|exec\\(.{0,20}(input|request|用户)", "命中违规：eval/exec 用户输入"),
    ("(忽略|跳过|不用).{0,4}(鉴权|验证|校验|授权)", "命中违规：跳过鉴权/校验"),
]


def find_violations(text: str) -> list:
    hits = []
    for pattern, msg in BAD_VIOLATIONS:
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(msg)
    return hits


def find_missing_good(text: str) -> list:
    missing = []
    for pattern, msg in GOOD_REQUIREMENTS:
        if not re.search(pattern, text, re.IGNORECASE):
            missing.append(msg)
    return missing


def main():
    if len(sys.argv) < 2:
        print("用法: validate.py <sample.md>", file=sys.stderr)
        sys.exit(EXIT_FILE_ERROR)

    sample_path = sys.argv[1]
    text = read_sample(sample_path)
    fname = Path(sample_path).name.lower()
    is_bad = "bad" in fname

    errors = []

    violations = find_violations(text)
    if is_bad:
        if not violations:
            errors.append("BAD 样例未命中任何已知违规模式（应至少命中一条）")
        else:
            errors.append(f"BAD 样例命中 {len(violations)} 条违规（预期失败）：{'; '.join(violations)}")
    else:
        if violations:
            errors.append(f"GOOD 样例命中违规（不应有）：{'; '.join(violations)}")
        missing = find_missing_good(text)
        errors.extend(missing)

    if errors:
        print(f"验证失败（{len(errors)} 项）：", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(EXIT_FAIL)

    print("验证通过")
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
