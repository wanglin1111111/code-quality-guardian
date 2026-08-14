---
name: code-quality-guardian
version: 1.1.0
description: |
  代码质量保障与智能辅助专家：代码审查、测试生成、缺陷定位、SQL 优化、性能分析、安全漏洞扫描。当用户需要代码质量检查、生成测试、审查 PR、分析日志、扫描安全漏洞、生成代码或 API 文档时使用。不适用于：运行时入侵检测、渗透测试执行（用 codex-security）、生产环境变更操作。
---

# SKILL.md - code-quality-guardian

## 任务边界

**做什么**：静态代码审查（安全/性能/可维护性/正确性/测试覆盖）、测试用例生成、SQL 与复杂度分析、日志异常检测、安全模式扫描建议。
**不做什么**：渗透测试与漏洞利用、生产环境直接变更、密钥与凭据管理代行。
**红线**：安全扫描产出必须覆盖：注入类（SQL/命令）、硬编码密钥、反序列化、路径穿越、越权；修复建议不得引入新的不安全模式。

## Gotchas 速查（详见 references/gotchas.md）

1. f-string/format 拼 SQL 是最常见注入点，参数化（占位符+参数元组）是唯一正解——'输入已过滤'不是理由
2. 命令拼接 shell=True + 字符串插值 = 命令注入；用参数列表形式（shell=False）从根上消除
3. os.path.join(base, user_input) 防不了路径穿越（user_input 含 ../ 时 join 直接放行），必须再套 resolve+相对性校验
4. pickle.loads/yaml.load(未指定 Loader) 处理不可信输入=任意代码执行，改 JSON 或 safe_load
5. 硬编码密钥一旦进 Git 历史，删除文件无效——需要轮换密钥+历史重写（或平台 BFG 清理）
6. JWT 校验必须固定允许的算法白名单，'alg: none' 与算法混淆攻击（RS256→HS256）都有现成利用链

## 核心能力

本技能覆盖软件开发生命周期的质量保障场景，提供十大能力模块：

### 1. 代码审查 (Code Review)
- **结构化审查**：按安全性、性能、可维护性、正确性、测试覆盖五个维度评分
- **严重性分级**：CRITICAL / HIGH / MEDIUM / LOW / INFO 五级
- **修复建议**：每条问题附带具体修复代码示例
- **PR审查**：支持 Git diff 解析，逐行标注问题

### 2. 测试用例生成 (Test Generation)
- **单元测试**：根据函数签名自动生成边界值、等价类、异常场景测试
- **集成测试**：API 端点测试、数据库交互测试模板
- **测试覆盖率分析**：识别未覆盖的代码路径
- **框架适配**：支持 pytest / Jest / JUnit / Go test 等主流框架

### 3. 代码规范校验 (Lint & Standards)
- **命名规范**：变量/函数/类命名一致性检查
- **复杂度检测**：圈复杂度(Cyclomatic Complexity)超标告警
- **重复代码检测**：识别 Copy-Paste 代码块
- **安全编码规范**：OWASP Top 10 违规检测

### 4. 日志分析与告警 (Log Analysis)
- **异常模式检测**：自动识别错误堆栈、异常频率
- **根因分析**：关联错误日志与代码变更
- **告警规则生成**：基于日志模式生成监控告警规则
- **日志格式化建议**：结构化日志最佳实践

### 5. SQL 查询优化 (SQL Optimization)
- **慢查询识别**：检测全表扫描、未使用索引、笛卡尔积
- **执行计划分析**：解读 EXPLAIN 输出，定位瓶颈
- **重写建议**：提供优化后的 SQL 版本
- **索引建议**：推荐合适的索引策略

### 6. 性能瓶颈分析 (Performance Profiling)
- **热点识别**：定位 CPU/内存密集型代码段
- **内存泄漏检测**：识别未释放的资源、循环引用
- **并发问题**：竞态条件、死锁风险、锁粒度分析
- **优化建议**：算法改进、缓存策略、批量处理

### 7. 缺陷定位与修复 (Bug Detection & Fix)
- **静态分析**：类型错误、空指针、越界访问、资源泄漏
- **运行时问题**：异常处理缺失、错误码未检查
- **智能修复**：提供修复代码 diff，附带解释
- **回归预防**：建议添加防护性测试用例

### 8. 安全漏洞扫描 (Security Scan)
- **OWASP Top 10**：注入、XSS、CSRF、敏感数据泄露等
- **依赖安全**：已知 CVE 漏洞检测（基于 package-lock / requirements.txt）
- **密钥检测**：硬编码 API Key、密码、Token 扫描
- **权限校验**：越权访问、权限提升风险检测

### 9. 代码生成与补全 (Code Generation & Completion)
- **自然语言生成代码**：根据描述生成 API、CRUD、测试类等完整代码
- **多框架适配**：FastAPI/Flask/Express/Gin/Spring Boot/React 等
- **函数补全**：为不完整的函数体自动补全模板代码
- **注释自动生成**：为无注释的函数/类/方法自动添加 docstring/JSDoc
- **多语言支持**：Python / JS / TS / Java / Go

