#!/usr/bin/env python3
"""
Code Generator & Completer — 代码生成与补全引擎
功能：自然语言→代码生成、函数补全、注释自动生成、接口文档生成
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta


@dataclass
class GeneratedCode:
    description: str
    language: str
    code: str
    explanation: str
    dependencies: List[str]

    def to_dict(self):
        return asdict(self)


@dataclass
class CompletionResult:
    original_code: str
    language: str
    completion: str
    full_code: str
    confidence: str

    def to_dict(self):
        return asdict(self)


@dataclass
class DocResult:
    source_code: str
    language: str
    doc_format: str  # markdown / openapi / jsdoc / javadoc
    documentation: str

    def to_dict(self):
        return asdict(self)


class CodeGenerator:
    """代码生成与补全引擎"""

    LANGUAGE_FRAMEWORKS = {
        "python": ["FastAPI", "Flask", "Django", "pytest"],
        "javascript": ["Express", "React", "Vue", "Jest"],
        "typescript": ["Express", "React", "NestJS", "Jest"],
        "java": ["Spring Boot", "JUnit"],
        "go": ["Gin", "Echo", "Go test"],
    }

    def generate_from_description(self, description: str, language: str,
                                  framework: str = "") -> GeneratedCode:
        """根据自然语言描述生成代码"""

        code = ""
        deps = []
        explanation = ""

        if language == "python":
            code, deps, explanation = self._gen_python(description, framework)
        elif language in ("javascript", "typescript"):
            code, deps, explanation = self._gen_js(description, framework, language)
        elif language == "java":
            code, deps, explanation = self._gen_java(description, framework)
        elif language == "go":
            code, deps, explanation = self._gen_go(description, framework)
        else:
            code = f"# TODO: 根据描述生成 {language} 代码\n# {description}"
            explanation = f"请提供更详细的 {language} 代码需求"

        return GeneratedCode(
            description=description,
            language=language,
            code=code.strip(),
            explanation=explanation,
            dependencies=deps,
        )

    def _gen_python(self, desc: str, framework: str) -> Tuple[str, List[str], str]:
        """Python 代码生成"""
        desc_lower = desc.lower()
        deps = []

        if "api" in desc_lower or "接口" in desc_lower or "endpoint" in desc_lower:
            if framework == "FastAPI" or "fastapi" in desc_lower:
                deps = ["fastapi", "pydantic"]
                code = f'''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="{desc}", version="1.0.0")


class RequestModel(BaseModel):
    """请求模型"""
    name: str
    description: Optional[str] = None


class ResponseModel(BaseModel):
    """响应模型"""
    id: int
    name: str
    status: str


@app.post("/api/resource", response_model=ResponseModel, summary="创建资源")
async def create_resource(req: RequestModel):
    """
    根据描述创建新资源

    Args:
        req: 请求体，包含名称和可选描述

    Returns:
        创建的资源信息

    Raises:
        HTTPException: 当参数无效时返回 400
    """
    if not req.name:
        raise HTTPException(status_code=400, detail="name 不能为空")

    # TODO: 实现业务逻辑
    return ResponseModel(id=1, name=req.name, status="created")


@app.get("/api/resource/{{resource_id}}", summary="获取资源")
async def get_resource(resource_id: int):
    """根据 ID 获取资源详情"""
    # TODO: 从数据库查询
    return {{"id": resource_id, "name": "example"}}


@app.get("/", summary="健康检查")
async def health_check():
    return {{"status": "healthy", "version": "1.0.0"}}
'''
                explanation = "生成 FastAPI 应用骨架，包含请求/响应模型、CRUD 端点、错误处理"

            elif framework == "Flask" or "flask" in desc_lower:
                deps = ["flask"]
                code = f'''from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/api/resource", methods=["POST"])
def create_resource():
    """创建资源"""
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({{"error": "name 不能为空"}}), 400

    # TODO: 实现业务逻辑
    return jsonify({{"id": 1, "name": data["name"], "status": "created"}}), 201


@app.route("/api/resource/<int:resource_id>", methods=["GET"])
def get_resource(resource_id):
    """获取资源详情"""
    return jsonify({{"id": resource_id, "name": "example"}})


if __name__ == "__main__":
    app.run(debug=True, port=8000)
'''
                explanation = "生成 Flask 应用骨架，包含 POST/GET 路由和 CORS 支持"

            else:
                deps = ["flask"]
                code = f'''from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/api/resource", methods=["POST"])
def create_resource():
    """创建资源"""
    data = request.get_json()
    if not data:
        return jsonify({{"error": "请求体不能为空"}}), 400

    # TODO: 实现业务逻辑
    return jsonify({{"id": 1, "status": "created"}}), 201


if __name__ == "__main__":
    app.run(debug=True)
'''
                explanation = "生成基础 Flask API 骨架"

        elif "crud" in desc_lower or "增删改查" in desc:
            deps = ["sqlalchemy"]
            code = f'''from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
engine = create_engine("sqlite:///app.db")
Session = sessionmaker(bind=engine)


class Item(Base):
    """数据模型"""
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))


class ItemCRUD:
    """CRUD 操作封装"""

    def create(self, name: str, description: str = "") -> Item:
        session = Session()
        item = Item(name=name, description=description)
        session.add(item)
        session.commit()
        session.refresh(item)
        session.close()
        return item

    def get(self, item_id: int) -> Optional[Item]:
        session = Session()
        item = session.query(Item).filter(Item.id == item_id).first()
        session.close()
        return item

    def update(self, item_id: int, name: str = "", description: str = "") -> Optional[Item]:
        session = Session()
        item = session.query(Item).filter(Item.id == item_id).first()
        if item:
            if name:
                item.name = name
            if description:
                item.description = description
            session.commit()
            session.refresh(item)
        session.close()
        return item

    def delete(self, item_id: int) -> bool:
        session = Session()
        item = session.query(Item).filter(Item.id == item_id).first()
        if item:
            session.delete(item)
            session.commit()
            session.close()
            return True
        session.close()
        return False


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    crud = ItemCRUD()
    # 测试
    item = crud.create("测试项目", "这是一个测试")
    print(f"创建成功: {{item.id}} - {{item.name}}")
'''
            explanation = "生成基于 SQLAlchemy 的完整 CRUD 操作类"

        elif "test" in desc_lower or "测试" in desc:
            deps = ["pytest"]
            code = f'''import pytest


class TestExample:
    """测试类"""

    def setup_method(self):
        """每个测试方法执行前运行"""
        self.data = {{"key": "value"}}

    def teardown_method(self):
        """每个测试方法执行后运行"""
        pass

    def test_basic(self):
        """基本功能测试"""
        assert self.data["key"] == "value"

    def test_with_params(self):
        """参数化测试场景"""
        test_cases = [
            (1, 2, 3),
            (0, 0, 0),
            (-1, 1, 0),
        ]
        for a, b, expected in test_cases:
            assert a + b == expected

    def test_exception(self):
        """异常场景测试"""
        with pytest.raises(ValueError):
            raise ValueError("test error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
            explanation = "生成 pytest 测试类，包含 setup/teardown、参数化、异常测试"

        else:
            code = f'''"""
{desc}
自动生成的代码模块
"""


class Service:
    """服务类"""

    def __init__(self):
        self.config = {{}}

    def process(self, data: dict) -> dict:
        """
        处理数据

        Args:
            data: 输入数据字典

        Returns:
            处理结果字典
        """
        # TODO: 实现业务逻辑
        return {{"status": "success", "data": data}}


if __name__ == "__main__":
    service = Service()
    result = service.process({{"test": "data"}})
    print(result)
'''
            explanation = "生成基础 Python 服务类骨架，可根据具体需求扩展"

        return code, deps, explanation

    def _gen_js(self, desc: str, framework: str, lang: str) -> Tuple[str, List[str], str]:
        """JavaScript/TypeScript 代码生成"""
        suffix = "ts" if lang == "typescript" else "js"
        deps = []

        if "api" in desc.lower() or "接口" in desc:
            if framework == "Express" or "express" in desc.lower():
                deps = ["express", "cors"]
                code = f'''const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

/**
 * 创建资源
 * @route POST /api/resource
 * @param {{Object}} req.body - 请求体
 * @returns {{Object}} 创建的资源信息
 */
app.post("/api/resource", (req, res) => {{
    const {{ name, description }} = req.body;

    if (!name) {{
        return res.status(400).json({{ error: "name 不能为空" }});
    }}

    // TODO: 实现业务逻辑
    res.status(201).json({{ id: 1, name, status: "created" }});
}});

/**
 * 获取资源详情
 * @route GET /api/resource/:id
 * @returns {{Object}} 资源信息
 */
app.get("/api/resource/:id", (req, res) => {{
    const {{ id }} = req.params;
    // TODO: 从数据库查询
    res.json({{ id: parseInt(id), name: "example" }});
}});

const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {{
    console.log(`Server running on port ${{PORT}}`);
}});
'''
                explanation = "生成 Express.js API 骨架，包含路由和错误处理"

        elif "react" in desc.lower() or "组件" in desc:
            if lang == "typescript":
                deps = ["react", "@types/react"]
                code = f'''import React, {{ useState, useEffect }} from "react";

interface Props {{
    title: string;
    onAction?: (data: string) => void;
}}

const Component: React.FC<Props> = ({{ title, onAction }}) => {{
    const [data, setData] = useState<string>("");
    const [loading, setLoading] = useState<boolean>(false);

    useEffect(() => {{
        // TODO: 组件挂载时执行
        console.log("Component mounted");
    }}, []);

    const handleAction = async () => {{
        setLoading(true);
        try {{
            // TODO: 实现异步操作
            onAction?.(data);
        }} catch (error) {{
            console.error("操作失败:", error);
        }} finally {{
            setLoading(false);
        }}
    }};

    return (
        <div className="component">
            <h2>{{title}}</h2>
            <input
                value={{data}}
                onChange={{e => setData(e.target.value)}}
                placeholder="请输入"
            />
            <button onClick={{handleAction}} disabled={{loading}}>
                {{loading ? "处理中..." : "提交"}}
            </button>
        </div>
    );
}};

export default Component;
'''
            else:
                deps = ["react"]
                code = f'''import React, {{ useState, useEffect }} from "react";

function Component({{ title, onAction }}) {{
    const [data, setData] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {{
        console.log("Component mounted");
    }}, []);

    const handleAction = async () => {{
        setLoading(true);
        try {{
            onAction?.(data);
        }} catch (error) {{
            console.error("操作失败:", error);
        }} finally {{
            setLoading(false);
        }}
    }};

    return (
        <div className="component">
            <h2>{{title}}</h2>
            <input
                value={{data}}
                onChange={{e => setData(e.target.value)}}
                placeholder="请输入"
            />
            <button onClick={{handleAction}} disabled={{loading}}>
                {{loading ? "处理中..." : "提交"}}
            </button>
        </div>
    );
}}

export default Component;
'''
            explanation = "生成 React 函数组件，包含状态管理、副作用处理和 TypeScript 类型"

        else:
            deps = []
            code = f'''/**
 * {desc}
 * @description 自动生成的 {lang} 代码
 */

class Service {{
    constructor() {{
        this.config = {{}};
    }}

    /**
     * 处理数据
     * @param {{Object}} data - 输入数据
     * @returns {{Object}} 处理结果
     */
    process(data) {{
        // TODO: 实现业务逻辑
        return {{ status: "success", data }};
    }}
}}

module.exports = Service;
'''
            explanation = f"生成基础 {lang} 服务类"

        return code, deps, explanation

    def _gen_java(self, desc: str, framework: str) -> Tuple[str, List[str], str]:
        """Java 代码生成"""
        if framework == "Spring Boot" or "spring" in desc.lower():
            deps = ["spring-boot-starter-web", "spring-boot-starter-validation"]
            code = f'''package com.example.demo.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;

@RestController
@RequestMapping("/api/resource")
public class ResourceController {{

    /**
     * 创建资源
     * @param request 请求体
     * @return 创建的资源
     */
    @PostMapping
    public ResponseEntity<ResourceResponse> create(
            @Valid @RequestBody ResourceRequest request) {{
        // TODO: 实现业务逻辑
        ResourceResponse response = new ResourceResponse();
        response.setId(1L);
        response.setName(request.getName());
        response.setStatus("created");
        return ResponseEntity.ok(response);
    }}

    /**
     * 获取资源详情
     * @param id 资源 ID
     * @return 资源信息
     */
    @GetMapping("/{{id}}")
    public ResponseEntity<ResourceResponse> get(@PathVariable Long id) {{
        // TODO: 从数据库查询
        return ResponseEntity.ok(new ResourceResponse(id, "example", "active"));
    }}

    /**
     * 删除资源
     * @param id 资源 ID
     * @return 204 No Content
     */
    @DeleteMapping("/{{id}}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {{
        // TODO: 实现删除逻辑
        return ResponseEntity.noContent().build();
    }}
}}

// 请求 DTO
class ResourceRequest {{
    @NotBlank(message = "name 不能为空")
    private String name;

    private String description;

    // getters and setters
}}

// 响应 DTO
class ResourceResponse {{
    private Long id;
    private String name;
    private String status;

    // constructors, getters and setters
}}
'''
            explanation = "生成 Spring Boot REST Controller，包含 CRUD 端点和 DTO"
        else:
            deps = []
            code = f'''/**
 * {desc}
 */
public class Service {{
    /**
     * 处理数据
     * @param data 输入数据
     * @return 处理结果
     */
    public Result process(Data data) {{
        // TODO: 实现业务逻辑
        return Result.success(data);
    }}
}}
'''
            explanation = "生成基础 Java 服务类"

        return code, deps, explanation

    def _gen_go(self, desc: str, framework: str) -> Tuple[str, List[str], str]:
        """Go 代码生成"""
        if framework == "Gin" or "gin" in desc.lower():
            deps = ["github.com/gin-gonic/gin"]
            code = f'''package main

import (
    "net/http"
    "github.com/gin-gonic/gin"
)

type ResourceRequest struct {{
    Name        string `json:"name" binding:"required"`
    Description string `json:"description"`
}}

type ResourceResponse struct {{
    ID      int64  `json:"id"`
    Name    string `json:"name"`
    Status  string `json:"status"`
}}

func CreateResource(c *gin.Context) {{
    var req ResourceRequest
    if err := c.ShouldBindJSON(&req); err != nil {{
        c.JSON(http.StatusBadRequest, gin.H{{"error": err.Error()}})
        return
    }}

    // TODO: 实现业务逻辑
    resp := ResourceResponse{{ID: 1, Name: req.Name, Status: "created"}}
    c.JSON(http.StatusCreated, resp)
}}

func GetResource(c *gin.Context) {{
    id := c.Param("id")
    // TODO: 从数据库查询
    resp := ResourceResponse{{ID: 1, Name: "example", Status: "active"}}
    c.JSON(http.StatusOK, resp)
}}

func main() {{
    r := gin.Default()
    r.POST("/api/resource", CreateResource)
    r.GET("/api/resource/:id", GetResource)
    r.Run(":8000")
}}
'''
            explanation = "生成 Gin 框架 API 骨架，包含路由绑定和请求验证"
        else:
            deps = []
            code = f'''package main

import "fmt"

// Service 服务结构体
type Service struct {{
    config map[string]string
}}

// Process 处理数据
func (s *Service) Process(data map[string]interface{{}}) map[string]interface{{}} {{
    // TODO: 实现业务逻辑
    return map[string]interface{{}}{{
        "status": "success",
        "data": data,
    }}
}}

func main() {{
    svc := &Service{{}}
    result := svc.Process(map[string]interface{{}}{{"test": "data"}})
    fmt.Println(result)
}}
'''
            explanation = "生成基础 Go 服务类"

        return code, deps, explanation

    def complete_function(self, partial_code: str, language: str) -> CompletionResult:
        """补全不完整的函数/代码"""
        code = partial_code.strip()

        if language == "python":
            if not code.endswith(":"):
                code += ":"
            completion = '''
    """TODO: 添加函数文档"""
    # TODO: 实现函数逻辑
    pass
'''
        elif language in ("javascript", "typescript"):
            completion = '''
    // TODO: 实现函数逻辑
    return null;
};'''
        elif language == "java":
            completion = '''
    // TODO: 实现方法逻辑
    return null;
}'''
        else:
            completion = "\n// TODO: 实现"

        full_code = code + completion
        return CompletionResult(
            original_code=partial_code,
            language=language,
            completion=completion.strip(),
            full_code=full_code,
            confidence="中",
        )

    def generate_comments(self, code: str, language: str) -> str:
        """为代码自动生成注释"""
        lines = code.split("\n")
        commented = []

        for line in lines:
            stripped = line.strip()

            if language == "python":
                if stripped.startswith("def ") and '"""' not in line and "##" not in line:
                    # 提取函数名
                    match = re.match(r"def\s+(\w+)\s*\(([^)]*)\)", stripped)
                    if match:
                        fn_name = match.group(1)
                        params = [p.strip().split("=")[0].split(":")[0].strip()
                                  for p in match.group(2).split(",") if p.strip()]
                        commented.append(line)
                        commented.append(f'    """TODO: {fn_name} 函数描述')
                        if params:
                            commented.append(f"    Args:")
                            for p in params:
                                if p and p != "self":
                                    commented.append(f"        {p}: TODO 参数描述")
                        commented.append('    Returns:')
                        commented.append('        TODO 返回值描述')
                        commented.append('    """')
                        continue
                elif stripped.startswith("class ") and '"""' not in line:
                    class_name = re.search(r"class\s+(\w+)", stripped)
                    if class_name:
                        commented.append(line)
                        commented.append(f'    """{class_name.group(1)} 类描述"""')
                        continue

            elif language in ("javascript", "typescript"):
                if stripped.startswith("function ") or stripped.startswith("const ") or stripped.startswith("async "):
                    commented.append(f"// TODO: {stripped[:50]}")
                    commented.append(line)
                    continue
                elif stripped.startswith("class "):
                    commented.append(f"/** {stripped[6:].split('{')[0].strip()} 类描述 */")
                    commented.append(line)
                    continue

            commented.append(line)

        return "\n".join(commented)


