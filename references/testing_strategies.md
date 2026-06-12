# 测试策略指南

## 测试金字塔

```
        /\
       /  \        E2E 测试（少量）
      /────\
     /      \      集成测试（适量）
    /────────\
   /          \    单元测试（大量）
  /────────────\
```

**比例建议**：单元测试 70% / 集成测试 20% / E2E 测试 10%

## 单元测试策略

### AAA 模式（Arrange-Act-Assert）
```python
def test_user_creation():
    # Arrange: 准备测试数据和前置条件
    user_data = {"name": "Alice", "email": "alice@example.com"}
    db = MockDatabase()

    # Act: 执行被测试的操作
    user = create_user(db, user_data)

    # Assert: 验证结果
    assert user.name == "Alice"
    assert user.id is not None
    db.save.assert_called_once()
```

### 边界值分析
```python
# 等价类划分 + 边界值
@pytest.mark.parametrize("input_val,expected", [
    (0, "zero"),           # 下边界
    (1, "positive"),       # 最小正常值
    (100, "positive"),     # 正常值
    (-1, "negative"),      # 上边界（负方向）
    (999999, "positive"),  # 大数值
    (None, "error"),       # 空值
])
def test_classify_number(input_val, expected):
    assert classify(input_val) == expected
```

### Mock 与 Stub
```python
from unittest.mock import Mock, patch

# 使用 patch 替换外部依赖
@patch("module.requests.get")
def test_api_call(mock_get):
    mock_get.return_value.json.return_value = {"status": "ok"}
    result = fetch_data("https://api.example.com")
    assert result["status"] == "ok"
    mock_get.assert_called_once_with("https://api.example.com")
```

## 集成测试策略

### API 端点测试
```python
def test_create_user_api(client):
    """测试用户创建 API 的完整流程"""
    response = client.post("/api/users", json={
        "name": "Bob",
        "email": "bob@example.com"
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Bob"

    # 验证数据确实写入数据库
    user = db.query("SELECT * FROM users WHERE name = ?", "Bob")
    assert user is not None
```

### 数据库集成测试
```python
@pytest.fixture
def test_db():
    """创建测试用数据库"""
    db = create_test_database()
    yield db
    db.drop_all()  # 清理

def test_user_repository(test_db):
    repo = UserRepository(test_db)
    user = repo.create(name="Test", email="test@example.com")
    found = repo.find_by_id(user.id)
    assert found.name == "Test"
```

## 异常测试

### 异常类型验证
```python
import pytest

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_invalid_input():
    with pytest.raises(ValueError, match="must be positive"):
        process(-1)

def test_api_failure():
    with pytest.raises(APIError) as exc_info:
        fetch_external_data(timeout=1)
    assert "timeout" in str(exc_info.value).lower()
```

## 测试数据管理

### Fixture 模式
```python
@pytest.fixture
def sample_user():
    """标准用户 fixture"""
    return User(name="Alice", email="alice@test.com", role="user")

@pytest.fixture
def admin_user():
    """管理员用户 fixture"""
    return User(name="Admin", email="admin@test.com", role="admin")

def test_user_can_edit_own_profile(sample_user):
    assert can_edit(sample_user, sample_user) == True

def test_user_cannot_edit_other_profile(sample_user, admin_user):
    assert can_edit(sample_user, admin_user) == False
```

### 工厂模式（Factory Pattern）
```python
import factory

class UserFactory(factory.Factory):
    class Meta:
        model = User

    name = factory.Faker("name")
    email = factory.Faker("email")
    role = "user"

# 生成测试数据
user = UserFactory()              # 随机数据
admin = UserFactory(role="admin") # 指定字段
```

## 测试覆盖率

### 覆盖率目标
| 层级 | 行覆盖率 | 分支覆盖率 |
|------|----------|------------|
| 核心模块 | ≥90% | ≥85% |
| 业务逻辑 | ≥80% | ≥75% |
| 工具函数 | ≥95% | ≥90% |

### 覆盖率分析
```bash
# Python (pytest-cov)
pytest --cov=src --cov-report=html

# JavaScript (Jest)
jest --coverage --coverageReporters=html

# Go
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## 测试命名规范

### 命名模式
```
test_<function>_<scenario>_<expected>
```

| 场景 | 示例 |
|------|------|
| 正常路径 | `test_create_user_valid_input` |
| 边界值 | `test_create_user_empty_name` |
| 异常 | `test_create_user_duplicate_email` |
| 状态转换 | `test_cancel_order_refunds_balance` |