### 10. API 接口文档生成 (API Documentation)
- **自动提取端点**：从源代码提取路由/注解定义
- **多格式输出**：Markdown / OpenAPI 3.0 / JSDoc / Javadoc
- **框架适配**：FastAPI / Flask / Express / Spring Boot / Gin
- **结构化文档**：方法、路径、参数、响应示例

## 工作流程

### 通用审查流程

```
输入 → 多维扫描 → 问题分级 → 修复建议 → 报告输出
```

1. **输入解析**：识别输入类型（源代码文件 / Git diff / 日志文件 / SQL 查询）
2. **多维扫描**：并行执行静态分析、规范检查、安全扫描、复杂度检测
3. **问题分级**：按严重性排序，标注影响范围
4. **修复建议**：生成可执行的修复代码 diff
5. **报告输出**：结构化 Markdown 报告 + 机器可读 JSON

### 专项工作流

#### 代码审查工作流
```
Git Diff / 代码文件 → 静态分析 → 安全扫描 → 复杂度检查 → 审查报告
```

#### 测试生成工作流
```
函数/类定义 → 边界分析 → 等价类划分 → 测试框架适配 → 测试代码输出
```

#### SQL 优化工作流
```
SQL 语句 → 语法解析 → 执行计划模拟 → 瓶颈定位 → 优化建议 + 重写版本
```

#### 日志分析工作流
```
日志文件 → 模式提取 → 异常聚类 → 根因定位 → 告警规则
```

## 输入格式

### 源代码审查
```
用户提供：
- 编程语言（必填）
- 代码内容（必填）
- 审查维度（可选：security / performance / maintainability / all）
- 严重性阈值（可选：CRITICAL / HIGH / MEDIUM / LOW）
```

### 测试生成
```
用户提供：
- 编程语言（必填）
- 函数/类代码（必填）
- 测试框架（可选：pytest / jest / junit / go-test）
- 覆盖场景（可选：unit / integration / edge-cases）
```

### SQL 优化
```
用户提供：
- SQL 语句（必填）
- 数据库类型（可选：MySQL / PostgreSQL / SQLite / SQL Server）
- 表结构信息（可选：DDL）
```

### 日志分析
```
用户提供：
- 日志内容（必填）
- 日志格式（可选：plain / json / syslog）
- 分析维度（可选：errors / patterns / anomalies）
```

### PR 审查
```
用户提供：
- Git diff 内容（必填）
- 文件变更列表（可选）
- 审查重点（可选：security-breaking / performance / style）
```

## 输出格式

### 审查报告模板
```markdown
## 🔍 代码质量审查报告

**文件**: `path/to/file.py`
**语言**: Python
**审查时间**: 2026-06-12
**严重性分布**: 🔴 CRITICAL: 0 | 🟠 HIGH: 2 | 🟡 MEDIUM: 3 | 🔵 LOW: 1 | ⚪ INFO: 2

### 严重问题 (HIGH)

#### 1. SQL 注入风险 [HIGH]
**位置**: line 45
**问题**: 使用字符串拼接构建 SQL 查询
```python
# 当前
query = f"SELECT * FROM users WHERE id = {user_id}"
# 修复
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```
**影响**: 攻击者可通过 `user_id` 参数注入任意 SQL
**OWASP**: A03:2021 – Injection

### 中等问题 (MEDIUM)
...

### 统计摘要
| 维度 | 评分 | 说明 |
|------|------|------|
| 安全性 | 7/10 | 存在 SQL 注入风险 |
| 正确性 | 9/10 | 边界条件处理完善 |
| 可维护性 | 6/10 | 函数过长(87行)，建议拆分 |
| 性能 | 8/10 | 无明显瓶颈 |
| 测试覆盖 | N/A | 未提供测试文件 |
```

### JSON 机器输出
```json
{
  "file": "path/to/file.py",
  "language": "python",
  "timestamp": "2026-06-12T12:40:00+08:00",
  "summary": {
    "critical": 0, "high": 2, "medium": 3, "low": 1, "info": 2,
    "overall_score": 7.2
  },
  "issues": [
    {
      "severity": "HIGH",
      "category": "security",
      "line": 45,
      "title": "SQL 注入风险",
      "description": "使用字符串拼接构建 SQL 查询",
      "fix": "使用参数化查询",
      "owasp": "A03:2021 – Injection",
      "code_before": "query = f\"SELECT * FROM users WHERE id = {user_id}\"",
      "code_after": "query = \"SELECT * FROM users WHERE id = %s\"\ncursor.execute(query, (user_id,))"
    }
  ],
  "dimensions": {
    "security": 7, "correctness": 9, "maintainability": 6, "performance": 8
  }
}
```

## 支持的语言与框架

### 编程语言
- **系统级**: C / C++ / Rust / Go
- **后端**: Python / Java / C# / Node.js / PHP / Ruby
- **前端**: JavaScript / TypeScript / HTML / CSS
- **数据**: SQL / R / Julia
- **移动**: Swift / Kotlin / Dart

