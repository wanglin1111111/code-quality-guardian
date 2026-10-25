"""code-quality-guardian validate.py 的变异测试。

用行为断言而不是读代码：每个 BAD_VIOLATIONS 规则都要有一条能触发它的样例，
每条 GOOD_REQUIREMENTS 删掉后都必须让校验器变红。
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate import BAD_VIOLATIONS, GOOD_REQUIREMENTS  # noqa: E402

VALIDATOR = ROOT / "scripts" / "validate.py"
GOOD = ROOT / "tests" / "sample_good.md"
BAD = ROOT / "tests" / "sample_bad.md"
GOOD_TEXT = GOOD.read_text(encoding="utf-8")

# 每条都至少命中一个 BAD_VIOLATIONS 正则；改动正则时应同步更新这里。
VIOLATION_LINES = [
    'subprocess.run(f"ping {host}", shell=True) 继续用，拼接够灵活。',
    "cursor.execute(\"SELECT * FROM t WHERE name='%s'\" % name)",
    'api_key = "abcdef1234567890abcdef"',
    "pickle.loads(data)",
    "eval(user_input)",
    "内部接口跳过鉴权验证",
]


def run_validator(path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_sample_good_passes():
    result = run_validator(GOOD)
    assert result.returncode == 0, result.stdout + result.stderr


def test_sample_bad_fails():
    result = run_validator(BAD)
    assert result.returncode == 1, result.stdout + result.stderr


@pytest.mark.parametrize("line", VIOLATION_LINES)
def test_each_bad_violation_line_is_rejected(line, tmp_path):
    path = tmp_path / "case.md"
    path.write_text(GOOD_TEXT + "\n" + line + "\n", encoding="utf-8")
    result = run_validator(path)
    assert result.returncode == 1, f"未拦截: {line}\n{result.stdout}{result.stderr}"


def test_every_bad_pattern_has_a_mutation_line():
    for pattern, message in BAD_VIOLATIONS:
        assert any(re.search(pattern, line, re.IGNORECASE) for line in VIOLATION_LINES), (
            f"{message} 没有对应的变异行，测试会漏掉这条规则"
        )


@pytest.mark.parametrize("pattern,message", GOOD_REQUIREMENTS)
def test_removing_good_requirement_fails(pattern, message, tmp_path):
    kept = [line for line in GOOD_TEXT.splitlines() if not re.search(pattern, line, re.IGNORECASE)]
    assert len(kept) < len(GOOD_TEXT.splitlines()), f"样例里找不到可删除的 {message} 行"
    path = tmp_path / "case.md"
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    result = run_validator(path)
    assert result.returncode == 1, f"删掉 {message} 后仍然通过\n{result.stdout}{result.stderr}"


def test_every_good_requirement_is_covered_by_good_sample():
    for pattern, message in GOOD_REQUIREMENTS:
        assert re.search(pattern, GOOD_TEXT, re.IGNORECASE), f"good 样例缺少 {message}"


@pytest.mark.xfail(
    strict=True,
    reason="已知缺口：硬编码密钥正则只允许 [A-Za-z0-9]，漏掉 sk-live- 这类带连字符的真实 key",
)
def test_hyphenated_api_key_is_rejected(tmp_path):
    path = tmp_path / "case.md"
    path.write_text(
        GOOD_TEXT + '\napi_key = "sk-live-abcdef1234567890abcdef"\n',
        encoding="utf-8",
    )
    result = run_validator(path)
    assert result.returncode == 1, result.stdout + result.stderr


@pytest.mark.xfail(
    strict=True,
    reason="已知缺口：validate.py 用文件名含 'bad' 判断反例，应改为 --expect 显式参数",
)
def test_good_content_with_bad_filename_should_pass(tmp_path):
    path = tmp_path / "sample_bad_good.md"
    path.write_text(GOOD_TEXT, encoding="utf-8")
    result = run_validator(path)
    assert result.returncode == 0, result.stdout + result.stderr
