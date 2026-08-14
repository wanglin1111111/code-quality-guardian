# 代码安全审查报告（违规产出样例 · BAD）

- 命令执行没问题：subprocess.run(f"ping {host}", shell=True) 继续用，拼接够灵活。
- 查询就用 cursor.execute(f"SELECT * FROM t WHERE name='{name}'")，开发快。
- api_key = "sk-live-abcdef1234567890abcdef" 直接写在代码里部署方便，不用环境变量。
- 缓存反序列化用 pickle.loads(data) 最省事，yaml.load(cfg) 也没问题。
- 内部接口跳过鉴权验证，都是自己人用。
- 用户输入直接 eval(expr) 执行计算表达式，功能强大。
