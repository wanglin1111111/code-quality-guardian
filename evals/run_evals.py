#!/usr/bin/env python3
"""
Eval Runner — Code Quality Guardian 评测运行器
读取 evals.json，执行各脚本并自动验证 assertions
"""

import sys
import os
import json
import re
from datetime import datetime, timezone, timedelta

# 确保能导入 scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.code_reviewer import CodeReviewer
from scripts.security_scanner import SecurityScanner
from scripts.sql_optimizer import SQLOptimizer
from scripts.complexity_analyzer import ComplexityAnalyzer
from scripts.log_analyzer import LogAnalyzer
from scripts.test_generator import TestGenerator
from scripts.code_generator import CodeGenerator, APIDocGenerator


def normalize_capability(cap: str) -> str:
    """将能力名称统一为标准形式（支持模糊匹配：去空格后比较）"""
    aliases = {
        "安全扫描": "安全漏洞扫描",
        "SQL优化": "SQL 查询优化",
        "SQL 优化": "SQL 查询优化",
        "API 文档": "API 文档生成",
        "API文档生成": "API 文档生成",
        "代码生成与补全": "代码生成",
    }
    # 精确匹配
    if cap in aliases:
        return aliases[cap]
    # 模糊匹配：去空格、转小写后比较
    cap_norm = cap.replace(" ", "").lower()
    for alias, canonical in aliases.items():
        if alias.replace(" ", "").lower() == cap_norm:
            return canonical
    # 标准名称本身（也做去空格归一化）
    canonical_names = ["代码审查", "安全漏洞扫描", "SQL 查询优化", "日志分析",
                       "复杂度分析", "测试用例生成", "代码生成", "API 文档生成"]
    for cn in canonical_names:
        if cn.replace(" ", "").lower() == cap_norm:
            return cn
    return cap


