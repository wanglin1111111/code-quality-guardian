# 安全编码模式库

## 注入防御

### SQL 注入防护
```python
# ❌ 危险：字符串拼接
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ 安全：参数化查询
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

### 命令注入防护
```python
# ❌ 危险：shell=True + 用户输入
subprocess.run(f"ping {host}", shell=True)

# ✅ 安全：参数列表 + shell=False
subprocess.run(["ping", "-c", "1", host], shell=False)
```

### 代码注入防护
```python
# ❌ 危险：eval
result = eval(user_input)

# ✅ 安全：ast.literal_eval（仅字面量）
import ast
result = ast.literal_eval(user_input)

# ✅ 更安全：JSON 解析
import json
result = json.loads(user_input)
```

### XSS 防护
```python
# ❌ 危险：直接输出用户输入
html = f"<div>{user_input}</div>"

# ✅ 安全：HTML 转义
import html
html = f"<div>{html.escape(user_input)}</div>"

# ✅ 安全：使用模板引擎（自动转义）
# Jinja2: {{ user_input }}
```

## 认证授权

### JWT 安全
```python
# ✅ 使用强签名算法
import jwt
token = jwt.encode(payload, secret, algorithm="HS256")

# ❌ 避免：alg:none 攻击
# 始终验证算法
jwt.decode(token, secret, algorithms=["HS256"])
```

### 密码存储
```python
# ❌ 危险：明文存储
db.save(user, password=password)

# ✅ 安全：bcrypt 哈希
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# ❌ 危险：弱哈希
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()

# ✅ 安全：Argon2（推荐）
from argon2 import PasswordHasher
ph = PasswordHasher()
hashed = ph.hash(password)
```

## 加密最佳实践

### 对称加密
```python
# ✅ AES-GCM（认证加密）
from cryptography.fernet import Fernet
key = Fernet.generate_key()
f = Fernet(key)
encrypted = f.encrypt(data)

# ❌ 避免：ECB 模式（不隐藏模式）
# ❌ 避免：自实现加密算法
```

### 随机数
```python
# ❌ 危险：伪随机（可预测）
import random
token = random.randint(100000, 999999)

# ✅ 安全：加密随机
import secrets
token = secrets.token_hex(32)
session_id = secrets.token_urlsafe(16)
```

## 敏感数据处理

### 日志脱敏
```python
def mask_sensitive(data: str) -> str:
    """脱敏处理：隐藏敏感字段"""
    patterns = {
        'phone': (r'\d{11}', '*******1234'),  # 手机号
        'id_card': (r'\d{18}', '******************'),
        'credit_card': (r'\d{16}', '**** **** **** 1234'),
        'email': (r'[\w\.-]+@[\w\.-]+', '***@***.***'),
    }
    for pattern, replacement in patterns.items():
        data = re.sub(pattern[0], replacement[1], data)
    return data
```

### 敏感信息检测
```python
# 扫描代码中的硬编码敏感信息
SENSITIVE_PATTERNS = [
    (r'(password|passwd|pwd)\s*[=:]\s*["\'][^"\']+["\']', "password"),
    (r'(api_key|apikey)\s*[=:]\s*["\'][^"\']+["\']', "api_key"),
    (r'(secret|token)\s*[=:]\s*["\'][^"\']+["\']', "secret"),
    (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', "private_key"),
]
```
