"""Code Generator 单元测试"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.code_generator import CodeGenerator, APIDocGenerator


class TestCodeGenerator:
    """CodeGenerator 测试"""

    def setup_method(self):
        self.gen = CodeGenerator()

    def test_generate_fastapi(self):
        result = self.gen.generate_from_description("创建一个 API", "python", "FastAPI")
        assert "FastAPI" in result.code
        assert "fastapi" in result.dependencies

    def test_generate_flask(self):
        result = self.gen.generate_from_description("创建一个 API", "python", "Flask")
        assert "Flask" in result.code
        assert "flask" in result.dependencies

    def test_generate_crud(self):
        result = self.gen.generate_from_description("CRUD 增删改查", "python")
        assert "CRUD" in result.code or "crud" in result.code.lower()

    def test_generate_test_class(self):
        result = self.gen.generate_from_description("测试类", "python")
        assert "pytest" in result.code
        assert "TestExample" in result.code

    def test_generate_express(self):
        result = self.gen.generate_from_description("create an API", "javascript", "Express")
        assert "express" in result.code
        assert "express" in result.dependencies

    def test_generate_react_ts(self):
        result = self.gen.generate_from_description("React 组件", "typescript", "React")
        assert "React" in result.code
        assert "interface" in result.code

    def test_generate_spring_boot(self):
        result = self.gen.generate_from_description("Spring Boot API", "java", "Spring Boot")
        assert "Spring" in result.code or "RestController" in result.code

    def test_generate_gin(self):
        result = self.gen.generate_from_description("Gin API", "go", "Gin")
        assert "gin" in result.code

    def test_complete_function_python(self):
        result = self.gen.complete_function("def hello(name)", "python")
        assert "pass" in result.completion or "TODO" in result.completion
        assert result.full_code.startswith("def hello")

    def test_complete_function_js(self):
        result = self.gen.complete_function("function hello(name) {", "javascript")
        assert result.full_code.startswith("function hello")

    def test_generate_comments_python(self):
        code = "def add(a, b):\n    return a + b"
        result = self.gen.generate_comments(code, "python")
        assert '"""' in result or "TODO" in result

    def test_generate_comments_js(self):
        code = "function add(a, b) {\n    return a + b;\n}"
        result = self.gen.generate_comments(code, "javascript")
        assert "TODO" in result or "//" in result


class TestAPIDocGenerator:
    """APIDocGenerator 测试"""

    def setup_method(self):
        self.doc_gen = APIDocGenerator()

    def test_extract_fastapi_endpoints(self):
        code = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/items")
async def get_items():
    """获取所有 items"""
    pass

@app.post("/items")
async def create_item():
    """创建 item"""
    pass
'''
        result = self.doc_gen.generate(code, "python", "markdown")
        assert "items" in result.documentation
        assert "GET" in result.documentation

    def test_extract_express_endpoints(self):
        code = '''
app.get("/users", (req, res) => {
    res.json([]);
});
app.post("/users", (req, res) => {
    res.json({});
});
'''
        result = self.doc_gen.generate(code, "javascript", "markdown")
        assert "users" in result.documentation

    def test_openapi_format(self):
        code = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
async def health():
    pass
'''
        result = self.doc_gen.generate(code, "python", "openapi")
        assert '"openapi": "3.0.0"' in result.documentation

    def test_no_endpoints_found(self):
        code = "x = 1\ny = 2\n"
        result = self.doc_gen.generate(code, "python", "markdown")
        assert "未检测到" in result.documentation