def extract_code_block(prompt: str) -> str:
    """从 prompt 中提取代码块"""
    match = re.search(r"```(?:\w*)\n(.*?)```", prompt, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 尝试无语言标识的代码块
    match = re.search(r"```\n(.*?)```", prompt, re.DOTALL)
    if match:
        return match.group(1).strip()
    return prompt


def run_eval(eval_case: dict) -> dict:
    """运行单个 eval 并返回结果"""
    eval_id = eval_case["id"]
    capability = normalize_capability(eval_case["capability"])
    prompt = eval_case["prompt"]
    code = extract_code_block(prompt)

    result = {
        "id": eval_id,
        "category": eval_case["category"],
        "capability": capability,
        "status": "unknown",
        "outputs": {},
        "assertion_results": [],
    }

    try:
        if capability == "代码审查":
            reviewer = CodeReviewer("python")
            report = reviewer.review(code, "eval_input.py")
            result["outputs"] = {
                "markdown": report.to_markdown(),
                "json": json.loads(report.to_json()),
                "overall_score": report.overall_score,
                "issues": [i.to_dict() for i in report.issues],
                "issue_count": len(report.issues),
                "severity_counts": report.summary,
                "dimensions": report.dimensions,
            }

        elif capability == "安全漏洞扫描":
            scanner = SecurityScanner("python")
            report = scanner.scan(code, "eval_input.py")
            result["outputs"] = {
                "markdown": report.to_markdown(),
                "json": json.loads(report.to_json()),
                "risk_score": report.risk_score,
                "risk_level": report.risk_level,
                "issues": [i.to_dict() for i in report.issues],
                "issue_count": len(report.issues),
            }

        elif capability == "SQL 查询优化":
            optimizer = SQLOptimizer("MySQL")
            report = optimizer.analyze(code)
            result["outputs"] = {
                "markdown": report.to_markdown(),
                "json": json.loads(report.to_json()),
                "issues": [i.to_dict() for i in report.issues],
                "optimized_sql": report.optimized_sql,
                "index_suggestions": report.index_suggestions,
                "complexity_score": report.complexity_score,
            }

        elif capability == "日志分析":
            analyzer = LogAnalyzer()
            report = analyzer.analyze(code, log_file="eval_input.log")
            result["outputs"] = {
                "markdown": report.to_markdown(),
                "json": json.loads(report.to_json()),
                "patterns": [p.to_dict() for p in report.patterns],
                "root_causes": report.root_causes,
                "alert_rules": report.alert_rules,
                "format_issues": report.format_issues,
                "time_range": report.time_range,
            }

        elif capability == "复杂度分析":
            analyzer = ComplexityAnalyzer("python")
            report = analyzer.analyze(code, "eval_input.py")
            result["outputs"] = {
                "markdown": report.to_markdown(),
                "json": json.loads(report.to_json()),
                "results": [r.to_dict() for r in report.results],
                "avg_cyclomatic": report.avg_cyclomatic,
                "hotspot_functions": report.hotspot_functions,
            }

        elif capability == "测试用例生成":
            # 从 prompt 中提取函数名
            fn_match = re.search(r"(?:def|function)\s+(\w+)", code)
            func_name = fn_match.group(1) if fn_match else "unknown"

            lang = "python"
            framework = "pytest"
            if "jest" in prompt.lower() or "Jest" in prompt:
                lang = "javascript"
                framework = "jest"

            gen = TestGenerator(lang, framework)
            suite = gen.generate(code, func_name)
            result["outputs"] = {
                "markdown": suite.to_markdown(),
                "code": suite.to_code(),
                "test_count": len(suite.test_cases),
                "categories": [tc.category for tc in suite.test_cases],
                "coverage": suite.coverage_estimate,
            }

        elif capability == "代码生成":
            gen = CodeGenerator()
            # 从 prompt 提取描述
            desc = prompt.replace("生成一个", "").replace("生成", "").strip()
            framework = ""
            if "fastapi" in prompt.lower():
                framework = "FastAPI"
            elif "flask" in prompt.lower():
                framework = "Flask"

            generated = gen.generate_from_description(desc, "python", framework)
            result["outputs"] = {
                "code": generated.code,
                "dependencies": generated.dependencies,
                "explanation": generated.explanation,
            }

        elif capability == "API 文档生成":
            doc_gen = APIDocGenerator()
            doc_result = doc_gen.generate(code, "python", "markdown")
            result["outputs"] = {
                "documentation": doc_result.documentation,
                "doc_format": doc_result.doc_format,
            }

        result["status"] = "executed"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["error_type"] = type(e).__name__

    return result


def _build_full_text(outputs: dict) -> str:
    """从 outputs 构建完整的可搜索文本"""
    parts = []
    # 收集所有字符串类型的输出
    for key, val in outputs.items():
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    parts.append(" ".join(str(v) for v in item.values()))
                else:
                    parts.append(str(item))
        elif isinstance(val, dict):
            parts.append(" ".join(str(v) for v in val.values()))
        else:
            parts.append(str(val))
    return " ".join(parts)


def _get_issues(outputs: dict) -> list:
    """获取 issues 列表"""
    return outputs.get("issues", outputs.get("results", outputs.get("patterns", [])))


def _get_issues_text(issues: list) -> str:
    """从 issues 列表构建文本"""
    return " ".join(
        str(i.get("description", "")) + " " + str(i.get("title", "")) + " "
        + str(i.get("fix", "")) + " " + str(i.get("suggestion", ""))
        + " " + str(i.get("severity", "")) + " " + str(i.get("category", ""))
        for i in issues
    ) if issues else ""


def check_assertion(assertion: dict, eval_result: dict) -> dict:
    """检查单个 assertion 是否满足"""
    aid = assertion["id"]
    text = assertion["text"]
    outputs = eval_result.get("outputs", {})

    passed = False
    reason = ""
    text_lower = text.lower()

    if not outputs:
        return {"id": aid, "text": text, "passed": False, "reason": "无输出结果"}

    full_text = _build_full_text(outputs)
    full_lower = full_text.lower()
    issues = _get_issues(outputs)
    issues_text = _get_issues_text(issues)
    issues_lower = issues_text.lower()

    # ---- 1. 严重性级别检查 ----
    if ("high" in text_lower or "critical" in text_lower) and issues:
        if "high" in text_lower and "critical" in text_lower:
            passed = any(i.get("severity") in ("HIGH", "CRITICAL") for i in issues)
            reason = f"HIGH/CRITICAL 问题数: {sum(1 for i in issues if i.get('severity') in ('HIGH','CRITICAL'))}"
        elif "critical" in text_lower:
            passed = any(i.get("severity") == "CRITICAL" for i in issues)
            reason = f"CRITICAL 数: {sum(1 for i in issues if i.get('severity')=='CRITICAL')}"
        elif "high" in text_lower:
            passed = any(i.get("severity") in ("HIGH", "CRITICAL") for i in issues)
            reason = f"HIGH+ 数: {sum(1 for i in issues if i.get('severity') in ('HIGH','CRITICAL'))}"
        if passed:
            return {"id": aid, "text": text, "passed": True, "reason": reason}

    # ---- 2. 关键词检测（在输出中搜索断言提及的关键词）----
    detection_keywords = [
        "eval", "exec", "SQL", "注入", "XSS", "shell", "硬编码", "密码",
        "SELECT *", "前导通配符", "OR 条件", "子查询", "UNION", "ORDER BY",
        "连接超时", "ConnectionTimeout", "内存溢出", "OOM", "fatal", "FATAL",
        "CRITICAL", "随机", "random", "secrets", "SSL", "verify",
        "参数化", "JOIN", "索引", "FULLTEXT", "LIMIT",
        "BaseModel", "Pydantic", "FastAPI", "describe", "test(", "it(",
        "pytest.raises", "ValueError", "discount",
        "连接不稳定", "下游服务", "告警", "alert",
    ]
    for kw in detection_keywords:
        if kw.lower() in text_lower and kw.lower() in full_lower:
            passed = True
            reason = f"在输出中检测到 '{kw}'"
            break
    if passed:
        return {"id": aid, "text": text, "passed": True, "reason": reason}

    # ---- 3. CWE / OWASP 映射 ----
    cwe_match = re.search(r"CWE-(\d+)", text)
    if cwe_match and issues:
        cwe_id = f"CWE-{cwe_match.group(1)}"
        passed = any(cwe_id in str(i.get("cwe", "")) for i in issues)
        return {"id": aid, "text": text, "passed": passed,
                "reason": f"CWE 映射 {cwe_id} {'存在' if passed else '未找到'}"}

    # ---- 4. 评分 / 阈值检查 ----
    if ("评分" in text_lower or "score" in text_lower or "分" in text
            or "不低" in text or "不超" in text):
        # 从多个字段获取评分
        score = -1
        for field in ["overall_score", "risk_score", "complexity_score", "avg_cyclomatic"]:
            val = outputs.get(field, -1)
            if isinstance(val, (int, float)) and val >= 0:
                score = val
                break

        if score >= 0:
            # 提取阈值
            num_match = re.search(r"[>≥>=]+\s*(\d+)", text)
            if num_match:
                threshold = int(num_match.group(1))
                if "不低" in text or "不超" in text_lower:
                    if "不低" in text:
                        passed = score >= threshold
                        reason = f"评分 {score} {'≥' if passed else '<'} {threshold}"
                    else:
                        passed = score <= threshold
                        reason = f"评分 {score} {'≤' if passed else '>'} {threshold}"
                else:
                    passed = score >= threshold
                    reason = f"评分 {score} {'≥' if passed else '<'} {threshold}"
                return {"id": aid, "text": text, "passed": passed, "reason": reason}

    # ---- 5. 不应/不能/不会 类断言 ----
    if any(w in text for w in ["不应", "不能", "不会", "不因", "没有"]):
        if "崩溃" in text or "异常" in text or "error" in text_lower:
            passed = eval_result.get("status") == "executed"
            return {"id": aid, "text": text, "passed": passed,
                    "reason": "脚本正常执行无崩溃" if passed else f"脚本异常: {eval_result.get('error', '')}"}
        elif "误报" in text or "误标" in text:
            ic = outputs.get("issue_count", len(issues))
            score = outputs.get("overall_score", 0)
            passed = ic == 0 or score >= 7
            return {"id": aid, "text": text, "passed": passed,
                    "reason": f"问题数={ic}, 评分={score}"}

    # ---- 6. 结构性检查 ----
    # issues 列表为空
    if "列表为空" in text or "空" in text and "issues" in text_lower:
        ic = outputs.get("issue_count", len(issues) if isinstance(issues, list) else -1)
        passed = ic == 0
        return {"id": aid, "text": text, "passed": passed, "reason": f"issues 数量: {ic}"}

    # issues 非空 / 至少 N 个
    at_least = re.search(r"至少\s*(\d+)", text)
    if at_least and issues:
        n = int(at_least.group(1))
        passed = len(issues) >= n
        return {"id": aid, "text": text, "passed": passed, "reason": f"issues 数量 {len(issues)} {'≥' if passed else '<'} {n}"}

    # to_json() 正常
    if "to_json" in text_lower:
        passed = "json" in outputs
        return {"id": aid, "text": text, "passed": passed,
                "reason": "to_json() 正常" if passed else "to_json() 缺失"}

    # suggestion 非空
    if "非空" in text and "suggestion" in text_lower and issues:
        passed = all(i.get("suggestion", "") != "" for i in issues)
        return {"id": aid, "text": text, "passed": passed,
                "reason": "所有 suggestion 非空" if passed else "存在空 suggestion"}

    # 花括号转义
    if "转义" in text and "{{" in text:
        code_out = outputs.get("code", "")
        passed = "{{" not in code_out
        return {"id": aid, "text": text, "passed": passed,
                "reason": "无 {{ 残留" if passed else "存在 {{ 转义残留"}

    # ---- 7. 输出结构存在性检查 ----
    # 检查某些字段是否存在
    if "包含" in text or "输出包含" in text or "生成" in text:
        for field_key in ["markdown", "code", "documentation", "dependencies",
                          "root_causes", "alert_rules", "format_issues",
                          "time_range", "index_suggestions", "optimized_sql",
                          "explanation", "coverage"]:
            if field_key.replace("_", " ") in text_lower and field_key in outputs:
                val = outputs[field_key]
                passed = bool(val) if not isinstance(val, list) else len(val) > 0
                reason = f"{field_key} 字段存在且非空" if passed else f"{field_key} 为空"
                return {"id": aid, "text": text, "passed": passed, "reason": reason}

    # 维度评分检查
    if "维度" in text and "评分" in text_lower:
        dims = outputs.get("dimensions", {})
        passed = bool(dims) and len(dims) > 0
        return {"id": aid, "text": text, "passed": passed,
                "reason": f"维度评分存在，共 {len(dims)} 个维度" if passed else "无维度评分"}

    # 如果自动检查未能确定，标记为需人工审核
    return {"id": aid, "text": text, "passed": None, "reason": "需人工审核"}


def print_report(all_results: list):
    """打印评测报告"""
    total = 0
    passed = 0
    failed = 0
    manual = 0
    errors = 0

    print("=" * 70)
    print(f"  Code Quality Guardian — 评测报告")
    print(f"  时间: {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    for eval_result in all_results:
        eval_id = eval_result["id"]
        capability = eval_result["capability"]
        category = eval_result["category"]
        status = eval_result["status"]

        emoji = "✅" if status == "executed" else "❌"
        print(f"\n{emoji} [{eval_id}] {category} — {capability}")

        if status == "error":
            errors += 1
            print(f"   ❌ 执行错误: {eval_result.get('error_type')}: {eval_result.get('error')}")
            continue

        for ar in eval_result.get("assertion_results", []):
            total += 1
            if ar["passed"] is True:
                passed += 1
                print(f"   ✅ [{ar['id']}] {ar['text']}")
            elif ar["passed"] is False:
                failed += 1
                print(f"   ❌ [{ar['id']}] {ar['text']}")
                print(f"      ↳ {ar['reason']}")
            else:
                manual += 1
                print(f"   ⚠️  [{ar['id']}] {ar['text']} (需人工审核)")

    print("\n" + "=" * 70)
    print(f"  汇总: 共 {total} 条断言 | ✅ 通过 {passed} | ❌ 失败 {failed} | ⚠️ 待审 {manual} | 脚本错误 {errors}")
    print(f"  通过率: {passed}/{total} ({passed/total*100:.1f}%)" if total > 0 else "  无断言")
    print("=" * 70)

    return passed, failed, manual, errors


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Code Quality Guardian 评测运行器")
    parser.add_argument("--evals", default=os.path.join(os.path.dirname(__file__), "evals.json"),
                        help="eval JSON 文件路径 (默认: evals/evals.json)")
    parser.add_argument("--filter", default="",
                        help="按类别过滤: core / edge / pitfall")
    parser.add_argument("--json", action="store_true", dest="output_json",
                        help="以 JSON 格式输出详细结果")
    args = parser.parse_args()

    with open(args.evals, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    evals = eval_data["evals"]

    # 过滤
    if args.filter:
        category_map = {"core": "核心样本", "edge": "边界样本", "pitfall": "已知坑"}
        target = category_map.get(args.filter, args.filter)
        evals = [e for e in evals if e["category"] == target]

    all_results = []

    for eval_case in evals:
        print(f"⏳ 运行 [{eval_case['id']}] {eval_case['capability']}...")
        result = run_eval(eval_case)

        # 检查 assertions
        for assertion in eval_case.get("assertions", []):
            ar = check_assertion(assertion, result)
            result["assertion_results"].append(ar)

        all_results.append(result)

    # 输出
    if args.output_json:
        print(json.dumps(all_results, indent=2, ensure_ascii=False, default=str))
    else:
        print_report(all_results)


if __name__ == "__main__":
    main()