### 测试框架
- Python: pytest / unittest / nose2
- JavaScript: Jest / Mocha / Vitest
- Java: JUnit / TestNG
- Go: testing / testify
- Rust: cargo test

### 数据库
- MySQL / PostgreSQL / SQLite / SQL Server / Oracle / MongoDB

### 代码分析工具
- 静态分析: 内置规则引擎 + 语言特定模式
- 安全扫描: OWASP Top 10 + CWE Top 25
- 复杂度: 圈复杂度 + 认知复杂度

## 使用示例

### 示例 1: 代码审查
```
用户: 审查这段 Python 代码的安全性和性能
[粘贴代码]

助手: [执行审查 → 输出结构化报告]
```

### 示例 2: 生成测试用例
```
用户: 为这个函数生成 pytest 测试用例
[粘贴函数代码]

助手: [分析函数 → 生成边界测试 + 异常测试 + 集成测试]
```

### 示例 3: SQL 优化
```
用户: 优化这个 SQL 查询
SELECT * FROM orders o JOIN users u ON o.user_id = u.id WHERE o.status = 'active'

助手: [分析 → 建议 SELECT 具体字段 + 添加索引 + 执行计划分析]
```

### 示例 4: 日志分析
```
用户: 分析这些日志中的异常模式
[粘贴日志]

助手: [聚类分析 → 识别高频错误 → 根因定位 → 告警规则建议]
```

### 示例 5: 安全扫描
```
用户: 扫描这段代码的安全漏洞
[粘贴代码]

助手: [OWASP 检测 → CWE 映射 → 修复建议]
```

## 质量保障最佳实践

### 审查 Checklist
- [ ] 输入验证（所有外部输入）
- [ ] 错误处理（异常捕获 + 日志记录）
- [ ] 资源管理（文件/连接/内存释放）
- [ ] 并发安全（锁/原子操作/线程安全）
- [ ] 敏感数据（加密/脱敏/不硬编码）
- [ ] 依赖安全（无已知 CVE）
- [ ] 代码复杂度（函数 <50 行，圈复杂度 <10）

### 安全编码规范
- 使用参数化查询防止 SQL 注入
- 对所有用户输入进行验证和清洗
- 使用 HTTPS + 证书验证
- 密码/密钥使用环境变量或密钥管理服务
- 遵循最小权限原则

### 性能优化原则
- 避免 N+1 查询
- 使用批量操作替代单条循环
- 合理使用缓存（避免缓存雪崩/击穿）
- 延迟加载非关键资源
- 使用连接池

## 内置脚本

### scripts/code_reviewer.py
完整代码审查引擎，支持多维度扫描和严重性分级。

### scripts/test_generator.py
测试用例自动生成器，支持多框架和多种测试场景。

### scripts/sql_optimizer.py
SQL 查询分析和优化建议引擎。

### scripts/log_analyzer.py
日志分析工具，支持异常检测和根因定位。

### scripts/security_scanner.py
安全漏洞扫描器，覆盖 OWASP Top 10 和 CWE Top 25。

### scripts/complexity_analyzer.py
代码复杂度分析工具，计算圈复杂度和认知复杂度。

### scripts/code_generator.py
代码生成与补全引擎，支持自然语言→代码、函数补全、注释生成、API文档生成。

## 参考文档

### references/code_review_checklist.md
代码审查标准 Checklist，覆盖安全、性能、可维护性等维度。

### references/security_patterns.md
安全编码模式库，包含注入防御、认证授权、加密等最佳实践。

### references/performance_patterns.md
性能优化模式库，包含数据库优化、缓存策略、并发处理等。

### references/testing_strategies.md
测试策略指南，包含单元测试、集成测试、E2E 测试的设计方法。

### 使用示例（续）

### 示例 6: 代码生成
```
用户: 生成一个 FastAPI 的用户管理 API
助手: [生成完整的 FastAPI 应用代码，含模型、CRUD 端点、错误处理]
```

### 示例 7: 函数补全
```
用户: 补全这个函数
def calculate_total(items):
助手: [自动补全函数体 + docstring + 类型提示]

### 示例 8: 自动生成注释
```
用户: 为这段代码生成注释
[粘贴无注释代码]
助手: [为每个函数/类添加 docstring/JSDoc]
```

### 示例 9: API 文档生成
```
用户: 生成这个 API 的文档
[粘贴 FastAPI/Express 代码]
助手: [提取所有端点 → 生成 Markdown/OpenAPI 格式文档]
```


---

## 输出规范（validate.py 断言）

本技能产出的分析/方案文档，必须同时满足：
- **应含**：本文件输出规范所列合规要素
- **不应含**：红线违规模式（详见 scripts/validate.py BAD_VIOLATIONS）

校验命令：`python scripts/validate.py <文档路径>`（exit 0=通过，1=违规或缺失，2=文件错误）
双样例：`tests/sample_good.md` → 0；`tests/sample_bad.md` → 1。两者必须同时验证通过才视为技能可用。
