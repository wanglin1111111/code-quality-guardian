# Code Quality Guardian 🛡️

> 代码质量保障与智能辅助 — 覆盖代码审查、测试生成、SQL 优化、日志分析、安全扫描、复杂度分析、代码生成与补全、API 文档生成

> **🎯 赛道申报：AI 开发赛道 — 编码开发类**
>
> | 申报项 | 内容 |
> |---|---|
> | **技能名称** | Code Quality Guardian（代码质量守护者） |
> | **赛道分类** | AI 开发 / 编码开发辅助 |
> | **一句话定位** | 覆盖编码全流程的 AI 质量守护 Skill：写前生成、写中审查、写后验证、事后诊断 |
> | **核心能力（8 项）** | 代码审查 / 测试生成 / SQL 优化 / 日志分析 / 安全扫描（OWASP Top 10 + CWE Top 25）/ 复杂度分析 / 代码生成与补全 / API 文档生成 |
> | **工程形态** | 7 个独立 Python 引擎脚本（约 4400 行，零外部依赖）+ 4 份方法论参考文档 + 双样例测试集 |
> | **语言覆盖** | Python / JavaScript / TypeScript / Java / Go / SQL |
> | **输出格式** | 结构化 Markdown（人读）+ JSON（机读，可接 CI） |
> | **与 Agent 生态的集成** | 标准 SKILL.md 入口，可作为 Claude Code / Codex / OpenClaw 等 Agent Harness 的可调用技能；validate.py 校验（exit 0/1/2 规范） |
> | **验证状态** | 双样例断言通过（sample_good → exit 0，sample_bad → exit≠0），pass:verified |

---

## 安装

```bash
# 克隆仓库
git clone https://github.com/wanglin1111111/code-quality-guardian.git
cd code-quality-guardian

# 安装依赖（需要 Python >= 3.9）
pip install -e .
```

## 快速开始

### 代码审查
```bash
python scripts/code_reviewer.py <代码文件> [语言] [--json]
```
```
审查这段 Python 代码的安全性和性能
[粘贴代码]
```

### 测试生成
```bash
python scripts/test_generator.py <代码文件> <函数名> [--framework pytest|jest|go-test] [--json]
```
```
为这个函数生成 pytest 测试用例
[粘贴函数代码]
```

### SQL 优化
```bash
python scripts/sql_optimizer.py <SQL文件> [--db-type MySQL|PostgreSQL|SQLite] [--json]
```
```
优化这个 SQL 查询
[粘贴 SQL]
```

### 日志分析
```bash
python scripts/log_analyzer.py <日志文件> [--format plain|json|syslog] [--json]
```
```
分析这些日志中的异常
[粘贴日志内容]
```

### 安全扫描
```bash
python scripts/security_scanner.py <代码文件> [语言] [--json]
```
```
扫描这段代码的安全漏洞
[粘贴代码]
```

### 复杂度分析
```bash
python scripts/complexity_analyzer.py <代码文件> [语言] [--json]
```

### 代码生成
```bash
python scripts/code_generator.py generate <描述> [语言] [框架]
python scripts/code_generator.py complete <代码> <语言>
python scripts/code_generator.py comment <代码> <语言>
python scripts/code_generator.py doc <代码文件> <语言> [--format markdown|openapi]
```

## 内置脚本

| 脚本 | 功能 |
|------|------|
| `scripts/code_reviewer.py` | 多维代码审查（安全/性能/质量） |
| `scripts/test_generator.py` | 测试用例自动生成（pytest/Jest/go-test） |
| `scripts/sql_optimizer.py` | SQL 慢查询识别与优化建议 |
| `scripts/log_analyzer.py` | 日志异常检测与根因分析 |
| `scripts/security_scanner.py` | OWASP Top 10 + CWE Top 25 安全扫描 |
| `scripts/complexity_analyzer.py` | 圈复杂度 + 认知复杂度分析 |
| `scripts/code_generator.py` | 代码生成、补全、注释生成、API 文档生成 |

## 技能内容

- 10 大能力模块（代码审查 / 测试生成 / 规范校验 / 日志分析 / SQL 优化 / 性能分析 / 缺陷定位 / 安全扫描 / 代码生成与补全 / API 文档生成）
- 7 个 Python 引擎脚本（共约 4400 行）
- 4 份参考文档（审查 Checklist / 安全模式 / 性能模式 / 测试策略）
- 支持 Python / JS / TS / Java / Go / SQL 多语言
- 结构化 Markdown + JSON 双格式输出

## 赛事对标

| 赛事方向 | 对应能力 |
|----------|----------|
| 代码审查 | `code_reviewer.py` 五维度审查 + 严重性分级 |
| 测试用例编写 | `test_generator.py` 多框架测试生成 |
| 代码规范校验 | 内置命名/复杂度/重复代码检测 |
| 日志分析 | `log_analyzer.py` 异常聚类 + 根因分析 |
| SQL 优化 | `sql_optimizer.py` 慢查询识别 + 索引建议 |
| 缺陷定位 | 静态分析 + 智能修复建议 |
| 安全漏洞扫描 | `security_scanner.py` OWASP Top 10 |

## 许可证

MIT License