class APIDocGenerator:
    """API 接口文档生成器"""

    def generate(self, source_code: str, language: str,
                 format: str = "markdown") -> DocResult:
        """从源代码提取 API 端点并生成文档"""

        endpoints = []

        if language == "python":
            endpoints = self._extract_fastapi_endpoints(source_code)
            if not endpoints:
                endpoints = self._extract_flask_endpoints(source_code)
        elif language in ("javascript", "typescript"):
            endpoints = self._extract_express_endpoints(source_code)
        elif language == "java":
            endpoints = self._extract_spring_endpoints(source_code)
        elif language == "go":
            endpoints = self._extract_gin_endpoints(source_code)

        if format == "openapi":
            documentation = self._to_openapi(endpoints, language)
        elif format == "markdown":
            documentation = self._to_markdown(endpoints, language)
        else:
            documentation = self._to_markdown(endpoints, language)

        return DocResult(
            source_code=source_code,
            language=language,
            doc_format=format,
            documentation=documentation,
        )

    def _extract_fastapi_endpoints(self, code: str) -> List[Dict]:
        """提取 FastAPI 端点"""
        endpoints = []
        patterns = [
            (r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']\s*\)', "path"),
            (r'async\s+def\s+(\w+)\s*\(', "handler"),
        ]

        path_lines = {}
        for i, line in enumerate(code.split("\n")):
            for pat, key in patterns:
                match = re.search(pat, line)
                if match:
                    if key == "path":
                        method, path = match.group(1), match.group(2)
                        path_lines[i] = {"method": method.upper(), "path": path, "handler": ""}
                    elif key == "handler" and i - 1 in path_lines:
                        path_lines[i - 1]["handler"] = match.group(1)

        for idx, ep in path_lines.items():
            # 提取 docstring
            doc_lines = code.split("\n")[idx + 1:idx + 6]
            docstring = ""
            for dl in doc_lines:
                stripped = dl.strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring = stripped.strip('"""').strip("'''")
                    break
                elif stripped.startswith('"') or stripped.startswith("'"):
                    docstring = stripped.strip('"').strip("'")
                    break

            endpoints.append({
                "method": ep["method"],
                "path": ep["path"],
                "handler": ep["handler"],
                "description": docstring or "暂无描述",
            })

        return endpoints

    def _extract_flask_endpoints(self, code: str) -> List[Dict]:
        """提取 Flask 端点"""
        endpoints = []
        pattern = r'@app\.route\(["\']([^"\']+)["\'],\s*methods\s*=\s*\[([^\]]+)\]\)'

        for match in re.finditer(pattern, code):
            path = match.group(1)
            methods_str = match.group(2)
            methods = [m.strip().strip('"').strip("'") for m in methods_str.split(",")]

            # 查找下一行的函数名
            rest = code[match.end():match.end() + 200]
            fn_match = re.search(r"def\s+(\w+)", rest)

            endpoints.append({
                "method": methods[0] if methods else "GET",
                "path": path,
                "handler": fn_match.group(1) if fn_match else "unknown",
                "description": "暂无描述",
            })

        return endpoints

    def _extract_express_endpoints(self, code: str) -> List[Dict]:
        """提取 Express.js 端点"""
        endpoints = []
        pattern = r'app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'

        for match in re.finditer(pattern, code):
            method = match.group(1).upper()
            path = match.group(2)

            # 提取注释中的描述
            start = max(0, match.start() - 200)
            context = code[start:match.start()]
            comment_match = re.search(r'/\*\*([^*]+)\*/', context)
            desc = comment_match.group(1).strip() if comment_match else "暂无描述"

            endpoints.append({
                "method": method,
                "path": path,
                "handler": "",
                "description": desc,
            })

        return endpoints

    def _extract_spring_endpoints(self, code: str) -> List[Dict]:
        """提取 Spring Boot 端点"""
        endpoints = []
        patterns = [
            (r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*["\']([^"\']+)["\']\s*\)', "annotation"),
            (r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']\s*\)', "base"),
        ]

        base_path = ""
        lines = code.split("\n")

        for i, line in enumerate(lines):
            for pat, ptype in patterns:
                match = re.search(pat, line)
                if match:
                    if ptype == "base":
                        base_path = match.group(1)
                    else:
                        annotation = match.group(1)
                        path = match.group(2)
                        full_path = base_path + path

                        # 查找方法签名
                        sig_match = re.search(r'(?:public|private)\s+\w+\s+(\w+)\s*\(', lines[i + 1] if i + 1 < len(lines) else "")
                        handler = sig_match.group(1) if sig_match else "unknown"

                        # 提取注释
                        doc = ""
                        for j in range(max(0, i - 3), i):
                            comment = lines[j].strip()
                            if comment.startswith("/**") or comment.startswith("*") or comment.startswith("//"):
                                doc += comment.strip("*/ ").strip()
                            else:
                                break

                        method_map = {
                            "GetMapping": "GET", "PostMapping": "POST",
                            "PutMapping": "PUT", "DeleteMapping": "DELETE",
                            "PatchMapping": "PATCH",
                        }
                        endpoints.append({
                            "method": method_map.get(annotation, "GET"),
                            "path": full_path,
                            "handler": handler,
                            "description": doc or "暂无描述",
                        })

        return endpoints

    def _extract_gin_endpoints(self, code: str) -> List[Dict]:
        """提取 Gin 端点"""
        endpoints = []
        pattern = r'r\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*["\']([^"\']+)["\']'

        for match in re.finditer(pattern, code):
            method = match.group(1).upper()
            path = match.group(2)
            endpoints.append({
                "method": method,
                "path": path,
                "handler": "",
                "description": "暂无描述",
            })

        return endpoints

    def _to_markdown(self, endpoints: List[Dict], language: str) -> str:
        """生成 Markdown 格式 API 文档"""
        if not endpoints:
            return "# API 文档\n\n未检测到 API 端点。\n"

        lines = []
        lines.append(f"# API 文档\n")
        lines.append(f"> 自动生成于 {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')} | "
                     f"语言: {language} | 端点数量: {len(endpoints)}\n")

        # 按方法分组
        methods_order = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        grouped = {}
        for ep in endpoints:
            grouped.setdefault(ep["method"], []).append(ep)

        for method in methods_order:
            if method not in grouped:
                continue
            lines.append(f"## {method}\n")
            for ep in grouped[method]:
                lines.append(f"### {ep['path']}\n")
                lines.append(f"| 属性 | 值 |")
                lines.append(f"|------|-----|")
                lines.append(f"| 方法 | {ep['method']} |")
                lines.append(f"| 路径 | `{ep['path']}` |")
                if ep["handler"]:
                    lines.append(f"| 处理器 | `{ep['handler']}` |")
                lines.append(f"| 描述 | {ep['description']} |")
                lines.append("")
                lines.append("**请求参数**:\n")
                lines.append("| 参数 | 类型 | 必填 | 说明 |")
                lines.append("|------|------|------|------|")
                lines.append("| TODO | TODO | TODO | TODO |")
                lines.append("")
                lines.append("**响应示例**:\n")
                lines.append("```json")
                lines.append('{"code": 200, "message": "success", "data": {}}')
                lines.append("```\n")

        return "\n".join(lines)

    def _to_openapi(self, endpoints: List[Dict], language: str) -> str:
        """生成 OpenAPI 3.0 格式文档"""
        if not endpoints:
            return '{"openapi": "3.0.0", "info": {"title": "API", "version": "1.0.0"}, "paths": {}}'

        paths = {}
        for ep in endpoints:
            path_key = ep["path"]
            paths[path_key] = {
                ep["method"].lower(): {
                    "summary": ep["description"],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            },
                        }
                    },
                }
            }

        doc = {
            "openapi": "3.0.0",
            "info": {
                "title": "API 文档",
                "version": "1.0.0",
                "description": f"自动生成于 {datetime.now(timezone(timedelta(hours=8))).isoformat()}",
            },
            "paths": paths,
        }
        return json.dumps(doc, indent=2, ensure_ascii=False)


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="代码生成与补全引擎")
    subparsers = parser.add_subparsers(dest="action", help="子命令")

    # generate 子命令
    gen_parser = subparsers.add_parser("generate", help="根据描述生成代码")
    gen_parser.add_argument("description", help="功能描述")
    gen_parser.add_argument("language", nargs="?", default="python", help="编程语言")
    gen_parser.add_argument("framework", nargs="?", default="", help="框架名称")

    # complete 子命令
    comp_parser = subparsers.add_parser("complete", help="补全函数代码")
    comp_parser.add_argument("code", help="不完整的代码")
    comp_parser.add_argument("language", help="编程语言")

    # comment 子命令
    comment_parser = subparsers.add_parser("comment", help="自动生成注释")
    comment_parser.add_argument("code", help="源代码")
    comment_parser.add_argument("language", help="编程语言")

    # doc 子命令
    doc_parser = subparsers.add_parser("doc", help="生成 API 文档")
    doc_parser.add_argument("code_file", help="源代码文件路径")
    doc_parser.add_argument("language", help="编程语言")
    doc_parser.add_argument("--format", default="markdown",
                            choices=["markdown", "openapi"],
                            help="文档格式 (默认: markdown)")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    gen = CodeGenerator()
    doc_gen = APIDocGenerator()

    if args.action == "generate":
        result = gen.generate_from_description(args.description, args.language, args.framework)
        print(result.code)
        print(f"\n# 依赖: {', '.join(result.dependencies) if result.dependencies else '无'}")
        print(f"# 说明: {result.explanation}")

    elif args.action == "complete":
        result = gen.complete_function(args.code, args.language)
        print(result.full_code)

    elif args.action == "comment":
        result = gen.generate_comments(args.code, args.language)
        print(result)

    elif args.action == "doc":
        try:
            with open(args.code_file, "r", encoding="utf-8") as f:
                source = f.read()
        except FileNotFoundError:
            print(f"错误: 文件 '{args.code_file}' 不存在")
            sys.exit(1)
        except PermissionError:
            print(f"错误: 无权读取文件 '{args.code_file}'")
            sys.exit(1)
        result = doc_gen.generate(source, args.language, args.format)
        print(result.documentation)


if __name__ == "__main__":
    main()
