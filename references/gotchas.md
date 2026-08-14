# Gotchas — 代码安全真实坑位库

> 只写模型猜不到的：利用链、修复正解、历史污染处理。

## 1. 注入类
- SQL：f-string/format/% 拼接是注入点，**参数化（占位符+参数元组）是唯一正解**；"输入已过滤"在二次拼接/宽字节/存储过程场景全部失效。
- 命令：`shell=True` + 字符串插值 = 命令注入（`; rm -rf`、`$(...)`、反引号全通行）；参数列表形式 `run(["cmd", arg], shell=False)` 从根上消除。

## 2. 反序列化
- `pickle.loads` / `yaml.load`（未指定 SafeLoader）处理不可信输入 = **任意代码执行**（pickle 字节码直接构造 RCE payload；yaml 有现成 `!!python/object/apply` 利用链）。改 JSON / `yaml.safe_load`。

## 3. 路径穿越
- `os.path.join(base, user_input)` 防不住 `../`（join 遇绝对路径段/相对回退段直接放行）。正解：`Path(base).resolve()` 后校验结果仍在 base 之下（`is_relative_to`）。

## 4. 密钥与历史污染
- 硬编码密钥进 Git 历史：**删文件无效**，任何有 clone 权限的人都能从历史翻出。正解顺序：立即轮换密钥 → 历史重写（filter-repo/BFG）→ 通知可能缓存方（GitHub fork/PR 缓存）。
- `.env` 必须在 `.gitignore` **先于**首次提交添加，顺序反了就进历史。

## 5. JWT 与鉴权
- 校验须固定算法白名单（`algorithms=["HS256"]`）：`alg: none` 与 RS256→HS256 算法混淆（把公钥当 HMAC 密钥）都有现成利用链。
- IDOR：接口只查 ID 不校验 owner 是最常见越权；修复=每个对象访问带 `obj.owner == current_user` 断言。

## 6. 日志与错误页
- 日志打印 token/密码/全文 Authorization 头 → 日志系统变成凭据泄露面；错误页抛堆栈（debug=True 上线）泄露路径/依赖版本。

## 时效声明

本坑位库基于公开法规与案例整理（截至 2026-08），法规调整频繁，执行前以主管部门当日有效文件为准。技能输出为方法论框架，不构成法律意见。
