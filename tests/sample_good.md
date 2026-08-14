# 代码安全审查报告（合规产出样例 · GOOD）

## 发现与修复

1. SQL 注入：`cursor.execute("SELECT * FROM users WHERE id=" + uid)` → 参数化占位符 `execute("... WHERE id=%s", (uid,))`。
2. 命令注入：shell=True 字符串插值调用 convert → 参数列表 shell=False 形式。
3. 硬编码密钥：配置模块内联密钥常量 → 移到环境变量/密钥管理，并轮换该密钥（已进 Git 历史，gotchas #5）。
4. 反序列化：缓存模块 pickle 反序列化 → 改 JSON；配置加载 yaml 未指定 SafeLoader → 改 safe_load。
5. 路径穿越：join 后未做 resolve 相对性校验，`../` 可逃逸 base → 补 resolve+is_relative_to 断言。
6. 越权（IDOR）：订单查询接口补 owner 校验（`order.user_id == current_user.id`）。

## 结论

注入/密钥/反序列化/穿越/越权五类全覆盖，修复建议均为安全模式（参数化/shell=False/safe_load/白名单）。
