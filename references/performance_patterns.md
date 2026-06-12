# 性能优化模式库

## 数据库优化

### N+1 查询问题
```python
# ❌ 危险：N+1 查询
for user in users:
    orders = db.query("SELECT * FROM orders WHERE user_id = ?", user.id)

# ✅ 安全：批量查询
user_ids = [u.id for u in users]
orders = db.query(f"SELECT * FROM orders WHERE user_id IN ({','.join('?' * len(user_ids))})", user_ids)
```

### 索引策略
```sql
-- ✅ 覆盖索引（Covering Index）
CREATE INDEX idx_orders_user_status ON orders(user_id, status, created_at);

-- ✅ 联合索引遵循最左前缀原则
-- WHERE a = ? AND b > ? AND c = ? → 索引 (a, b, c)

-- ❌ 避免：索引列上使用函数
WHERE YEAR(created_at) = 2024
-- ✅ 改为范围查询
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'
```

### 批量操作
```python
# ❌ 低效：循环插入
for item in items:
    db.execute("INSERT INTO table (col) VALUES (?)", (item,))

# ✅ 高效：批量插入
db.executemany("INSERT INTO table (col) VALUES (?)", [(item,) for item in items])

# ❌ 低效：循环更新
for id, val in updates:
    db.execute("UPDATE table SET col = ? WHERE id = ?", (val, id))

# ✅ 高效：CASE WHEN
db.execute("""
    UPDATE table SET col = CASE id
        WHEN ? THEN ?
        WHEN ? THEN ?
    END WHERE id IN (?, ?)
""", values)
```

## 缓存策略

### 缓存模式
```python
# Cache-Aside（最常用）
def get_user(user_id):
    user = cache.get(f"user:{user_id}")
    if user is None:
        user = db.query("SELECT * FROM users WHERE id = ?", user_id)
        cache.set(f"user:{user_id}", user, ttl=3600)
    return user

# Write-Through（写一致性）
def update_user(user_id, data):
    db.execute("UPDATE users SET ... WHERE id = ?", user_id)
    cache.set(f"user:{user_id}", data, ttl=3600)
```

### 缓存防护
```python
# 防止缓存穿透
def get_order(order_id):
    cache_key = f"order:{order_id}"
    result = cache.get(cache_key)
    if result is None:
        result = db.query("SELECT * FROM orders WHERE id = ?", order_id)
        if result is None:
            # 缓存空值，防止穿透
            cache.set(cache_key, {"empty": True}, ttl=60)
        else:
            cache.set(cache_key, result, ttl=3600)
    return result

# 防止缓存雪崩：TTL 随机偏移
import random
cache.set(key, value, ttl=3600 + random.randint(0, 300))
```

## 并发优化

### 连接池
```python
# ✅ 使用连接池
from sqlalchemy import create_engine
engine = create_engine(
    "postgresql://...",
    pool_size=10,        # 连接池大小
    max_overflow=5,      # 溢出连接数
    pool_timeout=30,     # 获取连接超时
    pool_recycle=3600,   # 连接回收时间
)
```

### 锁优化
```python
# ❌ 粗粒度锁
lock = threading.Lock()
def process_data(data):
    with lock:
        # 整个函数被锁住
        validate(data)
        transform(data)
        save(data)

# ✅ 细粒度锁
def process_data(data):
    validate(data)  # 无需锁
    with item_lock(data.id):  # 仅锁定相关项
        transform(data)
        save(data)
```

## 内存优化

### 大文件处理
```python
# ❌ 危险：一次性加载大文件
with open("large_file.csv") as f:
    data = f.readlines()  # 可能 OOM

# ✅ 安全：流式读取
with open("large_file.csv") as f:
    for line in f:
        process(line)
```

### 生成器替代列表
```python
# ❌ 低效：构建完整列表
def get_all_users():
    return [db.query(f"SELECT * FROM users LIMIT {i}, 1") for i in range(1000000)]

# ✅ 高效：生成器
def get_all_users():
    for i in range(1000000):
        yield db.query(f"SELECT * FROM users LIMIT {i}, 1")
```

## 算法优化

### 查找优化
```python
# ❌ O(n)：列表查找
if item in large_list:
    process(item)

# ✅ O(1)：集合查找
item_set = set(large_list)
if item in item_set:
    process(item)

# ❌ O(n²)：嵌套循环
for a in list_a:
    for b in list_b:
        if a.id == b.id:
            match(a, b)

# ✅ O(n)：字典查找
b_map = {b.id: b for b in list_b}
for a in list_a:
    if a.id in b_map:
        match(a, b_map[a.id])
```
